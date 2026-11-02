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


class Asm:
    def __init__(self):
        self.ins, self.labels, self.fix = [], {}, []

    def raw(self, op, dst=0, src=0, off=0, imm=0):
        self.ins.append([op, dst, src, off, imm & 0xffffffff])

    def label(self, n):
        self.labels[n] = len(self.ins)

    def lddw(self, dst, v):
        self.raw(0x18, dst, 0, 0, v & 0xffffffff)
        self.raw(0x00, 0, 0, 0, (v >> 32) & 0xffffffff)

    def call(self, h): self.raw(0x85, 0, 0, 0, h)
    def mov(self, dst, imm): self.raw(0xb7, dst, 0, 0, imm)
    def movr(self, dst, src): self.raw(0xbf, dst, src)
    def add(self, dst, imm): self.raw(0x07, dst, 0, 0, imm)
    def addr(self, dst, src): self.raw(0x0f, dst, src)
    def mulr(self, dst, src): self.raw(0x2f, dst, src)
    def lsh(self, dst, imm): self.raw(0x67, dst, 0, 0, imm)
    def arsh(self, dst, imm): self.raw(0xc7, dst, 0, 0, imm)
    def rsh(self, dst, imm): self.raw(0x77, dst, 0, 0, imm)
    def ldxb(self, dst, src, off=0): self.raw(0x71, dst, src, off)
    def ldxdw(self, dst, src, off=0): self.raw(0x79, dst, src, off)
    def stxb(self, dst, off, src): self.raw(0x73, dst, src, off)
    def stxw(self, dst, off, src): self.raw(0x63, dst, src, off)
    def stxdw(self, dst, off, src): self.raw(0x7b, dst, src, off)

    def jmp(self, op, dst, imm, lbl):
        self.fix.append((len(self.ins), lbl))
        self.raw(op, dst, 0, 0, imm)

    def jlt(self, dst, imm, lbl): self.jmp(0xa5, dst, imm, lbl)
    def jsgt(self, dst, imm, lbl): self.jmp(0x65, dst, imm, lbl)
    def jne(self, dst, imm, lbl): self.jmp(0x55, dst, imm, lbl)
    def ret(self): self.raw(0x95)

    def code(self):
        for i, lbl in self.fix:
            self.ins[i][3] = self.labels[lbl] - (i + 1)
        return b"".join(struct.pack("<BBhI", op, (dst & 15) | (src << 4), off, imm)
                        for op, dst, src, off, imm in self.ins)
