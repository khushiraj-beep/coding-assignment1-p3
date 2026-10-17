
import socket

HOST = "127.0.0.1"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

invalid_packet = b"This is not a valid JSON packet"

client.sendto(invalid_packet, (HOST, PORT))

print("Invalid UDP packet sent successfully!")

client.close()
