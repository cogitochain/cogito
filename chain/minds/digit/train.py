#!/usr/bin/env python3
import gzip
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preprocess import to_input  # noqa: E402
from weights import pack, sha256_hex  # noqa: E402


def idx(path):
    with gzip.open(path, "rb") as f:
        raw = f.read()
    dims = raw[3]
    shape = [int.from_bytes(raw[4 + 4 * i:8 + 4 * i], "big") for i in range(dims)]
    return np.frombuffer(raw, dtype=np.uint8, offset=4 + 4 * dims).reshape(shape)


def _prep(args):
    img, box, shift = args
    return to_input(img.astype(np.float32) / 255.0, box=box, shift=shift)


def prep_all(images, variants, rng, pool):
    jobs = []
    for box, jitter in variants:
        for img in images:
            shift = (int(rng.integers(-1, 2)), int(rng.integers(-1, 2))) if jitter else (0, 0)
            jobs.append((img, box, shift))
    return np.stack(pool.map(_prep, jobs, chunksize=2000))


def forward(W1, W2, xq):
    q1 = np.round(np.clip(W1, -128 / 127, 1) * 127)
    q2 = np.round(np.clip(W2, -128 / 127, 1) * 127)
    acc = xq @ q1.T
    h = np.clip(np.floor(np.maximum(acc, 0) / 256), 0, 255)
    y = h @ q2.T
    return q1, q2, acc, h, y
