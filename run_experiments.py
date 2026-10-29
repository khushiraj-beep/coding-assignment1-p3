
import csv
import os
import re
import subprocess
import sys
import time

PY = sys.executable
RESULTS_FILE = "experiment_results.csv"

CONDITIONS = [
    ("Baseline", []),
    ("10% packet loss", ["--loss", "0.1"]),
    ("50 ms delay", ["--delay", "0.05"]),
]

PROTOCOLS = ("SW", "GBN", "SR")


def stop_process(process):
    if process is None:
        return

    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def run_one(protocol, condition, settings):
    receiver = None
    emulator = None
    start = time.perf_counter()
    retransmissions = 0
    success = False

    if protocol in ("SW", "GBN"):
        receiver_command = [
            PY, "arq_receiver.py",
            "--protocol", protocol,
            "--port", "5000",
            "--output", f"received_{protocol.lower()}.txt",
        ]
        sender_script = (
            "sw_sender.py" if protocol == "SW"
            else "gbn_sender.py"
        )
    else:
        receiver_command = [
            PY, "sr_receiver.py",
            "--port", "5000",
            "--output", "received_sr.txt",
        ]
        sender_script = "sr_sender.py"

    try:
        receiver = subprocess.Popen(
            receiver_command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.5)

        emulator = subprocess.Popen(
            [PY, "channel_emulator.py", *settings],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.5)

        command = [
            PY, sender_script, "sample.txt",
            "--host", "127.0.0.1",
            "--port", "5001",
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=90,
        )

        output = result.stdout + "\n" + result.stderr

        # Detect successful completion using each sender's own message.
        if protocol == "SR":
            success = (
                result.returncode == 0
                and "File transfer completed successfully" in output
            )
            match = re.findall(
                r"Timeout: retransmitted packet \d+", output
            )
            retransmissions = len(match)
        else:
            success = (
                result.returncode == 0
                and f"Protocol: {protocol}" in output
            )
            match = re.search(r"Retransmissions:\s*(\d+)", output)
            if match:
                retransmissions = int(match.group(1))
            else:
                retransmissions = sum(
                    1 for line in output.splitlines()
                    if "Retransmitted packet" in line
                )

        elapsed = time.perf_counter() - start

        if not success:
            print(f"\nFAILED: {protocol} / {condition}")
            print(output)
        else:
            print(
                f"SUCCESS: {protocol} / {condition} | "
                f"{elapsed:.3f}s | "
                f"{retransmissions} retransmissions"
            )

        return {
            "protocol": protocol,
            "experiment": condition,
            "time_seconds": round(elapsed, 3),
            "retransmissions": retransmissions,
            "success": success,
        }

    except (subprocess.TimeoutExpired, OSError) as error:
        print(f"FAILED: {protocol} / {condition}: {error}")
        return {
            "protocol": protocol,
            "experiment": condition,
            "time_seconds": round(time.perf_counter() - start, 3),
            "retransmissions": retransmissions,
            "success": False,
        }

    finally:
        stop_process(emulator)
        stop_process(receiver)


def main():
    required = [
        "sample.txt",
        "packet.py",
        "channel_emulator.py",
        "sw_sender.py",
        "gbn_sender.py",
        "sr_sender.py",
        "arq_receiver.py",
        "sr_receiver.py",
    ]

    missing = [name for name in required if not os.path.isfile(name)]
    if missing:
        print("Missing required files:", ", ".join(missing))
        return

    results = []

    for condition, settings in CONDITIONS:
        for protocol in PROTOCOLS:
            print(f"\nRunning {protocol}: {condition}")
            results.append(run_one(protocol, condition, settings))

    fields = [
        "protocol",
        "experiment",
        "time_seconds",
        "retransmissions",
        "success",
    ]

    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    passed = sum(row["success"] for row in results)
    print(f"\nResults saved to {RESULTS_FILE}")
    print(f"Successful runs: {passed}/{len(results)}")

    if passed != len(results):
        print(
            "Some runs failed. Fix those before using the results "
            "for performance comparisons."
        )


if __name__ == "__main__":
    main()
