#version 330 core

layout(location = 0) in vec3 vertex;

uniform mat4 transformation;
uniform vec4 vertexColor;

out vec4 fragmentColor;

void main() {
	gl_Position = transformation * vec4(vertex.xyz, 1);
	fragmentColor = vertexColor;
}
