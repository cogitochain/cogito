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
