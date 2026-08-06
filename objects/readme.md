Short description of <lang> for object creating:

Base:
* filename `${line}.txt` - use `${line}` as row by default in `images/blocks.png`
* `# any text` - comment (from start of line)
* `param_name new_value`
* `prefix some_prefix_` - prefix for next object names
* `postfix _some_postfix`
* `param_name None` - remove old value
* `object_name` (without spaces) - create `object_name` with current params, `main.x += 1`, `main.y = ${line}` and reset texture vars

Texture planes:
`main` - default texture for all planes of block
`side` - default for `left`, `right`, `front` and `back` (not for `top` or `bottom`), by default = `main`

Examples:
* `main 3`   - exec `main.x = 3`
* `main x y` - exec `main.x = x` and `main.y = y`
* `top x [y]`    - default = `main`
* `bottom x [y]` - default = `top`
* `side x [y]` - default = `main`
* `left  x [y]` - default = `side`
* `right x [y]` - default = `left`
* `front x [y]` - default = `side`
* `back  x [y]` - default = `front`
