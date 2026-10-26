#!/usr/bin/env python3
import base64
import os
import struct
import sys

from weights import load_weights


def forward(w1, w2, x):
    h = []
    for row in w1:
        acc = sum(w * xi for w, xi in zip(row, x))
        h.append(min(255, max(0, acc) >> 8))
    return h, [sum(w * hj for w, hj in zip(row, h)) for row in w2]


def forward_np(w1, w2, xs):
    import numpy as np
    w1 = np.asarray(w1, dtype=np.int64)
    w2 = np.asarray(w2, dtype=np.int64)
    xs = np.asarray(xs, dtype=np.int64)
    h = np.clip(np.maximum(xs @ w1.T, 0) >> 8, 0, 255)
    return h @ w2.T


def log_data(y):
    return base64.b64encode(struct.pack("<16i", *y)).decode()


def parse_input(s):
    if os.path.exists(s):
        return list(open(s, "rb").read())
    try:
        b = bytes.fromhex(s)
    except ValueError:
        b = base64.b64decode(s)
    return list(b)


if __name__ == "__main__":
    w1, w2 = load_weights(sys.argv[1])
    x = parse_input(sys.argv[2])
    assert len(x) == 256, "input must be 256 bytes"
    _, y = forward(w1, w2, x)
    print("y = %s" % y)
    print("answer(0..9) = %d" % max(range(10), key=lambda k: (y[k], -k)))
    print("Program data: %s" % log_data(y))
