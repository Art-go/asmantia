import io
import json
import os

from Object import Obj
from Tilemap import TileMap, Tileset
from Vec2 import Vec2


class Map(Obj):
    maps: list[TileMap]

    def __init__(self, maps, *, pos=None, parent=None):
        super().__init__(pos=pos, parent=parent)
        self.maps = maps

    @classmethod
    def from_folder(cls, folder: str | os.PathLike, tileset: Tileset, *, parent=None):
        with open(folder + "/info.json") as f:
            info: dict = json.load(f)
        mp = cls([], pos=-Vec2.from_tuple(info.get("offset", (0, 0))), parent=parent)
        info["mapping"] = {int(k): v for k, v in info["mapping"].items()}
        for m in info["layers"]:
            with open(f"{folder}/{info["name"]}_{m}.png", "rb") as f:
                mp.maps.append(TileMap.from_image(io.BytesIO(f.read()), tileset, info["mapping"], parent=mp))
        return mp

    @classmethod
    def from_folder_server(cls, folder: str | os.PathLike):
        with open(folder + "/info.json") as f:
            info: dict = json.load(f)
        return info,

    def render(self, cam):
        for m in self.maps:
            m.render(cam)
