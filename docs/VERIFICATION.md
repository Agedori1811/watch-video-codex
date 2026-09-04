# Verification scope

This document separates automated evidence from paths that require real hardware,
accounts, cookies, or changing third-party sites. A green CI run does **not** imply that
the latter paths were exercised.

## Automated on every pull request

The `CI` workflow runs with read-only repository permissions:

| Coverage | Ubuntu | Windows | macOS |
|---|---:|---:|---:|
| Python 3.10 portable unit suite | Yes | Yes | Yes |
| Locked `uv` dependency install | Yes | Yes | Yes |
| Real ffmpeg local-file processing | Yes | Yes | Yes |
| Japanese filename/content UTF-8 path | Yes | Yes | Yes |
| Local sidecar Caption-first path | Yes | Yes | Yes |
| CLI validation and safe failure output | Yes | Yes | Yes |
| Existing Bash regression suite | Yes | No | No |
| Tesseract OCR integration | Yes | No | No |
| Locked dependency vulnerability audit | Yes | No | No |

Python 3.10, 3.11, 3.12, 3.13, and 3.14 also run the standard-library unit suite on
Ubuntu. The release job independently checks version/tag consistency, synchronized
plugin payloads, portable tests, bundle creation, and a SHA-256 checksum.

## Deliberately not claimed by CI

- Real Windows NVIDIA CUDA inference and the installed CUDA/cuDNN runtime combination.
- A first-time Whisper model download and transcription on all three operating systems.
- Browser-cookie extraction, exported cookie files, private/login-gated media, or any
  account-specific source.
- Live YouTube, X, Instagram, TikTok, Vimeo, Loom, or Reddit extraction. These are
  affected by site changes, geography, authentication, and rate limits.
- The mutating installer path in `scripts/setup.py`. Package-manager command construction
  is unit tested; CI installs prerequisites explicitly and exercises `--check`.
- Native Windows/macOS Tesseract OCR. Ubuntu exercises OCR in the existing suite.

## Minimal checks on the target Windows/CUDA machine

Run these after installing the NVIDIA driver, CUDA 12 libraries, cuDNN 9, `uv`, and
ffmpeg. Use a short, non-sensitive local clip first:

```powershell
python scripts/setup.py --check
uv run --locked --script watch-video --diagnose
uv run --locked --script watch-video .\short-local.mp4 --no-captions --device cuda --model tiny --no-ocr
```

The diagnosis must report at least one CUDA device, and `SUMMARY.md` must report a
`cuda/float16` transcription backend. If CUDA is required, keep `--device cuda`; unlike
`--device auto`, it will fail instead of silently using CPU.

For authentication, make one separate test with a disposable/non-sensitive private
source and the intended browser:

```powershell
uv run --locked --script watch-video "<private URL>" --cookies-from-browser edge --captions-only --no-ocr
```

Confirm that the URL query or token is absent from console output, `SUMMARY.md`,
`metadata.json`, and `.watch-video.json`. Never commit the output directory or cookies.

## Reporting a failure

Re-run with `WATCH_VIDEO_DEBUG=1` only when debugging locally; the default deliberately
hides tracebacks. Include OS, Python/uv/ffmpeg versions, `--diagnose` output, the stage
that failed, and a redacted error. Do not attach cookies, signed URLs, private media, or
generated artifacts containing confidential material.
