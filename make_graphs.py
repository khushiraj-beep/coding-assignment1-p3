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
        "protocol",
        "experiment",
        "time_seconds",
        "retransmissions",
        "goodput_bytes_per_sec",
        "success",
    }

    if not required.issubset(rows[0]):
        print("CSV is missing required performance metrics.")
        print("Run run_experiments.py first.")
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

    graphs = [
        (
            "time_seconds",
            "Transfer Time Comparison",
            "Time (seconds)",
            "transfer_time_comparison.png",
        ),
        (
            "retransmissions",
            "Retransmissions Comparison",
            "Number of Retransmissions",
            "retransmissions_comparison.png",
        ),
        (
            "goodput_bytes_per_sec",
            "Goodput Comparison",
            "Goodput (bytes/second)",
            "goodput_comparison.png",
        ),
    ]

    for metric, title, ylabel, filename in graphs:
        plt.figure(figsize=(9, 5))
        plotted = False

        for protocol in protocols:
            values = []
            labels = []

            for condition in conditions:
                samples = grouped.get((protocol, condition), [])

                if samples:
                    average = sum(
                        float(sample[metric])
                        for sample in samples
                    ) / len(samples)

                    values.append(average)
                    labels.append(condition)

            if values:
                plt.plot(
                    labels,
                    values,
                    marker="o",
                    label=protocol,
                )
                plotted = True

        if plotted:
            plt.title(title)
            plt.xlabel("Network Condition")
            plt.ylabel(ylabel)
            plt.legend()
            plt.grid(True)
            plt.tight_layout()

            path = os.path.join(GRAPH_DIR, filename)
            plt.savefig(path, dpi=300)
            print(f"Saved {path}")
        else:
            print(f"No successful data available for {title}")

        plt.close()


if __name__ == "__main__":
    make_graphs()