# Changelog

## 1.2.1 — 2026-09-04
- Added native Ubuntu, Windows, and macOS GitHub Actions CI, Python 3.10–3.14
  compatibility checks, and a cross-platform locked-dependency integration smoke test.
- Added `watch-video.lock` with hashes and included it in both Codex skill and release
  bundles for reproducible `uv run --locked --script` installs.
- Pinned Python 3.10 to the newest `onnxruntime` release with Linux, Windows, and
  macOS wheels while preserving current dependency selection on newer Python versions.
- Added portable tests for CLI validation, Caption-first behavior, UTF-8 paths/content,
  CUDA fallback, wrapper behavior, setup package mapping, and credential redaction.
- Hardened operational failures: concise non-traceback messages by default, safer
  external-command logging, numeric/path validation, and optional OCR failure fallback.
- Fixed Windows `winget` package identifiers/agreements, Linux's tesseract package name,
  required `ffprobe` checks, and cross-platform UTF-8 file I/O.
- Documented CI scope, intentionally unverified hardware/auth paths, minimal manual
  checks, and a version-checked release procedure with SHA-256 bundle checksums.

## 1.2.0 — 2026-09-02
- **Caption-first transcription:** authored subtitles, then automatic subtitles, then
  local Whisper. Local `.vtt`/`.srt` sidecars and explicit `--captions` are supported.
- **Automatic CUDA selection:** NVIDIA uses `cuda/float16`; CPU uses `cpu/int8`.
  `--diagnose` shows CUDA visibility, and auto mode falls back safely if CUDA fails.
- **Hardware-aware model default:** `medium` on CUDA and `small` on CPU.
- **SNS context:** sanitized metadata records post text/description, creator/uploader,
  upload date, engagement counts, canonical URL, language, and chapters when exposed by
  the site's yt-dlp extractor.
- **Extractor resilience:** installs yt-dlp's default challenge components plus
  `curl-cffi` impersonation support, and automatically enables installed Node/Bun/QuickJS
  when Deno is absent.
- **Provenance:** SUMMARY and transcript identify manual caption, automatic caption,
  sidecar caption, or local Whisper so an agent can distinguish evidence quality.

## 1.1.3 — 2026-08-31
- **Fix: the version constant lagged the manifests.** `WATCH_VIDEO_VERSION` still said
  `1.1.1` while the plugin shipped as 1.1.2, so every output folder's `.watch-video.json`
  recorded the wrong version.
- **Python ceiling lifted** from `>=3.10,<3.13` to `>=3.10`. `ctranslate2` 4.8.1 publishes
  3.13/3.14 wheels and `faster-whisper` 1.2.1 declares no upper bound; the CLI and the
  transcribe test were both run under Python 3.13 to confirm.
- **Transcription is now verified on Windows** — the faster-whisper path was the last one
  never exercised there. Suite on Windows 11: 17 pass, 2 skip, 0 fail.
- **Two Windows-only test failures fixed** (dev-only; no user-facing change):
  `wrapper_test.sh` compared the wrapper's resolved native path against a POSIX `$TMP`, so
  it always failed under Git Bash; `build_test.sh` died with rc=127 where `zip` is absent
  and now SKIPs like the other prereq-guarded tests.

## 1.1.2 — 2026-08-30
- **Fix: frame extraction failed on ffmpeg 9** with `Unrecognized option 'vsync'`. ffmpeg 9
  removed `-vsync`, which every run passed unconditionally, so the tool died at the frames
  stage on any machine with a current ffmpeg. It now probes ffmpeg once for `-fps_mode`
  (added in 5.1) and falls back to `-vsync` for older builds, rather than parsing distro
  version strings like `4.4.2-0ubuntu0.22.04.1`.
- **Windows is now verified**, not merely expected to work: full pipeline run on Windows 11
  with ffmpeg 9.0.1 + uv 0.12.7 + tesseract 5.5.3 — acquire, frames, dedupe, whisper and OCR
  all produced correct output.

## 1.1.1 — 2026-06-07
- **Cross-platform invocation:** the plugin runs the wrapper via `uv run` (the one
  required dependency) instead of a hardcoded `python3`, so it no longer assumes a
  `python3` on PATH — works on Linux/macOS/Windows.
- **Docs:** comprehensive release README + `docs/USER-GUIDE.md`; a Platform support table
  (Linux/macOS supported; **Windows not yet maintainer-tested** — please open an issue);
  supported-sources list (Loom, YouTube, Vimeo, TikTok, Instagram, X, + any `yt-dlp`
  site); marketplace `metadata.description`.
- Genericized dependency-install hints (no longer `dnf`-only); internal process docs
  (specs/plans) moved out of the published repo.

## 1.1.0 — 2026-06-07
- Packaged as a Claude Code / Codex / claude.ai-web skill (thin wrapper around the CLI).
- CLI additions (non-destructive): `.watch-video.json` manifest, `--clean`/`--clean-older-than`,
  `--no-source`, `timeline.md` on by default + `--no-timeline`, `--ocr-tuned`, `--no-transcribe`,
  stale-artifact reconciliation.
- New: `scripts/watch-run.py` wrapper, `scripts/setup.py` bootstrap, `scripts/build-skill.sh`,
  `SKILL.md`, `commands/watch.md`, plugin manifests, smoke tests.

## 1.0.0
- Initial single-file CLI: local Loom/URL/file → transcript + deduped frames + OCR.
