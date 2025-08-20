import json
import socket
import types

import Network
import SoftError

ip = "127.0.0.1"
port = 8080
private_key = Network.generate_eph_key()
public_key = private_key.public_key().export_key(format="PEM")


def handle_packet(pck, dta, expected_ptype: Network.PacketType):
    if isinstance(pck[0], SoftError.SoftError):
        raise ConnectionError(f"Something gone wrong: {pck}")
    if pck[0] != expected_ptype:
        raise ConnectionError(f"Wrong ptype: {pck}, expected {expected_ptype}")
    dta.inb = dta.inb[pck[2]:]


sock = socket.socket()
sock.connect((ip, port))
data = types.SimpleNamespace(addr=(ip, port), outb=b"", inb=b"", AES_key=b"", salt=b"")

packet = Network.simple_buffered_recv(sock, data)
handle_packet(packet, data, Network.PacketType.INTRODUCTION)
server_info = {
}
server_info.update(json.loads(packet[1].decode()))

packet = Network.prepare_packet(b"\x00\xFF\xEF", Network.PacketType.INTRODUCTION_REPLY)
#packet = Network.prepare_packet(bytes(reversed(range(256))), Network.PacketType.INTRODUCTION_REPLY)
#packet = Network.prepare_packet(bytes(reversed(range(256))), Network.PacketType.INTRODUCTION_REPLY)
Network.send_raw(sock, data, packet, send_all=True)

packet = Network.simple_buffered_recv(sock, data)
handle_packet(packet, data, Network.PacketType.ACCEPT)

packet = Network.simple_buffered_recv(sock, data)
handle_packet(packet, data, Network.PacketType.INITIAL_DATA)
packet = json.loads(packet[1].decode())
sheet, char_info = packet["sheet"], packet["info"]