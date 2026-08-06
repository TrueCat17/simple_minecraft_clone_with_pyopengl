old_print = print
def my_print(*args, **kwargs):
	kwargs.setdefault('flush', True)
	old_print(*args, **kwargs)
__builtins__.print = my_print


import time
from pyglm import glm

from OpenGL.GL import *
import OpenGL.GLUT as oglut


import os, sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.dont_write_bytecode = True

import config
import blocks
import interface
from world import World


def init_opengl():
	oglut.glutInit(sys.argv)
	
	oglut.glutInitContextVersion(3, 3)
	oglut.glutInitContextFlags(oglut.GLUT_FORWARD_COMPATIBLE | oglut.GLUT_DEBUG)
	oglut.glutInitContextProfile(oglut.GLUT_CORE_PROFILE)
	
	oglut.glutInitDisplayMode(oglut.GLUT_RGBA | oglut.GLUT_DOUBLE | oglut.GLUT_DEPTH | oglut.GLUT_MULTISAMPLE)
	
	oglut.glutInitWindowSize(1920 // 2, 1080 // 2)
	oglut.glutCreateWindow(b'Simple MineCraft Clone')
	oglut.glutDisplayFunc(ogl_draw)
	oglut.glutIdleFunc(ogl_draw)
	oglut.glutReshapeFunc(resize)
	oglut.glutKeyboardFunc(on_keyboard_down)
	oglut.glutKeyboardUpFunc(on_keyboard_up)
	oglut.glutSpecialFunc(on_special_key_down)
	oglut.glutSpecialUpFunc(on_special_key_up)
	oglut.glutMouseFunc(on_mouse)
	oglut.glutPassiveMotionFunc(on_mousemove)
	
	glClearColor(0.1, 0.5, 0.9, 0)
	glEnable(GL_DEPTH_TEST)
	
	glEnable(GL_CULL_FACE)
	glCullFace(GL_FRONT)
	
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	glEnable(GL_BLEND)
	
	glEnable(GL_MULTISAMPLE)


def mouse_to_center():
	oglut.glutWarpPointer(world.window_width // 2, world.window_height // 2)

def resize(w, h):
	glViewport(0, 0, w, h)
	
	world.window_width = w
	world.window_height = h
	world.projection_3d = glm.perspective(glm.radians(config.CAMERA_FOV / 2), w / h, 0.1, 1000)
	
	projection_2d = glm.ortho(0, w, h, 0, 0, 1)
	interface.set_2d_projection(projection_2d)
	
	mouse_to_center()

hide_interface = False
pressed_keys = {}
def on_keyboard_down(key, x, y):
	pressed_keys[key.lower()] = True
	
	if   key == b'b':
		world.chunk_border.enable = not world.chunk_border.enable
	elif key == b'f':
		world.fullscreen = not world.fullscreen
		oglut.glutFullScreenToggle()
	elif key == b'z':
		world.prev_block_id()
	elif key == b'x':
		world.next_block_id()
	elif key == b'c':
		world.player.physics = not world.player.physics
	elif key == b'h':
		global hide_interface
		hide_interface = not hide_interface
	elif key in b'+=':
		world.dist_to_render += 1
	elif key == b'-':
		world.dist_to_render = max(0, world.dist_to_render - 1)

def on_keyboard_up(key, x, y):
	pressed_keys[key.lower()] = False


ctrl  = False
shift = False
def on_special_key_down(key, x, y):
	global ctrl, shift
	if key == 114:
		ctrl = True
	elif key == 112:
		shift = True
def on_special_key_up(key, x, y):
	global ctrl, shift
	if key == 114:
		ctrl = False
		mouse_to_center()
	elif key == 112:
		shift = False


def on_mousemove(x, y):
	if ctrl:
		return
	
	dx = x - world.window_width  // 2
	dy = y - world.window_height // 2
	if not dx and not dy:
		return
	
	m = 10
	dx = max(-m, min(dx, m))
	dy = max(-m, min(dy, m))
	
	world.cam.rotate(dx, dy)
	mouse_to_center()

left_click = middle_click = right_click = False
def on_mouse(button, state, x, y):
	global left_click, middle_click, right_click
	
	if state != oglut.GLUT_DOWN:
		return
	
	if   button == oglut.GLUT_LEFT_BUTTON:
		left_click = True
	elif button == oglut.GLUT_MIDDLE_BUTTON:
		middle_click = True
	elif button == oglut.GLUT_RIGHT_BUTTON:
		right_click = True


prev_time = None
prev_dtimes = []
def ogl_draw():
	global prev_time, left_click, middle_click, right_click
	
	cur_time = time.time()
	if prev_time is None:
		dtime = 0.020
	else:
		dtime = cur_time - prev_time
	prev_time = cur_time
	
	prev_dtimes.append(dtime)
	if len(prev_dtimes) > 60:
		prev_dtimes.pop(0)
	mdtime = sum(prev_dtimes) / len(prev_dtimes)
	fps = round(1 / mdtime)
	
	
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	glBindTexture(GL_TEXTURE_2D, blocks_texture_id)
	
	world.update(pressed_keys, shift, left_click, middle_click, right_click, dtime)
	left_click = middle_click = right_click = False
	
	count_rendered_chunks = world.draw()
	
	
	if not hide_interface:
		spacing = 5
		text_size = config.FONT_YSIZE * 3
		image_size = 32
		
		x = spacing
		y = spacing
		
		strings = [
			'wasd, space, shift + space\n'
			'ctrl - free mouse\n'
			'b - chunk borders\n'
			'f - fullscreen\n'
			'z/x - prev/next block\n'
			'c - physics\n'
			'h - hide interface',
			
			'rendered chunks: %i' % count_rendered_chunks,
			'dist to render: %i' % world.dist_to_render,
			'fps: %i, dtime: %.1f' % (fps, mdtime * 1000),
			'pos: %.1f, %.1f, %.1f' % tuple(world.player.pos),
		]
		for string in strings:
			w, h = interface.draw_text(string, size = text_size, x = x, y = y, spacing = spacing)
			y += h + spacing
		
		block = blocks.blocks[world.block_id]
		interface.draw_image(
			'blocks',
			dst = (spacing, world.window_height - spacing - image_size, image_size, image_size),
			src = block.front_rect,
		)
		interface.draw_text(
			'- current block: %s' % block.name,
			size = text_size,
			x = image_size + spacing * 2,
			y = world.window_height - spacing - image_size // 2 - text_size // 2,
		)
	
	
	oglut.glutSwapBuffers()
	
	dtime = time.time() - cur_time
	time_to_sleep = config.FRAME_TIME - dtime - 0.0001
	if time_to_sleep > 0:
		time.sleep(time_to_sleep)

def main():
	init_opengl()
	
	interface.init()
	global blocks_texture_id
	blocks_texture_id = interface.load_texture('blocks')
	
	global world
	world = World()
	
	oglut.glutMainLoop()

main()
