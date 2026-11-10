#!/usr/bin/env python3
import os
import re
import struct
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from reference import forward_np  # noqa: E402
from weights import load_weights, random_weights  # noqa: E402


def main():
    work, vso, sso, inputs = sys.argv[1:5]
    if sys.argv[5] == "--weights":
        w1, w2 = load_weights(sys.argv[6])
    else:
        w1, w2 = random_weights(int(sys.argv[6]), int(sys.argv[7]), int(sys.argv[8]))
    n_in = len(w1[0])
    raw = open(inputs, "rb").read()
    xs = [list(raw[i:i + n_in]) for i in range(0, len(raw), n_in)]
    ys = forward_np(w1, w2, xs).tolist()
    env = dict(os.environ, MIND_SO="%s %s" % (os.path.abspath(vso), os.path.abspath(sso)),
               MIND_INPUTS=os.path.abspath(inputs), MIND_MODE="run")
    out = subprocess.run(["cargo", "test", "--release", "--test", "mind_vm", "--", "--ignored", "--nocapture"],
                         cwd=work, env=env, capture_output=True, text=True).stdout
    runs = mism = 0
    cus = {}
    for m in re.finditer(r"mind-run (\S+) idx=(\d+) mode=(\w+) cu=(\d+) rc=(\d+) logged=([0-9a-f]*)", out):
        path, i, mode, cu, rc, logged = m.groups()
        i = int(i)
        got = list(struct.unpack("<16i", bytes.fromhex(logged))) if len(logged) == 128 else None
        runs += 1
        want = [((v + 2**31) % 2**32) - 2**31 for v in ys[i]]
        if rc != "0" or got != want:
            mism += 1
            print("MISMATCH %s idx=%d mode=%s rc=%s got=%s want=%s" % (os.path.basename(path), i, mode, rc, got, want))
        cus[os.path.abspath(path)] = int(cu)
    ok = runs == 4 * len(xs) and mism == 0
    print("mind-check inputs=%d runs=%d mismatches=%d vector_cu=%s scalar_cu=%s verdict=%s" % (
        len(xs), runs, mism, cus.get(os.path.abspath(vso)), cus.get(os.path.abspath(sso)), "PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
