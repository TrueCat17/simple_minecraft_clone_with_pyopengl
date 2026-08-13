import os
import time

import json
import pickle
import zlib

from pyglm import glm
from OpenGL.GL import *


import config
CHUNK_SIZE = config.CHUNK_SIZE

LAST = CHUNK_SIZE - 1


from blocks import blocks
import landscape

import shaders
import buffers


class Chunk:
	def __init__(self, world, x, z):
		self.world = world
		
		self.x, self.z = x, z
		self.model_matrix = glm.translate(glm.mat4(1.0), glm.vec3(x * CHUNK_SIZE, 0, z * CHUNK_SIZE))
		
		self.has_model = False
		self.model_is_loaded = False
		self.first_loading = True
		self.make_model_instantly = False
		
		self.vertex_data             = self.uv_data             = None
		self.transparent_vertex_data = self.transparent_uv_data = None
		self.water_vertex_data       = self.water_uv_data       = None
		
		self.remove_time = None
		self.transformation = None
		
		group = (x * 23 + z * 17) % 51
		self.data_path  = world.path + 'chunks/%s/%s_%s'              % (group, x, z)
		self.model_path = world.path + 'cached_chunk_models/%s/%s_%s' % (group, x, z)
		
		if not self.read():
			landscape.generate(self)
			self.saved = False
		
		self.set_corner_points()
	
	
	def get_max_y(self):
		min_air_on_top = config.CHUNK_HEIGHT
		for line in self.columns:
			for column in line:
				resource, count = column[-1]
				if resource != 0:
					return config.CHUNK_HEIGHT
				if min_air_on_top > count:
					min_air_on_top = count
		return config.CHUNK_HEIGHT - min_air_on_top
	
	def set_corner_points(self):
		ys = []
		y = self.max_y
		while y >= 0:
			ys.append(y)
			if y % CHUNK_SIZE == 0:
				y -= CHUNK_SIZE
			else:
				y = (y // CHUNK_SIZE) * CHUNK_SIZE
		
		EDGES = (0, CHUNK_SIZE)
		points = self.corner_points = []
		for y in ys:
			for x in EDGES:
				for z in EDGES:
					points.append(glm.vec4(x, y, z, 1))
		
		self.need_update_visible = True
	
	def update_visible(self):
		self.need_update_visible = False
		
		cam = self.world.cam
		dx = abs(self.x - cam.chunk_x)
		dz = abs(self.z - cam.chunk_z)
		if dx <= 2 and dz <= 2:
			self.visible = True
			return
		
		self.visible = False
		
		min_w = 2 ** -10
		neg_min_w = -min_w
		
		transformation = self.transformation
		for point in self.corner_points:
			opengl_screen_point = transformation * point
			
			w = opengl_screen_point.w
			if neg_min_w < w < min_w:
				w = neg_min_w if w < 0.0 else min_w
			
			opengl_screen_point /= w
			x, y, z, w = opengl_screen_point
			
			if -1.0 <= x <= 1.0 and -1.0 <= y <= 1.0 and 0.0 <= z <= 1.0:
				self.visible = True
				return
	
	
	def get_resource(self, x, y, z):
		column = self.columns[x][z]
		return self.get_resource_in_column(column, y)
	
	def get_resource_in_column(self, column, y):
		if y < 0 or y >= config.CHUNK_HEIGHT:
			return 0
		
		tmp_y = 0
		for resource, count in column:
			tmp_y += count
			if tmp_y > y:
				return resource
	
	def set_blocks_in_column(self, y, count, resource, column = None, pos = None, make_model_instantly = False, update_max_y = True):
		if column is None:
			x, z = pos
			column = self.columns[x][z]
		
		if y < 0:
			return
		count = min(count, config.CHUNK_HEIGHT - y)
		if count <= 0:
			return
		
		if update_max_y:
			old_max_y = self.max_y
			update_max_y = (old_max_y <= y + count)
		
		# find index and save [tmp_resource and tmp_count]
		tmp_y = 0
		for i, (tmp_resource, tmp_count) in enumerate(column):
			if tmp_y + tmp_count >= y:
				break
			tmp_y += tmp_count
		
		# divide on 2 parts (if need: bottom size != 0)
		bottom_size = y - tmp_y
		if bottom_size > 0:
			column[i][1] = bottom_size
			i += 1
			column.insert(i, [tmp_resource, tmp_count - bottom_size])
		
		# add new resources
		column.insert(i, [resource, count])
		i += 1
		
		# remove old resources
		removed = 0
		while count > 0:
			if column[i][1] > count:
				column[i][1] -= count
				break
			
			count -= column[i][1]
			column.pop(i)
		
		# optimize
		i = 0
		while i < len(column):
			if column[i][1] == 0:
				column.pop(i)
				continue
			
			if i != len(column) - 1:
				if column[i][0] == column[i + 1][0]:
					column[i][1] += column[i + 1][1]
					column.pop(i + 1)
					continue
			
			i += 1
		
		self.reload_model(make_model_instantly = make_model_instantly)
		
		if update_max_y:
			self.max_y = self.get_max_y()
			if old_max_y != self.max_y:
				self.set_corner_points()
		
		self.saved = False
	
	
	def add_side_left(self, vertex_data, uv_data, x, y, z, resource, count, full_opaque):
		light = 0.8
		
		y_max = y + count
		z1 = z + 1
		if x != 0:
			near_column = self.columns[x - 1][z]
		else:
			near_chunk = self.world.chunks[(self.x - 1, self.z)]
			near_column = near_chunk.columns[LAST][z]
		
		uv = blocks[resource].left_uv
		
		near_y = 0
		for near_resource, near_count in near_column:
			near_y_max = near_y + near_count
			if near_y_max < y:
				near_y = near_y_max
				continue
			
			if near_resource == resource or blocks[near_resource].full_opaque:
				near_y = near_y_max
				if near_y >= y_max:
					return
				continue
			
			tmp_min_y = max(y, near_y)
			tmp_max_y = min(y_max, near_y_max)
			for i in range(tmp_min_y, tmp_max_y):
				i1 = i + 1
				
				vertex_data.extend([
					x, i1, z1, light,
					x, i , z , light,
					x, i1, z , light,
					x, i1, z1, light,
					x, i , z1, light,
					x, i , z , light,
				])
			
			uv_data.extend(uv * (tmp_max_y - tmp_min_y))
			
			near_y = near_y_max
			if near_y >= y_max:
				return
	
	
	def add_side_right(self, vertex_data, uv_data, x, y, z, resource, count, full_opaque):
		light = 0.8
		
		y_max = y + count
		x1 = x + 1
		z1 = z + 1
		if x != LAST:
			near_column = self.columns[x + 1][z]
		else:
			near_chunk = self.world.chunks[(self.x + 1, self.z)]
			near_column = near_chunk.columns[0][z]
		
		uv = blocks[resource].right_uv
		
		near_y = 0
		for near_resource, near_count in near_column:
			near_y_max = near_y + near_count
			if near_y_max < y:
				near_y = near_y_max
				continue
			
			if near_resource == resource or blocks[near_resource].full_opaque:
				near_y = near_y_max
				if near_y >= y_max:
					return
				continue
			
			tmp_min_y = max(y, near_y)
			tmp_max_y = min(y_max, near_y_max)
			for i in range(tmp_min_y, tmp_max_y):
				i1 = i + 1
				
				vertex_data.extend([
					x1, i1, z , light,
					x1, i , z1, light,
					x1, i1, z1, light,
					x1, i1, z , light,
					x1, i , z , light,
					x1, i , z1, light,
				])
			
			uv_data.extend(uv * (tmp_max_y - tmp_min_y))
			
			near_y = near_y_max
			if near_y >= y_max:
				return
	
	
	def add_side_front(self, vertex_data, uv_data, x, y, z, resource, count, full_opaque):
		light = 0.8
		
		y_max = y + count
		x1 = x + 1
		z1 = z + 1
		if z != LAST:
			near_column = self.columns[x][z + 1]
		else:
			near_chunk = self.world.chunks[(self.x, self.z + 1)]
			near_column = near_chunk.columns[x][0]
		
		uv = blocks[resource].front_uv
		
		near_y = 0
		for near_resource, near_count in near_column:
			near_y_max = near_y + near_count
			if near_y_max < y:
				near_y = near_y_max
				continue
			
			if near_resource == resource or blocks[near_resource].full_opaque:
				near_y = near_y_max
				if near_y >= y_max:
					return
				continue
			
			tmp_min_y = max(y, near_y)
			tmp_max_y = min(y_max, near_y_max)
			for i in range(tmp_min_y, tmp_max_y):
				i1 = i + 1
				
				vertex_data.extend([
					x1, i1, z1, light,
					x , i , z1, light,
					x , i1, z1, light,
					x1, i1, z1, light,
					x1, i , z1, light,
					x , i , z1, light,
				])
			
			uv_data.extend(uv * (tmp_max_y - tmp_min_y))
			
			near_y = near_y_max
			if near_y >= y_max:
				return
	
	
	def add_side_back(self, vertex_data, uv_data, x, y, z, resource, count, full_opaque):
		light = 0.8
		
		y_max = y + count
		x1 = x + 1
		if z != 0:
			near_column = self.columns[x][z - 1]
		else:
			near_chunk = self.world.chunks[(self.x, self.z - 1)]
			near_column = near_chunk.columns[x][LAST]
		
		uv = blocks[resource].back_uv
		
		near_y = 0
		for near_resource, near_count in near_column:
			near_y_max = near_y + near_count
			if near_y_max < y:
				near_y = near_y_max
				continue
			
			if near_resource == resource or blocks[near_resource].full_opaque:
				near_y = near_y_max
				if near_y >= y_max:
					return
				continue
			
			tmp_min_y = max(y, near_y)
			tmp_max_y = min(y_max, near_y_max)
			for i in range(tmp_min_y, tmp_max_y):
				i1 = i + 1
				
				vertex_data.extend([
					x,  i1, z, light,
					x1, i , z, light,
					x1, i1, z, light,
					x,  i1, z, light,
					x,  i , z, light,
					x1, i , z, light,
				])
			
			uv_data.extend(uv * (tmp_max_y - tmp_min_y))
			
			near_y = near_y_max
			if near_y >= y_max:
				return
	
	
	def add_top(self, vertex_data, uv_data, x, y, z, resource, count):
		light = 1.0
		
		y += count
		x1 = x + 1
		z1 = z + 1
		
		vertex_data.extend([
			x , y, z1, light,
			x1, y, z , light,
			x1, y, z1, light,
			x , y, z1, light,
			x , y, z , light,
			x1, y, z , light,
		])
		
		uv = blocks[resource].top_uv
		uv_data.extend(uv)
	
	
	def add_bottom(self, vertex_data, uv_data, x, y, z, resource, count):
		light = 0.6
		
		x1 = x + 1
		z1 = z + 1
		
		vertex_data.extend([
			x,  y, z , light,
			x1, y, z1, light,
			x1, y, z , light,
			x,  y, z , light,
			x,  y, z1, light,
			x1, y, z1, light,
		])
		
		uv = blocks[resource].bottom_uv
		uv_data.extend(uv)
	
	
	def add_diag(self, vertex_data, uv_data, x, y, z, resource, count):
		light = 0.8
		
		t = (x * 17 + z * 991) % 5
		x += (t - 2) / 2 / 16
		
		t = (x * 53 + z * 37) % 5
		z += (t - 2) / 2 / 16
		
		block = blocks[resource]
		uv_usual     = block.left_uv
		uv_reflected = block.left_uv_reflected_h
		uv = uv_usual + uv_reflected + uv_reflected + uv_usual
		
		for y in range(y, y + count):
			x1 = x + 1
			y1 = y + 1
			z1 = z + 1
			
			vertex_data.extend([
				x,  y1, z , light,
				x1, y , z1, light,
				x1, y1, z1, light,
				x,  y1, z , light,
				x,  y , z , light,
				x1, y , z1, light,
				
				x1, y1, z1, light,
				x , y , z , light,
				x , y1, z , light,
				x1, y1, z1, light,
				x1, y , z1, light,
				x , y , z , light,
				
				x1, y1, z , light,
				x , y , z1, light,
				x , y1, z1, light,
				x1, y1, z , light,
				x1, y , z , light,
				x , y , z1, light,
				
				x , y1, z1, light,
				x1, y , z , light,
				x1, y1, z , light,
				x , y1, z1, light,
				x , y , z1, light,
				x1, y , z , light,
			])
			
			uv_data.extend(uv)
	
	
	
	def make_model(self):
		if self.has_model:
			if not self.model_is_loaded:
				self.read_model()
			return
		
		add_diag = self.add_diag
		
		add_side_left  = self.add_side_left
		add_side_right = self.add_side_right
		add_side_front = self.add_side_front
		add_side_back  = self.add_side_back
		add_top    = self.add_top
		add_bottom = self.add_bottom
		
		
		vertex_data = self.vertex_data = []
		uv_data     = self.uv_data     = []
		
		transparent_vertex_data = self.transparent_vertex_data = []
		transparent_uv_data     = self.transparent_uv_data     = []
		
		for x, line in enumerate(self.columns):
			for z, column in enumerate(line):
				y = 0
				prev_resource_full_opaque = False
				last_i = len(column) - 1
				for i, (resource, count) in enumerate(column):
					need_render = (resource >= 8)
					
					if need_render:
						block = blocks[resource]
						
						if block.diag:
							add_diag(transparent_vertex_data, transparent_uv_data, x, y, z, resource, count)
							full_opaque = False
						
						else:
							full_opaque = block.full_opaque
							
							if full_opaque:
								cur_vertex_data = vertex_data
								cur_uv_data     = uv_data
							else:
								cur_vertex_data = transparent_vertex_data
								cur_uv_data     = transparent_uv_data
							
							add_side_left (cur_vertex_data, cur_uv_data, x, y, z, resource, count, full_opaque)
							add_side_right(cur_vertex_data, cur_uv_data, x, y, z, resource, count, full_opaque)
							add_side_front(cur_vertex_data, cur_uv_data, x, y, z, resource, count, full_opaque)
							add_side_back (cur_vertex_data, cur_uv_data, x, y, z, resource, count, full_opaque)
							
							if i != last_i:
								next_resource = column[i + 1][0]
								next_resource_full_opaque = blocks[next_resource].full_opaque
							else:
								next_resource_full_opaque = False
							
							if not next_resource_full_opaque:
								add_top   (cur_vertex_data, cur_uv_data, x, y, z, resource, count)
							if not prev_resource_full_opaque:
								add_bottom(cur_vertex_data, cur_uv_data, x, y, z, resource, count)
					else:
						full_opaque = False
					
					y += count
					prev_resource_full_opaque = full_opaque
		
		
		water_vertex_data = self.water_vertex_data = []
		water_uv_data     = self.water_uv_data     = []
		
		for x, line in enumerate(self.columns):
			for z, column in enumerate(line):
				y = 0
				for resource, count in column:
					need_render = (0 < resource < 8)
					
					if need_render:
						add_top   (water_vertex_data, water_uv_data, x, y,         z, resource, count)
						add_bottom(water_vertex_data, water_uv_data, x, y + count, z, resource, count)
					
					y += count
		
		
		self.has_model = True
		self.write_model()
		self.load_model()
	
	
	def load_model(self):
		self.command_list_id = buffers.create(self.vertex_data, 4, self.uv_data)
		
		if self.transparent_vertex_data:
			self.transparent_command_list_id = buffers.create(self.transparent_vertex_data, 4, self.transparent_uv_data)
		else:
			self.transparent_command_list_id = None
		
		if self.water_vertex_data:
			self.water_command_list_id = buffers.create(self.water_vertex_data, 4, self.water_uv_data)
		else:
			self.water_command_list_id = None
		
		self.model_is_loaded = True
		if self.first_loading:
			self.first_loading = False
			self.loaded_time = time.time()
		self.make_model_instantly = False
	
	
	def remove_model(self):
		if not self.model_is_loaded:
			return
		
		self.model_is_loaded = False
		
		buffers.remove(self.command_list_id)
		self.command_list_id = None
		
		if self.transparent_command_list_id is not None:
			buffers.remove(self.transparent_command_list_id)
			self.transparent_command_list_id = None
		
		if self.water_command_list_id is not None:
			buffers.remove(self.water_command_list_id)
			self.water_command_list_id = None
	
	
	def reload_model(self, make_model_instantly = False):
		self.make_model_instantly |= make_model_instantly
		
		if self.has_model:
			self.remove_model()
			
			# dont read old data from cache
			self.has_model = False
			os.remove(self.model_path)
	
	
	def remove_self_from_world(self):
		self.write()
		self.remove_model()
		del self.world.chunks[(self.x, self.z)]
	
	def remove(self):
		if self.model_is_loaded:
			if self.remove_time is None:
				self.remove_time = time.time()
		else:
			self.remove_self_from_world()
	
	
	def update_transformation(self):
		if self.transformation is None or self.world.projection_view_matrix_is_new:
			self.transformation = self.world.projection_view_matrix * self.model_matrix
			self.need_update_visible = True
		
		if self.need_update_visible:
			self.update_visible()
	
	def update(self):
		if not self.model_is_loaded:
			return
		
		if self.remove_time is not None:
			alpha = 1.0 - (time.time() - self.remove_time) / config.CHUNK_APPEARANCE_TIME
			if alpha < 0.0:
				self.remove_self_from_world()
				return
			self.alpha = alpha
		else:
			alpha = (time.time() - self.loaded_time) / config.CHUNK_APPEARANCE_TIME
			self.alpha = 1.0 if alpha > 1.0 else alpha
	
	
	def draw(self):
		shaders.set('chunk_opaque')
		shaders.set_mat4('transformation', self.transformation)
		shaders.set_float('alpha', self.alpha)
		
		buffers.draw(self.command_list_id)
	
	
	def draw_transparent(self):
		if self.transparent_command_list_id is None:
			return
		
		shaders.set('chunk_transparent')
		shaders.set_mat4('transformation', self.transformation)
		shaders.set_float('alpha', self.alpha)
		
		buffers.draw(self.transparent_command_list_id)
	
	
	def draw_water(self):
		if self.water_command_list_id is None:
			return
		
		shaders.set('chunk_opaque')
		shaders.set_mat4('transformation', self.transformation)
		shaders.set_float('alpha', self.alpha)
		
		buffers.draw(self.water_command_list_id)
	
	
	
	def write(self):
		if self.saved:
			return
		
		directory = os.path.dirname(self.data_path)
		os.makedirs(directory, exist_ok = True)
		
		props = [self.max_y, self.columns]
		
		# json for security (on case: chunk data from other people)
		content = json.dumps(props, ensure_ascii = False, separators=(',', ':'), check_circular = False)
		content = content.encode('utf-8')
		content = zlib.compress(content, level = 3)
		
		with open(self.data_path, 'wb') as f:
			f.write(content)
		
		self.saved = True
	
	def read(self):
		if not os.path.exists(self.data_path):
			return False
		
		with open(self.data_path, 'rb') as f:
			content = f.read()
		
		content = zlib.decompress(content)
		content = content.decode('utf-8')
		props = json.loads(content)
		self.max_y, self.columns = props
		
		self.has_model = os.path.exists(self.model_path)
		self.saved = True
		
		return True
	
	
	def write_model(self):
		directory = os.path.dirname(self.model_path)
		os.makedirs(directory, exist_ok = True)
		
		props = (
			self.vertex_data,             self.uv_data,
			self.transparent_vertex_data, self.transparent_uv_data,
			self.water_vertex_data,       self.water_uv_data,
		)
		
		# pickle for speed (model data - just cache; dont use it from other people; recalc it)
		content = pickle.dumps(props, protocol = 4)
		content = zlib.compress(content, level = 5)
		
		with open(self.model_path, 'wb') as f:
			f.write(content)
	
	def read_model(self):
		with open(self.model_path, 'rb') as f:
			content = f.read()
		
		content = zlib.decompress(content)
		props = pickle.loads(content)
		
		(
			self.vertex_data,             self.uv_data,
			self.transparent_vertex_data, self.transparent_uv_data,
			self.water_vertex_data,       self.water_uv_data,
		) = props
		
		self.load_model()
