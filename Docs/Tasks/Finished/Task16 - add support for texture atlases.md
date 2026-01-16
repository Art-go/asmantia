---
tags:
  - task
Status: Finished
id: 16
aliases:
  - task#16
---
>[!tldr] Quick Description
>add an atlas class which manages itself, and make GLUtils.batch_draw, as well as DrawQueue support UV

## Steps
- [x] Add support for UV
	- [x] Which i envision as [[Task19 - Add Texture Class]]
- [x] Add Atlas Class
- [x] Add a `Packer`
	- [x] "Implement" `GuillotinePacker`
		- [x] Fix it...
	- [x] "Implement" `SkylinePacker`
		- [x] Fix it...
		- [x] Make text renderer use it
- [x] make it so you can load sprite atlas as Atlas and get either `Texture` or `pygame.Surface` for each sprite
- [ ] ? Make cached chunks use atlases, probably in [[TaskX - Refactor Tile System]]^cache-tiles

## Relevant new tasks
- [[Task24 - Rect class]]
- [[Task25 - Transpose SkylinePacker]]
- [[Task26 - Add transparency flag to Texture]]