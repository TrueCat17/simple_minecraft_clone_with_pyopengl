import config
CHUNK_SIZE = config.CHUNK_SIZE

from wire import add_wire_to_vertex_biffer

import shaders
import buffers


def get_vertex_data():
	inc = CHUNK_SIZE // config.CHUNK_BORDER_LINE_COUNT
	
	points = set()
	for i in range(0, CHUNK_SIZE + 1, inc):
		points.add((i, 0))
		points.add((i, CHUNK_SIZE))
		points.add((0, i))
		points.add((CHUNK_SIZE, i))
	
	dist = config.CHUNK_HEIGHT
	wire_size = config.CHUNK_BORDER_LINE_WIDTH
	
	res = []
	for x, z in points:
		point1 = [x, +dist, z]
		point2 = [x, -dist, z]
		add_wire_to_vertex_biffer(res, point1, point2, wire_size)
	
	corners = [(0, 0), (0, CHUNK_SIZE), (CHUNK_SIZE, CHUNK_SIZE), (CHUNK_SIZE, 0)]
	for y in range(0, dist + 1, inc * 2):
		for x1, z1 in corners:
			for x2, z2 in corners:
				same_x = x1 == x2
				same_z = z1 == z2
				if int(same_x) + int(same_z) != 1:
					continue
				
				point1 = [x1, y, z1]
				point2 = [x2, y, z2]
				add_wire_to_vertex_biffer(res, point1, point2, wire_size)
	
	return res


class ChunkBorder:
	def __init__(self, world):
		self.world = world
		self.enable = config.CHUNK_BORDER_ENABLED_DEFAULT
		self.transformation = None
		
		vertex_data = get_vertex_data()
		
		self.command_list_id = buffers.create(vertex_data, 3, None)
	
	def draw(self):
		if not self.enable:
			self.transformation = None
			return
		
		world = self.world
		if self.transformation is None or world.projection_view_matrix_is_new:
			self.transformation = world.projection_view_matrix * world.cam.chunk.model_matrix
		
		shaders.set('line')
		shaders.set_mat4('transformation', self.transformation)
		shaders.set_float4('vertexColor', config.CHUNK_BORDER_COLOR)
		
		buffers.draw(self.command_list_id)
