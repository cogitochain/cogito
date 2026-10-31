#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
agave="$1"
applied=0
for p in "$here"/0*.patch; do
  git -C "$agave" apply --check "$p"
  git -C "$agave" apply "$p"
  echo "applied $(basename "$p")"
  applied=$((applied + 1))
done
echo "patches applied=$applied failed=0"
