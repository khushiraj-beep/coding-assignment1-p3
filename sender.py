
import socket
from packet import encode_packet

HOST = "127.0.0.1"
PORT = 5000
INPUT_FILE = "sample.txt"
CHUNK_SIZE = 1024

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

with open(INPUT_FILE, "rb") as file:
    file_data = file.read()

chunks = [
    file_data[i:i + CHUNK_SIZE]
    for i in range(0, len(file_data), CHUNK_SIZE)
]

print("File:", INPUT_FILE)
print("Total chunks:", len(chunks))

try:
    for seq_num, chunk in enumerate(chunks, start=1):
        packet = {
            "type": "DATA",
            "seq_num": seq_num,
            "ack_num": None,
            "payload": chunk
        }

        encoded_packet = encode_packet(packet)
        client.sendto(encoded_packet, (HOST, PORT))
        print(f"Sent chunk {seq_num}")

    end_packet = {
        "type": "END",
        "seq_num": len(chunks),
        "ack_num": None,
        "payload": b""
    }

    client.sendto(encode_packet(end_packet), (HOST, PORT))
    print("File transfer packets sent!")

finally:
    client.close()
