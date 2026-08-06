#version 330 core

layout(location = 0) in vec2 vertex;
layout(location = 1) in vec2 UV;

out vec2 fragUV;
out vec4 fragColor;
out vec4 fragBackground;

uniform mat4 transformation;
uniform vec4 vertexColor;
uniform vec4 vertexBackground;

void main() {
	gl_Position = transformation * vec4(vertex.xy, 0, 1);
	fragUV = UV;
	fragColor      = vertexColor;
	fragBackground = vertexBackground;
}
