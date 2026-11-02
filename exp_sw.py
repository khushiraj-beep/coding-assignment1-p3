import os, threading, time
import pandas as pd
from common import *
from stop_and_wait import Sender, Receiver

def one_run(loss, seed, size=60_000):
    src, dst = "/tmp/exp_sw_src.bin", "/tmp/exp_sw_dst.bin"
    with open(src, "wb") as f:
        f.write(os.urandom(size))
    a, b = ("127.0.0.1", 9001), ("127.0.0.1", 9002)
    s_ch = LossyChannel(a, b, loss, seed)
    r_ch = LossyChannel(b, a, loss, seed + 100)
    rx = Receiver(r_ch, linger=1.0)
    t = threading.Thread(target=rx.receive_file, args=(dst,))
    t.start()
    stats = Sender(s_ch).send_file(src)
    t.join()
    s_ch.close(); r_ch.close()
    assert sha256_file(src) == sha256_file(dst), "FILE MISMATCH"
    return stats

rows = []
for loss in (0.05, 0.10, 0.20):
    for seed in (1, 2, 3):
        s = one_run(loss, seed)
        rows.append({"protocol": "SW", "loss": loss, "window": 1,
                     "seed": seed, "sent": s["sent"], "retx": s["retx"],
                     "elapsed_s": round(s["elapsed"], 3),
                     "goodput_KBps": round(s["goodput"] / 1024, 2)})
    print(f"done loss={loss:.0%}")

df = pd.DataFrame(rows)
df.to_csv("sw_results.csv", index=False)
summary = df.groupby(["loss"])[["retx", "elapsed_s", "goodput_KBps"]].mean().round(2)
print(summary)
