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
