import logging
from enum import IntEnum


class Status(IntEnum):
    CONNECTED = 100
    PENDING = 20


class SocketClosed(Exception):
    ...


def close_connection(sel, sock, addr=None):
    logging.info(f"Closing {addr if addr else 'Unknown'}")
    if sel.get_key(sock):
        sel.unregister(sock)
    sock.close()


def recv(sel, sock, data, *args, **kwargs):
    try:
        return sock.recv(*args, **kwargs)
    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
        logging.error(f"Read fail: {data.addr} (disconnected)")
        close_connection(sel, sock, data.addr)
        raise SocketClosed


def send(sel, sock, data, msg: bytes, *args, send_all: bool = False, **kwargs):
    try:
        if send_all:
            state = sock.getblocking()
            sock.setblocking(True)
            sent = 0
            while sent < len(msg):
                sent += sock.send(msg[sent:], *args, **kwargs)
            sock.setblocking(state)
        else:
            return sock.send(msg, *args, **kwargs)
    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
        logging.error(f"Read fail: {data.addr} (disconnected)")
        close_connection(sel, sock, data.addr)
        raise SocketClosed
