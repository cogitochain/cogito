import json
import unittest

from common import FIXTURES, TRAIN_LOG, WEIGHTS, fixtures
import weights


class WeightsRefusals(unittest.TestCase):
    def code(self, blob):
        with self.assertRaises(weights.WeightsError) as cm:
            weights.validate(blob)
        return cm.exception.code

    def test_bad_size(self):
        self.assertEqual(self.code(b"COGMIND1" + bytes(10)), "BAD_SIZE")


class RandomWeights(unittest.TestCase):
    def test_deterministic_and_bounded(self):
        a = weights.random_weights(256, 64, 9)
        b = weights.random_weights(256, 64, 9)
        self.assertEqual(a, b)
        self.assertNotEqual(a, weights.random_weights(256, 64, 10))
        self.assertTrue(all(-15 <= v <= 15 for m in a for row in m for v in row))
