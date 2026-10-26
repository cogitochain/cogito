import base64
import struct
import unittest

from common import input_bytes, FIXTURE_BIN, WEIGHTS, fixtures
import reference
from weights import load_weights, random_weights


class ReferenceArithmetic(unittest.TestCase):
    def test_hidden_clamp_and_shift(self):
        w1 = [[1] * 256, [-1] * 256, [0] * 255 + [127]] + [[0] * 256 for _ in range(125)]
        w2 = [[1] + [0] * 127] + [[0] * 128 for _ in range(15)]
        x = [255] * 256
        h, y = reference.forward(w1, w2, x)
        self.assertEqual(h[0], 255)
        self.assertEqual(h[1], 0)
        self.assertEqual(h[2], (127 * 255) >> 8)
        self.assertEqual(y[0], 255)

    def test_random_shapes_agree(self):
        import random
        rng = random.Random(7)
        for hidden in (16, 48, 128):
            w1, w2 = random_weights(256, hidden, hidden)
            xs = [[rng.randrange(256) for _ in range(256)] for _ in range(4)]
            ys = reference.forward_np(w1, w2, xs).tolist()
            for x, y in zip(xs, ys):
                self.assertEqual(reference.forward(w1, w2, x)[1], y)
