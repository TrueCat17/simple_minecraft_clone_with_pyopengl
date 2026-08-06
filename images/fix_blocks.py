from PIL import Image

im = Image.open('blocks_orig.png').convert('RGBA')
im_px = im.load()
w, h = im.size
count_x, count_y = w // 16, h // 16

# make a frame from the copied pixels for each element

margin = 24
new_size = 16 + margin * 2
r = range(-margin, 16 + margin)

res = Image.new('RGBA', (count_x * new_size, count_y * new_size))
res_px = res.load()

def in_bounds(n, min_value, max_value):
	return min_value if n < min_value else max_value if n > max_value else n

for y in range(count_y):
	for x in range(count_x):
		part = im.crop((x * 16, y * 16, (x + 1) * 16, (y + 1) * 16))
		res.paste(part, (x * new_size + margin, y * new_size + margin))
		
		# fill frame by the nearest pixel
		for ty in r:
			from_y = y * 16 + in_bounds(ty, 0, 15)
			to_y = y * new_size + margin + ty
			
			for tx in r:
				if 0 <= tx <= 15 and 0 <= ty <= 15:
					continue
				
				from_x = x * 16 + in_bounds(tx, 0, 15)
				to_x = x * new_size + margin + tx
				
				res_px[to_x, to_y] = im_px[from_x, from_y]


# Fix colors of transparent pixels,
# because the linear filter ignores the alpha channel and only works with rgb
# Thereforce, transparent pixels must have the desired color, not just (0, 0, 0, 0)
# alpha = 1 for image optimizators, that can think (r, g, b, 0) = (0, 0, 0, 0)

w, h = res.size
d = (-1, 0, +1)
for y in range(h):
	for x in range(w):
		r, g, b, a = res_px[x, y]
		if a > 128:
			continue
		
		sr = sg = sb = 0
		count = 0
		for dy in d:
			ty = y + dy
			if not (0 <= ty < h):
				continue
			
			for dx in d:
				tx = x + dx
				if not (0 <= tx < w):
					continue
				
				r, g, b, a = res_px[tx, ty]
				if a < 128:
					continue
				
				sr += r
				sg += g
				sb += b
				count += 1
		
		if count:
			sr = round(sr / count)
			sg = round(sg / count)
			sb = round(sb / count)
		
		res_px[x, y] = (sr, sg, sb, 1)


res.save('blocks.png')
