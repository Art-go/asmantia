import logging
import os

import pygame
from OpenGL import GL

import logging_setup
from Character import Character, CharSheet
from Engine import Vec2, Camera, GLUtils, Debug, UiElement, Canvas, UiRenderer, UiTextRenderer, UiProgressBar
from Map import Map
from Tilemap import Tileset

########
# Init #
########
pygame.init()
logging_setup.setup_logging(logging.DEBUG)

################################
# Constants and Read-only(ish) #
################################
FLAGS = pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.OPENGL
pygame.display.set_caption("Asmantia Client")
ROOT = True

fonts = {
    'Nicks': pygame.font.Font('Assets/Fonts/Exo2-Bold.ttf', 12),
    'Debug': pygame.font.Font('Assets/Fonts/Exo2-Regular.ttf', 16),
    'ChInfo.H1': pygame.font.Font('Assets/Fonts/Exo2-Bold.ttf', 20),
    'ChInfo.H2': pygame.font.Font('Assets/Fonts/Exo2-Bold.ttf', 14),
    'ChInfo.Values': pygame.font.Font('Assets/Fonts/Exo2-Bold.ttf', 13),
}

ZOOM_FACTOR = 2 ** (1 / 4)
MIN_W = 160
MAX_W = 1600

#############
# Variables #
#############
width, height, vsync = 1600, 960, 2
pygame.display.set_mode((width, height),
                        flags=FLAGS,
                        vsync=vsync % 2)

mouse_pos = Vec2()
offset = Vec2()
clock = pygame.time.Clock()

# Signals #
signals = []
signal_debug_string = ""

# Debug #
M_debug = Debug.DebugManager(fonts['Debug'], (width, height),
                             [("topright", Vec2(-5, 5)), ("topleft", Vec2(5, 5))])
debug = bool(os.environ.get("DEBUG", False))
controls = True
expected_fps = 60

hui = True
fps, dt, dt_spike = 0, 0, 0

#########
# Tiles #
#########
tileset = Tileset().load_set("Assets/Tiles/Tileset.png")
opened_map = Map.from_folder("Data/Maps/test_map", tileset)

###############
# Scene Setup #
###############
# Player #
Character.setup_nicks(font=fonts["Nicks"], fore=(255, 255, 255), back=(0, 0, 0, 127))
speed = 15
cam = Camera(400, (width, height), parent=None, center=True)
objects = [opened_map]

# """
# UI #
canvas = Canvas(cam=cam)

ch_info_size = (400, 500)
ch_info = pygame.Surface(ch_info_size, pygame.SRCALPHA)
pygame.draw.rect(ch_info, (0, 0, 0, 127), (0, 0, *ch_info_size))

ch_info = UiRenderer(ch_info, pos=(5, -5), relpos=(0, 1), pivot=(0, 1), parent=canvas)
icon_block = UiElement(parent=ch_info, size=(80, 80))
name_block = UiElement(parent=ch_info, pos=(80, 0), size=(ch_info_size[0] - icon_block.size.x, 80))
bars_block = UiElement(parent=ch_info, pos=(0, 80), size=(ch_info_size[0], 60))

bars_back = pygame.Surface((100, 10), pygame.SRCALPHA)
pygame.draw.rect(bars_back, (30, 30, 30), (0, 0, 100, 10))
bars_back_tex = GLUtils.surface_to_texture(bars_back)

health_bar = pygame.Surface((100, 10), pygame.SRCALPHA)
pygame.draw.rect(health_bar, (200, 10, 10), (0, 0, 100, 10))
health_bar_tex = GLUtils.surface_to_texture(health_bar)

mana_bar = pygame.Surface((100, 10), pygame.SRCALPHA)
pygame.draw.rect(mana_bar, (50, 90, 200), (0, 0, 100, 10))
mana_bar_tex = GLUtils.surface_to_texture(mana_bar)

stats_block = UiElement(parent=ch_info, pos=(0, 140), size=(ch_info_size[0], 120))
sheet = CharSheet()
ui = {
    "background": ch_info,
    ## icon block ##
    "player_sprite": UiRenderer(pygame.image.load("Assets/Sprites/Characters.png").convert_alpha().subsurface((0, 0, 4, 4)), pos=(10, 10),
                                pivot=(0, 0), parent=icon_block, relpos=(0, 0), size=(60, 60)),
    ## name block
    "player_name": UiTextRenderer(sheet.name, font=fonts["ChInfo.H1"], fore=(255, 255, 255), back=(0, 0, 0, 0),
                                  parent=name_block, pos=(5, 2), relpos=(0, 0.5), pivot=(0, 1)),
    "player_title": UiTextRenderer(sheet.title, font=fonts["ChInfo.H2"], fore=(255, 255, 255), back=(0, 0, 0, 0),
                                   parent=name_block, pos=(5, 0), relpos=(0, 0.5), pivot=(0, 0)),
    "player_level": UiTextRenderer(f"LVL {sheet.level}", font=fonts["ChInfo.H2"], fore=(255, 255, 255),
                                   back=(0, 0, 0, 0), parent=name_block, pos=(-10, 0), relpos=(1, 0.5), pivot=(1, 1)),
    "player_race": UiTextRenderer(sheet.race, font=fonts["ChInfo.H2"], fore=(255, 255, 255), back=(0, 0, 0, 0),
                                  parent=name_block, pos=(-10, 0), relpos=(1, 0.5), pivot=(1, 0)),
    ## bars block ##
    "h_text": UiTextRenderer(f"{sheet.health}/{sheet.max_health}", font=fonts["ChInfo.Values"], fore=(255, 255, 255),
                             back=(0, 0, 0, 0), parent=bars_block, pos=(40, 20), relpos=(0, 0), pivot=(0.5, 0.5)),
    "h_bar": UiProgressBar(img_back=bars_back, tex_back=bars_back_tex,
                           img_bar=health_bar, tex_bar=health_bar_tex,
                           parent=bars_block, progress=sheet.health / sheet.max_health,
                           pos=(80, 20), size=(ch_info_size[0] - 80 - 10, 10), pivot=(0, 0.5)),
    "m_text": UiTextRenderer(f"{sheet.mana}/{sheet.max_mana}", font=fonts["ChInfo.Values"], fore=(255, 255, 255),
                             back=(0, 0, 0, 0), parent=bars_block, pos=(40, 40), relpos=(0, 0), pivot=(0.5, 0.5)),
    "m_bar": UiProgressBar(img_back=bars_back, tex_back=bars_back_tex,
                           img_bar=mana_bar, tex_bar=mana_bar_tex,
                           parent=bars_block, progress=(sheet.mana / sheet.max_mana) if sheet.max_mana > 0 else 0,
                           pos=(80, 40), size=(ch_info_size[0] - 80 - 10, 10), pivot=(0, 0.5)),
    ## stats block ##

}
# """

