#!/usr/bin/env python3
import struct
import sys

from weights import load_weights, random_weights

RO = 0x0
TEXT = 0x100000000
HEAP = 0x300000000
INPUT = 0x400000000
OUT = 16


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


def layout(n_in, hidden):
    ha = HEAP
    ya = ha + ((hidden + 64 + 63) // 64) * 64
    slice_a = ya + 64
    return ha, ya, slice_a


def errors(a):
    a.label("err_accounts")
    a.mov(0, 1)
    a.ret()
    a.label("err_len")
    a.mov(0, 2)
    a.ret()


def prologue(a, n_in, early=False):
    a.lddw(6, INPUT)
    a.ldxdw(2, 6, 0)
    a.jne(2, 0, "err_accounts")
    a.ldxdw(2, 6, 8)
    a.jne(2, n_in, "err_len")
    if early:
        a.fix.append((len(a.ins), "start"))
        a.raw(0x05)
        errors(a)
        a.label("start")


def epilogue(a, ya, slice_a, early=False):
    a.lddw(3, ya)
    a.lddw(4, slice_a)
    a.stxdw(4, 0, 3)
    a.mov(3, 4 * OUT)
    a.stxdw(4, 8, 3)
    a.movr(1, 4)
    a.mov(2, 1)
    a.call(LOGDATA)
    a.mov(0, 0)
    a.ret()
    if not early:
        errors(a)


OPS = {"ld": 0x00, "st": 0x01, "ldbc.d": 0x02, "zero": 0x08, "dpbusd": 0x50, "max.d": 0x20,
       "shri.d": 0x34, "narrowus.d.b": 0x60}


def build_vector(w1, w2):
    try:
        return _build_vector(w1, w2, False)
    except struct.error:
        return _build_vector(w1, w2, True)


def _build_vector(w1, w2, early):
    hidden, n_in = len(w1), len(w1[0])
    assert n_in % 4 == 0 and hidden % 16 == 0 and len(w2) == OUT
    groups = hidden // 16
    chunks = [list(range(c, min(c + 8, groups))) for c in range(0, groups, 8)]
    ha, ya, slice_a = layout(n_in, hidden)
    xa = INPUT + 16
    count = 0
    for _ in range(2):
        desc_list, desc_index = [], {}

        def desc(op, imm8=0, out=0, in0=0, in1=0, off=0):
            key = (op, imm8, out, in0, in1, off)
            if key not in desc_index:
                desc_index[key] = len(desc_list)
                desc_list.append(bytes([OPS[op], imm8, out, in0, in1, 0]) + struct.pack("<h", off) + bytes(8))
            return RO + 16 * desc_index[key]

        a = Asm()

        def v(op, imm8=0, out=0, in0=0, in1=0, off=0):
            a.lddw(1, desc(op, imm8, out, in0, in1, off))
            a.call(AVX)

        prologue(a, n_in, early)
        w1a = RO + 16 * count
        pos = w1a
        for chunk in chunks:
            nk = len(chunk)
            for k in range(nk):
                v("zero", out=k)
            for st in range(n_in // 4):
                a.lddw(2, xa + 4 * st)
                v("ldbc.d", out=8)
                a.lddw(2, pos)
                for k in range(nk):
                    v("ld", out=9 + k, off=k * 64)
                    v("dpbusd", out=k, in0=8, in1=9 + k)
                pos += nk * 64
            v("zero", out=20)
            a.lddw(2, ha + chunk[0] * 16)
            for k in range(nk):
                v("max.d", out=k, in0=k, in1=20)
                v("shri.d", imm8=8, out=k, in0=k)
                v("narrowus.d.b", out=21, in0=k)
                v("st", in0=21, off=k * 16)
        w2a = pos
        v("zero", out=0)
        for st in range(hidden // 4):
            a.lddw(2, ha + 4 * st)
            v("ldbc.d", out=8)
            a.lddw(2, w2a + st * 64)
            v("ld", out=9)
            v("dpbusd", out=0, in0=8, in1=9)
        a.lddw(2, ya)
        v("st", in0=0)
        epilogue(a, ya, slice_a, early)
        count = len(desc_list)
    data = bytearray(b"".join(desc_list))
    for chunk in chunks:
        for st in range(n_in // 4):
            for k in chunk:
                for n in range(16):
                    data += bytes((w & 0xff) for w in w1[16 * k + n][4 * st:4 * st + 4])
    for st in range(hidden // 4):
        for n in range(OUT):
            data += bytes((w & 0xff) for w in w2[n][4 * st:4 * st + 4])
    return a.code(), bytes(data)


def build_scalar(w1, w2):
    hidden, n_in = len(w1), len(w1[0])
    ha, ya, slice_a = layout(n_in, hidden)
    xa = INPUT + 16
    w1a = RO
    w2a = w1a + hidden * n_in
    a = Asm()
    prologue(a, n_in)
    a.lddw(6, w1a)
    a.lddw(7, ha)
    a.mov(8, 0)
    a.label("l1_out")
    a.mov(0, 0)
    a.lddw(9, xa)
    a.mov(4, 0)
    a.label("l1_in")
    a.ldxb(2, 9)
    a.ldxb(3, 6)
    a.lsh(3, 56)
    a.arsh(3, 56)
    a.mulr(2, 3)
    a.addr(0, 2)
    a.add(9, 1)
    a.add(6, 1)
    a.add(4, 1)
    a.jlt(4, n_in, "l1_in")
    a.jsgt(0, 0, "l1_pos")
    a.mov(0, 0)
    a.label("l1_pos")
    a.rsh(0, 8)
    a.jlt(0, 256, "l1_ok")
    a.mov(0, 255)
    a.label("l1_ok")
    a.stxb(7, 0, 0)
    a.add(7, 1)
    a.add(8, 1)
    a.jlt(8, hidden, "l1_out")
    a.lddw(6, w2a)
    a.mov(8, 0)
    a.lddw(1, ya)
    a.label("l2_out")
    a.mov(0, 0)
    a.lddw(9, ha)
    a.mov(4, 0)
    a.label("l2_in")
    a.ldxb(2, 9)
    a.ldxb(3, 6)
    a.lsh(3, 56)
    a.arsh(3, 56)
    a.mulr(2, 3)
    a.addr(0, 2)
    a.add(9, 1)
    a.add(6, 1)
    a.add(4, 1)
    a.jlt(4, hidden, "l2_in")
    a.stxw(1, 0, 0)
    a.add(1, 4)
    a.add(8, 1)
    a.jlt(8, OUT, "l2_out")
    epilogue(a, ya, slice_a)
    data = b"".join(bytes((w & 0xff) for w in row) for row in w1) + b"".join(bytes((w & 0xff) for w in row) for row in w2)
    return a.code(), data


def elf(code, data):
    pad = lambda b: b + bytes((-len(b)) % 8)
    ro, tx = pad(data), pad(code)
    ehsize, phsize = 64, 56
    off_ro = ehsize + 2 * phsize
    off_tx = off_ro + len(ro)
    PT_LOAD, PF_X, PF_R = 1, 1, 4
    eh = b"\x7fELF" + bytes([2, 1, 1, 0, 0]) + bytes(7)
    eh += struct.pack("<HHIQQQIHHHHHH", 3, 247, 1, TEXT, ehsize, 0, 3, ehsize, phsize, 2, 64, 0, 0)
    ph = struct.pack("<IIQQQQQQ", PT_LOAD, PF_R, off_ro, RO, RO, len(ro), len(ro), 8)
    ph += struct.pack("<IIQQQQQQ", PT_LOAD, PF_X, off_tx, TEXT, TEXT, len(tx), len(tx), 8)
    return eh + ph + ro + tx
