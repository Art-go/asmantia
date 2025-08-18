import gzip
import json
import logging
import os
import selectors
import signal
import socket
import sys
import types

import pygame

import Network
from Character import CharSheet

################################
# Constants and Read-only(ish) #
################################
# Server config #
with open("server.cfg.json", "r") as f:
    config: dict = json.load(f)
# Config Loading #
IP = config.get("ip", "127.0.0.1")
PORT = config.get("port", 8080)
SERVER_CAPACITY = config.get("capacity", 2)

with open("Data/credentials.json", "r") as f:
    all_creds: dict[str, dict] = json.load(f)

# Logging #
logging.basicConfig(level=logging.DEBUG,
                    format="{asctime}:{levelname}:{name}:{message}", style="{",
                    stream=sys.stdout
                    )

#############
# Variables #
#############
clock = pygame.time.Clock()

characters = {}
for filename in os.listdir("Data/Char Sheets"):
    with open(os.path.join("Data/Char Sheets", filename), 'r') as f:
        ch_sheet = CharSheet.from_json(f.read(), True)
        characters[ch_sheet.ID]=ch_sheet

###############
# Scene Setup #
###############

##########
# Server #
##########
sel = selectors.DefaultSelector()
listening = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listening.bind((IP, PORT))


def accept_connection(key):
    conn, addr = key.fileobj.accept()
    logging.info(f"Connecting...: {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", status=Network.Status.PENDING, info=None)
    events = selectors.EVENT_READ
    sel.register(conn, events, data=data)
    Network.send(sel, conn, data, b"ASMANTIA SERVER: PENDING FOR CRED", send_all=True)


def finish_connection(key):
    data = key.data
    info = all_creds.get(Network.recv(sel, key.fileobj, data, 1024).decode(), None)
    if not info:
        Network.send(sel, key.fileobj, data, b"REJECT", send_all=True)
        Network.close_connection(sel, key.fileobj)
        return
    Network.send(sel, key.fileobj, data, b"ACCEPT", send_all=True)
    logging.info(f"Connection Complete: {data.addr}")
    Network.send(sel, key.fileobj, data, json.dumps(info).encode(), send_all=True)
    data.outb += gzip.compress(characters[info["sheet"]].to_json().encode())
    data.status = Network.Status.CONNECTED
    sel.modify(key.fileobj, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)


def handle_conn(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = Network.recv(sel, sock, data, 1024)
        if recv_data:
            logging.debug(f"Receiving {recv_data!r} from {data.addr}")
            data.outb += recv_data
        else:
            logging.info(f"Closing connection: {data.addr}")
            Network.close_connection(sel, sock, addr=data.addr)
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            logging.debug(f"Sending {data.outb!r} to {data.addr}")
            sent = Network.send(sel, sock, data, data.outb)
            data.outb = data.outb[sent:]


hui = True


def handle_sigint(_signum, _frame):
    global hui
    logging.info("KeyboardInterrupt")
    hui = False


signal.signal(signal.SIGINT, handle_sigint)
dt = 0
try:
    listening.listen()
    logging.info(f"Listening {(IP, PORT)}")
    listening.setblocking(False)
    sel.register(listening, selectors.EVENT_READ, data=None)
    while hui:
        evnts = sel.select(timeout=-1)
        for k, m in evnts:
            try:
                if k.data is None:
                    accept_connection(k)
                elif k.data.status is Network.Status.PENDING:
                    finish_connection(k)
                elif k.data.status is Network.Status.CONNECTED:
                    handle_conn(k, m)
                else:
                    logging.warning(f"Unknown Status: {k.data.status}")
            except Network.SocketClosed:
                logging.warning("Socket closed abruptly")

        dt = clock.tick(60)
except Exception as e:
    logging.exception(e)
finally:
    logging.info("Exiting")
    sel.close()
