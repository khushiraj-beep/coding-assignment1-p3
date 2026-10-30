# coding-assignment1-p3

Reliable UDP File Transfer using Stop-and-Wait, Go-Back-N and Selective Repeat ARQ

## Project Overview

This project explores reliable file transfer over UDP using Automatic Repeat reQuest (ARQ) protocols. It includes a Selective Repeat implementation with a sender, receiver, packet encoding and decoding, retransmission timeout management, and a channel emulator for testing different network conditions.

## Selective Repeat Implementation

The Selective Repeat implementation includes:

- **Sender:** Divides the input file into chunks, sends packets within a transmission window, and processes acknowledgements.
- **Receiver:** Receives and buffers packets, acknowledges received chunks, and reconstructs the original file.
- **Selective retransmission:** Retransmits packets that have not been acknowledged before their timeout.
- **Adaptive RTO:** Adjusts the retransmission timeout based on observed acknowledgement timings.
- **Integrity verification:** Uses SHA-256 hashing to verify the received file.

## Channel Emulator

The channel emulator allows experiments under different simulated network conditions:

- Packet loss
- Packet corruption
- Packet duplication
- Packet reordering
- Network delay
- Delay jitter

## Project Files

| File | Description |
|---|---|
| `sr_sender.py` | Selective Repeat sender |
| `sr_receiver.py` | Selective Repeat receiver |
| `packet.py` | Packet encoding and decoding |
| `rto.py` | Retransmission timeout estimation |
| `channel_emulator.py` | Network-condition simulation |
| `test_sr.py` | Protocol tests |
| `run_experiments.py` | Automated experiment runner |
| `make_graphs.py` | Experiment graph generation |
| `experiment_results.csv` | Recorded experiment results |
| `transfer_time.png` | Transfer-time graph |
| `retransmissions.png` | Retransmission graph |

## Requirements

- Python 3
- Matplotlib for generating graphs

Install Matplotlib:

```powershell
py -m pip install matplotlib
```

## Running the Project

Run the tests:

```powershell
py test_sr.py
```

Run the automated experiments:

```powershell
py run_experiments.py
```

Generate the graphs:

```powershell
py make_graphs.py
```

## Experimental Results

| Experiment | Transfer Time | Retransmissions | Status |
|---|---:|---:|---|
| Baseline | 0.214 seconds | 0 | Success |
| 10% packet loss | 0.726 seconds | 6 | Success |
| 50 ms delay | 0.869 seconds | 0 | Success |

## Observations

1. The baseline transfer completed without retransmissions.
2. Under 10% simulated packet loss, six retransmissions occurred, but the file transfer still succeeded.
3. Under 50 ms simulated delay, the transfer took longer than the baseline without retransmissions in this run.
4. The results demonstrate that the Selective Repeat implementation can complete transfers under the tested conditions.

## Conclusion

The experiments demonstrate reliable file transfer over UDP using Selective Repeat ARQ. Acknowledgements and selective retransmissions support recovery from packet loss, while timeout estimation helps determine when packets should be retransmitted. The channel emulator makes it possible to evaluate the implementation under different simulated network conditions.

*Note: The recorded timings are specific to this test environment. Stop-and-Wait and Go-Back-N are listed in the repository title, but their implementation and test results must be verified separately.*
