import json
import unittest

from common import FIXTURES, TRAIN_LOG, WEIGHTS, fixtures
import weights


class WeightsFile(unittest.TestCase):
    def setUp(self):
        with open(WEIGHTS, "rb") as f:
            self.blob = f.read()

    def test_size_and_magic(self):
        self.assertEqual(len(self.blob), 34824)
        self.assertEqual(weights.SIZE, 34824)
        self.assertEqual(self.blob[:8], b"COGMIND1")

    def test_shape(self):
        w1, w2 = weights.validate(self.blob)
        self.assertEqual((len(w1), len(w1[0])), (128, 256))
        self.assertEqual((len(w2), len(w2[0])), (16, 128))
        self.assertTrue(all(-128 <= v <= 127 for row in w1 + w2 for v in row))

    def test_hash_matches_training_log_and_fixtures(self):
        h = weights.sha256_hex(self.blob)
        with open(TRAIN_LOG) as f:
            self.assertEqual(json.load(f)["weights_sha256"], h)
        self.assertEqual(fixtures()["weights_sha256"], h)

    def test_pack_round_trip(self):
        w1, w2 = weights.validate(self.blob)
        self.assertEqual(weights.pack(w1, w2), self.blob)

    def test_row_major_layout(self):
        w1, w2 = weights.validate(self.blob)
        self.assertEqual(w1[3][5], weights._i8(self.blob[8 + 3 * 256 + 5]))
        self.assertEqual(w2[7][9], weights._i8(self.blob[8 + 128 * 256 + 7 * 128 + 9]))


class WeightsRefusals(unittest.TestCase):
    def code(self, blob):
        with self.assertRaises(weights.WeightsError) as cm:
            weights.validate(blob)
        return cm.exception.code

    def test_bad_size(self):
        self.assertEqual(self.code(b"COGMIND1" + bytes(10)), "BAD_SIZE")

    def test_bad_magic(self):
        w1, w2 = weights.random_weights(256, 128, 1)
        blob = weights.pack(w1, w2)
        self.assertEqual(self.code(b"NOTMIND!" + blob[8:]), "BAD_FORMAT")

    def test_zero_w1(self):
        w1, w2 = weights.random_weights(256, 128, 2)
        blob = weights.pack([[0] * 256 for _ in range(128)], w2)
        self.assertEqual(self.code(blob), "ZERO_WEIGHTS")

    def test_zero_w2(self):
        w1, w2 = weights.random_weights(256, 128, 3)
        blob = weights.pack(w1, [[0] * 128 for _ in range(16)])
        self.assertEqual(self.code(blob), "ZERO_WEIGHTS")

    def test_pack_rejects_out_of_range(self):
        w1, w2 = weights.random_weights(256, 128, 4)
        w1[0][0] = 128
        with self.assertRaises(AssertionError):
            weights.pack(w1, w2)


class RandomWeights(unittest.TestCase):
    def test_deterministic_and_bounded(self):
        a = weights.random_weights(256, 64, 9)
        b = weights.random_weights(256, 64, 9)
        self.assertEqual(a, b)
        self.assertNotEqual(a, weights.random_weights(256, 64, 10))
        self.assertTrue(all(-15 <= v <= 15 for m in a for row in m for v in row))


if __name__ == "__main__":
    unittest.main()
