import base64
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest

from common import input_bytes, DIGIT_SCALAR_SHA256, DIGIT_VECTOR_SHA256, MINDS, OP_COUNTS, WEIGHTS, fixtures
import gen_mind
import sbpf
from reference import forward
from weights import load_weights, random_weights


def build(kind, w1, w2):
    code, data = (gen_mind.build_vector if kind == "vector" else gen_mind.build_scalar)(w1, w2)
    return gen_mind.elf(code, data)


class Generator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w1, cls.w2 = load_weights(WEIGHTS)
        cls.vector = build("vector", cls.w1, cls.w2)
        cls.scalar = build("scalar", cls.w1, cls.w2)


    def test_elf_layout(self):
        for blob in (self.vector, self.scalar):
            machine, entry, segs = sbpf.load_elf(blob)
            self.assertEqual(machine, 247)
            self.assertEqual(entry, sbpf.TEXT)
            self.assertEqual([(t, fl, va) for t, fl, va, _ in segs], [(1, 4, sbpf.RO), (1, 1, sbpf.TEXT)])
            self.assertEqual(len(segs[1][3]) % 8, 0)

    def test_syscall_hashes(self):
        self.assertEqual(gen_mind.murmur3_32(b"sol_log_data"), gen_mind.LOGDATA)
        self.assertNotEqual(gen_mind.AVX, gen_mind.LOGDATA)
        self.assertEqual(gen_mind.murmur3_32(b""), 0)

    def test_vector_ops_decode(self):
        _, _, segs = sbpf.load_elf(self.vector)
        ro, text = segs[0][3], segs[1][3]
        ins = sbpf.decode(text)
        known = set(gen_mind.OPS.values())
        names = {v: k for k, v in gen_mind.OPS.items()}
        seen = []
        for i, (op, regs, _, imm) in enumerate(ins):
            if op == 0x85 and imm == gen_mind.AVX:
                lo, hi = ins[i - 2], ins[i - 1]
                self.assertEqual((lo[0], lo[1] & 15), (0x18, 1))
                d = lo[3] | (hi[3] << 32)
                self.assertLess(d + 16, len(ro))
                self.assertIn(ro[d], known)
                self.assertEqual(ro[d + 5], 0)
                self.assertEqual(ro[d + 8:d + 16], bytes(8))
                seen.append(names[ro[d]])
        with open(OP_COUNTS) as f:
            counts = json.load(f)
        self.assertEqual(len(seen), counts["vector"]["vector_ops"])
        self.assertEqual(len(ins), counts["vector"]["instruction_slots"])
        by_kind = {}
        for layer in counts["vector"]["by_layer"].values():
            for k, n in layer.items():
                if k != "total":
                    by_kind[k] = by_kind.get(k, 0) + n
        self.assertEqual({k: seen.count(k) for k in set(seen)}, by_kind)
        self.assertEqual(seen.count("dpbusd") * counts["vector"]["dpbusd_multiply_adds_each"], counts["multiply_adds"])


    def test_weights_in_rodata(self):
        _, _, segs = sbpf.load_elf(self.scalar)
        ro = segs[0][3]
        flat = bytes(w & 0xff for row in self.w1 for w in row) + bytes(w & 0xff for row in self.w2 for w in row)
        self.assertEqual(ro[:len(flat)], flat)
