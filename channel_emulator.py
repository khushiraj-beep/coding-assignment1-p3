
import argparse
import random
import select
import socket
import time

HOST = "127.0.0.1"
BUFFER_SIZE = 65535


def main():
    parser = argparse.ArgumentParser(description="UDP channel emulator")
    parser.add_argument("--listen-port", type=int, default=5001)
    parser.add_argument("--receiver-port", type=int, default=5000)
    parser.add_argument("--loss", type=float, default=0.0)
    parser.add_argument("--corrupt", type=float, default=0.0)
    parser.add_argument("--duplicate", type=float, default=0.0)
    parser.add_argument("--reorder", type=float, default=0.0)
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--jitter", type=float, default=0.0)
    args = parser.parse_args()

    for name in ("loss", "corrupt", "duplicate", "reorder"):
        if not 0 <= getattr(args, name) <= 1:
            parser.error(f"--{name} must be between 0 and 1")

    if args.delay < 0 or args.jitter < 0:
        parser.error("--delay and --jitter cannot be negative")

    # Sender communicates with this socket on port 5001.
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender_socket.bind((HOST, args.listen_port))
    sender_socket.setblocking(False)

    # Receiver replies to this socket; ACKs are then forwarded to sender.
    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver_socket.bind((HOST, 0))
    receiver_socket.setblocking(False)

    receiver = (HOST, args.receiver_port)
    sender_address = None
    pending = None
    scheduled = []

    print(f"Emulator listening on {HOST}:{args.listen_port}")
    print(f"Receiver is {HOST}:{args.receiver_port}")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            readable, _, _ = select.select(
                [sender_socket, receiver_socket], [], [], 0.01
            )
            now = time.monotonic()

            # Deliver packets whose simulated delay has expired.
            due = [item for item in scheduled if item[0] <= now]
            scheduled = [item for item in scheduled if item[0] > now]
            for _, target, data in due:
                target.sendto(data, receiver if target is receiver_socket else sender_address)

            for sock in readable:
                data, address = sock.recvfrom(BUFFER_SIZE)

                if sock is receiver_socket:
                    if sender_address is not None:
                        sender_socket.sendto(data, sender_address)
                        print("Forwarded ACK to sender")
                    continue

                sender_address = address

                if random.random() < args.loss:
                    print("Dropped sender packet")
                    continue

                if random.random() < args.corrupt and data:
                    damaged = bytearray(data)
                    damaged[-1] ^= 1
                    data = bytes(damaged)
                    print("Corrupted sender packet")

                wait = max(
                    0.0,
                    args.delay + random.uniform(-args.jitter, args.jitter)
                )

                if random.random() < args.reorder:
                    if pending is None:
                        pending = (data, wait)
                        print("Holding packet for reordering")
                        continue
                    previous_data, previous_wait = pending
                    scheduled.append((time.monotonic() + wait, receiver_socket, data))
                    scheduled.append((time.monotonic() + previous_wait, receiver_socket, previous_data))
                    pending = None
                    print("Reordered packets")
                else:
                    scheduled.append((time.monotonic() + wait, receiver_socket, data))

                if random.random() < args.duplicate:
                    scheduled.append((time.monotonic() + wait, receiver_socket, data))
                    print("Duplicated packet")

            # Release a held packet if no second packet arrives soon.
            if pending is not None:
                data, wait = pending
                scheduled.append((now + wait + 0.05, receiver_socket, data))
                pending = None

    except KeyboardInterrupt:
        print("\nEmulator stopped.")
    finally:
        sender_socket.close()
        receiver_socket.close()


if __name__ == "__main__":
    main()
