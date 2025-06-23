import os
import signal
import sys
from getpass import getpass

import pygame

from Character import Character
from Renderer import Renderer
from Tileset import Tileset
from Map import Map
from Vec2 import Vec2
from Camera import Camera
import Utils
import socket
import selectors
import logging

pygame.init()

###########
# Network #
###########
CRED_CYPHER = b"%$?_.$/@.@/?*>$>--^^-%_>_$=|$/."

ip = input("Enter ip (empty for 127.0.0.1):") or "127.0.0.1"
port = int(input("Enter port (empty for 8080):") or 8080)
creds = getpass("Credentials: ") if not os.environ.get("DEBUG", False) else input("DEBUG:")
###########
# Logging #
###########
logging.basicConfig(level=logging.INFO,
                    format="{asctime}:{levelname}:{name}:{message}", style="{",
                    stream=sys.stdout
                    )


def handle_sigint(_signum, _frame):
    global hui
    logging.info("KeyboardInterrupt")
    hui = False


signal.signal(signal.SIGINT, handle_sigint)

sock = socket.socket()
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((ip, port))
    print(s.recv(1024))
    s.send(bytes([b ^ CRED_CYPHER[i % len(CRED_CYPHER)] for i, b in enumerate(creds.encode())]))
    print(s.recv(1024))
    s.send(b"Hello, world")
    print(s.recv(1024))

################################
# Constants and Read-only(ish) #
################################
screen = pygame.display.set_mode((1536, 1024), flags=pygame.RESIZABLE, vsync=True)
pygame.display.set_caption("Asmantia Client")

fonts = {
    'Nicks': pygame.font.Font('Assets/Fonts/Exo2-Bold.ttf', 12),
    'Debug': pygame.font.Font('Assets/Fonts/Exo2-Regular.ttf', 16),
}

# WASD #
SPEED = 0.25

ZOOM_FACTOR = 2 ** 0.25
MIN_W = 96
MAX_W = 3072

#############
# Variables #
#############
mouse_pos = Vec2()
offset = Vec2()
clock = pygame.time.Clock()

# Signals #
signals = []
signal_debug_string = ""

# Debug #
Utils.update_debug_info(pos=[["topright", Vec2(-5, 5)], ["topleft", Vec2(5, 5)]],
                        screen=screen,
                        font=fonts['Debug'])
custom_debug_string = ""
debug = bool(os.environ.get("DEBUG", False))
controls = True
limit_fps = True
expected_fps = 60

hui = True
fps, frame, dt, dt_spike = 0, 0, 0, 0


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
player = Character(name="God Almighty",
                   sprite=Renderer(pygame.image.load("Assets/Sprites/Sprites.png")
                                   .subsurface((20, 0, 4, 4))
                                   .convert_alpha()),
                   pos=(100, 200))
cam = Camera(384, screen, parent=player, center=True)

objects = [opened_map, player]

#############
# Main Loop #
#############
try:
    while hui:
        signals.clear()
        Utils.clear_debug()

        ##################
        # Event Handling #
        ##################
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    hui = False
                case pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        ...
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_F1:
                            controls = not controls
                        case pygame.K_F1:
                            limit_fps = not limit_fps
                        case pygame.K_F3:
                            debug = not debug
                        case pygame.K_RIGHTBRACKET:
                            dt_spike = 0
                        case pygame.K_e:
                            cam.width = max(cam.width / ZOOM_FACTOR, MIN_W)
                        case pygame.K_q:
                            cam.width = min(cam.width * ZOOM_FACTOR, MAX_W)
                case pygame.VIDEORESIZE:
                    Utils.update_debug_info()
                    cam.recalculate_zoom()
                case pygame.MOUSEMOTION:
                    mouse_pos = Vec2.from_tuple(pygame.mouse.get_pos())

        ##################
        # Input Handling #
        ##################
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            offset.y -= SPEED
        if keys[pygame.K_s]:
            offset.y += SPEED
        if keys[pygame.K_a]:
            offset.x -= SPEED
        if keys[pygame.K_d]:
            offset.x += SPEED

        ####################
        # Physics Handling #
        ####################
        player.pos += offset.normalize() * dt * expected_fps / 1000
        offset = Vec2()

        ###########
        # Drawing #
        ###########
        screen.fill((0, 0, 0))

        # Signal processing #

        if signals:
            signal_debug_string = str(signals)

        # Render everything #
        cam.render(objects)

        # Controls #
        if controls:
            Utils.debug('Controls:', 1)
            Utils.debug('Movement: W A S D; Zoom: Q E', 1)
            Utils.debug('Toggle: Controls: F1, FPS limit: F2, Debug: F3', 1)
            Utils.debug('Clear max_dt: ]', 1)
        # Debug Tools #
        Utils.debug(f'FPS: {float(fps):.1f}, locked: {limit_fps}; dt: {dt}, Max dt: {dt_spike}')
        Utils.debug(f'Connected to: {ip}:{port} as {creds.split("+")[0]}')
        if debug:
            Utils.debug(f'Cam: P: {cam.pos.int_tuple}/{cam.global_pos.int_tuple}, Zm: {cam.zoom:.3g}, W: '
                        f'{float(cam.width):.6g}, ')
            Utils.debug(f'UL: {cam.world_up_left.int_tuple}, DR: {cam.world_down_right.int_tuple}; '
                        f'Scrn: S: {cam.size.tuple}, WS: {cam.world_size.int_tuple}')
            Utils.debug(f'Mouse: Sc: {mouse_pos.int_tuple}, Wr: {cam.screen_to_world(mouse_pos).int_tuple}')
            Utils.debug(f'Player: {player.pos.int_tuple}')
            Utils.debug(custom_debug_string)
            Utils.debug(signal_debug_string)

        Utils.debug_draw()
        ################
        # End of frame #
        ################
        pygame.display.flip()
        fps = clock.get_fps()
        dt = clock.tick(expected_fps if limit_fps else 0)
        dt_spike = max(dt, dt_spike)
        frame += 0
finally:
    pygame.quit()
    # sel.close()
