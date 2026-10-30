
from rto import RTOEstimator
from packet import encode_packet, decode_packet


def test_rto_initial_value():
    estimator = RTOEstimator()
    assert estimator.get_rto() == 0.5


def test_rto_increases_after_timeout():
    estimator = RTOEstimator()
    initial = estimator.get_rto()
    estimator.on_timeout()
    assert estimator.get_rto() > initial


def test_rto_stays_within_maximum():
    estimator = RTOEstimator()
    for _ in range(20):
        estimator.on_timeout()
    assert estimator.get_rto() <= estimator.max_rto


def test_packet_round_trip():
    original = {
        "type": "DATA",
        "transfer_id": "test-transfer",
        "seq_num": 1,
        "ack_num": None,
        "payload": b"hello"
    }
    encoded = encode_packet(original)
    decoded = decode_packet(encoded)
    assert decoded["payload"] == b"hello"
    assert decoded["seq_num"] == 1
    assert decoded["type"] == "DATA"
