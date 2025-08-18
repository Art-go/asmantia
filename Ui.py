import pygame

import Camera
from Object import Obj
from Renderer import Renderer, TextRenderer
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
    def __init__(self, img, parent: "Canvas | UiElement", relpos: tuple | Vec2 = (0, 0), size: tuple | Vec2 = (0, 0),
                 **kwargs):
        super().__init__(img=img, size=size, relpos=relpos, parent=parent, **kwargs)


class UiTextRenderer(UiElement, TextRenderer):
    def __init__(self, text: str, font: pygame.font.Font, fore: tuple, back: tuple, parent: Canvas | UiElement, **kwargs):
        super().__init__(parent=parent, text=text, font=font, fore=fore, back=back, **kwargs)


class UiProgressBar(UiElement):
    def __init__(self, img_back, img_bar, parent, progress: float = 0, pos=(0, 0), size=(100, 10), relpos=(0, 0),
                 pivot=(0, 0), *, tex_back=None, tex_bar=None):
        super().__init__(parent=parent, pos=pos, size=size, relpos=relpos, pivot=pivot)
        self._progress = 0
        self.back = UiRenderer(img=img_back, tex=tex_back, size=size, parent=self)
        self.bar = UiRenderer(img=img_bar, tex=tex_bar, size=size, parent=self)
        self.progress=progress

    def render(self, *args, **kwargs):
        self.back.render(*args, **kwargs)
        self.bar.render(*args, **kwargs)

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, progress):
        self._progress=progress
        s: Vec2 = self.size.copy()
        s.x = s.x * self._progress
        self.bar.size = s