#############
# Main Loop #
#############
try:
    while hui:
        signals.clear()
        ##################
        # Event Handling #
        ##################
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    hui = False
                case pygame.MOUSEWHEEL:
                    cam.width = max(min(cam.width / (ZOOM_FACTOR ** event.y), MAX_W), MIN_W)
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_F1:
                            controls = not controls
                        case pygame.K_F2:
                            vsync = (vsync + 1) % 3
                            pygame.display.set_mode((width, height),
                                                    flags=FLAGS,
                                                    vsync=vsync % 2)
                        case pygame.K_F3:
                            debug = not debug
                        case pygame.K_RIGHTBRACKET:
                            dt_spike = 0
                        case pygame.K_e:
                            cam.width = max(cam.width / ZOOM_FACTOR, MIN_W)
                        case pygame.K_q:
                            cam.width = min(cam.width * ZOOM_FACTOR, MAX_W)
                        case pygame.K_COMMA:
                            if ROOT:
                                speed -= 0.25
                        case pygame.K_PERIOD:
                            if ROOT:
                                speed += 0.25
                case pygame.VIDEORESIZE:
                    GL.glViewport(0, 0, event.w, event.h)
                    M_debug.update_size((event.w, event.h))
                    cam.size = Vec2(event.w, event.h)
                    cam.width = cam.width
                    width, height = cam.size.tuple
                case pygame.MOUSEMOTION:
                    mouse_pos = Vec2.from_tuple(pygame.mouse.get_pos())

        ##################
        # Input Handling #
        ##################
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            offset.y -= 1
        if keys[pygame.K_s]:
            offset.y += 1
        if keys[pygame.K_a]:
            offset.x -= 1
        if keys[pygame.K_d]:
            offset.x += 1

        ####################
        # Physics Handling #
        ####################
        cam.pos += offset.normalize() * speed * dt * expected_fps / 1000
        offset = Vec2()

        ###########
        # Drawing #
        ###########
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GLUtils.set_size_center(cam.width, height / width * cam.width)
        GL.glLoadIdentity()
        GL.glTranslatef(-cam.global_pos.x, -cam.global_pos.y, 0)

        # Signal processing #
        if signals:
            signal_debug_string = str(signals)
            for sig in signals:
                match sig:
                    case _:
                        ...

        # Render everything #
        cam.render(objects)

        ############
        #    UI    #
        ############
        # Reset Pos #

        # Ui Update #
        ## Health ##
        ui["h_bar"].progress = sheet.health / sheet.max_health
        ui["h_text"].text = f"{sheet.health} / {sheet.max_health}"
        ## Mana ##
        ui["m_bar"].progress = sheet.mana / sheet.max_mana
        ui["m_text"].text = f"{sheet.mana} / {sheet.max_mana}"

        # Render #
        canvas.render()

        # Controls #
        if controls:
            M_debug('Controls:', 1)
            M_debug('Movement: W A S D; Zoom: Q E', 1)
            M_debug('Toggle: Controls: F1, FPS lock cycle: F2, Debug: F3', 1)
            M_debug('Clear max_dt: ]', 1)
            if ROOT:
                M_debug('Root:', 1)
                M_debug('Speed: < >', 1)
        else:
            M_debug('Controls: F1', 1)
        # Debug #
        M_debug(f'FPS: {float(fps):.1f}, lock: {['NONE', 'VSYNC', 'MANUAL'][vsync]}')
        M_debug(f'dt: {dt}, Max dt: {dt_spike}')
        if debug:
            M_debug(f'Cam: P: {cam.pos.int_tuple}/{cam.global_pos.int_tuple}, Zm: {cam.zoom:.3g}, W: '
                        f'{float(cam.width):.6g}')
            M_debug(f'UL: {cam.world_up_left.int_tuple}, DR: {cam.world_down_right.int_tuple}; '
                        f'Scrn: S: {cam.size.tuple}, WS: {cam.world_size.int_tuple}')
            M_debug(f'Mouse: Sc: {mouse_pos.int_tuple}, Wr: {cam.screen_to_world(mouse_pos).int_tuple}')
            M_debug(f'Signals: {signal_debug_string}')

        # Render debug #
        M_debug.draw()
        ################
        # End of frame #
        ################
        pygame.display.flip()
        fps = clock.get_fps()
        dt = clock.tick(expected_fps if vsync == 2 else 0)
        dt_spike = max(dt, dt_spike)
finally:
    pygame.quit()
