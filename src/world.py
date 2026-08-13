import os
import shutil
import time
import json

from pyglm import glm
from OpenGL.GL import *
import OpenGL.GLUT as oglut

import config
CHUNK_SIZE = config.CHUNK_SIZE

import blocks
from player import Player
from camera import Camera
from chunk import Chunk
from chunk_border import ChunkBorder
from selected_block import SelectedBlock


class World:
	def __init__(self):
		self.dist_to_render = config.RENDER_DISTANCE_IN_CHUNKS_DEFAULT
		self.fullscreen = False
		
		player = self.player = Player(self)
		self.cam = Camera(player)
		self.chunk_border = ChunkBorder(self)
		self.selected_block = SelectedBlock(self)
		
		self.projection_view_matrix = None
		
		self.block_id = blocks.get_block_id('stone')
		
		self.path = config.project_dir + '../world/'
		self.params_path = self.path + 'params.txt'
		self.chunks = {}
		
		new = False
		if not self.read_params():
			new = True
			self.last_save_time = 0
			self.last_save_data = ''
		
		pos = player.pos
		ipos = glm.ivec3(glm.floor(pos))
		cam_chunk_x = ipos.x // CHUNK_SIZE
		cam_chunk_z = ipos.z // CHUNK_SIZE
		
		dist_to_create = self.dist_to_render + 1
		r = range(-dist_to_create, dist_to_create + 1)
		for x in r:
			for z in r:
				self.create_chunk(cam_chunk_x + x, cam_chunk_z + z)
		
		if new:
			chunk = self.chunks[(cam_chunk_x, cam_chunk_z)]
			column = chunk.columns[ipos.x % CHUNK_SIZE][ipos.z % CHUNK_SIZE]
			top_air = column[-1]
			count = top_air[1]
			
			pos.y = config.CHUNK_HEIGHT - count + player.cam_height
		
		self.lost_dtime = 0
	
	
	def get_resource(self, x, y, z):
		chunk_x = x // CHUNK_SIZE
		chunk_z = z // CHUNK_SIZE
		chunk = self.chunks[(chunk_x, chunk_z)]
		
		x %= CHUNK_SIZE
		z %= CHUNK_SIZE
		resource = chunk.get_resource(x, y, z)
		return resource
	
	def set_resource(self, x, y, z, resource, count = 1):
		chunk_x = x // CHUNK_SIZE
		chunk_z = z // CHUNK_SIZE
		chunk = self.chunks[(chunk_x, chunk_z)]
		
		x %= CHUNK_SIZE
		z %= CHUNK_SIZE
		chunk.set_blocks_in_column(y, count, resource, pos = (x, z), make_model_instantly = True)
	
	
	def next_block_id(self):
		while True:
			self.block_id = (self.block_id + 1) % len(blocks.blocks)
			block = blocks.blocks[self.block_id]
			if block and block.has_texture:
				break
	
	def prev_block_id(self):
		while True:
			self.block_id = (self.block_id - 1) % len(blocks.blocks)
			block = blocks.blocks[self.block_id]
			if block and block.has_texture:
				break
	
	
	def create_chunk(self, x, z):
		self.chunks[(x, z)] = Chunk(self, x, z)
	
	def update_tick(self, pressed_keys, shift, tick_time):
		player = self.player
		
		dx = dz = 0
		if pressed_keys.get(b'w'):
			dz += 1
		if pressed_keys.get(b's'):
			dz -= 1
		if pressed_keys.get(b'a'):
			dx -= 1
		if pressed_keys.get(b'd'):
			dx += 1
		player.move(dx, dz, tick_time)
		
		if pressed_keys.get(b' '):
			player.fly_or_jump(-1 if shift else 1, tick_time)
		
		player.update()
	
	def update(self, pressed_keys, shift, left_click, middle_click, right_click, dtime):
		selected_block = self.selected_block
		selected_block.update()
		
		need_update = False
		if selected_block.enable:
			if left_click:
				selected_block.remove()
				need_update = True
			elif right_click:
				selected_block.add(self.block_id)
				need_update = True
			elif middle_click:
				self.block_id = self.get_resource(*selected_block.pos)
		
		tick_time = 1 / 60
		self.lost_dtime += dtime
		while self.lost_dtime > tick_time or need_update:
			self.lost_dtime -= tick_time
			need_update = False
			self.update_tick(pressed_keys, shift, tick_time)
		
		cam = self.cam
		cam.update()
		old_projection_view_matrix = self.projection_view_matrix
		self.projection_view_matrix = self.projection_3d * cam.view_matrix
		self.projection_view_matrix_is_new = self.projection_view_matrix != old_projection_view_matrix
		
		
		cam_chunk_x = cam.chunk_x
		cam_chunk_z = cam.chunk_z
		
		chunks = self.chunks
		to_create     = []
		to_make_model = []
		
		dist_to_create = self.dist_to_render + 1
		dist_to_remove = dist_to_create + 1
		
		r = range(-dist_to_create, dist_to_create + 1)
		for dx in r:
			for dz in r:
				pos = (cam_chunk_x + dx, cam_chunk_z + dz)
				if pos not in chunks:
					to_create.append(pos)
		
		r = range(-self.dist_to_render, self.dist_to_render + 1)
		for dx in r:
			for dz in r:
				pos = (cam_chunk_x + dx, cam_chunk_z + dz)
				chunk = chunks.get(pos)
				if chunk is None or not chunk.model_is_loaded:
					to_make_model.append(pos)
		
		
		for x, z in to_create:
			self.create_chunk(x, z)
		
		for (x, z), chunk in chunks.copy().items():
			dx = abs(cam_chunk_x - x)
			dz = abs(cam_chunk_z - z)
			if max(dx, dz) > dist_to_remove:
				chunk.remove()
		
		for chunk in chunks.values():
			chunk.update_transformation()
		
		
		def get_dist_to_cam(pos):
			x, z = pos
			dx = cam_chunk_x - x
			dz = cam_chunk_z - z
			dist2 = dx * dx + dz * dz
			return dist2 + (1e6 if not chunks[pos].visible else 0)
		to_make_model.sort(key = get_dist_to_cam)
		
		for chunk in chunks.values():
			if chunk.make_model_instantly:
				chunk.make_model()
		
		st = time.time()
		for pos in to_make_model:
			chunk = chunks[pos]
			if chunk.model_is_loaded:
				continue
			
			chunk.make_model()
			if time.time() - st > config.FRAME_TIME:
				break
		
		# copy, because chunk can remove itself
		for chunk in chunks.copy().values():
			chunk.update()
		
		self.write_params()
	
	
	def draw(self):
		self.chunk_border.draw()
		self.selected_block.draw()
		
		chunks = [chunk for chunk in self.chunks.values() if chunk.model_is_loaded and chunk.visible]
		
		cam_chunk_x = self.cam.chunk_x
		cam_chunk_z = self.cam.chunk_z
		def get_dist_to_cam(chunk):
			dx = cam_chunk_x - chunk.x
			dz = cam_chunk_z - chunk.z
			return dx * dx + dz * dz
		chunks.sort(key = get_dist_to_cam)
		
		for chunk in chunks:
			chunk.draw()
		
		for chunk in chunks:
			chunk.draw_transparent()
		
		for chunk in reversed(chunks):
			chunk.draw_water()
		
		return len(chunks)
	
	
	def get_params(self):
		player = self.player
		pos = player.pos
		
		return {
			'SEED': config.SEED,
			'CHUNK_SIZE': CHUNK_SIZE,
			'CHUNK_HEIGHT': config.CHUNK_HEIGHT,
			'dist_to_render': self.dist_to_render,
			'x': pos.x,
			'y': pos.y,
			'z': pos.z,
			'rot_x': player.rot_x,
			'rot_y': player.rot_y,
			'physics': player.physics,
			'chunk_border': self.chunk_border.enable,
			'fullscreen': self.fullscreen,
			'block_id': self.block_id,
		}
	
	def write_params(self):
		if time.time() - self.last_save_time < 1:
			return
		self.last_save_time = time.time()
		
		for chunk in self.chunks.values():
			chunk.write()
		
		params = self.get_params()
		json_data = json.dumps(params, indent = 4)
		
		if json_data == self.last_save_data:
			return
		self.last_save_data = json_data
		
		os.makedirs(self.path, exist_ok = True)
		with open(self.params_path, 'wb') as f:
			f.write(json_data.encode('utf-8'))
	
	def read_params(self):
		if not os.path.exists(self.params_path):
			return False
		
		with open(self.params_path, 'rb') as f:
			json_data = f.read().decode('utf-8')
		
		cur_params = self.get_params()
		params = json.loads(json_data)
		
		cur_keys = sorted(cur_params.keys())
		keys = sorted(params.keys())
		if keys != cur_keys:
			raise Exception('cur_keys %s != keys %s' % (cur_keys, keys))
		
		remove_old_world = False
		for name in params:
			if name.isupper() and params[name] != cur_params[name]:
				print('Major world param <%s> was changed (%s -> %s), removing old world' % (name, params[name], cur_params[name]))
				shutil.rmtree(self.path)
				return False
		
		
		player = self.player
		pos = player.pos
		
		self.dist_to_render = params['dist_to_render']
		
		pos.x = params['x']
		pos.y = params['y']
		pos.z = params['z']
		
		player.rot_x = params['rot_x']
		player.rot_y = params['rot_y']
		self.cam.rotate(0, 0)
		
		player.physics = params['physics']
		self.chunk_border.enable = params['chunk_border']
		self.fullscreen = params['fullscreen']
		if self.fullscreen:
			oglut.glutFullScreenToggle()
		
		self.block_id = params['block_id']
		
		self.last_save_time = time.time()
		self.last_save_data = json_data
		return True
