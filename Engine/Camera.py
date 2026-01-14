from typing import Iterable

from .GLUtils import DrawQueue
from .object import Obj
from .vec2 import Vec2


class Camera(Obj):
    width: int
    zoom: float | int
    world_up_left: Vec2
    world_down_right: Vec2
    center: bool
    queue: DrawQueue

    def __init__(self, width: int, size: tuple[int, int], *, pos: Vec2 | tuple | None = None, parent: Obj = None):
        """


        :type width: int
        :type size: tuple[int, int]
        :type pos: Vec2 | tuple | None
        :type parent: Obj
        """
        super().__init__(pos=pos, parent=parent)
        self.size = Vec2.from_tuple(size)
        self.width = width
        self.queue = DrawQueue()
        self.recalculate_zoom()
        self.update()

    def recalculate_zoom(self):
        self.zoom = self.size.x / self._width

    @property
    def world_size(self):
        return self.size / self.zoom

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, w: int):
        if w <= 0:
            return
        self._width = w
        self.recalculate_zoom()

    @property
    def global_pos(self):
        return super().global_pos

    def screen_to_world(self, screen_pos):
        """

        :type screen_pos: Vec2
        :rtype: Vec2
        """
        return screen_pos / self.zoom + self.global_pos - self.world_size / 2

    def world_to_screen(self, world_pos):
        """

        :type world_pos: Vec2
        :rtype: Vec2
        """
        return (world_pos - self.global_pos + self.world_size / 2) * self.zoom

    def render(self, to_render: Obj | Iterable[Obj]):
        self.update()
        if isinstance(to_render, Obj):
            to_render = (to_render,)
        for obj in to_render:
            obj.render(self)
        self.queue()

    def update(self):
        self.world_up_left = self.global_pos - self.world_size / 2
        self.world_down_right = self.screen_to_world(self.size)
