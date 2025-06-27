import pygame

import GLUtils
from Vec2 import Vec2


#############
# Functions #
#############
def render_text(text: str, font: pygame.font.Font, pos, fore=(255, 255, 255), back=(0, 0, 0)):
    surf, tex = prerender_text(text, font, fore, back)
    text_rect: pygame.Rect = surf.get_rect(**pos)
    GLUtils.queue_draw(text_rect.x, text_rect.y, text_rect.width, text_rect.height, tex)


def prerender_text(text: str, font: pygame.font.Font, fore=(255, 255, 255), back=(0, 0, 0)):
    if (text, font, fore, back) in prerendered_text:
        return prerendered_text[text, font, fore, back]
    rendered_text = font.render(text, True, fore)
    background = pygame.Surface(
        (rendered_text.get_width() + 6, rendered_text.get_height() + 6), pygame.SRCALPHA)
    background.fill(back)
    background.blit(rendered_text, (3, 3))
    prerendered_text[text, font, fore, back] = background, GLUtils.surface_to_texture(background)
    return prerendered_text[text, font, fore, back]


prerendered_text = {}

# Debug #
debug_relpos = []
debug_pos = []
debug_offset = []
debug_screen = None
debug_font = None
debug_queue = []


def update_debug_info(pos: list[list[str | Vec2]] = None, size=None, font=None):
    global debug_relpos, debug_screen, debug_font
    if pos:
        debug_relpos = pos
    if size:
        debug_screen = pygame.Surface(size)
    if font:
        debug_font = font
    debug_pos.clear()
    for p in debug_relpos:
        debug_pos.append(p.copy())
        if p[0] == "topright":
            debug_pos[-1][1] += Vec2(debug_screen.get_size()[0], 0)


def clear_debug():
    global debug_offset
    debug_offset = [Vec2(0, 0) for _ in debug_pos]


def debug(text: str, p: int = 0):
    assert (isinstance(debug_font, pygame.font.Font))
    assert (isinstance(debug_screen, pygame.Surface))
    pos = {debug_pos[p][0]: (debug_pos[p][1] + debug_offset[p]).tuple}
    surf, tex = prerender_text(text, debug_font)
    text_rect: pygame.Rect = surf.get_rect(**pos)
    debug_queue.append((text_rect.x, text_rect.y, text_rect.width, text_rect.height, tex))
    debug_offset[p].y += text_rect.height


def draw_debug():
    GLUtils.batch_draw(debug_queue)
    debug_queue.clear()
