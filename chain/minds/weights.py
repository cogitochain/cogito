import hashlib
import sys

MAGIC = b"COGMIND1"
IN, HIDDEN, OUT = 256, 128, 16
SIZE = len(MAGIC) + HIDDEN * IN + OUT * HIDDEN


class WeightsError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _i8(b):
    return b - 256 if b > 127 else b


def validate(blob):
    if len(blob) != SIZE:
        raise WeightsError("BAD_SIZE", "Weights file must be exactly 34,824 bytes (got %d)." % len(blob))
    if blob[:8] != MAGIC:
        raise WeightsError("BAD_FORMAT", "Not a COGITO weights file (missing COGMIND1 header).")
    w1b = blob[8:8 + HIDDEN * IN]
    w2b = blob[8 + HIDDEN * IN:]
    if not any(w1b):
        raise WeightsError("ZERO_WEIGHTS", "W1 is all zeros: this mind would always answer 0.")
    if not any(w2b):
        raise WeightsError("ZERO_WEIGHTS", "W2 is all zeros: this mind would always answer 0.")
    w1 = [[_i8(w1b[j * IN + i]) for i in range(IN)] for j in range(HIDDEN)]
    w2 = [[_i8(w2b[k * HIDDEN + j]) for j in range(HIDDEN)] for k in range(OUT)]
    return w1, w2


def load_weights(path):
    with open(path, "rb") as f:
        return validate(f.read())


def pack(w1, w2):
    assert len(w1) == HIDDEN and all(len(r) == IN for r in w1)
    assert len(w2) == OUT and all(len(r) == HIDDEN for r in w2)
    flat = [int(w) for r in w1 for w in r] + [int(w) for r in w2 for w in r]
    assert all(-128 <= w <= 127 for w in flat)
    return MAGIC + bytes(w & 0xff for w in flat)


def sha256_hex(blob):
    return hashlib.sha256(blob).hexdigest()


def random_weights(n_in, hidden, seed):
    s = seed
    def nxt():
        nonlocal s
        s = (s * 6364136223846793005 + 1442695040888963407) & (2**64 - 1)
        return (s >> 33) & 0xff
    w1 = [[(nxt() % 31) - 15 for _ in range(n_in)] for _ in range(hidden)]
    w2 = [[(nxt() % 31) - 15 for _ in range(hidden)] for _ in range(OUT)]
    return w1, w2


if __name__ == "__main__":
    try:
        w1, w2 = load_weights(sys.argv[1])
    except WeightsError as e:
        print("weights verdict=REFUSED code=%s reason=%s" % (e.code, e))
        sys.exit(1)
    print("weights verdict=OK sha256=%s" % sha256_hex(open(sys.argv[1], "rb").read()))
