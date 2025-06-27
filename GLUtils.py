import pygame
from OpenGL.GL import *
from OpenGL.GLU import *


def surface_to_texture(surface):
    """Convert pygame.Surface to OpenGL texture"""
    # wtf is wrong with inspection
    # noinspection PyTypeChecker
    texture_data = pygame.image.tostring(surface, "RGBA")
    w, h = surface.get_size()

    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, texture_data)

    # Set texture parameters
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    return texture


def draw_quad(x, y, width, height, texture):
    """Draw 2D quad with texture at specified position"""
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture)

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex2f(x, y)
    glTexCoord2f(1, 0)
    glVertex2f(x + width, y)
    glTexCoord2f(1, 1)
    glVertex2f(x + width, y + height)
    glTexCoord2f(0, 1)
    glVertex2f(x, y + height)
    glEnd()

    glDisable(GL_TEXTURE_2D)
    glDisable(GL_BLEND)


def batch_draw(texture_list):
    """Draw multiple textures in one batch"""
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    for x, y, w, h, tex in texture_list:
        glBindTexture(GL_TEXTURE_2D, tex)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex2f(x, y)
        glTexCoord2f(1, 0)
        glVertex2f(x + w, y)
        glTexCoord2f(1, 1)
        glVertex2f(x + w, y + h)
        glTexCoord2f(0, 1)
        glVertex2f(x, y + h)
        glEnd()
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_BLEND)


queue = []


def queue_draw(x, y, width, height, texture):
    queue.append((x, y, width, height, texture))


def draw_queue():
    batch_draw(queue)
    queue.clear()


def set_size_center(w, h):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-w / 2, w / 2, h / 2, -h / 2)
    glMatrixMode(GL_MODELVIEW)
