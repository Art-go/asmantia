---
tags:
  - task
Status: Pending
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
- [ ] Add a Packer
- [x] make it so you can load sprite atlas as Atlas and get either `Texture` or `pygame.Surface` for each sprite
- [ ] Make cached tiles use atlases, probably in [[TaskX - Refactor Tile System]]^cache-tiles