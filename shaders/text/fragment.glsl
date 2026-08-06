#version 330 core

in vec2 fragUV;
in vec4 fragColor;
in vec4 fragBackground;

out vec4 color;

uniform sampler2D myTextureSampler;

void main() {
	color = texture(myTextureSampler, fragUV) * fragColor;
	if (color.a == 0) {
		color = fragBackground;
	}
}
