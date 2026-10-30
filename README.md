# Reliable Data Transfer over UDP

A Python-based implementation of reliable file transfer over UDP using three Automatic Repeat reQuest (ARQ) protocols: Stop-and-Wait, Go-Back-N and Selective Repeat.

## 1. Project Overview

UDP provides a connectionless method of data transmission but does not guarantee packet delivery, ordering or duplicate protection. This project implements reliability mechanisms on top of UDP to support accurate file transfer under different network conditions.

The project includes three ARQ protocols, a UDP channel emulator and an experimental framework for comparing their performance.

## 2. Project Objectives

- Implement Stop-and-Wait, Go-Back-N and Selective Repeat.
- Support packet sequencing and acknowledgement handling.
- Implement retransmission mechanisms to recover from packet loss.
- Simulate network conditions such as packet loss and delay.
- Transfer files and verify the received output.
- Compare protocol performance using transfer time and retransmission counts.

## 3. Technologies Used

- **Language:** Python
- **Networking:** UDP sockets
- **Libraries:** Python standard library, Matplotlib and Pytest
- **Data integrity:** SHA-256 hashing
- **Development environment:** Visual Studio Code

## 4. Project Structure

```text
coding-assignment1-p3/
│
├── packet.py
├── rto.py
├── channel_emulator.py
│
├── sw_sender.py
├── gbn_sender.py
├── arq_receiver.py
│
├── sr_sender.py
├── sr_receiver.py
│
├── run_experiments.py
├── make_graphs.py
├── experiment_results.csv
│
├── test_packet.py
├── test_sr.py
├── test_sr_receiver_manual.py
├── test_sr_sender_delay.py
├── test_sr_sender_loss.py
├── test_udp_corruption.py
├── test_udp_invalid.py
│
├── sample.txt
├── received_sw.txt
├── received_gbn.txt
├── received_sr.txt
│
└── graphs/
    ├── transfer_time_comparison.png
    └── retransmissions_comparison.png
```

## 5. Protocol Implementations

### Stop-and-Wait (SW)

The sender transmits one packet at a time and waits for its acknowledgement before sending the next packet. If an acknowledgement is not received within the timeout period, the packet is retransmitted.

### Go-Back-N (GBN)

The sender can transmit multiple packets within a predefined window. When a packet is lost, the sender retransmits the outstanding packets from the missing sequence number onward.

### Selective Repeat (SR)

The sender maintains a transmission window and retransmits only those packets for which acknowledgements have not been received. This avoids retransmitting packets that were successfully delivered.

## 6. UDP Channel Emulator

The channel emulator is used to introduce different network conditions during file transfer.

The supported conditions include:

- Packet loss
- Packet corruption
- Packet duplication
- Packet reordering
- Network delay
- Jitter

This allows the protocols to be evaluated beyond normal network conditions.

## 7. Installation and Execution

### Install dependencies

```bash
py -m pip install pytest matplotlib
```

### Run the test suite

```bash
py -m pytest -v
```

### Run the experiments

```bash
py run_experiments.py
```

### Generate comparison graphs

```bash
py make_graphs.py
```

### Run individual protocols

Use separate terminals for the receiver and sender processes.

**Stop-and-Wait**

```bash
py arq_receiver.py --protocol SW
py sw_sender.py sample.txt
```

**Go-Back-N**

```bash
py arq_receiver.py --protocol GBN
py gbn_sender.py sample.txt
```

**Selective Repeat**

```bash
py sr_receiver.py
py sr_sender.py sample.txt
```

## 8. Experimental Evaluation

The three protocols were evaluated under baseline conditions, 10% packet loss and 50 ms network delay.

The following results were obtained:

| Protocol | Condition | Transfer Time (s) | Retransmissions |
|---|---|---:|---:|
| SW | Baseline | 1.754 | 0 |
| GBN | Baseline | 1.181 | 0 |
| SR | Baseline | 1.172 | 0 |
| SW | 10% packet loss | 3.810 | 4 |
| GBN | 10% packet loss | 2.746 | 12 |
| SR | 10% packet loss | 1.603 | 2 |
| SW | 50 ms delay | 3.584 | 0 |
| GBN | 50 ms delay | 1.885 | 0 |
| SR | 50 ms delay | 1.972 | 0 |

All nine experiment runs completed successfully.

### Performance Graphs

**Transfer Time Comparison**

![Transfer Time Comparison](graphs/transfer_time_comparison.png)

**Retransmissions Comparison**

![Retransmissions Comparison](graphs/retransmissions_comparison.png)

The results show differences in transfer time and retransmission behaviour across the three protocols. Under the tested packet-loss condition, Selective Repeat recorded the lowest transfer time and retransmission count.

## 9. File Integrity Verification

The SHA-256 hashes of the original file and the files received through all three protocols were compared.

The following hash was obtained for each file:

```text
1489DB471C4B885498DE2EB6B161DD42CB2260CF31AEA7E716DC2E91AA5A4414
```

The matching hashes confirm that the received files were identical to the original file in these tests.

## 10. Testing

The project includes tests for packet encoding and decoding, RTO behaviour, packet handling and transfer scenarios involving different network conditions.

The test suite was executed using:

```bash
py -m pytest -v
```

The four tests in the verified test run passed successfully.

## 11. Conclusion

This project demonstrates how reliability can be implemented over UDP using different ARQ protocols. The experimental results provide a comparison of their behaviour under normal and impaired network conditions.

The implementation also demonstrates the use of acknowledgements, retransmissions, timeout handling, channel emulation and file integrity verification.

## 12. Team Contributions

| Team Member | Roll Number | Contribution |
|---|---|---|
| Khushi Raj | 24155024 | Implemented and tested Stop-and-Wait and Go-Back-N protocols. |
| Ankita Priyadarshini | 2405933 | Worked on UDP communication, packet structure, sequence numbers and checksums. |
| Adyasha Pattnaik | 24158035 | Implemented Selective Repeat, acknowledgement handling and retransmission/RTO logic. |
| Rishiraj Mazumder | 241551017 | Worked on the channel emulator, experiments, data collection and performance graphs. |

All team members contributed to integration, testing, documentation and viva preparation.

## 13. Repository

**GitHub:** https://github.com/khushiraj-beep/coding-assignment1-p3