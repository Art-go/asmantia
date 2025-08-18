import pygame

import GLUtils
import Utils
from Object import Obj
from Vec2 import Vec2


class Renderer(Obj):
    src: pygame.Surface
    tex: int
    size: Vec2

    def __init__(self, img: pygame.Surface, pos=None, *, tex=None, parent=None, scalable=True, pivot=(0.5, 0.5), scale=(1, 1)):
        super().__init__(pos=pos, parent=parent)
        self.src = img.convert_alpha()
        self.tex = tex if tex is not None else GLUtils.surface_to_texture(self.src)
        self.size = Vec2.from_tuple(self.src.get_size())
        self.scalable = scalable
        self.pivot = pivot
        self.scale = scale

    def render(self, cam):
        """
        :type cam: Camera.Camera
        """
        pos = self.global_pos
        size = self.size if self.scalable else self.size / cam.zoom
        size *= self.scale
        pos -= size * self.pivot
        GLUtils.queue_draw(pos.x, pos.y, size.x, size.y, self.tex)


class TextRenderer(Renderer):
    def __init__(self, text: str, font: pygame.font.Font, fore: tuple, back: tuple,
                 pos=None, *, parent=None, scalable=True, pivot=(0.5, 0.5), scale=(1, 1)):
        self.font = font
        self.fore = fore
        self.back = back
        self._text = text
        text = Utils.prerender_text(text, font, fore, back)
        super().__init__(text[0], pos=pos, tex=text[1], parent=parent, scalable=scalable, pivot=pivot, scale=scale)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        text = Utils.prerender_text(text, self.font, self.fore, self.back)
        self.src = text[0]
        self.tex = text[1]

