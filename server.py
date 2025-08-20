import base64
import json
import logging
import os
import selectors
import signal
import socket
import types

import pygame

import Network
from SoftError import SoftError
from Character import CharSheet
import jsonschema
# noinspection PyUnusedImports
import logging_setup

################################
# Constants and Read-only(ish) #
################################
# Server config #
with open("server.cfg.json", "r") as f:
    config: dict = json.load(f)
# Config Loading #
IP = config.get("ip", "127.0.0.1")
PORT = config.get("port", 8080)
SERVER_NAME = config.get("name", "Unnamed server, idk, probably unsafe or smth, would be a good idea to contact admin")
SERVER_CAPACITY = config.get("capacity", 2)
TICKRATE = config.get("tickrate", 60)

with open("Data/credentials.json", "r") as f:
    all_creds: dict[str, dict] = json.load(f)

private_key = Network.generate_eph_key()
public_key = private_key.public_key()

#############
# Variables #
#############
clock = pygame.time.Clock()

characters = {}
for filename in os.listdir("Data/Char Sheets"):
    with open(os.path.join("Data/Char Sheets", filename), 'r') as f:
        ch_sheet = CharSheet.from_json(f.read(), True)
        characters[ch_sheet.ID] = ch_sheet

###############
# Scene Setup #
###############

##########
# Server #
##########
sel = selectors.DefaultSelector()
listening = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listening.bind((IP, PORT))


def decode(string: bytes):
    try:
        return string.decode()
    except UnicodeDecodeError:
        logging.exception(f"UNICODE_DECODE_ERROR {string!r}")
        return SoftError.UNICODE_DECODE_ERROR


def accept_connection(key):
    conn, addr = key.fileobj.accept()
    logging.info(f"Connecting...: {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", status=Network.Status.PENDING_KEY, info=None,
                                 aes_key=None, salt=None)
    sel.register(conn, selectors.EVENT_READ, data=data)
    data.salt = Network.gen_salt(16)
    packet = Network.prepare_packet(json.dumps(
        {
            "name": SERVER_NAME,
            "tickrate": TICKRATE,
            "public_key": base64.b85encode(public_key.export_key(format="raw")).decode(),
            "salt": base64.b85encode(data.salt).decode()
        }
    ).encode(), Network.PacketType.INTRODUCTION)
    Network.send_raw(conn, data, packet, sel, send_all=True)


def decode_json(string: str):
    try:
        return json.loads(string)
    except json.JSONDecodeError:
        logging.exception(f"JSON_DECODING_ERROR {string!r}")
        return SoftError.JSON_DECODING_ERROR


"""
x81_schema = jsonschema.Draft7Validator({
    "$schema": "https://json-schema.org/draft-07/schema",
    "type": "object",
    "properties": {
        "public_key": {
            "type": "string",
            "pattern": "(-----BEGIN PUBLIC KEY-----(\\n|\\r|\\r\\n)([0-9a-zA-Z\\+\\/=]{64}(\\n|\\r|\\r\\n))*([0-9a-zA-Z\\+\\/=]{1,63}(\\n|\\r|\\r\\n))?-----END PUBLIC KEY-----)"
        }
    },
    "required": [
        "public_key"
    ]
})
"""


def derive_key(key, pb_key):
    data = key.data
    data.aes_key = Network.derive_key(private_key, pb_key, data.salt)
    if not data.aes_key:
        Network.send_raw(sock=key.fileobj, data=data, sel=sel, send_all=True,
                         msg=Network.prepare_packet("problem with key".encode(),
                                                    Network.PacketType.REJECT))
        logging.error(f"Connection Rejected: {data.addr}: wasn't able to generate proper key: {data.aes_key}")
        Network.close_connection(sel, key.fileobj, addr=data.addr)
        return False
    data.status = Network.Status.PENDING_AUTH
    logging.info(f"AES Key for {data.addr}: {data.aes_key}")
    return True


def finish_connection(key, creds):
    data = key.data
    creds = decode(creds)
    if creds == SoftError.UNICODE_DECODE_ERROR:
        logging.info(f"Closing connection: {data.addr}")
        Network.close_connection(sel, key.fileobj, addr=data.addr)
        return False
    info = all_creds.get(creds, None)
    if not info:
        Network.send_raw(sock=key.fileobj, data=data, sel=sel, send_all=True,
                         msg=Network.prepare_packet("go fuck yourself".encode(), Network.PacketType.REJECT,
                                                    data.aes_key))
        logging.info(f"Connection Rejected: {data.addr}: Wrong Creds")
        Network.close_connection(sel, key.fileobj, data.addr)
        return False

    logging.info(f"Connection Complete: {data.addr}")

    data.outb += Network.prepare_packet(b"", Network.PacketType.ACCEPT, data.aes_key)
    data.outb += Network.prepare_packet(json.dumps({
        "sheet": characters[info["sheet"]].to_dict(),
        "info": info
    }).encode(), Network.PacketType.INITIAL_DATA, data.aes_key)

    data.status = Network.Status.CONNECTED
    data.info = info
    sel.modify(key.fileobj, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)
    return True


def handle_packet(pck, dta):
    if isinstance(pck[0], SoftError):
        if pck[0] == SoftError.PACKET_NOT_READY:
            if len(pck[1]):
                logging.warning(f"Received partial packet from {dta.addr}: {pck}")
            return 0.5
        logging.error(f"Something gone wrong: {pck}, {dta.addr}")
        return False
    dta.inb = dta.inb[pck[2]:]
    return True


def check_ptype(pck, *expected_ptypes: Network.PacketType):
    if pck[0] not in expected_ptypes:
        logging.error(f"Wrong ptype: {pck}, expected {expected_ptypes}")
        return False
    return True


def handle_conn(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = Network.recv_raw(sock, data, sel)
        if recv_data:
            data.inb += recv_data
            while not isinstance((packet := Network.recv_packet(data.inb, data.aes_key))[0], SoftError):
                res = handle_packet(packet, data)
                if res is not True:
                    return
                match data.status:
                    case Network.Status.PENDING_KEY:
                        if not check_ptype(packet, Network.PacketType.INTRODUCTION_REPLY):
                            return
                        if not derive_key(key, packet[1]):
                            return
                    case Network.Status.PENDING_AUTH:
                        if not check_ptype(packet, Network.PacketType.AUTH):
                            return
                        if not finish_connection(key, packet[1]):
                            return
                    case Network.Status.CONNECTED:
                        pass
                    case _:
                        logging.warning(f"Unknown status: {data}")
            res = handle_packet(packet, data)
            if res == 0.5:
                pass
            elif res is False:
                logging.info(f"Closing connection: {data.addr}")
                Network.close_connection(sel, sock, addr=data.addr)
                return
        else:
            logging.info(f"Disconnected: {data.addr}")
            logging.info(f"Closing connection: {data.addr}")
            Network.close_connection(sel, sock, addr=data.addr)
            return
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            sent = Network.send_raw(sock, data, data.outb, sel)
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
        events = sel.select(timeout=-1)
        for k, m in events:
            try:
                if k.data is None:
                    accept_connection(k)
                    continue
                handle_conn(k, m)
            except Network.SocketClosed:
                logging.warning("Socket closed abruptly")

        dt = clock.tick(TICKRATE)
except Exception as e:
    logging.exception(e)
finally:
    logging.info("Exiting")
    sel.close()
