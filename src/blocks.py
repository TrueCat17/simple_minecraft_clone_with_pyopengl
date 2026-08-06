from config import project_dir


blocks = [None] * 256
block_ids = {}

def get_block_id(name):
	res = block_ids.get(name)
	if res is None:
		raise Exception('Block <%s> not found' % (name, ))
	return res


next_id = 0

class Block:
	def __init__(self, name, params):
		prefix  = params.pop('prefix',  '')
		postfix = params.pop('postfix', '')
		self.name = name = prefix + name + postfix
		
		global next_id
		blocks[next_id] = self
		self.id = block_ids[name] = next_id
		next_id += 1
		
		physics = params.pop('physics', False)
		diag    = params.pop('diag',    False)
		full_opaque = params.pop('full_opaque', False) and not diag
		
		main = params.pop('main', None)
		
		top    = params.pop('top', main)
		bottom = params.pop('bottom', top)
		
		side = params.pop('side', main)
		
		left  = params.pop('left',  side)
		right = params.pop('right', left)
		
		front = params.pop('front', side)
		back  = params.pop('back',  front)
		
		
		self.physics = physics
		self.diag    = diag
		self.full_opaque = full_opaque
		
		def get_uv_by_pos(x, y, rect = None):
			margin = 24
			frame_size = 16 + margin * 2
			image_size = frame_size * 16
			
			x = (x * frame_size + margin) / image_size
			y = (y * frame_size + margin) / image_size
			s = 16 / image_size
			
			if rect is not None:
				rect[:] = [x, y, s, s]
			
			xs = x + s
			ys = y + s
			return [
				xs, y ,
				x , ys,
				x , y ,
				xs, y ,
				xs, ys,
				x , ys,
			]
		
		if main is None:
			self.has_texture = False
			return
		
		self.has_texture = True
		
		self.top_uv    = get_uv_by_pos(*top)
		self.bottom_uv = get_uv_by_pos(*bottom)
		
		self.left_uv   = get_uv_by_pos(*left)
		self.right_uv  = get_uv_by_pos(*right)
		
		self.front_rect = []
		self.front_uv = get_uv_by_pos(*front, rect = self.front_rect)
		self.back_uv  = get_uv_by_pos(*back)
		
		def get_reflected_h(uv):
			x1 = uv[0]
			x2 = uv[2]
			res = []
			for i in range(len(uv)):
				if i % 2 == 0:
					res.append(x1 if uv[i] == x2 else x2)
				else:
					res.append(uv[i])
			return res
		
		self.left_uv_reflected_h = get_reflected_h(self.left_uv)


Block(
	name = 'air',
	params = {}
)
Block(
	name = 'water',
	params = { 'main': (15, 6) }
)
start_usual_id = 8

default_params = {
	'physics': True,
	'diag':    False,
	'full_opaque': True,
}
sides = 'main top bottom side left right front back'.split(' ')

path = project_dir + '../objects/'
def load_file(fn, num_line):
	global next_id
	next_id = start_usual_id + num_line * 16
	
	with open(path + fn, 'rb') as f:
		content = f.read().decode('utf-8')
	
	cur_params = default_params.copy()
	cur_params['main'] = [0, num_line]
	
	for i, s in enumerate(content.split('\n'), 1):
		s = s.strip()
		if not s or s[0] == '#':
			continue
		
		if ' ' in s:
			while '  ' in s:
				s = s.replace('  ', ' ')
			
			params = s.split(' ')
			name = params[0]
			value1 = params[1]
			value2 = params[2] if len(params) == 3 else num_line
			
			if value1 == 'None':
				value1 = ''
			
			if name in sides:
				ok = True
				for value in (value1, value2):
					if type(value) is str and not value.isdigit():
						print('Invalid number %s in line `%s` (%s:%s)' % (value, s, fn, i))
						ok = False
						continue
				if not ok:
					continue
				
				cur_params[name] = [int(value1), int(value2)]
			
			else:
				if name not in ('prefix', 'postfix'):
					if value1 not in ('True', 'False'):
						print('Incorrect param %s in line `%s`, expected True or False (%s:%s)' % (name, s, fn, i))
						continue
					value1 = value1 == 'True'
				
				cur_params[name] = value1
		
		else:
			params = cur_params.copy()
			Block(name = s, params = params)
			if params:
				raise Exception('Unexpected params %s on creating <%s> (%s:%s)' % (', '.join(params.keys()), s, fn, i))
			
			cur_params['main'][0] += 1
			cur_params['main'][1] = num_line
			for prop in sides:
				if prop != 'main' and prop in cur_params:
					del cur_params[prop]

import os
for fn in sorted(os.listdir(path)):
	num_line, ext = os.path.splitext(fn)
	if ext == '.txt' and num_line.isdigit():
		load_file(fn, int(num_line))
