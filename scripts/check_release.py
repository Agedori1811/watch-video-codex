#!/usr/bin/env python3
"""Validate release-critical version and bundled-source invariants."""
import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", help="optional release tag to compare with the code version")
    args = parser.parse_args()

    cli = (ROOT / "watch-video").read_text(encoding="utf-8")
    match = re.search(r'^WATCH_VIDEO_VERSION = "([^"]+)"$', cli, re.MULTILINE)
    if not match:
        sys.exit("ERROR: WATCH_VIDEO_VERSION was not found")
    version = match.group(1)
    ok = True

    for rel in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
        manifest_version = json.loads((ROOT / rel).read_text(encoding="utf-8"))["version"]
        if manifest_version != version:
            ok = fail(f"{rel} version {manifest_version!r} != CLI version {version!r}") and ok

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if not re.search(rf"^## {re.escape(version)}(?:\s|$)", changelog, re.MULTILINE):
        ok = fail(f"CHANGELOG.md has no heading for {version}") and ok

    pairs = (
        ("watch-video", "skills/watch-video/watch-video"),
        ("watch-video.lock", "skills/watch-video/watch-video.lock"),
        ("scripts/setup.py", "skills/watch-video/scripts/setup.py"),
        ("scripts/watch-run.py", "skills/watch-video/scripts/watch-run.py"),
    )
    for left, right in pairs:
        left_path, right_path = ROOT / left, ROOT / right
        if not left_path.is_file() or not right_path.is_file():
            ok = fail(f"release payload missing: {left} or {right}") and ok
        elif left_path.read_bytes() != right_path.read_bytes():
            ok = fail(f"bundled copies differ: {left} and {right}") and ok

    if args.tag:
        tag_version = args.tag.rsplit("--v", 1)[-1] if "--v" in args.tag else args.tag.removeprefix("v")
        if tag_version != version:
            ok = fail(f"tag version {tag_version!r} != CLI version {version!r}") and ok

    if not ok:
        raise SystemExit(1)
    print(f"release metadata OK: {version}")


if __name__ == "__main__":
    main()
