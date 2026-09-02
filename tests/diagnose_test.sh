#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; CLI="$HERE/watch-video"
command -v uv >/dev/null || { echo "SKIP diagnose: uv missing"; exit 0; }
OUT="$(uv run --script "$CLI" --diagnose)"
printf '%s\n' "$OUT" | grep -q '^cuda_devices: ' || { echo "FAIL: CUDA status missing"; exit 1; }
printf '%s\n' "$OUT" | grep -q '^recommended_backend: ' || { echo "FAIL: backend recommendation missing"; exit 1; }
echo "PASS diagnose"
