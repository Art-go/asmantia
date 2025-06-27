import json
import logging
import selectors
import signal
import socket
import sys
import types

import pygame

import Network
from Network import send, recv, close_connection, SocketClosed, Status

################################
# Constants and Read-only(ish) #
################################
# Server config #
IP = "127.0.0.1"
PORT = 8080
SERVER_CAPACITY = 6

CRED_CIPHER = b"%$?_.$/3.@/?1>$>--^ ^-%_>_4=|9/."
with open("Data/credentials.json", "r") as f:
    all_creds: dict[str, dict] = json.load(f)

# Game constants #
SPEED = 0.25

# Logging #
logging.basicConfig(level=logging.DEBUG,
                    format="{asctime}:{levelname}:{name}:{message}", style="{",
                    stream=sys.stdout
                    )

#############
# Variables #
#############
clock = pygame.time.Clock()

###############
# Scene Setup #
###############

objects = []

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
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", status=Status.PENDING, info=None)
    events = selectors.EVENT_READ
    sel.register(conn, events, data=data)
    send(sel, conn, data, b"ASMANTIA SERVER: PENDING FOR CRED", send_all=True)


def finish_connection(key):
    data = key.data
    info = all_creds.get(
        bytes(
            [b ^ CRED_CIPHER[i % len(CRED_CIPHER)]
             for i, b in enumerate(recv(sel, key.fileobj, data, 1024))]
        ).decode(), None
    )
    if not info:
        send(sel, key.fileobj, data, b"REJECT", send_all=True)
        Network.close_connection(sel, socket)
        return
    send(sel, key.fileobj, data, b"ACCEPT", send_all=True)
    logging.info(f"Connection Complete: {data.addr}")
    send(sel, key.fileobj, data, json.dumps(info).encode(), send_all=True)
    data.status = Status.CONNECTED
    sel.modify(key.fileobj, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)


def handle_conn(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = recv(sel, sock, data, 1024)
        if recv_data:
            logging.info(f"Receiving {recv_data!r} from {data.addr}")
            data.outb += recv_data
        else:
            logging.info(f"Closing connection: {data.addr}")
            close_connection(sel, sock, addr=data.addr)
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            logging.info(f"Sending {data.outb!r} to {data.addr}")
            sent = send(sel, sock, data, data.outb)
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
                elif k.data.status is Status.PENDING:
                    finish_connection(k)
                elif k.data.status is Status.CONNECTED:
                    handle_conn(k, m)
                else:
                    logging.warning(f"Unknown Status: {k.data.status}")
            except SocketClosed:
                logging.warning("Socket closed abruptly")

        dt = clock.tick(60)
except Exception as e:
    logging.exception(e)
finally:
    logging.info("Exiting")
    sel.close()
