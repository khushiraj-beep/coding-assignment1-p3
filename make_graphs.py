
import csv
import matplotlib.pyplot as plt

with open("experiment_results.csv", newline="") as file:
    results = list(csv.DictReader(file))

names = [row["experiment"] for row in results]
times = [float(row["time_seconds"]) for row in results]
retransmissions = [
    int(row["retransmissions"] or 0) for row in results
]

# Graph 1: Transfer time
plt.figure()
plt.bar(names, times)
plt.title("Transfer Time Under Different Network Conditions")
plt.xlabel("Experiment")
plt.ylabel("Time (seconds)")
plt.tight_layout()
plt.savefig("transfer_time.png")
plt.close()

# Graph 2: Retransmissions
plt.figure()
plt.bar(names, retransmissions)
plt.title("Retransmissions Under Different Network Conditions")
plt.xlabel("Experiment")
plt.ylabel("Number of Retransmissions")
plt.tight_layout()
plt.savefig("retransmissions.png")
plt.close()

print("Graphs saved: transfer_time.png and retransmissions.png")
