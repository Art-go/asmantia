import base64
import gzip
import logging
import socket
from enum import IntEnum

# cryptography
from Crypto.PublicKey import ECC
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import HKDF
from Crypto.Hash import SHA512
from Crypto.Cipher import AES
from Crypto.Protocol.DH import import_x25519_public_key

from SoftError import SoftError

trailer = b"\xFF\xFF\xFF\xFF"
header = b"ASMN"
secure_header = b"SAMN"


class Status(IntEnum):
    CONNECTED = 100
    PENDING_KEY = 10
    PENDING_AUTH = 20


class PacketType(IntEnum):
    INTRODUCTION = 0x01
    INTRODUCTION_REPLY = 0x81
    AUTH = 0x82
    INITIAL_DATA = 0x02

    ACCEPT = 0x7F
    REJECT = 0x80


class SocketClosed(Exception): ...


def close_connection(sel, sock: socket.socket, addr=None):
    logging.info(f"Closing {addr if addr else 'Unknown'}")
    if sel and sel.get_key(sock):
        sel.unregister(sock)
    sock.close()


def recv_raw(sock: socket.socket, data, sel=None, size=4096, *args, **kwargs):
    try:
        # noinspection PyArgumentList
        msg = sock.recv(size, *args, **kwargs)
        logging.debug(f"Receiving {msg!r} from {data.addr}")
        return msg
    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
        logging.error(f"Read fail: {data.addr} (disconnected)")
        close_connection(sel, sock, data.addr)
        raise SocketClosed


def send_raw(sock: socket.socket, data, msg: bytes, sel=None, *args, send_all: bool = False, **kwargs):
    logging.debug(f"Sending {msg!r} to {data.addr}")
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


def prepare_packet(payload: bytes, ptype: PacketType, aes_key: bytes=None) -> bytes:
    if aes_key is None:
        return prepare_asmn(payload, ptype)
    else:
        return prepare_samn(payload, ptype, aes_key)


def prepare_asmn(payload: bytes, ptype: PacketType) -> bytes:
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


def prepare_samn(payload: bytes, ptype: PacketType, aes_key: bytes) -> bytes:
    asmn_packet = prepare_asmn(payload, ptype)

    nonce = get_random_bytes(12)
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    encrypted_payload, tag = cipher.encrypt_and_digest(asmn_packet)
    encrypted_payload = base64.b85encode(encrypted_payload)

    length = len(encrypted_payload)
    if length > 0xFFFFFFFF:
        raise ValueError("Payload too big")

    packet = secure_header
    # header
    assert len(nonce) == 12
    packet += nonce
    assert len(tag) == 16
    packet += tag
    packet += length.to_bytes(4, 'big')
    # payload
    packet += encrypted_payload
    # trailer
    packet += trailer

    return packet


CUT_THRESHOLD = 128


def recv_samn(buffer: bytes, aes_key: bytes):
    if len(buffer) < 40:
        return SoftError.PACKET_NOT_READY, (buffer[:CUT_THRESHOLD] if len(buffer) > CUT_THRESHOLD else buffer)
    if buffer[:4] != b"SAMN":
        return SoftError.PACKET_CORRUPTED, (buffer[:CUT_THRESHOLD] if len(buffer) > CUT_THRESHOLD else buffer)
    nonce = buffer[4:16]
    tag = buffer[16:32]
    length = int.from_bytes(buffer[32:36], 'big')
    if len(buffer) < length + 40:
        return SoftError.PACKET_NOT_READY, (buffer[:CUT_THRESHOLD] if len(buffer) > CUT_THRESHOLD else buffer)
    if buffer[length + 36:length + 40] != trailer:
        return SoftError.PACKET_CORRUPTED, (buffer[:CUT_THRESHOLD] if len(buffer) > CUT_THRESHOLD else buffer)
    payload = buffer[36:36 + length]
    try:
        payload = base64.b85decode(payload)
    except ValueError:
        return SoftError.BAD_PAYLOAD, repr(payload)
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    try:
        payload = cipher.decrypt_and_verify(payload, tag)
    except ValueError:
        return SoftError.BAD_PAYLOAD, repr(payload), nonce, tag
    logging.debug(f"decrypted: {payload}")
    return recv_packet(payload)[:2] + (length + 40,)


