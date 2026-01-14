import io
import json
import logging
import os
from math import ceil

import pygame
from OpenGL.GL import glDeleteTextures
from PIL import Image

from Engine import Camera
from Engine import GLUtils
from Engine import Obj
from Engine import Vec2

CHUNK_SIZE = 32

logger = logging.getLogger(__name__)

class Tile:

    def __init__(self, img: pygame.Surface):
        self.tile = img

    # noinspection PyMethodOverriding
    def render(self, surf, pos):
        """
        :type surf: pygame.Surface
        :type pos: list[Vec2]
        """
        for p in pos:
            surf.blit(self.tile, p.int_tuple)


class DirectionalTile(Tile):
    tile_vars: list[pygame.Surface]

    # noinspection PyMissingConstructor
    def __init__(self, imgs: list[pygame.Surface]):
        self.tile_vars = [i.convert_alpha() for i in imgs]

    # noinspection PyMethodOverriding
    def render(self, surf, pos):
        """
        :type surf: pygame.Surface
        :type pos: list[list[Vec2]]
        """
        for i, tpos in enumerate(pos):
            for p in tpos:
                surf.blit(self.tile_vars[i], p.int_tuple)


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
    cached_tex: int | None
    cached_valid: bool = False
    tile_pos_valid: bool = False
    size: Vec2
    is_empty: bool = True
    parent: "TileMap"

    def __init__(self, tileset, grid: list[list[Tile | None]], tile_size: int, size: Vec2, cpos: Vec2, pos,
                 parent: "TileMap"):
        super().__init__(pos=pos, parent=parent)
        self.cpos = cpos
        self.set = tileset
        self.tile_size = tile_size
        self.grid = grid
        self.size = size
        self.cached = pygame.Surface(self.size.tuple, pygame.SRCALPHA)
        self.cached_valid = False
        self.tile_pos_valid = False
        self.cached_tex = None

    def cache(self):
        self.cached.fill((0, 0, 0, 0))
        for t, pos in self.tile_pos.items():
            t.render(self.cached, self.tile_pos[t])
        if self.cached_tex is not None:
            glDeleteTextures([self.cached_tex])
        self.cached_tex = GLUtils.surface_to_texture(self.cached)
        self.cached_valid = True

    def render(self, cam: Camera):
        if not self.tile_pos_valid:
            self.update_tile_pos()
        if self.is_empty:
            return
        if self.global_pos >= cam.world_down_right:
            return
        if self.global_pos + self.size <= cam.world_up_left:
            return
        if not self.cached_valid:
            self.cache()

        pos = self.global_pos
        size = self.size
        cam.queue += pos.x, pos.y, size.x, size.y, self.cached_tex

    def check_empty(self):
        self.is_empty = True
        for t, p in self.tile_pos.items():
            if isinstance(t, DirectionalTile):
                for i in p:
                    if i:
                        self.is_empty = False
                        break
                else:
                    continue
                break
            elif p:
                self.is_empty = False
                break

    def update_tile_pos(self):
        self.tile_pos = {}
        cx, cy = self.cpos.tuple
        cw, ch = ceil(self.parent.size / CHUNK_SIZE).int_tuple
        for x, col in enumerate(self.grid):
            for y, cell in enumerate(col):
                if not cell:
                    continue
                if isinstance(cell, DirectionalTile):
                    if cell not in self.tile_pos:
                        self.tile_pos[cell] = [[] for _ in range(len(cell.tile_vars))]
                    index = 0
                    if (self.grid[x][y + 1] is cell) if y + 1 < CHUNK_SIZE else (
                            cy + 1 < ch and self.parent.grid[cx][cy + 1].grid[x][0] is cell):
                        index += 1
                    if (self.grid[x - 1][y] is cell) if x > 0 else (
                            cx > 0 and self.parent.grid[cx - 1][cy].grid[-1][y] is cell):
                        index += 2
                    if (self.grid[x][y - 1] is cell) if y > 0 else (
                            cy > 0 and self.parent.grid[cx][cy - 1].grid[x][-1] is cell):
                        index += 4
                    if (self.grid[x + 1][y] is cell) if x + 1 < CHUNK_SIZE else (
                            cx + 1 < cw and self.parent.grid[cx + 1][cy].grid[0][y] is cell):
                        index += 8
                    # bullshit.
                    # noinspection PyUnresolvedReferences
                    self.tile_pos[cell][index].append(Vec2(x, y) * self.tile_size)
                else:
                    if cell not in self.tile_pos:
                        self.tile_pos[cell] = []
                    self.tile_pos[cell].append(Vec2(x, y) * self.tile_size)

        self.check_empty()
        self.tile_pos_valid = True


class TileMap(Obj):
    set: Tileset
    grid: list[list[Chunk | None]]

    def __init__(self, width: int, height: int, tileset, tile_size: int = 16, *, pos=None, parent=None,
                 grid: list[list[Tile | str | int | None]] = None, mapping: dict[int, str] = None):
        super().__init__(pos=pos, parent=parent)
        self.set = tileset
        self.tile_size = tile_size
        self.size = Vec2(width, height)
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
                            logger.warning("Failed to load tile: not present in tileset")
                            grid[x][y] = None
                            continue
                    elif isinstance(cell, int):
                        c = mapping[cell]
                        if c in self.set.tiles:
                            grid[x][y] = self.set.tiles[c]
                        else:
                            logger.warning("Failed to load tile: not present in tileset")
                            grid[x][y] = None
                            continue
            # dividing to chunks
            size = Vec2(tile_size * CHUNK_SIZE, tile_size * CHUNK_SIZE)
            import time
            start = time.time()
            for cy, crow in enumerate(self.grid):
                for cx, chunk in enumerate(crow):
                    cgrid: list[list[Tile | None]] = [[None for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_SIZE)]
                    cpos = Vec2(cx * CHUNK_SIZE, cy * CHUNK_SIZE)
                    mn_y = min(cpos.y + CHUNK_SIZE, height)
                    for x in range(cpos.x, min(cpos.x + CHUNK_SIZE, width)):
                        cgrid[x % CHUNK_SIZE][:(mn_y - 1) % CHUNK_SIZE + 1] = grid[x][cpos.y:mn_y]

                    self.grid[cx][cy] = Chunk(tileset, cgrid, tile_size, size, Vec2(cx, cy), cpos * tile_size, self)
            logger.debug(f"time per TileMap: {time.time() - start}")

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
        rd_chunk = ceil(tl_chunk + ceil(cam.world_size / chunk_width)) + 1
        for col in self.grid[max(tl_chunk.x, 0):min(rd_chunk.x, len(self.grid))]:
            for chunk in col[max(tl_chunk.y, 0):min(rd_chunk.y, len(col))]:
                chunk.render(cam)
        tl_chunk = tl_chunk - 2
        rd_chunk = rd_chunk + 2
        for col in self.grid[max(tl_chunk.x, 0):min(rd_chunk.x, len(self.grid))]:
            for chunk in col[max(tl_chunk.y, 0):min(rd_chunk.y, len(col))]:
                if chunk.is_empty:
                    continue
                if not chunk.cached_valid:
                    chunk.cache()
                    break
            else:
                continue
            break
