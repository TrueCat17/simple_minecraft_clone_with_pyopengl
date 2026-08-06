from pyglm import glm
from OpenGL.GL import *


data = {}

def create(vertex_data, vertex_size, uv_data):
	vertex_id = glGenBuffers(1)
	glBindBuffer(GL_ARRAY_BUFFER, vertex_id)
	glBufferData(GL_ARRAY_BUFFER, len(vertex_data) * 4, (GLfloat * len(vertex_data))(*vertex_data), GL_STATIC_DRAW)
	point_count = len(vertex_data) // vertex_size
	
	if uv_data is not None:
		uv_id = glGenBuffers(1)
		glBindBuffer(GL_ARRAY_BUFFER, uv_id)
		glBufferData(GL_ARRAY_BUFFER, len(uv_data) * 4, (GLfloat * len(uv_data))(*uv_data), GL_STATIC_DRAW)
	else:
		uv_id = None
	
	glBindBuffer(GL_ARRAY_BUFFER, 0)
	
	
	command_list_id = glGenVertexArrays(1)
	glBindVertexArray(command_list_id)
	
	glEnableVertexAttribArray(0)
	glBindBuffer(GL_ARRAY_BUFFER, vertex_id)
	glVertexAttribPointer(0, vertex_size, GL_FLOAT, GL_FALSE, 0, None)
	
	if uv_id is not None:
		glEnableVertexAttribArray(1)
		glBindBuffer(GL_ARRAY_BUFFER, uv_id)
		glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, None)
	
	glBindVertexArray(0)
	
	data[command_list_id] = (vertex_id, uv_id, point_count)
	return command_list_id


def remove(command_list_id):
	vertex_id, uv_id, _point_count = data.pop(command_list_id)
	
	glDeleteBuffers(1, vertex_id)
	glDeleteBuffers(1, uv_id)
	glDeleteVertexArrays(1, command_list_id)


def draw(command_list_id):
	point_count = data[command_list_id][-1]
	
	glBindVertexArray(command_list_id)
	glDrawArrays(GL_TRIANGLES, 0, point_count)
