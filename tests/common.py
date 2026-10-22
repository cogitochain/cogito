import base64
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MINDS = os.path.join(ROOT, "chain", "minds")
sys.path.insert(0, MINDS)

WEIGHTS = os.path.join(MINDS, "digit", "weights.bin")
FIXTURES = os.path.join(MINDS, "fixtures", "inputs.json")
FIXTURE_BIN = os.path.join(MINDS, "fixtures", "inputs.bin")
TRAIN_LOG = os.path.join(MINDS, "digit", "train-log.json")
OP_COUNTS = os.path.join(MINDS, "digit", "op-counts.json")

DIGIT_VECTOR_SHA256 = "3d9120c51924f2a4b7bca64ebdcbf4044058ede9e30cb49f7d11f4e599d793f2"
DIGIT_SCALAR_SHA256 = "17665f6dbbd8c3d1d4ea6b4a52e7ab5e7e7a3567f300065aac26692cde735991"


def fixtures():
    with open(FIXTURES) as f:
        return json.load(f)


def input_bytes(row):
    v = row["input"]
    return bytes(v) if isinstance(v, list) else base64.b64decode(v)
