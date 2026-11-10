#!/usr/bin/env bash
set -euo pipefail
work="$(cd "$1" && pwd)"
so="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
inp="$(cd "$(dirname "$3")" && pwd)/$(basename "$3")"
mode="$4"
line="$(cd "$work" && MIND_SO="$so" MIND_INPUTS="$inp" MIND_MODE=bench cargo test --release --test mind_vm -- --ignored --nocapture 2>/dev/null | grep "^mind-bench .* mode=$mode ")"
echo "$line" | sed 's#^mind-bench [^ ]*/#mind-bench #'
ns="$(echo "$line" | sed -n 's/.* p50_ns=\([0-9]*\).*/\1/p')"
python3 -c "print('value=%.3f' % ($ns / 1000.0))"
