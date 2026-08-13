from config import CHUNK_SIZE, CHUNK_HEIGHT, SEED
EDGES = (0, CHUNK_SIZE - 1)

from blocks import blocks, get_block_id


def generate(chunk):
	chunk.columns = []
	chunk_params = (chunk.x, chunk.z, chunk.columns, chunk)
	
	for fn in (set_landscape, add_oaks, add_spruces, add_short_grass, add_cane):
		fn(*chunk_params)
	
	# name,   chance to add (0-9901)
	plant_params = (
		('berries', 30),
		('flower_white',   5),
		('flower_yellow', 20),
		('flower_red',    20),
		('flower_purple',  7),
		('flower_blue',   10),
		('oak_sapling',      15),
		('dark_oak_sapling', 15),
		('spruce_sapling',   15),
	)
	for params in plant_params:
		add_plants(*chunk_params, *params)
	
	# name,   max count of groups,   group size (cube),   chance of remove each block in group (0-101),   max height
	ore_params = (
		('coal_ore',     2, 4, 60, -1),
		('copper_ore',   3, 3, 50, -1),
		('iron_ore',     5, 2, 50, -1),
		('diamond_ore',  3, 2, 50, 20),
		('gold_ore',     3, 3, 40, -1),
		('redstone_ore',     3, 3, 60, 30),
		('lapis_lazuli_ore', 2, 3, 50, 30),
		('emerald_ore',  2, 1, 30, -1),
		('amethyst_block', 3, 3, 30, 30),
		('gravel', 2, 4, 10, -1),
	)
	for params in ore_params:
		add_ore(*chunk_params, *params)



def get_chunk_random(x, z, n):
	x2 = x + 23
	z2 = z - 37
	return 3 * x2 * x2 + 59 * x + 17 * z * x + 29 * z2 + 71 * z * z + 53 * z + 43 * n + 19 * (n - z) + 31 * (x - n) + 971 * SEED

get_chunk_height_cache = {}
def get_chunk_height(x, z):
	key = (x, z)
	res = get_chunk_height_cache.get(key)
	if res is not None:
		return res
	
	res = 0
	n = 3
	for i in range(n):
		res += (get_chunk_random(x, z, i) / 57) % 1
	res /= n
	res **= 3
	
	res = min(res * 80 + 20, CHUNK_HEIGHT - 10)
	
	get_chunk_height_cache[key] = res
	return res



WATER_LEVEL = 30

air_id        = 0
bedrock_id    = get_block_id('bedrock')
stone_id      = get_block_id('stone')
dirt_id       = get_block_id('dirt')
grass_id      = get_block_id('grass')
water_id      = get_block_id('water')
sand_id       = get_block_id('sand')

plant_ground_ids = (dirt_id, grass_id)

oak_log_id    = get_block_id('oak_log')
oak_leaves_id = get_block_id('oak_leaves')

dark_oak_log_id    = get_block_id('dark_oak_log')
dark_oak_leaves_id = get_block_id('dark_oak_leaves')

spruce_log_id    = get_block_id('spruce_log')
spruce_leaves_id = get_block_id('spruce_leaves')

short_grass_id = get_block_id('short_grass')
sea_grass_id   = get_block_id('sea_grass')

cane_id = get_block_id('cane')


def set_landscape(chunk_x, chunk_z, columns, chunk):
	from math import sqrt, pow
	
	base_height_00 = get_chunk_height(chunk_x, chunk_z)
	base_height_01 = get_chunk_height(chunk_x, chunk_z + 1)
	base_height_10 = get_chunk_height(chunk_x + 1, chunk_z)
	base_height_11 = get_chunk_height(chunk_x + 1, chunk_z + 1)
	
	max_y = 0
	
	p = 7
	for x in range(CHUNK_SIZE):
		line = []
		columns.append(line)
		
		x2 = x * x
		sx = CHUNK_SIZE - x
		sx2 = sx * sx
		
		for z in range(CHUNK_SIZE):
			z2 = z * z
			sz = CHUNK_SIZE - z
			sz2 = sz * sz
			
			w_00 = sqrt(x2 + z2)
			w_01 = sqrt(x2 + sz2)
			w_10 = sqrt(sx2 + z2)
			w_11 = sqrt(sx2 + sz2)
			
			m = max(w_00, w_01, w_10, w_11)
			
			# f(x) = 2 - x;   1 is a mirror:
			#   f(0.8) = 1.2
			#   f(1.5) = 0.5
			
			w_00 = pow((2 - w_00 / m), p)
			w_01 = pow((2 - w_01 / m), p)
			w_10 = pow((2 - w_10 / m), p)
			w_11 = pow((2 - w_11 / m), p)
			
			base_height = (w_00 * base_height_00 + w_01 * base_height_01 + w_10 * base_height_10 + w_11 * base_height_11) / (w_00 + w_01 + w_10 + w_11)
			base_height = round(base_height)
			
			column = [
				[bedrock_id, 1],
				[stone_id, base_height],
				[dirt_id, 2],
			]
			line.append(column)
			count = 1 + base_height + 2
			
			if count < WATER_LEVEL:
				column.append([water_id, WATER_LEVEL + 1 - count])
				count = WATER_LEVEL + 1
			else:
				if count == WATER_LEVEL:
					column.append([sand_id, 1])
				else:
					column.append([grass_id, 1])
				count += 1
			
			if count > max_y:
				max_y = count
			
			column.append([air_id, CHUNK_HEIGHT - count])
	
	chunk.max_y = max_y


