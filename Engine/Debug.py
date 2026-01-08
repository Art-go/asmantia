import logging

import pygame

from .GLUtils import DrawQueue, GL, GLU
from .TextRenderUtils import TRenderer
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
        surf, tex = TRender.prerender_text(text, self.manager.font, back=DEBUG_BACK)
        text_rect: pygame.Rect = surf.get_rect(**pos)
        self.manager.queue += (text_rect.x, text_rect.y, text_rect.width, text_rect.height, tex)
        self.offset.y += text_rect.height

    def reset_offset(self):
        self.offset = Vec2()

    def update_size(self):
        self.pos = self.relpos[1]
        match self.relpos[0]:
            case "topright":
                self.pos += Vec2(self.manager.debug_surface.get_size()[0], 0)


class DebugManager:
    displays: list[DebugDisplay]
    font: pygame.font.Font
    debug_surface: pygame.Surface

    _instance = None
    exist = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        logger.debug(f"Instance of {cls} requested")
        return cls._instance

    def __init__(self, font: pygame.font.Font = None, size: tuple[int, int] = None,
                 display_positions: list[tuple[str, Vec2]] = None):
        if self.exist:
            return
        elif font is None or size is None or display_positions is None:
            raise TypeError(f"On first init, {__name__}.{type(self)} needs all arguments provided")
        self.displays: list[DebugDisplay] = []
        self.update_size(size)
        for do in display_positions:
            self.displays.append(DebugDisplay(do, self))
        self.font = font
        self.exist = True
        self.queue: DrawQueue = DrawQueue()
        logger.debug(f"Instance of {type(self)} is created")

    def __call__(self, text, d=0):
        self.displays[d].add(text)

    def update_size(self, size: tuple[int, int]):
        self.debug_surface = pygame.Surface(size)
        for d in self.displays:
            d.update_size()

    def draw(self):
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GLU.gluOrtho2D(0, *self.debug_surface.get_size(), 0)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        
        for i in self.displays:
            i.reset_offset()
        
        self.queue()
        
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopMatrix()
