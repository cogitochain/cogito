#!/usr/bin/env python3
import struct
import sys

from weights import load_weights, random_weights


def murmur3_32(data, seed=0):
    c1, c2 = 0xcc9e2d51, 0x1b873593
    h = seed
    n = len(data) // 4
    for i in range(n):
        k = struct.unpack_from("<I", data, 4 * i)[0]
        k = (k * c1) & 0xffffffff
        k = ((k << 15) | (k >> 17)) & 0xffffffff
        k = (k * c2) & 0xffffffff
        h ^= k
        h = ((h << 13) | (h >> 19)) & 0xffffffff
        h = (h * 5 + 0xe6546b64) & 0xffffffff
    t = data[4 * n:]
    k = 0
    if len(t) >= 3:
        k ^= t[2] << 16
    if len(t) >= 2:
        k ^= t[1] << 8
    if len(t) >= 1:
        k ^= t[0]
        k = (k * c1) & 0xffffffff
        k = ((k << 15) | (k >> 17)) & 0xffffffff
        k = (k * c2) & 0xffffffff
        h ^= k
    h ^= len(data)
    h ^= h >> 16
    h = (h * 0x85ebca6b) & 0xffffffff
    h ^= h >> 13
    h = (h * 0xc2b2ae35) & 0xffffffff
    h ^= h >> 16
    return h


AVX = murmur3_32(b"sol_avx512")
LOGDATA = murmur3_32(b"sol_log_data")
