import pygame

from Vec2 import Vec2


#############
# Functions #
#############
def render_text(text: str, font: pygame.font.Font, scrn: pygame.Surface, pos, fore=(255, 255, 255), back=(0, 0, 0)):
    if (text, font, fore, back) in prerendered_text:
        rendered_text = prerendered_text[text, font, fore, back]
    else:
        prerendered_text[text, font, fore, back] = rendered_text = prerender_text(text, font, fore, back)
    text_rect = rendered_text.get_rect(**pos)
    scrn.blit(rendered_text, text_rect)
    return rendered_text


def prerender_text(text: str, font: pygame.font.Font, fore=(255, 255, 255), back=(0, 0, 0)):
    rendered_text = font.render(text, True, fore)
    background = pygame.Surface((rendered_text.get_width() + 6, rendered_text.get_height() + 6), pygame.SRCALPHA)
    background.fill(back)
    background.blit(rendered_text, (3, 3))
    return background


prerendered_text = {}

# Debug #
debug_relpos = []
debug_pos = []
debug_offset = []
debug_screen = None
debug_font = None
debug_blit_queue = []


def update_debug_info(pos: list[list[str | Vec2]] = None, screen=None, font=None):
    global debug_relpos, debug_screen, debug_font
    if pos:
        debug_relpos = pos
    if screen:
        debug_screen = screen
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
    debug_blit_queue.clear()


def debug(text: str, p: int = 0):
    assert (isinstance(debug_font, pygame.font.Font))
    assert (isinstance(debug_screen, pygame.Surface))
    pos = {debug_pos[p][0]: (debug_pos[p][1] + debug_offset[p]).tuple}
    rendered_text = debug_font.render(text, True, (255, 255, 255), (0, 0, 0))
    text_rect = rendered_text.get_rect(**pos)
    debug_offset[p].y += rendered_text.get_size()[1]

    debug_blit_queue.append((rendered_text, text_rect))


def debug_draw():
    assert (isinstance(debug_screen, pygame.Surface))
    for text, rect in debug_blit_queue:
        debug_screen.blit(text, rect)
