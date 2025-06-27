import logging
import sys
import os
import selectors
import signal
import socket
import types
from getpass import getpass

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

import Utils
from Camera import Camera
from Character import Character
from Map import Map
from Network import SocketClosed, recv, send
from Renderer import Renderer
from Tileset import Tileset
from Vec2 import Vec2
import GLUtils

pygame.init()

###########
# Network #
###########
CRED_CIPHER = b"%$?_.$/3.@/?1>$>--^ ^-%_>_4=|9/."

ip = input("Enter ip (empty for 127.0.0.1):") or "127.0.0.1"
port = int(input("Enter port (empty for 8080):") or 8080)
creds = getpass("Credentials: ") if not os.environ.get("DEBUG", False) else input("DEBUG:")


def handle_sigint(_signum, _frame):
    global hui
    logging.info("KeyboardInterrupt")
    hui = False


signal.signal(signal.SIGINT, handle_sigint)

logging.basicConfig(level=logging.INFO,
                    format="{asctime}:{levelname}:{name}:{message}", style="{",
                    stream=sys.stdout
                    )

sock = socket.socket()
sock.connect((ip, port))
sel = selectors.DefaultSelector()
data = types.SimpleNamespace(addr=(ip, port), outb=b"", inb=b"")
sel.register(sock, selectors.EVENT_READ | selectors.EVENT_WRITE)
assert recv(sel, sock, data, 1024) == b"ASMANTIA SERVER: PENDING FOR CRED"
# false positive inspection:
# noinspection PyTypeChecker
send(sel, sock, data, bytes([b ^ CRED_CIPHER[i % len(CRED_CIPHER)] for i, b in enumerate(creds.encode())]),
     send_all=True)
assert recv(sel, sock, data, 1024) == b"ACCEPT"
sock.setblocking(False)

################################
# Constants and Read-only(ish) #
################################
FLAGS = pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.OPENGL
pygame.display.set_caption("Asmantia Client")

fonts = {
    'Nicks': pygame.font.Font('Assets/Fonts/Exo2-Bold.ttf', 12),
    'Debug': pygame.font.Font('Assets/Fonts/Exo2-Regular.ttf', 16),
}

# WASD #
SPEED = 0.25

ZOOM_FACTOR = 2 ** 0.25
MIN_W = 160
MAX_W = 2400

#############
# Variables #
#############
width, height, vsync = 1600, 960, 1
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
Utils.update_debug_info(pos=[["topright", Vec2(-5, 5)], ["topleft", Vec2(5, 5)]],
                        size=(width, height),
                        font=fonts['Debug'])
debug = bool(os.environ.get("DEBUG", False))
controls = True
expected_fps = 60

hui = True
fps, dt, dt_spike = 0, 0, 0

#########
# Tiles #
#########
tileset = Tileset().load_set("Assets/Tiles/Tileset.png")
opened_map = Map.from_folder("Data/Maps/test_map_big", tileset)

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
cam = Camera(400, (width, height), parent=player, center=True)
objects = [opened_map, player]

#############
# Main Loop #
#############
try:
    while hui:
        signals.clear()
        Utils.clear_debug()
        ##################
        # Network update #
        ##################
        evnts = sel.select(timeout=-1)
        for k, m in evnts:
            try:
                pass
            except SocketClosed:
                logging.warning("Socket closed abruptly")
                # noinspection PyTypeChecker
                if not len(sel):
                    logging.critical("Connection blocked")
                    exit()

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
                case pygame.VIDEORESIZE:
                    glViewport(0, 0, event.w, event.h)
                    Utils.update_debug_info(size=(event.w, event.h))
                    cam.recalculate_zoom()
                    cam.size = Vec2(event.w, event.h)
                    width, height = cam.size.tuple
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
        glClear(GL_COLOR_BUFFER_BIT)
        GLUtils.set_size_center(cam.width, height / width * cam.width)
        glLoadIdentity()
        glTranslatef(-cam.global_pos.x, -cam.global_pos.y, 0)

        # Signal processing #
        if signals:
            signal_debug_string = str(signals)

        # Render everything #
        cam.render(objects)
        GLUtils.draw_queue()

        ############
        #    UI    #
        ############
        # Controls #
        if controls:
            Utils.debug('Controls:', 1)
            Utils.debug('Movement: W A S D; Zoom: Q E', 1)
            Utils.debug('Toggle: Controls: F1, FPS lock cycle: F2, Debug: F3', 1)
            Utils.debug('Clear max_dt: ]', 1)
        # Debug #
        Utils.debug(f'FPS: {float(fps):.1f}, lock: {['NONE', 'VSYNC', 'MANUAL'][vsync]}')
        Utils.debug(f'dt: {dt}, Max dt: {dt_spike}')
        Utils.debug(f'Connected to: {ip}:{port} as {creds.split("+")[0]}')
        if debug:
            Utils.debug(f'Cam: P: {cam.pos.int_tuple}/{cam.global_pos.int_tuple}, Zm: {cam.zoom:.3g}, W: '
                        f'{float(cam.width):.6g}')
            Utils.debug(f'UL: {cam.world_up_left.int_tuple}, DR: {cam.world_down_right.int_tuple}; '
                        f'Scrn: S: {cam.size.tuple}, WS: {cam.world_size.int_tuple}')
            Utils.debug(f'Mouse: Sc: {mouse_pos.int_tuple}, Wr: {cam.screen_to_world(mouse_pos).int_tuple}')
            Utils.debug(f'Player: {player.pos.int_tuple}')
            Utils.debug(f'Signals: {signal_debug_string}')

        #############
        # Render UI #
        #############
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, width, height, 0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        Utils.draw_debug()

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        ################
        # End of frame #
        ################
        pygame.display.flip()
        fps = clock.get_fps()
        dt = clock.tick(expected_fps if vsync == 2 else 0)
        dt_spike = max(dt, dt_spike)
finally:
    pygame.quit()
    sel.close()
    sock.close()
