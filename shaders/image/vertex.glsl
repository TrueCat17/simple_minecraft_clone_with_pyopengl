#version 330 core

layout(location = 0) in vec2 vertex;

out vec2 UV;

uniform mat4 transformation;
uniform vec4 rect;

void main() {
	gl_Position = transformation * vec4(vertex.xy, 0, 1);
	
	UV.x = vertex.x * rect[2] + rect[0];
	UV.y = vertex.y * rect[3] + rect[1];
}
