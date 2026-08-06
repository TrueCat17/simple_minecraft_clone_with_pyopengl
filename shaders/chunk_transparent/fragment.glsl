#version 330 core

in vec2 fragUV;
in float fragLight;
in float fragAlpha;

out vec4 color;

uniform sampler2D myTextureSampler;

void main() {
	color = texture(myTextureSampler, fragUV);
	if (color.a < 0.1) {
		discard;
		return;
	}
	
	color.rgb *= fragLight;
	color.a *= fragAlpha;
}
