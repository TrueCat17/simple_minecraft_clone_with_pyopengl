from pyglm import glm
import math

from blocks import blocks


def init(obj, cam_height, height, radius):
	obj.cam_height = cam_height
	obj.height = height
	obj.radius = radius
	
	obj.bottom_points = []
	obj.middle_points = []
	obj.top_points = []
	
	for h, points in [(0, obj.bottom_points), (1, obj.middle_points), (height, obj.top_points)]:
		dy = h - cam_height
		
		N = 16
		for i in range(N):
			v = 2 * math.pi * i / N
			dx = math.cos(v) * radius
			dz = math.sin(v) * radius
			points.append(glm.vec3(dx, dy, dz))
	
	obj.side_points = obj.bottom_points + obj.middle_points
	
	obj.on_ground = False


def vertical(obj):
	world = obj.world
	pos   = obj.pos
	speed = obj.speed
	
	pos.y += speed.y
	
	cache = {}
	def is_physics(pos):
		res = cache.get(pos)
		if res is not None:
			return res
		resource = world.get_resource(*pos)
		res = cache[pos] = blocks[resource].physics
		return res
	
	if speed.y < 0:
		points = obj.bottom_points
		dy = 1 + obj.cam_height
	else:
		points = obj.top_points
		dy = -points[0].y
	
	for dpoint in points:
		point = glm.ivec3(glm.floor(pos + dpoint))
		if is_physics(point):
			obj.on_ground = speed.y < 0
			pos.y = point.y + dy
			speed.y = 0
			break
	else:
		obj.on_ground = False


def horizontal(obj):
	ivec3  = glm.ivec3
	vec3   = glm.vec3
	floor  = glm.floor
	length = glm.length
	
	world = obj.world
	
	pos = obj.pos
	orig_pos = vec3(pos)
	
	speed = obj.speed
	speed_x = speed.x
	speed_z = speed.z
	
	if speed_x == 0 and speed_z == 0:
		return
	
	cache = {}
	def is_physics(pos):
		res = cache.get(pos)
		if res is not None:
			return res
		resource = world.get_resource(*pos)
		res = cache[pos] = blocks[resource].physics
		return res
	
	lost_speed_x = speed_x
	lost_speed_z = speed_z
	abs_lost_speed_x = abs(lost_speed_x)
	abs_lost_speed_z = abs(lost_speed_z)
	
	def sign(x):
		return -1 if x < 0 else 1 if x > 0 else 0
	sign_speed_x = sign(speed_x)
	sign_speed_z = sign(speed_z)
	
	sign_speed_x_part = sign_speed_x * obj.radius / 2
	sign_speed_z_part = sign_speed_z * obj.radius / 2
	side_points = []
	for point in obj.side_points:
		moved_point = vec3(point.x + sign_speed_x_part, point.y, point.z + sign_speed_z_part)
		useless = length(moved_point) < length(point)
		if not useless:
			side_points.append(point)
	
	for i in range(10):
		step = 2 ** -(3 + i)
		
		step_x = sign_speed_x * step
		step_z = sign_speed_z * step
		abs_step_x = abs(step_x)
		abs_step_z = abs(step_z)
		
		start_pos = vec3(pos)
		
		changed_x = changed_z = True
		while changed_x or changed_z:
			changed_x = changed_z = False
			
			if abs_lost_speed_x > abs_step_x:
				next_pos = vec3(start_pos)
				next_pos.x += step_x
				
				for dpoint in side_points:
					point = ivec3(floor(next_pos + dpoint))
					if is_physics(point):
						break
				else:
					changed_x = True
					start_pos = next_pos
					lost_speed_x -= step_x
					abs_lost_speed_x = abs(lost_speed_x)
			
			if abs_lost_speed_z > abs_step_z:
				next_pos = vec3(start_pos)
				next_pos.z += step_z
				
				for dpoint in side_points:
					point = ivec3(floor(next_pos + dpoint))
					if is_physics(point):
						break
				else:
					changed_z = True
					start_pos = next_pos
					lost_speed_z -= step_z
					abs_lost_speed_z = abs(lost_speed_z)
		
		pos.x = start_pos.x
		pos.z = start_pos.z
	
	if pos.x == orig_pos.x:
		speed.x = 0
	if pos.z == orig_pos.z:
		speed.z = 0
