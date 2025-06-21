import json
from dataclasses import dataclass

import pygame

from Object import Obj
from Renderer import Renderer, TextRenderer


class Character(Obj):
    font: pygame.font.Font
    fore: tuple
    back: tuple

    @classmethod
    def setup_nicks(cls, *, font: pygame.font.Font = None, fore: tuple = None, back: tuple = None):
        if font:
            cls.font = font
        if fore:
            cls.fore = fore
        if back:
            cls.back = back

    def __init__(self, name: str, sprite: Renderer, pos=None, *, parent=None):
        super().__init__(pos=pos, parent=parent)
        self.sprite = sprite
        sprite.parent = self
        y = sprite.size.y / 2 + 3
        self.name = TextRenderer(name, self.font, self.fore, self.back, parent=self, pos=(0, -y), scalable=False)

    def render(self, cam):
        self.sprite.render(cam)
        self.name.render(cam)


@dataclass
class CharSheet:
    health: int
    max_health: int
    mana: int
    max_mana: int

    @classmethod
    def from_dict(cls, d: dict) -> "CharSheet":
        return cls(**d)

    @classmethod
    def from_json(cls, jsons: str):
        return cls.from_dict(json.loads(jsons))
