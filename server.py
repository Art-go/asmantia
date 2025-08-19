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
SERVER_NAME = config.get("name", "Unnamed server, idk, probably unsafe or smth, would be a good idea to contact admin")
SERVER_CAPACITY = config.get("capacity", 2)
TICKRATE = config.get("tickrate", 60)

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


def accept_connection(key):
    conn, addr = key.fileobj.accept()
    logging.info(f"Connecting...: {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", status=Network.Status.PENDING, info=None)
    sel.register(conn, selectors.EVENT_READ, data=data)
    packet = Network.prepare_packet(json.dumps(
        {
            "name": SERVER_NAME,
            "tickrate": TICKRATE,
        }
    ).encode(), Network.PacketType.INTRODUCTION)
    Network.send_raw(conn, data, packet, sel, send_all=True)


def finish_connection(key, creds):
    data = key.data
    info = all_creds.get(creds, None)
    if not info:
        Network.send_raw(key.fileobj, data, b"REJECT", sel, send_all=True)
        logging.info(f"Connection Rejected: {data.addr}: Wrong Creds")
        Network.close_connection(sel, key.fileobj, data.addr)
        return

    logging.info(f"Connection Complete: {data.addr}")

    data.outb += Network.prepare_packet(json.dumps(info).encode(), Network.PacketType.ACCEPT)
    data.outb += Network.prepare_packet(characters[info["sheet"]].to_json().encode(), Network.PacketType.UPDATE)
    # TODO: make it(^) more than just receiving sheet

    data.status = Network.Status.CONNECTED
    sel.modify(key.fileobj, selectors.EVENT_READ | selectors.EVENT_WRITE, data=data)


def handle_packet(pck, dta, expected_ptype: Network.PacketType):
    if isinstance(pck[0], Network.SoftError):
        if pck[0] == Network.SoftError.PACKET_NOT_READY:
            logging.warn(f"Received partial packet from {dta.addr}: {pck}")
            return 0.5
        logging.error(f"Something gone wrong: {pck}")
        return False
    if pck[0] != expected_ptype:
        logging.error(f"Wrong ptype: {pck}, expected {expected_ptype}")
        return False
    dta.inb = dta.inb[pck[2]:]
    return True


def handle_conn(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = Network.recv_raw(sock, data, sel)
        if recv_data:
            logging.debug(f"Receiving {recv_data!r} from {data.addr}")
            data.inb += recv_data
            match data.status:
                case Network.Status.PENDING:
                    packet = Network.recv_packet(data.inb)
                    res = handle_packet(packet, data, Network.PacketType.INTRODUCTION_REPLY)
                    if res==0.5:
                        return
                    if res==False:
                        logging.info(f"Disconnected: {data.addr}")
                        logging.info(f"Closing connection: {data.addr}")
                        Network.close_connection(sel, sock, addr=data.addr)
                        return
                    finish_connection(key, packet[1].decode())
        else:
            logging.info(f"Disconnected: {data.addr}")
            logging.info(f"Closing connection: {data.addr}")
            Network.close_connection(sel, sock, addr=data.addr)
            return
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            logging.debug(f"Sending {data.outb!r} to {data.addr}")
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
