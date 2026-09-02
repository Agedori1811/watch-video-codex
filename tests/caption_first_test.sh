#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; CLI="$HERE/watch-video"
command -v uv >/dev/null || { echo "SKIP caption-first: uv missing"; exit 0; }
command -v ffmpeg >/dev/null || { echo "SKIP caption-first: ffmpeg missing"; exit 0; }

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
CLIP="$TMP/clip.mp4"
ffmpeg -y -f lavfi -i testsrc=duration=3:size=320x240:rate=4 \
       -f lavfi -i sine=frequency=440:duration=3 -shortest "$CLIP" >/dev/null 2>&1
CAPTION="$TMP/clip.ja.vtt"
printf 'WEBVTT\n\n00:00:00.000 --> 00:00:01.500\n字幕を優先します。\n\n00:00:01.500 --> 00:00:03.000\nWhisper は使いません。\n' > "$CAPTION"
OUT="$TMP/out"
uv run --script "$CLI" "$CLIP" --out "$OUT" --caption-language ja \
  --captions-only --no-ocr >/dev/null 2>&1

grep -q '字幕を優先します' "$OUT/transcript.md" || { echo "FAIL: caption text missing"; exit 1; }
grep -q 'source `sidecar-caption`' "$OUT/SUMMARY.md" || { echo "FAIL: caption provenance missing"; exit 1; }
grep -q 'Transcription backend.*`caption`' "$OUT/SUMMARY.md" || { echo "FAIL: caption backend missing"; exit 1; }
test -f "$OUT/metadata.md" || { echo "FAIL: metadata.md missing"; exit 1; }
test -f "$OUT/captions/source.vtt" || { echo "FAIL: source caption copy missing"; exit 1; }

CLI_PATH="$CLI" python3 - <<'PY'
import os, runpy, tempfile
from pathlib import Path
ns = runpy.run_path(os.environ["CLI_PATH"])
choose = ns["choose_caption"]
info = {
    "language": "ja",
    "subtitles": {"ja": [{}], "en": [{}]},
    "automatic_captions": {"ja": [{}]},
}
assert choose(info, "auto") == ("manual-caption", "ja")
assert choose({"automatic_captions": {"ja-JP": [{}]}}, "ja") == ("auto-caption", "ja-JP")

with tempfile.TemporaryDirectory() as d:
    rolling = Path(d) / "rolling.vtt"
    rolling.write_text(
        "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n<c>字幕</c><00:00:01.500><c>を</c>\n\n"
        "00:00:01.500 --> 00:00:03.000\n<c>字幕を</c><00:00:02.000><c>優先</c>\n\n"
        "00:00:03.000 --> 00:00:04.000\n<c>優先</c><00:00:03.500><c>します</c>\n",
        encoding="utf-8",
    )
    assert ns["parse_caption"](rolling) == [(1.0, "字幕を優先"), (3.0, "します")]
PY
echo "PASS caption-first"
