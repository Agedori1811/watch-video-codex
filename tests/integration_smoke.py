"""Cross-platform local-file and Caption-first smoke test for GitHub Actions."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "watch-video"


def require(binary):
    path = shutil.which(binary)
    if not path:
        raise SystemExit(f"ERROR: CI prerequisite missing: {binary}")
    return path


def call(args):
    result = subprocess.run(
        [require("uv"), "run", "--locked", "--script", str(CLI), *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)
    return result


def main():
    ffmpeg = require("ffmpeg")
    require("ffprobe")
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        clip = tmp / "日本語 clip.mp4"
        subprocess.run(
            [
                ffmpeg, "-y", "-f", "lavfi", "-i",
                "testsrc=duration=2:size=320x240:rate=4", "-f", "lavfi", "-i",
                "sine=frequency=440:duration=2", "-shortest", str(clip),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        caption = clip.with_suffix(".ja.vtt")
        caption.write_text(
            "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\n字幕優先の検証です。\n",
            encoding="utf-8",
        )
        out = tmp / "出力"
        result = call(
            [clip, "--out", out, "--caption-language", "ja", "--captions-only", "--no-ocr"]
        )
        if Path(result.stdout.strip()) != out / "SUMMARY.md":
            raise AssertionError(f"unexpected stdout entrypoint: {result.stdout!r}")
        required = ("SUMMARY.md", "metadata.json", "timeline.md", "transcript.md", ".watch-video.json")
        for name in required:
            if not (out / name).is_file():
                raise AssertionError(f"missing artifact: {name}")
        summary = (out / "SUMMARY.md").read_text(encoding="utf-8")
        if "source `sidecar-caption`" not in summary:
            raise AssertionError("Caption-first provenance missing")
        manifest = json.loads((out / ".watch-video.json").read_text(encoding="utf-8"))
        if manifest["tool"] != "watch-video":
            raise AssertionError("invalid manifest signature")
        print("PASS cross-platform integration smoke")


if __name__ == "__main__":
    main()
