
import socket
from packet import encode_packet, decode_packet

HOST = "127.0.0.1"
PORT = 5000
OUTPUT_FILE = "received_sample.txt"

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

received_chunks = {}

print(f"File receiver listening on {HOST}:{PORT}")

try:
    while True:
        raw_data, sender_address = server.recvfrom(65535)

        try:
            packet = decode_packet(raw_data)

            if packet["type"] == "DATA":
                seq_num = packet["seq_num"]
                payload = packet["payload"]

                if seq_num not in received_chunks:
                    received_chunks[seq_num] = payload
                    print(f"Received chunk {seq_num}")

                # Send an ACK for this chunk
                ack_packet = {
                    "type": "ACK",
                    "seq_num": 0,
                    "ack_num": seq_num,
                    "payload": b""
                }

                server.sendto(
                    encode_packet(ack_packet),
                    sender_address
                )

            elif packet["type"] == "END":
                total_chunks = packet["seq_num"]

                # Check whether every chunk has arrived
                if all(
                    i in received_chunks
                    for i in range(1, total_chunks + 1)
                ):
                    with open(OUTPUT_FILE, "wb") as file:
                        for i in range(1, total_chunks + 1):
                            file.write(received_chunks[i])

                    print(f"File saved as {OUTPUT_FILE}")
                    print("File transfer completed.")
                    break

                else:
                    print("Some chunks are missing. Transfer incomplete.")

        except (ValueError, KeyError) as error:
            print("Invalid packet:", error)

except KeyboardInterrupt:
    print("\nReceiver stopped.")

finally:
    server.close()
