import base64
import gzip
import logging
import socket
from enum import IntEnum

trailer = b"\xFF\xFF\xFF\xFF"
header = b"ASMN"


class Status(IntEnum):
    CONNECTED = 100
    PENDING = 20


class SocketClosed(Exception):
    ...


def close_connection(sel, sock: socket.socket, addr=None):
    logging.info(f"Closing {addr if addr else 'Unknown'}")
    if sel and sel.get_key(sock):
        sel.unregister(sock)
    sock.close()


def recv_raw(sock: socket.socket, data, sel=None, size=4096, *args, **kwargs):
    try:
        # noinspection PyArgumentList
        return sock.recv(size, *args, **kwargs)
    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
        logging.error(f"Read fail: {data.addr} (disconnected)")
        close_connection(sel, sock, data.addr)
        raise SocketClosed


def send_raw(sock: socket.socket, data, msg: bytes, sel=None, *args, send_all: bool = False, **kwargs):
    try:
        if send_all:
            state = sock.getblocking()
            sock.setblocking(True)
            sent = 0
            while sent < len(msg):
                # noinspection PyArgumentList
                sent += sock.send(msg[sent:], *args, **kwargs)
            sock.setblocking(state)
        else:
            # noinspection PyArgumentList
            return sock.send(msg, *args, **kwargs)
    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
        logging.error(f"Write fail: {data.addr} (disconnected)")
        close_connection(sel, sock, data.addr)
        raise SocketClosed


class PacketType(IntEnum):
    INTRODUCTION = 0x01
    INTRODUCTION_REPLY = 0x81

    UPDATE = 0x02

    ACCEPT = 0x7F
    REJECT = 0x80


def prepare_packet(payload: bytes, ptype: PacketType) -> bytes:
    """
    payload comes in, packet, ready to be sent, comes out
    payload is limited in size: 16MiB-1B, tho i doubt i will ever need more than that
    besides, this limit only applies after zipping and encoding

    the packets are simple:
    ["ASMN"][PacketType, 1 byte][Length of wrapped payload, 3 bytes][Payload wrapped in gzip and b85][0xFFFFFFFF]
    """
    if ptype not in PacketType:
        raise ValueError("Non-existent ptype was given")

    wrapped_payload = base64.b85encode(gzip.compress(payload))
    length = len(wrapped_payload)
    if length > 0xFFFFFF:
        raise ValueError("Payload too big")

    packet = header
    # header
    packet += ptype.to_bytes(1, 'big')
    packet += length.to_bytes(3, 'big')
    # payload
    packet += wrapped_payload
    # trailer
    packet += trailer

    return packet


class SoftError(IntEnum):
    NOT_ASMANTIA = 1
    NON_EXISTENT_PTYPE = 2
    PACKET_NOT_READY = 3
    NO_ANSWER = 4
    BAD_PAYLOAD = 5


def recv_packet(buffer: bytes):
    if len(buffer) < 12:
        return SoftError.PACKET_NOT_READY,
    if buffer[:4] != b"ASMN":
        return SoftError.NOT_ASMANTIA,
    ptype = buffer[4]
    if ptype not in PacketType:
        return SoftError.NON_EXISTENT_PTYPE,
    ptype = PacketType(ptype)
    length = int.from_bytes(buffer[5:8], 'big')
    if len(buffer) < length + 12 or buffer[length + 8 : length + 12] != trailer:
        return SoftError.PACKET_NOT_READY,
    payload = buffer[8:8 + length]
    try:
        payload = base64.b85decode(payload)
    except ValueError:
        return SoftError.BAD_PAYLOAD, repr(payload)
    try:
        payload = gzip.decompress(payload)
    except ValueError:
        return SoftError.BAD_PAYLOAD, repr(payload)
    return ptype, payload, length + 12


def simple_buffered_recv(sock: socket.socket, data):
    """
    Avoid using until necessary, instead try using select
    """
    blocking = sock.getblocking()
    sock.setblocking(True)
    safety = 100
    while (packet := recv_packet(data.inb))[0] == SoftError.PACKET_NOT_READY:
        data.inb += recv_raw(sock, data)
        safety -= 1
        if safety == 0:
            return SoftError.NO_ANSWER

    sock.setblocking(blocking)
    return packet

########################################################################################################################
# Server side
########################################################################################################################
# 01 - introduction, request for creds
# Payload example: {
#     "name": "Asmantia main",
#     "tickrate": 60,
#     ...
# }
#
# 02 - update, for now just charsheet, but will probably change it, i even have TODO for it, or will change it to
# init, starting info or something else, idk
########################################################################################################################
# Both sides
########################################################################################################################
# 7F - Accept, payload is empty
# 80 - Reject, payload sends you fuck yourself
########################################################################################################################
# Client side
########################################################################################################################
# 81 - simple auth, NO ENCRYPTION CUZ I'M FUCKING LAZY
# Payload example: {
#     "creds": "USERNAME+SALT"
# }
#
########################################################################################################################
