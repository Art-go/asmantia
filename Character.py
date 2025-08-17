import json
from dataclasses import dataclass, asdict

import pygame

from Object import Obj
from Renderer import Renderer, TextRenderer
from Vec2 import Vec2


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

    def __init__(self, name: str = None, sprite: Renderer = None, sheet: "CharSheet" = None, pos=None, *, parent=None):
        if sheet:
            self.sheet = sheet
            sprite = Renderer(sheet.sprite)
            name = sheet.name
            pos = sheet.pos
        else:
            self.sheet = CharSheet()
            sheet.sprite = sprite.src
            sheet.name = name
            sheet.pos = pos
        super().__init__(pos=pos, parent=parent)
        self.sprite = sprite
        self.sprite.parent = self
        y = self.sprite.size.y / 2 + 3
        self.name = name
        self.name_tag = TextRenderer(name, self.font, self.fore, self.back, parent=self, pos=(0, -y), scalable=False)

    def render(self, cam):
        self.sprite.render(cam)
        self.name_tag.render(cam)


@dataclass
class CharSheet:
    health: int = 5
    max_health: int = 5
    mana: int = 0
    max_mana: int = 0
    speed: float = 1
    level: int = 1
    sprite: pygame.Surface = None
    sprite_info: tuple[str, int, int, int, int] = None
    title: str = "Nobody"
    race: str = "Human"
    name: str = "Noname"
    pos: Vec2 = None
    server: bool = False
    ID: str = ""

    def __post_init__(self):
        self.pos = Vec2.from_tuple(self.pos) if self.pos else Vec2()
        if not self.ID:
            self.ID = f"{self.name}, {self.race}, {self.title}, PH"
        if self.sprite_info and not self.server:
            self.sprite = pygame.image.load(self.sprite_info[0])\
                                      .subsurface(self.sprite_info[1:])\
                                      .convert_alpha()

    @classmethod
    def from_dict(cls, d: dict, server: bool=False) -> "CharSheet":
        return cls(server=server, **d)

    @classmethod
    def from_json(cls, jsons: str, server: bool=False) -> "CharSheet":
        return cls.from_dict(json.loads(jsons), server=server)

    def to_json(self):
        dct = asdict(self)
        dct.pop("sprite")
        dct.pop("server")
        dct["pos"] = tuple(dct["pos"].values())
        return json.dumps(dct)
