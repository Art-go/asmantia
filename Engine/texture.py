from dataclasses import dataclass
from typing import Any, Type

import pygame

from .vec2 import Vec2
from . import GLUtils
from .packer import Packer, GuillotinePacker


@dataclass(slots=True)
class Texture:
    tex_id: int
    surf: pygame.Surface
    uv: tuple[float, float, float, float]  # u0, v0, u1, v1
    pos: Vec2
    size: Vec2


class TextureAtlas:
    def __init__(self,
                 surface: pygame.Surface,
                 subtextures: dict[Any, tuple[Vec2, Vec2]] = None,
                 packer: Type[Packer] = GuillotinePacker):
        """
        subtextures: dict[name: str, tuple[Vec2: Start, Vec2: Size]]
        packer: can be any implementation of .packer.Packer, defaults to Guillotine

        :type packer: Type[Packer]
        :type surface:
        :type subtextures dict[Any, tuple[Vec2, Vec2]]
        """
        self.surface = surface
        self.tex = GLUtils.surface_to_texture(surface)
        self.size = Vec2.from_tuple(surface.get_size())
        self.textures: dict[Any, Texture] = {}

        self.packer = packer(self.size)

        if subtextures:
            self.add(subtextures)

    def calculate_uv(self, xy: Vec2) -> Vec2:
        return xy / self.size

    def add(self, subtextures: dict[Any, tuple[Vec2, Vec2]]) -> None:
        """
        Adds pre-defined subtextures from dict
        Texture of atlas itself isn't modified

        :type subtextures: dict[Any, tuple[Vec2, Vec2]]
        """
        for name, (start_pos, size) in subtextures.items():
            self.packer.add_used_rect(start_pos, size)

            rect = pygame.Rect(start_pos.x, start_pos.y, size.x, size.y)
            subsurface = self.surface.subsurface(rect)

            u0, v0 = self.calculate_uv(start_pos)
            u1, v1 = self.calculate_uv(start_pos + size)

            texture = Texture(
                tex_id=self.tex,
                surf=subsurface,
                uv=(u0, v0, u1, v1),
                pos=start_pos,
                size=size
            )

            self.textures[name] = texture

    def pack(self, textures: dict[Any, pygame.Surface]) -> dict[Any, Texture]:
        """
        Packs new subtextures from dict
        !!! This changes the texture itself

        Returns dict of successfully packed textures

        :type textures: dict[Any, pygame.Surface]
        :rtype: tuple[dict[Any, Texture], dict[Any, pygame.Surface]]
        """
        packed = {}

        for name, surf in textures.items():
            size = Vec2.from_tuple(surf.get_size())
            position = self.packer.pack(size)

            if position is None:
                # No space available
                continue

            # Update tex and surface
            self.surface.blit(surf, (position.x, position.y))
            GLUtils.update_texture(self.tex, surf, position)

            u0, v0 = self.calculate_uv(position)
            u1, v1 = self.calculate_uv(position + size)

            texture = Texture(
                tex_id=self.tex,
                surf=surf.copy(),
                uv=(u0, v0, u1, v1),
                pos=position,
                size=size
            )

            self.textures[name] = texture
            packed[name] = texture

        return packed

    def __getitem__(self, name: str) -> Texture:
        return self.textures[name]

    def __contains__(self, name: str) -> bool:
        return name in self.textures

    def clear(self) -> None:
        self.textures.clear()

    def __iter__(self):
        for name, t in self.textures.items():
            yield name, t
