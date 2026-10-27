#!/usr/bin/env python3
import gzip
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from preprocess import to_input  # noqa: E402
from weights import pack, sha256_hex  # noqa: E402

SEED = 714
EPOCHS = 16
BATCH = 256
LR = 3e-3


def idx(path):
    with gzip.open(path, "rb") as f:
        raw = f.read()
    dims = raw[3]
    shape = [int.from_bytes(raw[4 + 4 * i:8 + 4 * i], "big") for i in range(dims)]
    return np.frombuffer(raw, dtype=np.uint8, offset=4 + 4 * dims).reshape(shape)


def _prep(args):
    img, box, shift = args
    return to_input(img.astype(np.float32) / 255.0, box=box, shift=shift)


def prep_all(images, variants, rng, pool):
    jobs = []
    for box, jitter in variants:
        for img in images:
            shift = (int(rng.integers(-1, 2)), int(rng.integers(-1, 2))) if jitter else (0, 0)
            jobs.append((img, box, shift))
    return np.stack(pool.map(_prep, jobs, chunksize=2000))


def forward(W1, W2, xq):
    q1 = np.round(np.clip(W1, -128 / 127, 1) * 127)
    q2 = np.round(np.clip(W2, -128 / 127, 1) * 127)
    acc = xq @ q1.T
    h = np.clip(np.floor(np.maximum(acc, 0) / 256), 0, 255)
    y = h @ q2.T
    return q1, q2, acc, h, y


def accuracy(W1, W2, x, labels):
    _, _, _, _, y = forward(W1, W2, x.astype(np.float32))
    return float((np.argmax(y[:, :10], axis=1) == labels).mean())


def main(src, out):
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    tr_x, tr_y = idx(os.path.join(src, "train-images-idx3-ubyte.gz")), idx(os.path.join(src, "train-labels-idx1-ubyte.gz"))
    te_x, te_y = idx(os.path.join(src, "t10k-images-idx3-ubyte.gz")), idx(os.path.join(src, "t10k-labels-idx1-ubyte.gz"))
    with Pool(8) as pool:
        X = prep_all(tr_x, [(12, False), (10, True), (11, True), (13, True)], rng, pool)
        XT = prep_all(te_x, [(12, False)], rng, pool)
    Y = np.tile(tr_y, 4).astype(np.int64)
    Xf = X.astype(np.float32)
    print("prep train=%d test=%d %.0fs" % (len(X), len(XT), time.time() - t0), flush=True)

    W1 = (rng.standard_normal((128, 256)) * 0.02).astype(np.float32)
    W2 = (rng.standard_normal((16, 128)) * 0.05).astype(np.float32)
    params = [W1, W2]
    m = [np.zeros_like(p) for p in params]
    v = [np.zeros_like(p) for p in params]
    step = 0
    steps_total = EPOCHS * (len(X) // BATCH)
    log = []
    for ep in range(EPOCHS):
        perm = rng.permutation(len(X))
        tot = 0.0
        for b in range(len(X) // BATCH):
            ix = perm[b * BATCH:(b + 1) * BATCH]
            xq, lab = Xf[ix], Y[ix]
            q1, q2, acc, h, y = forward(W1, W2, xq)
            z = y / 256.0
            z = z - z.max(1, keepdims=True)
            p = np.exp(z)
            p /= p.sum(1, keepdims=True)
            tot += float(-np.log(p[np.arange(BATCH), lab] + 1e-12).mean())
            dy = p.copy()
            dy[np.arange(BATCH), lab] -= 1
            dy /= BATCH * 256.0
            gW2 = (dy.T @ h) * 127
            dh = dy @ q2
            mask = (acc > 0) & (acc < 256 * 256)
            dacc = dh * mask / 256.0
            gW1 = (dacc.T @ xq) * 127
            step += 1
            lr = LR * 0.5 * (1 + np.cos(np.pi * step / steps_total))
            for i, g in enumerate((gW1, gW2)):
                m[i] = 0.9 * m[i] + 0.1 * g
                v[i] = 0.999 * v[i] + 0.001 * g * g
                mh = m[i] / (1 - 0.9 ** step)
                vh = v[i] / (1 - 0.999 ** step)
                params[i] -= (lr * mh / (np.sqrt(vh) + 1e-8)).astype(np.float32)
                np.clip(params[i], -128 / 127, 1, out=params[i])
        loss = tot / (len(X) // BATCH)
        tr_acc = accuracy(W1, W2, X[:60000], tr_y)
        log.append({"epoch": ep + 1, "loss": round(loss, 4), "train_acc": round(tr_acc, 4)})
        print("epoch %d loss %.4f train_acc %.4f %.0fs" % (ep + 1, loss, tr_acc, time.time() - t0), flush=True)

    q1, q2, _, _, _ = forward(W1, W2, X[:1].astype(np.float32))
    blob = pack(q1.astype(int).tolist(), q2.astype(int).tolist())
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "weights.bin"), "wb") as f:
        f.write(blob)
    np.save(os.path.join(out, "test-inputs.npy"), XT)
    test_acc = accuracy(W1, W2, XT, te_y)
    meta = {"seed": SEED, "epochs": EPOCHS, "batch": BATCH, "lr": LR, "augment": "box 12; box 10/11/13 with +-1 px shift",
            "train_set": "MNIST train (60,000)", "held_out": "MNIST t10k (10,000), never used in training",
            "weights_sha256": sha256_hex(blob), "seconds": round(time.time() - t0), "log": log,
            "test_acc_at_train_time": test_acc}
    with open(os.path.join(out, "train-log.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("train done sha256=%s held_out_acc=%.4f" % (meta["weights_sha256"], test_acc))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