def recv_packet(buffer: bytes, aes_key: bytes = None):
    if len(buffer) < 12:
        return SoftError.PACKET_NOT_READY, (buffer[:CUT_THRESHOLD] if len(buffer) > CUT_THRESHOLD else buffer)
    if buffer[:4] == b"SAMN":
        if aes_key is None:
            return SoftError.NO_AES_KEY, (buffer[:CUT_THRESHOLD] if len(buffer) > CUT_THRESHOLD else buffer)
        return recv_samn(buffer, aes_key)
    if buffer[:4] != b"ASMN":
        return SoftError.PACKET_CORRUPTED, (buffer[:CUT_THRESHOLD] if len(buffer) > CUT_THRESHOLD else buffer)
    ptype = buffer[4]
    if ptype not in PacketType:
        return SoftError.NON_EXISTENT_PTYPE, (buffer[:CUT_THRESHOLD] if len(buffer) > CUT_THRESHOLD else buffer)
    ptype = PacketType(ptype)
    length = int.from_bytes(buffer[5:8], 'big')
    if len(buffer) < length + 12:
        return SoftError.PACKET_NOT_READY, (buffer[:CUT_THRESHOLD] if len(buffer) > CUT_THRESHOLD else buffer)
    if buffer[length + 8:length + 12] != trailer:
        return SoftError.PACKET_CORRUPTED, (buffer[:CUT_THRESHOLD] if len(buffer) > CUT_THRESHOLD else buffer)
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


def simple_buffered_recv(sock: socket.socket, data, key: bytes = None):
    """
    Avoid using until necessary, instead try using select
    """
    blocking = sock.getblocking()
    sock.setblocking(True)
    safety = 100
    while (packet := recv_packet(data.inb, aes_key=key))[0] == SoftError.PACKET_NOT_READY:
        data.inb += recv_raw(sock, data)
        safety -= 1
        if safety == 0:
            return SoftError.NO_ANSWER,

    sock.setblocking(blocking)
    return packet


def generate_eph_key():
    return ECC.generate(curve="curve25519")


def derive_key(private_key: ECC.EccKey, public_key, salt):
    try:
        public_key = import_x25519_public_key(public_key)
        secret = public_key.pointQ * private_key.d
        return HKDF(secret.x.to_bytes(32, 'big'), 32, salt, SHA512)
    except Exception as e:
        logging.exception(f"Something gone wrong: {e}")
        return None


def gen_salt(len=12):
    return get_random_bytes(len)

########################################################################################################################
# ASMN Packet
# ["ASMN"][PacketType 1B][Length 3B][Payload wrapped in gzip and b85][0xFFFFFFFF]
#
# SAMN Packet
# ["SAMN"][NONCE 12B][TAG 16B][Length 4B][Encrypted payload wrapped in b85][0xFFFFFFFF]
########################################################################################################################
# Server side
########################################################################################################################
# 01 - INTRODUCTION, request for creds
# Payload example: {
#     "name": "Asmantia main",
#     "tickrate": 60,
#     "public_key": PEM format
#     "salt": 16-byte number
#     ...
# }
#
# 02 - INITIAL_DATA, send info about player and his charsheet
# Payload example: {
#     "info": {...},
#     "sheet": {...}
# }
########################################################################################################################
# Both sides
########################################################################################################################
# 7F - Accept, payload is empty
# 80 - Reject, payload sends you fuck yourself
########################################################################################################################
# Client side
########################################################################################################################
# 81 - INTRODUCTION_REPLY
# Payload example: {
#     "public_key": PEM format
# }
#
# 82 - AUTH, and it is encrypted!(hopefully)
# Payload example: "USERNAME+SALT"
#
########################################################################################################################
