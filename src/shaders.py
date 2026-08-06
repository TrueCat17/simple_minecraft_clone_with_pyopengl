from OpenGL.GL import *

def printOpenGLError():
	err = glGetError()
	if err != GL_NO_ERROR:
		print('GLERROR: ', gluErrorString(err))


shader_ids = {}
def load(name):
	if name in shader_ids:
		return shader_ids[name]
	
	from config import project_dir
	path = '%s../shaders/%s/' % (project_dir, name)
	
	with open(path + 'vertex.glsl', 'rb') as f:
		vertex_shader = f.read().decode('utf-8')
	
	with open(path + 'fragment.glsl', 'rb') as f:
		fragment_shader = f.read().decode('utf-8')
	
	shader_id = glCreateProgram()
	printOpenGLError()
	
	vertex_shader_id = glCreateShader(GL_VERTEX_SHADER)
	glShaderSource(vertex_shader_id, vertex_shader)
	glCompileShader(vertex_shader_id)
	if glGetShaderiv(vertex_shader_id, GL_COMPILE_STATUS) != GL_TRUE:
		err = glGetShaderInfoLog(vertex_shader_id)
		raise Exception(err)
	glAttachShader(shader_id, vertex_shader_id)
	printOpenGLError()
	
	fragment_shader_id = glCreateShader(GL_FRAGMENT_SHADER)
	glShaderSource(fragment_shader_id, fragment_shader)
	glCompileShader(fragment_shader_id)
	if glGetShaderiv(fragment_shader_id, GL_COMPILE_STATUS) != GL_TRUE:
		err = glGetShaderInfoLog(fragment_shader_id)
		raise Exception(err)
	glAttachShader(shader_id, fragment_shader_id)
	printOpenGLError()
	
	glLinkProgram(shader_id)
	if glGetProgramiv(shader_id, GL_LINK_STATUS) != GL_TRUE:
		err = glGetProgramInfoLog(shader_id)
		raise Exception(err)
	printOpenGLError()
	
	shader_ids[name] = shader_id
	return shader_id


last_shader_name = last_shader_id = None
def set(name):
	global last_shader_name, last_shader_id
	if last_shader_name == name:
		return
	
	last_shader_name = name
	last_shader_id = load(name)
	
	if glUseProgram(last_shader_id):
		printOpenGLError()


uniform_locations = {}
def get_uniform_location_of_cur_sharer(uniform_name):
	if last_shader_id is None:
		raise Exception('Use shaders.set() before')
	
	key = (last_shader_id, uniform_name)
	res = uniform_locations.get(key)
	if res is None:
		res = glGetUniformLocation(last_shader_id, uniform_name)
		if res < 0:
			print('Error on getting uniform <%s> of shader <%s>' % (uniform_name, last_shader_name))
	return res


def set_mat4(uniform_name, mat4):
	uniform_location = get_uniform_location_of_cur_sharer(uniform_name)
	from pyglm import glm
	glUniformMatrix4fv(uniform_location, 1, GL_FALSE, glm.value_ptr(mat4))

uniform_values = {}
def set_float(uniform_name, value):
	key = (last_shader_id, uniform_name)
	if uniform_values.get(key) == value:
		return
	uniform_values[key] = value
	
	uniform_location = get_uniform_location_of_cur_sharer(uniform_name)
	glUniform1f(uniform_location, value)

def set_float4(uniform_name, values):
	key = (last_shader_id, uniform_name)
	if uniform_values.get(key) == values:
		return
	uniform_values[key] = values
	
	uniform_location = get_uniform_location_of_cur_sharer(uniform_name)
	glUniform4f(uniform_location, *values)
