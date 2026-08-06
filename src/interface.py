import time

from pyglm import glm
from OpenGL.GL import *

from PIL import Image

import config
FONT_XSIZE, FONT_YSIZE = config.FONT_XSIZE, config.FONT_YSIZE

import shaders
import buffers


symbol_data = {}
def init_symbol_data():
	symbol_count = len(config.FONT_SYMBOLS)
	texture_width = symbol_count * FONT_XSIZE
	
	font_image = load_image('font')
	pixels = font_image.load()
	
	for index, c in enumerate(config.FONT_SYMBOLS + ' '):
		
		if c == ' ':
			symbol_width = FONT_XSIZE // 2
			offset = 0
			width = 1 / texture_width
		
		else:
			symbol_start = index * FONT_XSIZE
			symbol_end = symbol_start + FONT_XSIZE - 1
			
			for i in range(FONT_XSIZE):
				x = symbol_start + i
				
				empty = True
				for y in range(FONT_YSIZE):
					if pixels[x, y] != (0, 0, 0, 0):
						empty = False
						break
				
				if not empty:
					symbol_start = x - 1
					break
			
			for i in range(FONT_XSIZE):
				x = symbol_end - i
				
				empty = True
				for y in range(FONT_YSIZE):
					if pixels[x, y] != (0, 0, 0, 0):
						empty = False
						break
				
				if not empty:
					symbol_end = x + 2
					break
			
			symbol_width = symbol_end - symbol_start
			offset = symbol_start / texture_width
			width = symbol_width / texture_width
		
		uv = [
			offset, 0,
			offset + width, 0,
			offset + width, 1,
			offset, 0,
			offset + width, 1,
			offset, 1,
		]
		
		symbol_data[c] = (symbol_width / FONT_XSIZE, uv)


def init():
	vertex_data = (
		0, 0,
		1, 0,
		1, 1,
		0, 0,
		1, 1,
		0, 1,
	)
	
	global command_list_id
	command_list_id = buffers.create(vertex_data, 2, None)
	
	init_symbol_data()


def set_2d_projection(projection):
	global projection_2d
	projection_2d = projection


def load_image(name):
	path = '%s../images/%s.png' % (config.project_dir, name)
	return Image.open(path).convert('RGBA')

texture_ids = {}
def load_texture(name):
	texture_id = texture_ids.get(name)
	if texture_id is not None:
		return texture_id
	
	image = load_image(name)
	
	texture_id = texture_ids[name] = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, texture_id)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.width, image.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image.tobytes())
	
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	
	glBindTexture(GL_TEXTURE_2D, 0)
	return texture_id



def draw_image(name, dst, src = (0, 0, 1, 1)):
	texture_id = load_texture(name)
	glBindTexture(GL_TEXTURE_2D, texture_id)
	
	x, y, w, h = dst
	image_matrix = glm.translate(projection_2d, glm.vec3(x, y, 0))
	image_matrix = glm.scale(image_matrix, glm.vec3(w, h, 1))
	
	shaders.set('image')
	shaders.set_mat4('transformation', image_matrix)
	shaders.set_float4('rect', src)
	
	buffers.draw(command_list_id)



text_cache = []
def get_text_render_data(text, spacing):
	for elem in text_cache:
		if elem[1] == text and elem[2] == spacing:
			elem[0] = time.time()
			return elem[-3:]
	
	vertex_data = []
	uv_data = []
	
	x = 0
	y = 0
	w = 0
	for c in text:
		if c == '\n':
			w = max(w, x)
			x = 0
			y += 1 + spacing
			continue
		
		if c not in config.FONT_SYMBOLS and c != ' ':
			c = '?'
		symbol_width, symbol_uv = symbol_data[c]
		
		vertex_data.extend([
			x, y,
			x + symbol_width, y,
			x + symbol_width, y + 1,
			x, y,
			x + symbol_width, y + 1,
			x, y + 1,
		])
		
		uv_data.extend(symbol_uv)
		
		x += symbol_width
	
	command_list_id = buffers.create(vertex_data, 2, uv_data)
	
	w = max(w, x)
	h = y + 1
	
	text_cache.append([time.time(), text, spacing, command_list_id, w, h])
	text_cache.sort(key = lambda elem: elem[0], reverse = True)
	if len(text_cache) > 128:
		old_data = text_cache.pop(-1)
		old_command_list_id = old_data[3]
		
		buffers.remove(old_command_list_id)
	
	return text_cache[0][-3:]


def draw_text(text, size, x, y, color = None, background_color = None, spacing = 0):
	texture_id = load_texture('font')
	glBindTexture(GL_TEXTURE_2D, texture_id)
	
	text = text.lower()
	cur_command_list_id, w, h = get_text_render_data(text, spacing / size)
	w *= size
	h *= size
	
	text_matrix = glm.translate(projection_2d, glm.vec3(x, y, 0))
	text_matrix = glm.scale(text_matrix, glm.vec3(size))
	
	shaders.set('text')
	shaders.set_mat4('transformation', text_matrix)
	shaders.set_float4('vertexColor',      color            or config.FONT_COLOR_DEFAULT)
	shaders.set_float4('vertexBackground', background_color or config.FONT_BACKGROUND_COLOR_DEFAULT)
	
	buffers.draw(cur_command_list_id)
	
	return w, h
