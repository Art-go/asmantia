import pygame

import Camera
import Utils
from Object import Obj
from Renderer import Renderer
from Vec2 import Vec2, zero


class Canvas(Obj):
    def __init__(self, cam: Camera.Camera):
        super().__init__()
        self.cam = cam
        self.pivot = zero

    @property
    def size(self):
        return self.cam.size


class UiElement(Obj):
    parent: "Canvas | UiElement"

    def __init__(self, parent: "Canvas | UiElement", pos: tuple | Vec2 = (0, 0), size: tuple | Vec2 = (0, 0),
                 relpos: tuple | Vec2 = (0, 0), pivot: tuple| Vec2 = (0, 0), *args, **kwargs):
        self.size = zero
        # noinspection PyArgumentList
        super().__init__(pos=pos, parent=parent, *args, **kwargs)
        self.relpos = Vec2.from_tuple(relpos) if isinstance(relpos, tuple) else relpos
        size = Vec2.from_tuple(size) if isinstance(size, tuple) else size
        if size.x != 0 or size.y != 0:
            self.size = size
        self.pivot = Vec2.from_tuple(pivot) if isinstance(pivot, tuple) else pivot

    @property
    def global_pos(self):
        return self.pos + self.parent.global_pos + (self.parent.size * (self.relpos - self.parent.pivot))


class UiRenderer(UiElement, Renderer):
    def __init__(self, img, relpos: tuple | Vec2, parent: "Canvas | UiElement", size: tuple | Vec2 = (0, 0),
                 **kwargs):
        super().__init__(img=img, size=size, relpos=relpos, parent=parent, **kwargs)


class UiTextRenderer(UiRenderer):
    def __init__(self, text: str, font: pygame.font.Font, fore: tuple, back: tuple, pos: Vec2 | tuple,
                 parent: Canvas | UiElement, relpos: tuple | Vec2, **kwargs):
        text = Utils.prerender_text(text, font, fore, back)
        super().__init__(text[0], tex=text[1], parent=parent, relpos=relpos, pos=pos, **kwargs)
