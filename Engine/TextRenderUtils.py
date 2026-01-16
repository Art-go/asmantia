import logging

import pygame

from .GLUtils import DrawQueue
from .singleton import singleton
from .texture import Texture, TextureAtlas
from .packer import SkylinePacker
from .vec2 import Vec2

logger = logging.getLogger(__name__)


@singleton
class TRenderer:
    exists = False
    atlases: dict[pygame.font.Font, list[TextureAtlas]]
    prerendered_text: dict[
        tuple[str, pygame.font.Font, tuple[int, int, int] | tuple[int, int, int, int],
                                     tuple[int, int, int] | tuple[int, int, int, int]],
        Texture
    ]
    atlas_size = Vec2(2048, 2048)
    packer = SkylinePacker

    def __init__(self):
        self.prerendered_text = {}
        self.atlases = {}

    def render_text(self, text: str, font: pygame.font.Font, pos, queue: DrawQueue,
                    fore=(255, 255, 255), back=(0, 0, 0)):
        tex = self.prerender_text(text, font, fore, back)
        text_rect: pygame.Rect = tex.surf.get_rect(**pos)
        queue += (text_rect.x, text_rect.y, text_rect.width, text_rect.height), tex

    def prerender_text(self, text: str, font: pygame.font.Font, fore=(255, 255, 255), back=(0, 0, 0),
                       atlas: TextureAtlas = None) -> Texture:
        """
        Pre-renders text, if necessary, otherwise looks up Texture object

        :type text: str
        :type font: pygame.font.Font
        :type fore: tuple[int, int, int] | tuple[int, int, int, int]
        :type back: tuple[int, int, int] | tuple[int, int, int, int]
        :type atlas: TextureAtlas
        :rtype: Texture
        """

        if (text, font, fore, back) in self.prerendered_text:
            return self.prerendered_text[text, font, fore, back]

        rendered_text = font.render(text, True, fore)
        background = pygame.Surface(
            (rendered_text.get_width() + 6, rendered_text.get_height() + 6), pygame.SRCALPHA)
        background.fill(back)
        background.blit(rendered_text, (3, 3))
        text_size = Vec2.from_tuple(background.get_size())

        # adding to atlas
        # checking if it can even fit
        if self.atlas_size.lt_or(text_size):
            raise ValueError(f"String too long: can support {self.atlas_size}, given {text_size}")

        # checking if atlas is given
        if atlas is None:
            # if list of atlases exists for this font
            if font not in self.atlases:
                logger.debug(f"{self.__class__}: New atlas: New font")
                atlas = self.new_atlas()
                self.atlases[font] = [atlas]
            else:
                atlas = self.atlases[font][-1]

        # packing it to atlas
        texture = atlas.pack({(text, fore, back): background})

        # checking if it had successfully packed it, otherwise creating new atlas
        if not texture:
            logger.debug(f"{self.__class__}: New atlas: Not enough space")
            self.atlases[font].append(atlas := self.new_atlas())
            texture = atlas.pack({(text, fore, back): background})

        self.prerendered_text[text, font, fore, back] = texture[text, fore, back]
        return self.prerendered_text[text, font, fore, back]

    def new_atlas(self):
        return TextureAtlas.create_empty(self.atlas_size, packer=self.packer)