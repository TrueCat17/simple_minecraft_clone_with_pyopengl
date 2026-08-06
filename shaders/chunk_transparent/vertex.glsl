#version 330 core

layout(location = 0) in vec4 vertex;
layout(location = 1) in vec2 UV;

out vec2 fragUV;
out float fragLight;
out float fragAlpha;

uniform mat4 transformation;
uniform float alpha;

void main() {
	gl_Position = transformation * vec4(vertex.xyz, 1);
	fragUV = UV;
	fragLight = vertex[3];
	fragAlpha = alpha;
}
