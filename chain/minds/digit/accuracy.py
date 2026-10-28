#!/usr/bin/env python3
import os
import sys

import numpy as np

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, ".."))
sys.path.insert(0, here)
from preprocess import to_input  # noqa: E402
from reference import forward_np  # noqa: E402
from train import idx  # noqa: E402
from weights import load_weights  # noqa: E402

src, wpath = sys.argv[1], sys.argv[2]
images = idx(os.path.join(src, "t10k-images-idx3-ubyte.gz"))
labels = idx(os.path.join(src, "t10k-labels-idx1-ubyte.gz"))
xs = np.stack([to_input(im.astype(np.float32) / 255.0) for im in images])
w1, w2 = load_weights(wpath)
y = forward_np(w1, w2, xs)
answer = np.argmax(y[:, :10], axis=1)
correct = int((answer == labels).sum())
print("digits=%d correct=%d" % (len(labels), correct))
print("value=%.2f" % (100.0 * correct / len(labels)))
