import io
import json
import os

from Object import Obj
from Tilemap import TileMap, Tileset


class Map(Obj):
    maps: list[TileMap]

    def __init__(self, maps, *, pos=None, parent=None):
        super().__init__(pos=pos, parent=parent)
        self.maps = maps

    @classmethod
    def from_folder(cls, folder: str | os.PathLike, tileset: Tileset, *, parent=None):
        with open(folder + "/info.json") as f:
            info: dict = json.load(f)
        maps = []
        info["mapping"] = {int(k): v for k, v in info["mapping"].items()}
        for m in info["layers"]:
            with open(f"{folder}/{info["name"]}_{m}.png", "rb") as f:
                maps.append(TileMap.from_image(io.BytesIO(f.read()), tileset, info["mapping"]))
        return cls(maps, pos=info.get("pos", None), parent=parent)

    @classmethod
    def from_folder_server(cls, folder: str | os.PathLike):
        with open(folder + "/info.json") as f:
            info: dict = json.load(f)
        return info,

    def render(self, cam):
        for m in self.maps:
            m.render(cam)
