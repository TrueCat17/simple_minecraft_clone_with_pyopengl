class GetDistToPoint:
	def __init__(self, point):
		self.x, self.y, self.z = point
	def __call__(self, point):
		x, y, z = point
		dx = self.x - x
		dy = self.y - y
		dz = self.z - z
		return dx * dx + dy * dy + dz * dz

def add_wire_to_vertex_biffer(vertex_data, point1, point2, wire_size):
	x1, y1, z1 = point1
	x2, y2, z2 = point2
	halfsize = wire_size / 2
	
	nears1 = []
	nears2 = []
	
	d = (-halfsize, +halfsize)
	for dx in d:
		for dz in d:
			for dy in d:
				nears1.append([x1 + dx, y1 + dy, z1 + dz])
				nears2.append([x2 + dx, y2 + dy, z2 + dz])
	
	nears1.sort(key = GetDistToPoint(point2))
	nears2.sort(key = GetDistToPoint(point1))
	
	
	a1, a2, a3, a4 = nears1[4:]
	b1, b2, b3, b4 = nears2[4:]
	
	vertex_data.extend(a1 + a2 + b1)
	vertex_data.extend(b1 + a2 + b2)
	
	vertex_data.extend(a2 + a4 + b2)
	vertex_data.extend(b2 + a4 + b4)
	
	vertex_data.extend(a4 + a3 + b3)
	vertex_data.extend(a4 + b3 + b4)
	
	vertex_data.extend(a1 + b3 + a3)
	vertex_data.extend(a1 + b1 + b3)
