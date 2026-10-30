
import time


class RTOEstimator:
    """Adaptive retransmission timeout using RTT measurements."""

    def __init__(self, initial_rto=0.5, min_rto=0.1, max_rto=5.0):
        self.rto = initial_rto
        self.min_rto = min_rto
        self.max_rto = max_rto

        self.srtt = None
        self.rttvar = None
        self.alpha = 1 / 8
        self.beta = 1 / 4
        self.granularity = 0.01

    def update(self, rtt):
        """Update RTO from a valid, non-retransmitted packet RTT."""
        if rtt <= 0:
            return

        if self.srtt is None:
            self.srtt = rtt
            self.rttvar = rtt / 2
        else:
            self.rttvar = (
                (1 - self.beta) * self.rttvar
                + self.beta * abs(self.srtt - rtt)
            )
            self.srtt = (
                (1 - self.alpha) * self.srtt
                + self.alpha * rtt
            )

        self.rto = self.srtt + max(
            self.granularity, 4 * self.rttvar
        )
        self.rto = max(self.min_rto, min(self.rto, self.max_rto))

    def on_timeout(self):
        """Back off the timeout when a packet times out."""
        self.rto = min(self.rto * 2, self.max_rto)

    def get_rto(self):
        return self.rto
