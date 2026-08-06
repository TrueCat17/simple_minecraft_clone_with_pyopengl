from pyglm import glm
import math

import config
import player_physics


class Player:
	def __init__(self, world):
		self.world = world
		
		self.pos = glm.vec3(0)
		self.speed = glm.vec3(0)
		
		self.rot_x = 0
		self.rot_y = 0
		
		self.physics = config.PLAYER_PHYSICS_DEFAULT
		
		player_physics.init(self, cam_height = 1.5, height = 1.75, radius = 0.3)
	
	def move(self, dx, dz, dtime):
		acceleration = config.PLAYER_ACCELERATION if self.physics else config.PLAYER_NO_PHYSICS_ACCELERATION
		k = acceleration * dtime
		
		if dx and dz:
			k /= 2 ** 0.5
		dx *= k
		dz *= k
		
		angle = self.rot_y
		self.speed.x -= math.cos(angle) * dx - math.sin(angle) * dz
		self.speed.z += math.sin(angle) * dx + math.cos(angle) * dz
	
	def fly_or_jump(self, dy, dtime):
		speed = self.speed
		if self.physics:
			if dy > 0 and self.on_ground:
				speed.y = config.PLAYER_JUMP_ACCELERATION
		else:
			speed.y += dy * config.PLAYER_NO_PHYSICS_ACCELERATION * dtime
	
	def update(self):
		pos = self.pos
		speed = self.speed
		
		physics = self.physics
		if physics:
			speed.y -= config.PLAYER_GRAVITY
		
		friction_k = config.PLAYER_FRICTION_K if physics else config.PLAYER_NO_PHYSICS_FRICTION_K
		speed.x *= friction_k
		speed.z *= friction_k
		
		if physics:
			speed.y *= config.PLAYER_GRAVITY_FRICTION
			player_physics.vertical(self)
			player_physics.horizontal(self)
		else:
			speed.y *= config.PLAYER_NO_PHYSICS_GRAVITY_FRICTION
			pos += speed
		
		min_speed = config.PLAYER_MIN_SPEED if physics else config.PLAYER_NO_PHYSICS_MIN_SPEED
		if speed.x ** 2 + speed.z ** 2 < min_speed ** 2:
			speed.x = 0
			speed.z = 0
