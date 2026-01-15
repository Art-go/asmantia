from functools import wraps

import pygame
from OpenGL import GL, GLU

from .vec2 import Vec2
from .texture import Texture

def surface_to_texture(surface):
    texture_data = pygame.image.tostring(surface, "RGBA")
    w, h = surface.get_size()

    texture = GL.glGenTextures(1)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, w, h, 0,
                    GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, texture_data)

    # Set texture parameters
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)

    return texture

def surf_to_tex_default(surface):
    return Texture(surface_to_texture(surface), surface, (0, 0, 1, 1), Vec2(0, 0), Vec2.from_tuple(surface.get_size()))


def draw_quad(x, y, width, height, texture):
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture)

    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glBegin(GL.GL_QUADS)
    GL.glTexCoord2f(0, 0)
    GL.glVertex2f(x, y)
    GL.glTexCoord2f(1, 0)
    GL.glVertex2f(x + width, y)
    GL.glTexCoord2f(1, 1)
    GL.glVertex2f(x + width, y + height)
    GL.glTexCoord2f(0, 1)
    GL.glVertex2f(x, y + height)
    GL.glEnd()

    GL.glDisable(GL.GL_TEXTURE_2D)
    GL.glDisable(GL.GL_BLEND)


def batch_draw(texture_list):
    if len(texture_list)==0:
        return

    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

    current_tex = texture_list[0][1].tex_id
    GL.glBindTexture(GL.GL_TEXTURE_2D, current_tex)
    GL.glBegin(GL.GL_QUADS)

    for [x, y, w, h], tex in texture_list:
        tex_id, [u0, v0, u1, v1] = tex.tex_id, tex.uv
        if tex_id!=current_tex:
            GL.glEnd()
            GL.glBindTexture(GL.GL_TEXTURE_2D, tex_id)
            GL.glBegin(GL.GL_QUADS)
            current_tex = tex_id

        GL.glTexCoord2f(u0, v0); GL.glVertex2f(x, y)
        GL.glTexCoord2f(u1, v0); GL.glVertex2f(x + w, y)
        GL.glTexCoord2f(u1, v1); GL.glVertex2f(x + w, y + h)
        GL.glTexCoord2f(u0, v1); GL.glVertex2f(x, y + h)

    GL.glEnd()
    GL.glDisable(GL.GL_TEXTURE_2D)
    GL.glDisable(GL.GL_BLEND)


class DrawQueue:
    queue: list[tuple[tuple[int, int, int, int], Texture]]  # list[tuple[x, y, width, height, texture]]

    def __init__(self):
        self.queue = []

    def __iadd__(self, other: tuple[tuple[int, int, int, int], Texture]):
        self.append = self.queue.append(other)
        return self

    def add(self, x, y, width, height, texture: Texture):
        self.__iadd__(((x, y, width, height), texture))

    def __call__(self):
        batch_draw(self.queue)
        self.queue.clear()


def set_size_center(w, h):
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluOrtho2D(-w / 2, w / 2, h / 2, -h / 2)
    GL.glMatrixMode(GL.GL_MODELVIEW)

def screen_render(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GLU.gluOrtho2D(0, *self.size, 0)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()

        func(self, *args, **kwargs)

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopMatrix()

    return wrapper