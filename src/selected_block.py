from pyglm import glm

import config
CHUNK_SIZE = config.CHUNK_SIZE

from wire import add_wire_to_vertex_biffer

import shaders
import buffers

from blocks import get_block_id, blocks
air_id   = get_block_id('air')
water_id = get_block_id('water')


def get_vertex_data():
	cube_points = []
	for x in (0, 1):
		for z in (0, 1):
			for y in (0, 1):
				cube_points.append([x, y, z])
	
	wire_size = config.SELECTED_BLOCK_LINE_WIDTH
	
	res = []
	for point1 in cube_points:
		x1, y1, z1 = point1
		
		for point2 in cube_points:
			x2, y2, z2 = point2
			
			same_x = x1 == x2
			same_y = y1 == y2
			same_z = z1 == z2
			if int(same_x) + int(same_y) + int(same_z) != 2:
				continue
			
			add_wire_to_vertex_biffer(res, point1, point2, wire_size)
	
	return res


class SelectedBlock:
	def __init__(self, world):
		self.world = world
		self.cam = world.cam
		self.transformation = None
		
		vertex_data = get_vertex_data()
		self.command_list_id = buffers.create(vertex_data, 3, None)
	
	
	def update(self):
		vec3  = glm.vec3
		ivec3 = glm.ivec3
		floor = glm.floor
		
		self.enable = False
		
		world = self.world
		
		pos = vec3(world.player.pos)
		ipos = ivec3(floor(pos))
		
		resource = world.get_resource(*ipos)
		if resource >= 8:
			return
		
		direction = vec3(world.cam.direction)
		
		steps = []
		dist = 1.0
		for i in range(10):
			dist /= 2.0
			steps.append((dist, direction * dist))
		small_dist, small_step = steps[-1]
		
		prev_ipos = ipos
		resource = 0
		cur_dist = 0
		max_dist = 5
		while cur_dist < max_dist:
			for dist, step in steps:
				next_pos = pos + step
				next_ipos = ivec3(floor(next_pos))
				if ipos == next_ipos:
					pos = next_pos
					cur_dist += dist
			
			pos += small_step
			cur_dist += small_dist
			
			next_ipos = ivec3(floor(pos))
			if ipos != next_ipos:
				prev_ipos = ipos
				ipos = next_ipos
				
				resource = world.get_resource(*ipos)
				if resource >= 8:
					self.enable = True
					break
		
		self.resource = resource
		self.pos = ipos
		self.prev_pos = prev_ipos
	
	
	def draw(self):
		if not self.enable:
			return
		
		if self.transformation is None or self.world.projection_view_matrix_is_new:
			self.transformation = glm.translate(self.world.projection_view_matrix, glm.vec3(self.pos))
		
		shaders.set('line')
		shaders.set_mat4('transformation', self.transformation)
		shaders.set_float4('vertexColor', config.SELECTED_BLOCK_COLOR)
		
		buffers.draw(self.command_list_id)
	
	
	def update_near_chunks(self):
		pos = self.pos
		chunk_x = pos.x // CHUNK_SIZE
		chunk_z = pos.z // CHUNK_SIZE
		column_x = pos.x % CHUNK_SIZE
		column_z = pos.z % CHUNK_SIZE
		
		chunks_to_update = []
		chunks = self.world.chunks
		if column_x == 0:
			chunks_to_update.append(chunks[(chunk_x - 1, chunk_z)])
		if column_x == CHUNK_SIZE - 1:
			chunks_to_update.append(chunks[(chunk_x + 1, chunk_z)])
		if column_z == 0:
			chunks_to_update.append(chunks[(chunk_x, chunk_z - 1)])
		if column_z == CHUNK_SIZE - 1:
			chunks_to_update.append(chunks[(chunk_x, chunk_z + 1)])
		
		for chunk in chunks_to_update:
			chunk.reload_model(make_model_instantly = True)
	
	def remove(self):
		pos = self.pos
		chunk_x = pos.x // CHUNK_SIZE
		chunk_z = pos.z // CHUNK_SIZE
		column_x = pos.x % CHUNK_SIZE
		column_z = pos.z % CHUNK_SIZE
		
		world = self.world
		chunk = world.chunks[(chunk_x, chunk_z)]
		column = chunk.columns[(column_x, column_z)]
		
		x, y, z = pos
		start_y = y
		while True:
			if y >= config.CHUNK_HEIGHT:
				break
			
			if y != start_y:
				resource = chunk.get_resource_in_column(column, y)
				if not blocks[resource].diag:
					break
			
			empty_id = air_id
			for dx, dy, dz in [(0, +1, 0), (-1, 0, 0), (+1, 0, 0), (0, 0, -1), (0, 0, +1)]:
				resource = world.get_resource(x + dx, y + dy, z + dz)
				if resource == water_id:
					empty_id = water_id
					break
			
			chunk.set_blocks_in_column(y, 1, empty_id, column = column, make_model_instantly = True)
			y += 1
		
		self.update_near_chunks()
		
		self.update()
		self.transformation = None
	
	
	def add(self, block_id):
		pos = self.pos
		prev_pos = self.prev_pos
		
		cam_pos = glm.vec3(self.cam.player.pos)
		cam_pos = glm.ivec3(glm.floor(cam_pos))
		if prev_pos == cam_pos:
			return
		cam_pos.y -= 1
		if prev_pos == cam_pos:
			return
		
		same_x = pos.x == prev_pos.x
		same_y = pos.y == prev_pos.y
		same_z = pos.z == prev_pos.z
		if int(same_x) + int(same_y) + int(same_z) != 2:
			return
		
		resource = self.world.get_resource(*prev_pos)
		if resource >= 8:
			return
		
		self.world.set_resource(*prev_pos, self.world.block_id)
		self.update_near_chunks()
		
		self.update()
		self.transformation = None
