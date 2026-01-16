import logging
from functools import wraps

import pygame

from .GLUtils import DrawQueue, screen_render
from .TextRenderUtils import TRenderer
from .singleton import singleton
from .vec2 import Vec2

TRender = TRenderer()

DEBUG_BACK = (0, 0, 0, 127)

logger = logging.getLogger(__name__)


class DebugDisplay:
    pos: Vec2

    def __init__(self, relpos: tuple[str, Vec2], debug_manager):
        """

        :type debug_manager: DebugManager
        """
        self.offset: Vec2 = Vec2()
        self.relpos = relpos
        self.manager = debug_manager
        self.update_size()

    def add(self, text: str):
        pos = {self.relpos[0]: (self.pos + self.offset).tuple}
        tex = TRender.prerender_text(text, self.manager.font, back=DEBUG_BACK)
        text_rect: pygame.Rect = tex.surf.get_rect(**pos)
        self.manager.queue += (text_rect.x, text_rect.y, text_rect.width, text_rect.height), tex
        self.offset.y += text_rect.height

    def reset_offset(self):
        self.offset = Vec2()

    def update_size(self):
        self.pos = self.relpos[1]
        match self.relpos[0]:
            case "topright":
                self.pos += Vec2(self.manager.size[0], 0)


@singleton
class DebugManager:
    displays: list[DebugDisplay]
    font: pygame.font.Font
    screen: pygame.Surface
    queue: DrawQueue

    initialized = False

    def init(self, font: pygame.font.Font = None, size: tuple[int, int] = None,
             display_positions: list[tuple[str, Vec2]] = None):
        if self.initialized:
            raise RuntimeError("Init was called second time")
        self.initialized = True

        self.displays: list[DebugDisplay] = []
        self.update_size(size)
        for do in display_positions:
            self.displays.append(DebugDisplay(do, self))
        self.font = font
        self.queue: DrawQueue = DrawQueue()
        logger.debug(f"Instance of {self.__class__} is initialized")

    @staticmethod
    def check_init(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.initialized:
                raise RuntimeError("Instance wasn't initialized. Perhaps, you forgot to call .init()?")
            method(self, *args, **kwargs)

        return wrapper

    @check_init
    def __call__(self, text, d=0):
        self.displays[d].add(text)

    @check_init
    def update_size(self, size: tuple[int, int]):
        self.screen = pygame.Surface(size)
        for d in self.displays:
            d.update_size()

    @property
    def size(self):
        return self.screen.get_size()

    @check_init
    @screen_render
    def draw(self):
        for i in self.displays:
            i.reset_offset()

        self.queue()