def add_oaks(chunk_x, chunk_z, columns, chunk):
	tree_count = get_chunk_random(chunk_x, chunk_z, 123) % 11 - 5
	
	min_pos = 1
	max_pos = CHUNK_SIZE - 1 - min_pos
	diff_pos = max_pos - min_pos + 1
	
	min_height = 4
	max_height = 5
	diff_height = max_height - min_height + 1
	
	tree_list = []
	for i in range(10):
		if len(tree_list) >= tree_count:
			break
		
		x = get_chunk_random(chunk_x, chunk_z, oak_log_id * 51 + i * 2 + 0) % diff_pos + min_pos
		z = get_chunk_random(chunk_x, chunk_z, oak_log_id * 51 + i * 2 + 1) % diff_pos + min_pos
		
		column = columns[x][z]
		pre_last = column[-2]
		resource = pre_last[0]
		if resource not in plant_ground_ids:
			continue
		
		skip = False
		for tx, tz in tree_list:
			dx = abs(x - tx)
			dz = abs(z - tz)
			if max(dx, dz) < 2 or dx == dz:
				skip = True
				break
		if skip:
			continue
		
		tree_list.append((x, z))
		
		last = column[-1]
		y = CHUNK_HEIGHT - last[1] - pre_last[1]
		height = get_chunk_random(chunk_x, chunk_z, oak_log_id * 51 + i * 3) % diff_height + min_height
		
		r = get_chunk_random(chunk_x, chunk_z, oak_log_id * 51 + i * 31 - 19) % 971
		if r > 400:
			log_id    = oak_log_id
			leaves_id = oak_leaves_id
		else:
			log_id    = dark_oak_log_id
			leaves_id = dark_oak_leaves_id
		
		chunk.set_blocks_in_column(y,              1,      dirt_id,   column, update_max_y = False)
		chunk.set_blocks_in_column(y + 1,          height, log_id,    column, update_max_y = False)
		chunk.set_blocks_in_column(y + 1 + height, 2,      leaves_id, column, update_max_y = False)
		
		def add_leaves(x, y, z, count):
			for dy in range(count):
				if chunk.get_resource(x, y + dy, z) == 0:
					chunk.set_blocks_in_column(y + dy, 1, leaves_id, pos = (x, z), update_max_y = False)
		
		for dx, dz in ((-1, 0), (+1, 0), (0, -1), (0, +1)):
			add_leaves(x + dx, y + height - 1, z + dz, count = 3)
		
		for dx, dz in ((-1, -1), (-1, +1), (+1, -1), (+1, +1)):
			add_leaves(x + dx, y + height - 1, z + dz, count = 2)


def add_spruces(chunk_x, chunk_z, columns, chunk):
	tree_count = get_chunk_random(chunk_x, chunk_z, 234) % 7 - 4
	
	min_pos = 2
	max_pos = CHUNK_SIZE - 1 - min_pos
	diff_pos = max_pos - min_pos + 1
	
	min_height = 7
	max_height = 12
	diff_height = max_height - min_height + 1
	
	tree_list = []
	for i in range(10):
		if len(tree_list) >= tree_count:
			break
		
		x = get_chunk_random(chunk_x, chunk_z, spruce_log_id * 51 + i * 2 + 0) % diff_pos + min_pos
		z = get_chunk_random(chunk_x, chunk_z, spruce_log_id * 51 + i * 2 + 1) % diff_pos + min_pos
		
		column = columns[x][z]
		pre_last = column[-2]
		resource = pre_last[0]
		if resource not in plant_ground_ids:
			continue
		
		skip = False
		for tx, tz in tree_list:
			dx = abs(x - tx)
			dz = abs(z - tz)
			if max(dx, dz) < 3 or dx == dz:
				skip = True
				break
		if skip:
			continue
		
		tree_list.append((x, z))
		
		last = column[-1]
		y = CHUNK_HEIGHT - last[1] - pre_last[1]
		height = get_chunk_random(chunk_x, chunk_z, spruce_log_id * 51 + i * 3) % diff_height + min_height
		
		chunk.set_blocks_in_column(y,              1,      dirt_id,          column, update_max_y = False)
		chunk.set_blocks_in_column(y + 1,          height, spruce_log_id,    column, update_max_y = False)
		chunk.set_blocks_in_column(y + 1 + height, 1,      spruce_leaves_id, column, update_max_y = False)
		
		def add_leaves(x, y, z):
			if chunk.get_resource(x, y, z) == 0:
				chunk.set_blocks_in_column(y, 1, spruce_leaves_id, pos = (x, z), update_max_y = False)
		
		dy = height
		while dy > 3:
			for dx, dz in ((-1, 0), (+1, 0), (0, -1), (0, +1)):
				add_leaves(x + dx, y + dy, z + dz)
			
			if dy != height:
				for dx in range(-2, 3):
					for dz in range(-2, 3):
						if (dx, dz) not in ((-2, -2), (-2, 2), (2, -2), (2, 2)):
							add_leaves(x + dx, y + dy - 1, z + dz)
			
			dy -= 2


