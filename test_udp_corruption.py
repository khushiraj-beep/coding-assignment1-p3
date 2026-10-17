
import socket
from packet import encode_packet

HOST = "127.0.0.1"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

packet = {
    "type": "DATA",
    "seq_num": 1,
    "ack_num": None,
    "payload": b"Test corrupted packet"
}

encoded_packet = bytearray(encode_packet(packet))

# Change one byte in the payload without updating the checksum
position = encoded_packet.find(b"VGVzdCBjb3JydXB0ZWQgcGFja2V0")

if position == -1:
    print("Could not find the encoded payload.")
else:
    encoded_packet[position] = ord("A")
    client.sendto(bytes(encoded_packet), (HOST, PORT))
    print("Corrupted packet sent!")

client.close()
