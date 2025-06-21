import io
import json
import os
from math import ceil

import pygame
from PIL import Image

from Camera import Camera
from Object import Obj
from Renderer import Renderer
from Vec2 import Vec2

CHUNK_SIZE = 32


class Tile(Renderer):

    def __init__(self, img: pygame.Surface, *, parent=None):
        super().__init__(img, parent=parent)

    # noinspection PyMethodOverriding
    def render(self, cam, pos):
        """

        :type pos: list[Vec2]
        :type cam: Camera.Camera
        """
        if cam.zoom not in self.scaled_img:
            self.scale(cam.zoom)
        img = self.scaled_img[cam.zoom]
        for p in pos:
            cam.screen.blit(img, cam.world_to_screen(p).tuple)


class DirectionalTile(Tile):
    imgs: list[pygame.Surface]
    scaled_imgs: dict[int | float, list[pygame.Surface]]

    # noinspection PyMissingConstructor
    def __init__(self, imgs: list[pygame.Surface], *, parent=None):
        self.parent = parent
        self.imgs = [i.convert_alpha() for i in imgs]
        self.scaled_imgs = {}

    def scale(self, factor: int | float):
        assert len(self.scaled_imgs) < 1024
        self.scaled_imgs[factor] = []
        for i in self.imgs:
            self.scaled_imgs[factor].append(
                pygame.transform.scale(i, ceil(Vec2.from_tuple(i.get_size()) * factor).tuple))

    # noinspection PyMethodOverriding
    def render(self, cam, pos):
        """

        :type pos: list[list[Vec2]]
        :type cam: Camera.Camera
        """
        if cam.zoom not in self.scaled_imgs:
            self.scale(cam.zoom)
        for i, tpos in enumerate(pos):
            img = self.scaled_imgs[cam.zoom][i]
            for p in tpos:
                cam.screen.blit(img, cam.world_to_screen(p).tuple)


class Tileset:
    tiles: dict[str, Tile]

    def __init__(self, tile_size: int = 16):
        self.tile_size = tile_size

    def load_set(self, path: os.PathLike | str):
        tileset = pygame.image.load(path).convert_alpha()
        self.tiles = {}
        with open(path + ".json") as f:
            tiles: dict[str, dict[str, list]] = json.load(f)
        for t, tile in tiles["mapping"].items():
            match tile[0]:
                case "DIRECTIONAL":
                    imgs = []
                    for i in range(16):
                        imgs.append(tileset.subsurface(tile[1][i]))
                    self.tiles[t] = DirectionalTile(imgs)
                case _:
                    assert len(tile) == 4
                    self.tiles[t] = Tile(tileset.subsurface(tile))
        return self


class Chunk(Obj):
    set: Tileset
    grid: list[list[Tile | None]]
    tile_pos: dict[Tile, list[Vec2] | list[list[Vec2]]]
    cached: pygame.Surface
    cached_valid: bool = False
    cached_scaled: dict[int, pygame.Surface]
    cam: Camera
    size: Vec2
    is_empty: bool = True

    def __init__(self, tileset, tile_pos: dict[Tile, list[Vec2] | list[list[Vec2]]],
                 grid: list[list[Tile | None]], tile_size: int, size: Vec2, pos=None, parent=None):
        super().__init__(pos=pos, parent=parent)
        self.set = tileset
        self.tile_size = tile_size
        self.grid = grid
        self.tile_pos = tile_pos
        self.cached_scaled = {}
        self.size = size
        self.cached = pygame.Surface(self.size.tuple, pygame.SRCALPHA)
        self.cached_valid = False
        self.cam = Camera(self.size.x, self.cached, parent=self)
        self.check_empty()

    def scale(self, factor: int | float):
        assert len(self.cached_scaled) < 1024
        self.cached_scaled[factor] = pygame.transform.scale(self.cached, ceil(self.size * factor).tuple)

    def cache(self):
        self.cached.fill((0, 0, 0, 0))
        for t in self.set.tiles.values():
            t.render(self.cam, self.tile_pos[t])
        self.cached_valid = True

    def render(self, cam: Camera):
        if self.is_empty:
            return
        if self.global_pos > cam.world_down_right:
            return
        if self.global_pos + self.size < cam.world_up_left:
            return
        if not self.cached_valid:
            self.cache()
        if cam.zoom not in self.cached_scaled:
            self.scale(cam.zoom)
        cam.screen.blit(self.cached_scaled[cam.zoom], cam.world_to_screen(self.global_pos).tuple)

    def check_empty(self):
        self.is_empty = True
        for t, p in self.tile_pos.items():
            if isinstance(t, DirectionalTile):
                for i in p:
                    if i:
                        self.is_empty = False
                        break
            elif p:
                self.is_empty = False
                break


