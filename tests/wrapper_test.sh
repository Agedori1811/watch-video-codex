#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; WRAP="$HERE/scripts/watch-run.py"
command -v ffmpeg >/dev/null || { echo "SKIP wrapper: ffmpeg missing"; exit 0; }

# The wrapper prints a resolved NATIVE path. Under Git Bash that is a Windows path
# (C:\Users\...) while $TMP here is POSIX (/tmp/...) — same dir, different spelling.
# Canonicalize both sides before comparing.
canon() {
  p="$1"
  if command -v cygpath >/dev/null 2>&1; then p="$(cygpath -m "$p" 2>/dev/null || printf '%s' "$p")"; fi
  printf %s "$p" | sed 's|\\|/|g'; echo
}
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
CLIP="$TMP/clip.mp4"
ffmpeg -y -f lavfi -i testsrc=duration=3:size=320x240:rate=4 \
       -f lavfi -i sine=frequency=440:duration=3 -shortest "$CLIP" >/dev/null 2>&1
OUT="$TMP/out"
# Wrapper must print exactly the output dir on stdout (one line), and not choke on --ephemeral.
DIR="$(python3 "$WRAP" "$CLIP" --out "$OUT" --no-transcribe --ephemeral 2>/dev/null)"
test "$(canon "$DIR")" = "$(canon "$OUT")" || { echo "FAIL: wrapper stdout '$DIR' != '$OUT'"; exit 1; }
test -f "$OUT/SUMMARY.md" || { echo "FAIL: run produced no SUMMARY"; exit 1; }
# Cleanup pass-through removes the manifested dir.
python3 "$WRAP" --clean "$OUT" >/dev/null 2>&1
test ! -d "$OUT" || { echo "FAIL: cleanup pass-through did not delete"; exit 1; }
# bare --out (no slash) must produce an ABSOLUTE path
cd "$TMP"
BARE_DIR="$(python3 "$WRAP" "$CLIP" --out bareout --no-transcribe 2>/dev/null)"
case "$(canon "$BARE_DIR")" in
    /*|[A-Za-z]:/*) ;;  # POSIX /… or Windows C:/… — absolute, good
    *)  echo "FAIL: wrapper bare-out '$BARE_DIR' is not absolute"; exit 1 ;;
esac
# cleanup via wrapper must remove the dir
python3 "$WRAP" --clean "$BARE_DIR" >/dev/null 2>&1
test ! -d "$TMP/bareout" || { echo "FAIL: bare-out dir not cleaned"; exit 1; }
echo "PASS wrapper"
