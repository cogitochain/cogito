#!/usr/bin/env python3
import json
import os
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import gen_mind  # noqa: E402
from weights import load_weights  # noqa: E402

w1, w2 = load_weights(sys.argv[1])
code, data = gen_mind.build_vector(w1, w2)
names = {v: k for k, v in gen_mind.OPS.items()}
ins = [struct.unpack_from("<BBhI", code, i) for i in range(0, len(code), 8)]
ops = []
for i, (op, _, _, imm) in enumerate(ins):
    if op == 0x85 and imm == gen_mind.AVX:
        lo, hi = ins[i - 2][3], ins[i - 1][3]
        d = lo | (hi << 32)
        ops.append(names[data[d]])
n1 = 8 + 64 * (1 + 8 + 8)
nq = 1 + 8 * 4
n2 = 1 + 32 * 3 + 1
assert n1 + nq + n2 == len(ops), (n1, nq, n2, len(ops))
layers = {"layer1 (256 -> 128)": Counter(ops[:n1]), "requantize (relu, >>8, to bytes)": Counter(ops[n1:n1 + nq]),
          "layer2 (128 -> 16)": Counter(ops[n1 + nq:])}
scode, _ = gen_mind.build_scalar(w1, w2)
out = {
    "multiply_adds": 256 * 128 + 128 * 16,
    "vector": {"vector_ops": len(ops), "instruction_slots": len(code) // 8,
               "by_layer": {k: {"total": sum(c.values()), **dict(c)} for k, c in layers.items()},
               "dpbusd_multiply_adds_each": 64},
    "scalar": {"instruction_slots_static": len(scode) // 8,
               "inner_loop_instructions_per_multiply_add": 10},
    "note": "static counts from chain/minds/gen_mind.py; executed counts (CU) are in docs/whitepaper.md, Measured",
}
print(json.dumps(out, indent=1))
