#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; CLI="$HERE/watch-video"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
CLI_PATH="$CLI" OUT_PATH="$TMP" python3 - <<'PY'
import os, runpy, sys, types
from pathlib import Path

ns = runpy.run_path(os.environ["CLI_PATH"])
calls = []

class Segment:
    start = 1.25
    text = " backend test "

class Info:
    language = "ja"

class Model:
    def __init__(self, name, device, compute_type):
        calls.append((name, device, compute_type))
        if device == "cuda" and len(calls) > 1:
            raise RuntimeError("simulated missing CUDA runtime")
    def transcribe(self, *args, **kwargs):
        return iter([Segment()]), Info()

sys.modules["ctranslate2"] = types.SimpleNamespace(get_cuda_device_count=lambda: 1)
sys.modules["faster_whisper"] = types.SimpleNamespace(WhisperModel=Model)

out1 = Path(os.environ["OUT_PATH"]) / "gpu"
out1.mkdir()
result = ns["transcribe"]("dummy.mp4", out1, "auto", "ja")
assert result[2:] == ("cuda", "float16", "medium"), result
assert calls[-1] == ("medium", "cuda", "float16")

# A second CUDA construction fails; auto mode must retry as CPU/int8 with the small model.
out2 = Path(os.environ["OUT_PATH"]) / "fallback"
out2.mkdir()
result = ns["transcribe"]("dummy.mp4", out2, "auto", "ja")
assert result[2:] == ("cpu", "int8", "small"), result
assert calls[-1] == ("small", "cpu", "int8")
assert "backend test" in (out2 / "transcript.md").read_text()
PY
echo "PASS backend-unit"
