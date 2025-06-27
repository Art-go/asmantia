import pygame

import GLUtils
import Utils
from Object import Obj
from Vec2 import Vec2


class Renderer(Obj):
    src: pygame.Surface
    tex: int
    size: Vec2

    def __init__(self, img: pygame.Surface, pos=None, *, parent=None, scalable=True):
        super().__init__(pos=pos, parent=parent)
        self.src = img.convert_alpha()
        self.tex = GLUtils.surface_to_texture(img)
        self.size = Vec2.from_tuple(self.src.get_size())
        self.scalable = scalable

    def render(self, cam: "Camera.Camera"):
        pos = self.global_pos
        size = self.size if self.scalable else self.size / cam.zoom
        pos -= size / 2
        GLUtils.queue_draw(pos.x, pos.y, size.x, size.y, self.tex)


class TextRenderer(Renderer):
    def __init__(self, text: str, font: pygame.font.Font, fore: tuple, back: tuple, pos=None,
                 *, parent=None, scalable=True):
        super().__init__(Utils.prerender_text(text, font, fore, back)[0], pos, parent=parent, scalable=scalable)
