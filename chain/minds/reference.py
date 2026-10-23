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
