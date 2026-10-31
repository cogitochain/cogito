import base64
import struct
import unittest

from common import input_bytes, FIXTURE_BIN, WEIGHTS, fixtures
import reference
from weights import load_weights, random_weights


def answer(y):
    return max(range(10), key=lambda k: (y[k], -k))


class ReferenceAgainstFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w1, cls.w2 = load_weights(WEIGHTS)
        cls.rows = fixtures()["inputs"]

    def test_twelve_fixtures(self):
        self.assertEqual(len(self.rows), 12)
        self.assertEqual([r["name"] for r in self.rows[10:]], ["empty", "full"])

    def test_outputs_equal_recorded(self):
        for r in self.rows:
            x = list(input_bytes(r))
            self.assertEqual(len(x), 256)
            _, y = reference.forward(self.w1, self.w2, x)
            self.assertEqual(y, r["y"], r["name"])

    def test_answers_and_labels(self):
        for r in self.rows:
            self.assertEqual(answer(r["y"]), r["answer"], r["name"])
            if r["label"] is not None:
                self.assertEqual(r["answer"], r["label"], r["name"])

    def test_program_data_line(self):
        for r in self.rows:
            line = "Program data: " + reference.log_data(r["y"])
            if "log" in r:
                self.assertEqual(line, r["log"], r["name"])
            raw = base64.b64decode(line.split(": ", 1)[1])
            self.assertEqual(len(raw), 64)
            self.assertEqual(list(struct.unpack("<16i", raw)), r["y"])


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

    def test_parse_input_forms(self):
        b = bytes(range(256))
        self.assertEqual(reference.parse_input(b.hex()), list(b))
        self.assertEqual(reference.parse_input(base64.b64encode(b).decode()), list(b))
