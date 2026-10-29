# Experiment Analysis: Stop-and-Wait, Go-Back-N, and Selective Repeat

## 1. Objective

To compare the performance of Stop-and-Wait (SW), Go-Back-N (GBN), and Selective Repeat (SR) protocols under different network conditions.

## 2. Experimental Conditions

- Baseline: no simulated packet loss or delay.
- 10% packet loss: simulated packet loss probability of 10%.
- 50 ms delay: simulated one-way delay of 50 ms for data packets.

## 3. Results

| Network Condition | Protocol | Transfer Time (s) | Retransmissions |
|---|---|---:|---:|
| Baseline | SW | 1.805 | 0 |
| Baseline | GBN | 1.222 | 0 |
| Baseline | SR | 1.219 | 0 |
| 10% packet loss | SW | 4.370 | 5 |
| 10% packet loss | GBN | 2.775 | 12 |
| 10% packet loss | SR | 3.065 | 4 |
| 50 ms delay | SW | 3.622 | 0 |
| 50 ms delay | GBN | 1.899 | 0 |
| 50 ms delay | SR | 1.862 | 0 |

## 4. Observations

1. **Baseline:** GBN and SR completed the transfer faster than SW because their sliding windows allow multiple packets to be sent without waiting for an individual acknowledgment after each packet.
2. **Packet loss:** SW had the longest transfer time. GBN recorded the most retransmissions because it retransmits outstanding packets when a timeout occurs. SR recorded the fewest retransmissions in this run.
3. **Network delay:** GBN and SR had similar transfer times, while SW took longer.
4. **Overall:** The measured results show that sliding-window protocols performed better than SW in these experiments, particularly when network delay was introduced.

## 5. Conclusion

The experiment demonstrates the differences between Stop-and-Wait, Go-Back-N, and Selective Repeat. SW is simpler but can take longer because it waits for acknowledgments. GBN uses cumulative acknowledgments and retransmits outstanding packets after a timeout, whereas SR retransmits individual missing packets. In the 10% packet-loss run, SR had the fewest retransmissions, while GBN achieved the shortest transfer time.

## 6. Limitations

The results represent individual runs and may vary between executions. The emulator applies the configured delay to data packets but forwards acknowledgments without the same simulated delay. Multiple repeated trials and verification of received-file integrity under each condition would improve confidence in the measurements.