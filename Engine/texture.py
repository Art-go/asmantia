from dataclasses import dataclass
from typing import Any

import pygame

from .vec2 import Vec2
from . import GLUtils


@dataclass(slots=True)
class Texture:
    tex_id: int
    surf: pygame.Surface
    uv: tuple[float, float, float, float]  # u0, v0, u1, v1
    pos: Vec2
    size: Vec2


class TextureAtlas:
    def __init__(self, surface: pygame.Surface, subtextures: dict[Any, tuple[Vec2, Vec2]] = None):
        """
        subtextures: dict[name: str, tuple[Vec2: Start, Vec2: Size]]

        :type surface:
        :type subtextures dict[Any, tuple[Vec2, Vec2]]
        """
        self.surface = surface
        self.tex = GLUtils.surface_to_texture(surface)
        self.size = Vec2.from_tuple(surface.get_size())
        self.textures: dict[Any, Texture] = {}

        if subtextures:
            self.add(subtextures)

    def calculate_uv(self, xy: Vec2) -> Vec2:
        return xy / self.size

    def add(self, subtextures: dict[Any, tuple[Vec2, Vec2]]) -> None:
        """
        Adds subtextures from dict
        Texture of atlas itself isn't modified

        :type subtextures: dict[Any, tuple[Vec2, Vec2]]
        """
        for name, (start_pos, size) in subtextures.items():
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

    def __getitem__(self, name: str) -> Texture:
        return self.textures[name]

    def __contains__(self, name: str) -> bool:
        return name in self.textures

    def clear(self) -> None:
        self.textures.clear()

    def __iter__(self):
        for name, t in self.textures.items(): yield name, t
