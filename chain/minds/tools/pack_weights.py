#!/usr/bin/env python3
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from weights import pack, sha256_hex, validate  # noqa: E402

m = json.load(open(sys.argv[1]))
blob = pack(m["W1"], m["W2"])
validate(blob)
open(sys.argv[2], "wb").write(blob)
print("packed %s bytes=%d sha256=%s" % (sys.argv[2], len(blob), sha256_hex(blob)))
