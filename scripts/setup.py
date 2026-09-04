#!/usr/bin/env python3
"""Per-OS bootstrap for watch-video. Ensures uv + ffmpeg (required) and tesseract
(optional, warn-only). `--check` only verifies, never installs. See spec §8."""
import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

UV_INSTALL = "https://docs.astral.sh/uv/getting-started/installation/"


def have(b):
    return shutil.which(b) is not None


def install_uv():
    """Attempt the official uv installer (spec §8). Returns True if uv ends up present."""
    sysname = platform.system()
    if sysname == "Windows":
        cmd = ["powershell", "-ExecutionPolicy", "ByPass", "-c",
               "irm https://astral.sh/uv/install.ps1 | iex"]
    else:
        cmd = ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"]
    print(f"[setup] installing uv: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=False)
    except Exception as e:
        print(f"[setup] uv install attempt errored: {e}", file=sys.stderr)
    # uv installs to ~/.local/bin or ~/.cargo/bin — make it available in this process.
    if have("uv"):
        return True
    candidates = (
        Path.home() / ".local/bin/uv",
        Path.home() / ".local/bin/uv.exe",
        Path.home() / ".cargo/bin/uv",
        Path.home() / ".cargo/bin/uv.exe",
    )
    for p in candidates:
        if p.exists():
            os.environ["PATH"] = str(p.parent) + os.pathsep + os.environ.get("PATH", "")
            print(f"[setup] uv installed at {p}")
            return have("uv")
    return False


def refresh_windows_path():
    """Reload user/machine PATH after winget changes it."""
    if platform.system() != "Windows" or not have("powershell"):
        return
    script = (
        "[Environment]::GetEnvironmentVariable('Path','Machine') + ';' + "
        "[Environment]::GetEnvironmentVariable('Path','User')"
    )
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode == 0 and proc.stdout.strip():
        os.environ["PATH"] = proc.stdout.strip() + os.pathsep + os.environ.get("PATH", "")


def pkg_install(pkg):
    sysname = platform.system()
    package = pkg
    if sysname == "Linux" and pkg == "tesseract":
        package = "tesseract-ocr"
    if sysname == "Windows":
        package = {
            "ffmpeg": "Gyan.FFmpeg",
            "tesseract": "UB-Mannheim.TesseractOCR",
        }.get(pkg, pkg)
    if sysname == "Darwin" and have("brew"):
        return ["brew", "install", package]
    if sysname == "Linux":
        elevate = [] if hasattr(os, "geteuid") and os.geteuid() == 0 else ["sudo"]
        if have("dnf"):
            return [*elevate, "dnf", "install", "-y", package]
        if have("apt-get"):
            return [*elevate, "apt-get", "install", "-y", package]
    if sysname == "Windows" and have("winget"):
        return [
            "winget", "install", "--id", package, "--exact", "--silent",
            "--accept-package-agreements", "--accept-source-agreements",
        ]
    return None


def ensure(pkg, required, check_only):
    if have(pkg):
        print(f"[setup] {pkg}: present")
        return True
    if check_only:
        msg = f"[setup] {pkg}: MISSING"
        print(msg, file=sys.stderr)
        return not required
    cmd = pkg_install(pkg)
    if cmd is None:
        print(f"[setup] {pkg}: no supported package manager — install it manually.",
              file=sys.stderr)
        return not required
    print(f"[setup] installing {pkg}: {' '.join(cmd)}")
    installed = subprocess.run(cmd).returncode == 0
    if installed:
        refresh_windows_path()
    ok = installed and have(pkg)
    if not ok and required:
        print(f"[setup] FAILED to install required {pkg}.", file=sys.stderr)
    return ok or (not required)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify only, do not install")
    args = ap.parse_args()

    if sys.version_info < (3, 10):
        print("[setup] Python 3.10 or newer is required.", file=sys.stderr)
        sys.exit(1)

    ok = True
    if have("uv"):
        print("[setup] uv: present")
    elif args.check:
        print(f"[setup] uv: MISSING — install: {UV_INSTALL}", file=sys.stderr)
        ok = False
    else:
        # Attempt the official installer (spec §8). If it lands off-PATH, tell the user.
        if not install_uv():
            print(f"[setup] uv could not be made available on PATH. See: {UV_INSTALL}",
                  file=sys.stderr)
            ok = False

    ok = ensure("ffmpeg", required=True, check_only=args.check) and ok
    if have("ffprobe"):
        print("[setup] ffprobe: present")
    else:
        print(
            "[setup] ffprobe: MISSING — it must be installed with the ffmpeg package.",
            file=sys.stderr,
        )
        ok = False
    ensure("tesseract", required=False, check_only=args.check)  # optional: warn-only

    if not ok:
        print("[setup] one or more REQUIRED prerequisites are missing.", file=sys.stderr)
        sys.exit(1)
    print("[setup] required prerequisites satisfied (uv + ffmpeg). tesseract optional.")


if __name__ == "__main__":
    main()
