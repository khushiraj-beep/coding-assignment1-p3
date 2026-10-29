
import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt

RESULTS_FILE = "experiment_results.csv"
GRAPH_DIR = "graphs"


def make_graphs():
    if not os.path.exists(RESULTS_FILE):
        print(f"Missing results file: {RESULTS_FILE}")
        return

    with open(RESULTS_FILE, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    if not rows:
        print("No experiment results available.")
        return

    required = {
        "protocol", "experiment", "time_seconds",
        "retransmissions", "success"
    }
    if not required.issubset(rows[0]):
        print("The CSV does not contain protocol comparison results.")
        print("Run the experiment runner first.")
        return

    os.makedirs(GRAPH_DIR, exist_ok=True)

    grouped = defaultdict(list)
    for row in rows:
        if row["success"].strip().lower() == "true":
            grouped[(row["protocol"], row["experiment"])].append(row)

    conditions = [
        "Baseline",
        "10% packet loss",
        "50 ms delay",
    ]
    protocols = ["SW", "GBN", "SR"]

    for metric, title, filename in [
        ("time_seconds", "Transfer Time by Protocol",
         "transfer_time_comparison.png"),
        ("retransmissions", "Retransmissions by Protocol",
         "retransmissions_comparison.png"),
    ]:
        plt.figure(figsize=(9, 5))
        plotted = False

        for protocol in protocols:
            values = []
            labels = []

            for condition in conditions:
                samples = grouped.get((protocol, condition), [])
                if samples:
                    values.append(
                        sum(float(s[metric]) for s in samples) / len(samples)
                    )
                    labels.append(condition)

            if values:
                plt.plot(labels, values, marker="o", label=protocol)
                plotted = True

        if plotted:
            plt.title(title)
            plt.xlabel("Network Condition")
            ylabel = (
                "Time (seconds)"
                if metric == "time_seconds"
                else "Number of Retransmissions"
            )
            plt.ylabel(ylabel)
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            path = os.path.join(GRAPH_DIR, filename)
            plt.savefig(path)
            print(f"Saved {path}")
        else:
            print(f"No successful data available for {title}")

        plt.close()


if __name__ == "__main__":
    make_graphs()

