import pygame

from Object import Obj
from Vec2 import Vec2


class Camera(Obj):
    width: int
    screen: pygame.Surface
    zoom: float | int
    world_up_left: Vec2
    world_down_right: Vec2
    offset: Vec2
    center: bool

    def __init__(self, width: int, screen: pygame.Surface, *, pos=None, parent=None, center: bool = False):
        super().__init__(pos=pos, parent=parent)
        self.center = center
        self.screen = screen
        if center:
            self._width = screen.get_width()
            self.width = width
        else:
            self.offset = Vec2(0, 0)
            self._width = width
        self.recalculate_zoom()

    def recalculate_zoom(self):
        self.zoom = self.screen.get_width() / self._width
        if self.center:
            self.offset = -self.size / self.zoom / 2

    @property
    def size(self):
        return Vec2.from_tuple(self.screen.get_size())

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
        if self.center:
            self.offset = -self.size / self.zoom / 2

    @property
    def global_pos(self):
        return super().global_pos + self.offset

    def screen_to_world(self, screen_pos):
        """

        :type screen_pos: Vec2
        :rtype: Vec2
        """
        return screen_pos / self.zoom + self.global_pos

    def world_to_screen(self, world_pos):
        """

        :type world_pos: Vec2
        :rtype: Vec2
        """
        return (world_pos - self.global_pos) * self.zoom

    def render(self, to_render: Obj | list[Obj] | tuple[Obj]):
        self.update()
        if isinstance(to_render, Obj):
            to_render = (to_render,)
        for obj in to_render:
            obj.render(self)

    def update(self):
        self.world_up_left = self.global_pos
        self.world_down_right = self.screen_to_world(self.size)
