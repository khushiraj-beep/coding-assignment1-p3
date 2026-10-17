
from packet import encode_packet, decode_packet

# Create a sample packet
original_packet = {
    "type": "DATA",
    "seq_num": 1,
    "ack_num": None,
    "payload": b"Hello, reliable UDP!"
}

# Encode the packet
encoded = encode_packet(original_packet)
print("1. Packet encoded successfully")

# Decode the packet
decoded = decode_packet(encoded)
print("2. Packet decoded successfully")

# Verify the data
assert decoded["payload"] == original_packet["payload"]
assert decoded["seq_num"] == original_packet["seq_num"]
assert decoded["type"] == original_packet["type"]

print("3. Data verified successfully")
print("Decoded payload:", decoded["payload"].decode())

# Corrupt the checksum and test detection
corrupted = bytearray(encoded)
checksum_position = corrupted.find(b'"checksum":"')

if checksum_position == -1:
    raise ValueError("Checksum field not found")

hex_position = checksum_position + len(b'"checksum":"')
corrupted[hex_position] = (
    ord("0") if corrupted[hex_position] != ord("0") else ord("1")
)

try:
    decode_packet(bytes(corrupted))
    print("ERROR: Corruption was not detected")
except ValueError:
    print("4. Corrupted packet detected successfully")

# Test 5: Invalid packet detection
print("\nTesting invalid packet...")

invalid_data = b"This is not a valid JSON packet"

try:
    decode_packet(invalid_data)
    print("ERROR: Invalid packet was accepted")
except (ValueError, KeyError, UnicodeDecodeError) as error:
    print("5. Invalid packet rejected successfully")
    print("Reason:", error)

# Test 6: Invalid packet type
print("\nTesting invalid packet type...")

try:
    encode_packet({
        "type": "UNKNOWN",
        "seq_num": 1,
        "ack_num": None,
        "payload": b"Test"
    })
    print("ERROR: Invalid packet type was accepted")
except ValueError:
    print("6. Invalid packet type rejected successfully")


# Test 7: Negative sequence number
print("\nTesting negative sequence number...")

try:
    encode_packet({
        "type": "DATA",
        "seq_num": -1,
        "ack_num": None,
        "payload": b"Test"
    })
    print("ERROR: Negative sequence number was accepted")
except ValueError:
    print("7. Negative sequence number rejected successfully")


# Test 8: Invalid payload type
print("\nTesting invalid payload type...")

try:
    encode_packet({
        "type": "DATA",
        "seq_num": 1,
        "ack_num": None,
        "payload": "This should be bytes"
    })
    print("ERROR: Invalid payload was accepted")
except ValueError:
    print("8. Invalid payload type rejected successfully")