class TileMap(Obj):
    set: Tileset
    grid: list[list[Chunk | None]]

    def __init__(self, width: int, height: int, tileset, tile_size: int = 16, *, pos=None, parent=None,
                 grid: list[list[Tile | str | int | None]] = None, mapping: dict[int, str] = None):
        super().__init__(pos=pos, parent=parent)
        self.set = tileset
        self.tile_size = tile_size
        self.grid = [[None for _ in range(ceil(height / CHUNK_SIZE))] for _ in range(ceil(width / CHUNK_SIZE))]
        if grid:
            # converting all to Tiles
            for y, row in enumerate(grid):
                for x, cell in enumerate(row):
                    cell: int | str | Tile = grid[x][y]
                    if not cell:
                        continue
                    elif isinstance(cell, Tile):
                        grid[x][y] = cell
                    elif isinstance(cell, str):
                        if cell in self.set.tiles:
                            grid[x][y] = self.set.tiles[cell]
                        else:
                            print("Failed to load tile: not present in tileset")
                            continue
                    elif isinstance(cell, int):
                        c = mapping[cell]
                        if c in self.set.tiles:
                            grid[x][y] = self.set.tiles[c]
                        else:
                            print("Failed to load tile: not present in tileset")
                            continue
            # dividing to chunks
            size = Vec2(tile_size * CHUNK_SIZE, tile_size * CHUNK_SIZE)
            for cy, crow in enumerate(self.grid):
                for cx, chunk in enumerate(crow):
                    cgrid: list[list[Tile | None]] = [[None for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_SIZE)]
                    cpos = Vec2(cx * CHUNK_SIZE, cy * CHUNK_SIZE)

                    tile_pos = {}
                    for t in self.set.tiles.values():
                        tile_pos[t] = []
                        if isinstance(t, DirectionalTile):
                            tile_pos[t] = [[] for _ in range(16)]

                    for y in range(cpos.y, min(cpos.y + CHUNK_SIZE, height)):
                        for x in range(cpos.x, min(cpos.x + CHUNK_SIZE, width)):
                            cgrid[x % CHUNK_SIZE][y % CHUNK_SIZE] = cell = grid[x][y]
                            if not cell:
                                continue
                            if isinstance(cell, DirectionalTile):
                                index = 0
                                if y + 1 < height and grid[x][y + 1] is cell:
                                    index += 1
                                if x > 0 and grid[x - 1][y] is cell:
                                    index += 2
                                if y > 0 and grid[x][y - 1] is cell:
                                    index += 4
                                if x + 1 < width and grid[x + 1][y] is cell:
                                    index += 8
                                tile_pos[cell][index].append(Vec2(x * tile_size, y * tile_size))
                            else:
                                # noinspection PyTypeChecker
                                tile_pos[cell].append(Vec2(x * tile_size, y * tile_size))

                    self.grid[cx][cy] = Chunk(tileset, tile_pos, cgrid, tile_size, size, cpos * tile_size, self)

    @classmethod
    def from_image(cls, img: io.BytesIO, tileset, mapping: dict[int, str], tile_size: int = 16, *, pos=None,
                   parent=None):
        img = Image.open(img)
        if img.mode != 'P':
            raise ValueError("Image must be in palette mode")
        pixels = img.load()
        return cls(img.height, img.width, tileset, tile_size, pos=pos, parent=parent, mapping=mapping,
                   grid=[[int(pixels[x, y]) for y in range(img.height)] for x in range(img.width)])

    def render(self, cam: Camera):
        chunk_width = self.grid[0][0].size.x
        tl_chunk = ceil((cam.world_up_left - self.global_pos) // chunk_width)
        rd_chunk = ceil(tl_chunk + ceil(cam.world_size / chunk_width))+1
        for col in self.grid[max(tl_chunk.x, 0):min(rd_chunk.x, len(self.grid))]:
            for chunk in col[max(tl_chunk.y, 0):min(rd_chunk.y, len(col))]:
                chunk.render(cam)
        import Utils
