import logging
import selectors
import signal
import socket
import sys
import types
from enum import IntEnum

import pygame


##############
# Status Def #
##############
class Status(IntEnum):
    CONNECTED = 100
    PENDING = 20


################################
# Constants and Read-only(ish) #
################################
# Server config "
IP = "127.0.0.1"
PORT = 8080
SERVER_CAPACITY = 6

# Game constants #
SPEED = 0.25

# Logging #
logging.basicConfig(level=logging.DEBUG,
                    format="{asctime}:{levelname}:{name}:{message}", style="{",
                    stream=sys.stdout
                    )

CRED_CYPHER = b"%$?_.$/@.@/?*>$>--^^-%_>_$=|$/."

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


class SocketClosed(Exception):
    ...


def recv(sock, data, *args, **kwargs):
    try:
        return sock.recv(*args, **kwargs)
    except (BrokenPipeError, ConnectionResetError):
        logging.error(f"Read fail: {data.addr} (disconnected)")
        close_connection(sock, data.addr)
        raise SocketClosed


def send(sock, data, *args, **kwargs):
    try:
        return sock.send(*args, **kwargs)
    except (BrokenPipeError, ConnectionResetError):
        logging.error(f"Read fail: {data.addr} (disconnected)")
        close_connection(sock, data.addr)
        raise SocketClosed


def accept_connection(key):
    conn, addr = key.fileobj.accept()
    logging.info(f"Connecting...: {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", status=Status.PENDING)
    events = selectors.EVENT_READ
    sel.register(conn, events, data=data)
    send(conn, data, b"ASMANTIA SERVER: PENDING FOR CRED")


def finish_connection(key):
    data = key.data
    creds = recv(key.fileobj, data, 1024)
    send(key.fileobj, data, b"ACCEPT")
    logging.info(f"Connection Complete: {data.addr}")
    data.status = Status.CONNECTED
    sel.modify(key.fileobj, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)


def close_connection(sock, addr=None):
    logging.info(f"Closing {addr if addr else 'Unknown'}")
    sel.unregister(sock)
    sock.close()


def handle_conn(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = recv(sock, data, 1024)
        if recv_data:
            logging.info(f"Receiving {recv_data!r} from {data.addr}")
            data.outb += recv_data
        else:
            logging.info(f"Closing connection: {data.addr}")
            close_connection(sock, data.addr)
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            logging.info(f"Sending {data.outb!r} to {data.addr}")
            sent = send(sock, data, data.outb)
            data.outb = data.outb[sent:]


hui = True


def handle_sigint(_signum, _frame):
    global hui
    logging.info("KeyboardInterrupt")
    running = False


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

        dt = clock.tick(1/4)
except Exception as e:
    logging.exception(e)
finally:
    logging.info("Exiting")
    sel.close()
