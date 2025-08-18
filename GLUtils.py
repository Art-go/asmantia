import pygame
from OpenGL import GL, GLU


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
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    for x, y, w, h, tex in texture_list:
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0, 0)
        GL.glVertex2f(x, y)
        GL.glTexCoord2f(1, 0)
        GL.glVertex2f(x + w, y)
        GL.glTexCoord2f(1, 1)
        GL.glVertex2f(x + w, y + h)
        GL.glTexCoord2f(0, 1)
        GL.glVertex2f(x, y + h)
        GL.glEnd()
    GL.glDisable(GL.GL_TEXTURE_2D)
    GL.glDisable(GL.GL_BLEND)


queue = []


def queue_draw(x, y, width, height, texture):
    queue.append((x, y, width, height, texture))


def draw_queue():
    batch_draw(queue)
    queue.clear()


def set_size_center(w, h):
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluOrtho2D(-w / 2, w / 2, h / 2, -h / 2)
    GL.glMatrixMode(GL.GL_MODELVIEW)
