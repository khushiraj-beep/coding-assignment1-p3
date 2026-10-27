
import csv
import re
import subprocess
import sys
import time

PY = sys.executable

TESTS = [
    ("Baseline", []),
    ("10% packet loss", ["--loss", "0.1"]),
    ("50 ms delay", ["--delay", "0.05"]),
]

results = []

for name, settings in TESTS:
    print(f"\n=== {name} ===")

    receiver = subprocess.Popen(
        [PY, "sr_receiver.py"],
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

    start = time.perf_counter()
    try:
        run = subprocess.run(
            [PY, "sr_sender.py", "sample.txt"],
            capture_output=True,
            text=True,
            timeout=90,
        )
        elapsed = time.perf_counter() - start
        output = run.stdout + "\n" + run.stderr

        print(output)
        success = "File transfer completed successfully." in output
        retransmissions = len(
            re.findall(r"Timeout: retransmitted packet", output)
        )

        results.append({
            "experiment": name,
            "time_seconds": round(elapsed, 3),
            "retransmissions": retransmissions,
            "success": success,
        })

    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        print("Experiment timed out.")
        results.append({
            "experiment": name,
            "time_seconds": round(elapsed, 3),
            "retransmissions": "",
            "success": False,
        })

    finally:
        emulator.terminate()
        receiver.terminate()
        emulator.wait()
        receiver.wait()

with open("experiment_results.csv", "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "experiment",
            "time_seconds",
            "retransmissions",
            "success",
        ],
    )
    writer.writeheader()
    writer.writerows(results)

print("\nSaved results to experiment_results.csv")