def add_short_grass(chunk_x, chunk_z, columns, chunk):
	for x, line in enumerate(columns):
		for z, column in enumerate(line):
			water = False
			pre_last = column[-2]
			resource = pre_last[0]
			if resource == water_id:
				water = True
				pre_last = column[-3]
				resource = pre_last[0]
			
			if resource not in plant_ground_ids:
				continue
			
			# skip group?
			r = get_chunk_random(chunk_x, chunk_z, x // 3 + z // 2 * 19) % 317
			if r > 50:
				continue
			
			# skip unit in group?
			r = get_chunk_random(chunk_x, chunk_z, x * -122 + z * 55) % 123
			if r > 40:
				continue
			
			i = 2 if water else 1
			column[-i][1] -= 1
			if column[-i][1] == 0:
				column.pop(-i)
				i -= 1
			column.insert(-i, [sea_grass_id if water else short_grass_id, 1])


def add_cane(chunk_x, chunk_z, columns, chunk):
	for x, line in enumerate(columns):
		if x in EDGES:
			continue
		
		for z, column in enumerate(line):
			if z in EDGES:
				continue
			
			pre_last = column[-2]
			resource = pre_last[0]
			if resource != sand_id:
				continue
			
			r = get_chunk_random(chunk_x, chunk_z, x * 23 + z * 29) % 53
			if r > 10:
				continue
			
			count = 2 + r % 3
			
			for dx, dz in ((0, +1), (0, -1), (+1, 0), (-1, 0)):
				near_column = columns[x + dx][z + dz]
				pre_last = near_column[-2]
				resource = pre_last[0]
				if resource == water_id:
					break
			else:
				continue
			
			column[-1][1] -= count
			column.insert(-1, [cane_id, count])


def add_plants(chunk_x, chunk_z, columns, chunk, plant_name, chance):
	plant_id = get_block_id(plant_name)
	plant_rnd = plant_id * 29 + 17
	
	for x, line in enumerate(columns):
		for z, column in enumerate(line):
			pre_last = column[-2]
			resource = pre_last[0]
			if resource != grass_id:
				continue
			
			r = get_chunk_random(chunk_x, chunk_z, plant_rnd + x * 1001 - z * 13) % 9901
			if r > chance:
				continue
			
			column[-1][1] -= 1
			column.insert(-1, [plant_id, 1])


def add_ore(chunk_x, chunk_z, columns, chunk, ore_name, max_group_count, group_size, chance_to_remove, max_y):
	group_count = get_chunk_random(chunk_x, chunk_z, 231) % (max_group_count + 1)
	
	max_pos = CHUNK_SIZE - group_size
	
	chunk_max_y = chunk.max_y
	r = range(group_size)
	max_y = CHUNK_HEIGHT if max_y < 0 else max_y
	
	ore_id = get_block_id(ore_name)
	ore_rnd = ore_id * 1291 + 983
	
	for i in range(group_count):
		y = get_chunk_random(chunk_x, chunk_z, ore_rnd + i * 859 + 13) % chunk_max_y
		if y > max_y:
			continue
		
		x = get_chunk_random(chunk_x, chunk_z, ore_rnd + i * 117 + 7) % max_pos
		z = get_chunk_random(chunk_x, chunk_z, ore_rnd + i * 353 - 5) % max_pos
		
		for dx in r:
			tx = x + dx
			for dz in r:
				tz = z + dz
				pos = (tx, tz)
				
				for dy in r:
					ty = y + dy
					resource = chunk.get_resource(tx, ty, tz)
					if resource != stone_id:
						continue
					
					rnd = get_chunk_random(chunk_x, chunk_z, ore_rnd + 1234 + 17 * tx + 11 * ty + 37 * tz - tx * tz * 3) % 101
					if rnd < chance_to_remove:
						continue
					
					chunk.set_blocks_in_column(ty, 1, ore_id, pos = pos, update_max_y = False)
