#!/usr/bin/env python3
import json
import os
import sys

import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, ".."))
sys.path.insert(0, os.path.join(here, "..", "digit"))
from preprocess import to_input  # noqa: E402
from reference import forward_np  # noqa: E402
from train import idx  # noqa: E402
from weights import load_weights, sha256_hex  # noqa: E402

src, wpath, out = sys.argv[1:4]
images = idx(os.path.join(src, "t10k-images-idx3-ubyte.gz"))
labels = idx(os.path.join(src, "t10k-labels-idx1-ubyte.gz"))
items = []
for d in range(10):
    i = int(np.nonzero(labels == d)[0][0])
    items.append(("mnist-t10k-%d" % i, d, to_input(images[i].astype(np.float32) / 255.0)))
items.append(("empty", None, np.zeros(256, dtype=np.uint8)))
items.append(("full", None, np.full(256, 255, dtype=np.uint8)))
w1, w2 = load_weights(wpath)
ys = forward_np(w1, w2, np.stack([x for _, _, x in items]))
rows = []
for (name, label, x), y in zip(items, ys.tolist()):
    rows.append({"name": name, "label": label, "input": [int(v) for v in x.tolist()],
                 "y": y, "answer": max(range(10), key=lambda k: (y[k], -k))})
with open(os.path.join(out, "inputs.json"), "w") as f:
    json.dump({"mind": "digit", "weights_sha256": sha256_hex(open(wpath, "rb").read()), "inputs": rows}, f, indent=1)
with open(os.path.join(out, "inputs.bin"), "wb") as f:
    f.write(b"".join(bytes(x.tolist()) for _, _, x in items))
print("fixtures n=%d answers=%s" % (len(rows), [r["answer"] for r in rows]))
