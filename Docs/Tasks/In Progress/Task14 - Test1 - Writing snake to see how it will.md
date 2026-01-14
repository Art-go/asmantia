---
tags:
  - task
Status: In Progress
id: 14
aliases:
  - task#14
---
>[!tldr] Quick Description
> Try to write a snake to test the engine and see what can be impoved

## Steps
- [x] Copy `client.py` and get rid or everything not useful
- [x] Make a grid
	- [x] Make a grid class?
- [x] Add a snake
- [x] Add ticking
	- [x] Make snake move
- [x] Add apple
	- [x] Make snake eat apple
- [x] Add score
- [x] Add death
	- [x] Bound snake to the screen
- [ ] Add restart button
	- [ ] [[Task17 - Add UiButton]]
- [ ] Add start button
	- [ ] [[Task17 - Add UiButton]]
## Relevant new tasks
- Move input handling to Engine, tho this is probably deeply related to scene system
- do something with this snippet, probably move it to cam?
```python
###########  
# Drawing #  
###########  
GL.glClear(GL.GL_COLOR_BUFFER_BIT)  
GLUtils.set_size_center(cam.width, height / width * cam.width)  
GL.glLoadIdentity()  
GL.glTranslatef(-cam.global_pos.x, -cam.global_pos.y, 0)  
  
# Render everything #  
cam.render(objects)
```
- [[Task15 - (PERFOMANCE) Group rendering by texture]]