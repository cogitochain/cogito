#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
src="$1"
work="$2"
if [ ! -d "$work/src" ]; then
  mkdir -p "$work"
  cp -r "$src/." "$work/"
fi
cp "$here/mind_vm.rs" "$work/tests/mind_vm.rs"
cd "$work"
cargo test --release --test mind_vm --no-run
echo "mind-vm-build verdict=PASS"
