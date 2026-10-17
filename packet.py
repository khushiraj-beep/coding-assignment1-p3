
import json
import base64
import hashlib
import hmac


def calculate_checksum(data):
    return hashlib.sha256(data).hexdigest()


def encode_packet(packet):
    # Validate packet type
    if packet.get("type") not in ("DATA", "ACK", "END"):
        raise ValueError("Invalid packet type")

    # Validate sequence number
    seq_num = packet.get("seq_num", 0)
    if type(seq_num) is not int or seq_num < 0:
        raise ValueError("Invalid sequence number")

    # Validate acknowledgement number
    ack_num = packet.get("ack_num")
    if ack_num is not None:
        if type(ack_num) is not int or ack_num < 0:
            raise ValueError("Invalid acknowledgement number")

    # Validate payload
    payload = packet.get("payload", b"")
    if not isinstance(payload, bytes):
        raise ValueError("Payload must be bytes")

    # Convert binary payload to Base64 text
    encoded_payload = base64.b64encode(payload).decode("ascii")

    core = {
        "type": packet["type"],
        "transfer_id": packet.get("transfer_id", "transfer-1"),
        "seq_num": seq_num,
        "ack_num": ack_num,
        "payload": encoded_payload
    }

    # Calculate checksum over packet contents
    content = json.dumps(
        core, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")

    core["checksum"] = calculate_checksum(content)

    return json.dumps(
        core, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def decode_packet(raw_data):
    # Check the incoming data format
    if not isinstance(raw_data, bytes):
        raise ValueError("Packet data must be bytes")

    try:
        packet = json.loads(raw_data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Invalid packet format") from error

    # The packet must be a JSON object
    if not isinstance(packet, dict):
        raise ValueError("Packet must be a JSON object")

    # Check required fields
    required_fields = {
        "type", "transfer_id", "seq_num",
        "ack_num", "payload", "checksum"
    }

    if not required_fields.issubset(packet):
        raise ValueError("Packet is missing required fields")

    # Check packet type
    if packet["type"] not in ("DATA", "ACK", "END"):
        raise ValueError("Invalid packet type")

    # Check sequence number
    if type(packet["seq_num"]) is not int or packet["seq_num"] < 0:
        raise ValueError("Invalid sequence number")

    # Check acknowledgement number
    ack_num = packet["ack_num"]
    if ack_num is not None:
        if type(ack_num) is not int or ack_num < 0:
            raise ValueError("Invalid acknowledgement number")

    # Check field types
    if not isinstance(packet["transfer_id"], str):
        raise ValueError("Invalid transfer ID")

    if not isinstance(packet["payload"], str):
        raise ValueError("Invalid payload format")

    if not isinstance(packet["checksum"], str):
        raise ValueError("Invalid checksum format")

    # Verify checksum before decoding the payload
    received_checksum = packet.pop("checksum")

    content = json.dumps(
        packet, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")

    expected_checksum = calculate_checksum(content)

    if not hmac.compare_digest(received_checksum, expected_checksum):
        raise ValueError("Checksum mismatch: corrupted packet")

    # Decode Base64 payload
    try:
        packet["payload"] = base64.b64decode(
            packet["payload"], validate=True
        )
    except (ValueError, base64.binascii.Error) as error:
        raise ValueError("Invalid Base64 payload") from error

    packet["checksum"] = received_checksum

    return packet
