import pygame

from . import GLUtils
from .GLUtils import DrawQueue
from .singleton import Singleton


class TRenderer(Singleton):
    exists = False

    def __init__(self):
        super().__init__()
        self.prerendered_text = {}

    def render_text(self, text: str, font: pygame.font.Font, pos, queue: DrawQueue,
                    fore=(255, 255, 255), back=(0, 0, 0)):
        surf, tex = self.prerender_text(text, font, fore, back)
        text_rect: pygame.Rect = surf.get_rect(**pos)
        queue += (text_rect.x, text_rect.y, text_rect.width, text_rect.height), tex

    def prerender_text(self, text: str, font: pygame.font.Font, fore=(255, 255, 255), back=(0, 0, 0)):
        if (text, font, fore, back) in self.prerendered_text:
            return self.prerendered_text[text, font, fore, back]
        rendered_text = font.render(text, True, fore)
        background = pygame.Surface(
            (rendered_text.get_width() + 6, rendered_text.get_height() + 6), pygame.SRCALPHA)
        background.fill(back)
        background.blit(rendered_text, (3, 3))
        self.prerendered_text[text, font, fore, back] = background, GLUtils.surf_to_tex_default(background)
        return self.prerendered_text[text, font, fore, back]