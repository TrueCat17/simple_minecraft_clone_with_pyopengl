from pyglm import glm

import config


class Camera:
	def __init__(self, player):
		self.player = player
		self.world = player.world
		
		center = (config.CHUNK_SIZE - 1) / 2
		player.pos = glm.vec3(center, 0, center)
		
		self.rot_x_max = glm.radians(89.9)
		self.rot_x_min = -self.rot_x_max
		
		self.rot_speed = glm.radians(1) * config.CAMERA_ROTATION_SPEED
		
		self.ox = glm.vec3(1, 0, 0)
		self.oy = glm.vec3(0, 1, 0)
		self.oz = glm.vec3(0, 0, 1)
		
		self.rotate(0, 0)
	
	def rotate(self, dx, dy):
		player = self.player
		
		player.rot_y -= self.rot_speed * dx
		
		player.rot_x = min(max(self.rot_x_min, player.rot_x + self.rot_speed * dy), self.rot_x_max)
		
		direction      = glm.rotate(self.oz,   player.rot_x, self.ox)
		self.direction = glm.rotate(direction, player.rot_y, self.oy)
	
	def update(self):
		pos = self.player.pos
		self.view_matrix = glm.lookAt(
			pos,
			pos + self.direction,
			self.oy,
		)
		
		x = self.chunk_x = int(pos.x // config.CHUNK_SIZE)
		z = self.chunk_z = int(pos.z // config.CHUNK_SIZE)
		self.chunk = self.world.chunks[(x, z)]
