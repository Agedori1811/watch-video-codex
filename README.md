# watch-video

> Codex向け派生版です。原作は
> [`WebDevBar/watch-video`](https://github.com/WebDevBar/watch-video) で、MIT Licenseの条件を
> 維持したうえでCaption-first、CUDA自動選択、SNSメタデータ、Codex Plugin配布を調整しています。

**Give a coding agent the ability to "watch" a video — entirely on your own machine.**

`watch-video` turns a **Loom**, a **YouTube / Vimeo / TikTok / Instagram / X** link (or
any of the [~1000+ sites `yt-dlp` supports](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)),
or a **local file** into artifacts an LLM agent can actually read:

- a **timestamped transcript** (authored captions → automatic captions → local Whisper),
- **sanitized source metadata** (post text/description, author, date, engagement, chapters),
- a **deduplicated set of key frames** (so static screencasts don't waste tokens),
- **OCR of on-screen text** (so financial figures, dashboard numbers, and labels that
  are *shown but never spoken* survive), and
- a **`timeline.md`** that interleaves each frame with what was said and what was on
  screen at that moment.

It ships both as a **command-line tool** and as a **Claude Code / Codex plugin** (the
agent runs it for you and reads the result).

> **Everything runs locally** — `yt-dlp` + `ffmpeg` + `faster-whisper` + `tesseract`.
> No video or audio is sent to any cloud service. This is the whole point: recordings
> often contain private or financial data.
> Version: **1.2.1** · License: MIT

[![CI](https://github.com/Agedori1811/watch-video-codex/actions/workflows/ci.yml/badge.svg)](https://github.com/Agedori1811/watch-video-codex/actions/workflows/ci.yml)

---

## Table of contents

- [Why](#why)
- [Install](#install)
  - [As a Codex plugin](#a-as-a-codex-plugin-recommended)
  - [As a Claude Code plugin](#b-as-a-claude-code-plugin)
  - [As a Codex skill](#c-as-a-codex-skill)
  - [As a CLI](#d-as-a-cli)
  - [claude.ai web bundle](#e-claudeai-web-bundle-non-sensitive-videos-only)
- [Quick start](#quick-start)
- [Output](#output-what-the-agent-reads)
- [Options](#options)
- [Cleanup & ephemeral mode](#cleanup--ephemeral-mode)
- [Privacy](#privacy)
- [How it works](#how-it-works)
- [Development](#development)
- [Credits](#credits)

---

## Why

Coding agents increasingly receive **screen recordings** instead of written tickets —
usually a Loom where someone points at a dashboard and says "change *this* number."
Those recordings carry sparse, non-technical instructions *and* on-screen figures that
are never spoken. To act on one, an agent needs the video as readable text + frames.

Existing video plugins either send audio to a **cloud** transcription API (a non-starter
for private/financial recordings) or have **no OCR** and **no frame de-duplication**.
`watch-video` is built for the local + Loom-native + on-screen-numbers case. See
[`docs/WHY.md`](docs/WHY.md) for the full rationale and a feature comparison, and
[`docs/REFERENCE-PLUGINS.md`](docs/REFERENCE-PLUGINS.md) for prior art / credits.

---

## Install

### A. As a Codex plugin (recommended)

Add this public marketplace once:

```text
codex plugin marketplace add Agedori1811/watch-video-codex
codex plugin add watch-video@agedori-video-tools
```

Then restart the ChatGPT desktop app or start a new Codex session. In a new Work chat,
type `@watch-video` and paste a video URL. The plugin runs on the active Codex host;
use a local Windows host when you want to use the PC's NVIDIA GPU.

### Dependencies

| Tool | Required? | Purpose | Install |
|---|---|---|---|
| [`uv`](https://docs.astral.sh/uv/) | ✅ | runs the single-file script + its locked inline deps | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `ffmpeg` + `ffprobe` | ✅ | frame extraction and duration probing | `brew install ffmpeg` / `apt install ffmpeg` / `dnf install ffmpeg` |
| `tesseract` | optional | OCR of on-screen text | `brew install tesseract` / `apt install tesseract-ocr` / `dnf install tesseract` |

`yt-dlp` (including its default JavaScript challenge components and browser impersonation
extra), `faster-whisper`, `Pillow`, `numpy`, and `pytesseract` are pulled automatically by
`uv` on first run (Python 3.10+). Their complete transitive resolution and hashes are
committed in `watch-video.lock`; `uv run --locked --script watch-video …` refuses to
silently re-resolve it. Or run the bootstrap:

```bash
python3 scripts/setup.py        # installs uv + ffmpeg (required) and tesseract (optional)
python3 scripts/setup.py --check  # verify only, no install
```

(On **Windows**, use `python` or `py` if `python3` isn't on your PATH.)

For full YouTube support, install a JavaScript runtime. Deno is yt-dlp's recommended
choice; this fork also detects an installed Node.js/Bun/QuickJS runtime automatically.

### Platform support

| Platform | Status | Notes |
|---|---|---|
| **Linux** | ✅ Supported | Primary dev/test platform. |
| **macOS** | ✅ Supported | `setup.py` uses Homebrew; all deps available. All paths are POSIX. |
| **Windows** (incl. Claude CLI in PowerShell) | ✅ Supported — local-file path verified on Windows 11 | The plugin invokes the tool through **`uv run`** (the one required dep), so it does **not** depend on a `python3` on PATH, and all paths use `pathlib`. `uv`, `ffmpeg`, `tesseract`, `yt-dlp`, and `faster-whisper` all have Windows builds (`setup.py` uses `winget`). Two caveats: (1) run the bare CLI as `uv run --locked --script watch-video …` — the `./watch-video` shebang form is POSIX-only; (2) the **dev** scripts `tests/*.sh` and `scripts/build-skill.sh` are Bash, so they need **Git Bash or WSL** (end users don't run these). |

> **Windows base status (upstream 1.1.3).** Verified on Windows 11 with ffmpeg 9.0.1, uv 0.12.7 and
> tesseract 5.5.3, on **both** paths: a local file, and a YouTube URL through `yt-dlp`
> (download, format merge, frames, whisper, OCR). Only the **cookie options**
> (`--cookies-from-browser`, `--cookies`) remain unexercised there, and macOS is still
> not maintainer-smoke-tested. The 1.2 caption/CUDA changes have automated coverage but
> still require a final CUDA run on the target Windows PC. **If you hit any upstream issue,
> [open an issue](https://github.com/WebDevBar/watch-video/issues) and we'll try to
> address it.**

### B. As a Claude Code plugin

This repository **is** a single-plugin marketplace (`.claude-plugin/marketplace.json` at
its root). In Claude Code:

```
/plugin marketplace add webdevbar/watch-video
/plugin install watch-video@watch-video
```

(or `/plugin marketplace add /path/to/watch-video` for a local clone). Then invoke the
namespaced command on any video:

> Non-interactive equivalents (handy for scripting/CI): `claude plugin marketplace add webdevbar/watch-video` then `claude plugin install watch-video@watch-video`; `claude plugin validate .` checks the manifests.

```
/watch-video:watch https://www.loom.com/share/XXXX
/watch-video:watch ./recording.mp4 --no-ocr
```

The command runs the bundled CLI via a thin wrapper, applies sensible agent defaults
(tuned OCR on), prints the output directory, and the skill instructs the agent to read
the result in order. Dependencies: run `python3 scripts/setup.py` once (the plugin's
`SKILL.md` documents this).

### C. As a Codex skill

```bash
git clone https://github.com/Agedori1811/watch-video-codex ~/.codex/skills/watch-video
# or copy the built bundle (see Development → build-skill.sh)
```

The `.codex-plugin/plugin.json` manifest + shared `SKILL.md` drive it the same way.

### D. As a CLI

```bash
git clone https://github.com/Agedori1811/watch-video-codex
cd watch-video
chmod +x watch-video
./watch-video <loom-url | any-url | local-file.mp4> [options]
```

The shebang is `#!/usr/bin/env -S uv run --script`, so `uv` handles the environment.
**On Windows** (PowerShell/cmd) the shebang doesn't apply — run it explicitly:

```powershell
uv run --locked --script watch-video <loom-url | any-url | local-file.mp4> [options]
```

### E. claude.ai web bundle (non-sensitive videos only)

`scripts/build-skill.sh` produces a `watch.skill` bundle you can upload at
**Settings → Capabilities → Skills**. ⚠️ The hosted web sandbox runs the pipeline on
Anthropic's servers, so the video **leaves your machine** — use the web surface for
**non-sensitive / public** videos only. Sensitive recordings stay on Claude Code/Codex.

---

## Quick start

**Through an agent (Claude Code):**

```
/watch-video:watch https://www.loom.com/share/abc123
```

**As a CLI:**

```bash
# a local file
./watch-video ./demo.mp4

# a public URL (YouTube, Vimeo, etc. — anything yt-dlp supports)
./watch-video "https://www.youtube.com/watch?v=XXXX"

# a private/team Loom or any login-gated source (reads your browser cookies locally)
./watch-video https://www.loom.com/share/XXXX --cookies-from-browser firefox

# denser sampling + sharper OCR for a number-heavy dashboard recording
./watch-video ./dashboard.mp4 --periodic 2 --ocr-tuned

# verify CUDA is visible before the first long transcription
./watch-video --diagnose
```

**Sources:** local files, **Loom**, **YouTube**, **Vimeo**, **TikTok**, **Instagram**,
**X/Twitter**, and any other site [`yt-dlp` supports](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).
Login-gated or private videos need `--cookies-from-browser <browser>` (or `--cookies cookies.txt`).

Output lands in `./watch-video-out/<slug>/` (override with `--out`). The CLI prints the
path to `SUMMARY.md` on stdout; everything else goes to stderr.

---

## Output (what the agent reads)

In `./watch-video-out/<slug>/`:

| File | What it is |
|---|---|
| `SUMMARY.md` | **Read first.** Run metadata + the exact list of artifacts produced + read order. |
| `metadata.md` / `.json` | Sanitized post/video metadata: title, text/description, uploader, date, engagement, language, and chapters when available. |
| `timeline.md` | Each kept frame interleaved with the transcript line(s) spoken then + an OCR snippet. The primary comprehension doc. |
| `transcript.md` / `.txt` | Full timestamped transcript. |
| `captions/source.vtt` or `.srt` | Caption source used before Whisper, when available. |
| `frames/*.jpg` | The deduplicated key frames (timestamp in the filename). |
| `frames/ocr-combined.md` | All on-screen text, per frame. Cross-check exact numbers against the frame image (OCR can misread; the image is ground truth). |
| `frames/ocr/*.txt` | Per-frame raw OCR. |
| `contact-sheet.jpg` | A montage overview of all kept frames. |
| `.watch-video.json` | Hidden run manifest (tool signature, version, source, created, downloaded-source). Used as the ownership marker for safe cleanup — not for reading. |

**Read order** (skip any file a run didn't produce): `SUMMARY.md → metadata.md →
timeline.md → transcript.md → frames/*.jpg → frames/ocr-combined.md`.

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--out DIR` | `./watch-video-out/<slug>` | exact output folder for this run |
| `--model NAME` | `auto` | `medium` on CUDA, `small` on CPU; or choose `tiny`/`base`/`small`/`medium`/`large-v3` |
| `--device auto\|cuda\|cpu` | `auto` | prefer NVIDIA CUDA when visible; auto falls back to CPU if CUDA fails |
| `--compute-type TYPE` | `auto` | `float16` on CUDA, `int8` on CPU unless overridden |
| `--caption-language LANG` | `auto` | caption preference; declared source language, then Japanese/English by default |
| `--captions VTT\|SRT` | — | use a supplied local caption file before Whisper |
| `--no-captions` | — | skip caption discovery and force Whisper |
| `--captions-only` | — | do not fall back to Whisper when captions are unavailable |
| `--diagnose` | — | show dependency and CUDA visibility, then exit |
| `--periodic SECONDS` | `4` | sample a frame every N seconds |
| `--scene-threshold FLOAT` | `0.08` | extra frame on scene change (0–1) |
| `--max-frames N` | `200` | strict cap on kept frames (evenly thinned, endpoints kept) |
| `--dedupe-distance N` | `6` | perceptual-hash distance to treat frames as duplicates |
| `--ocr-tuned` | off | upscale + threshold + tuned PSM for sharper on-screen-number OCR |
| `--no-ocr` | — | skip OCR |
| `--no-timeline` | — | skip `timeline.md` |
| `--no-contact-sheet` | — | skip the montage |
| `--no-transcribe` | — | skip transcription (no model download) |
| `--no-source` | — | delete the **downloaded** source video after extraction (never a local input) |
| `--language LANG` | auto | force transcription language (e.g. `en`) |
| `--cookies-from-browser B` | — | private Loom auth via browser cookies (`firefox`/`chrome`/…) |
| `--cookies FILE` | — | a Netscape `cookies.txt` for yt-dlp |
| `--force` | — | allow writing into a non-empty directory not created by watch-video |
| `--clean …` / `--clean-older-than DAYS` | — | janitorial cleanup (see below) |

> **Safety:** a run refuses to write into a **non-empty directory it didn't create**
> (use `--force` to override), so it never clobbers your files.

---

## Cleanup & ephemeral mode

Output folders persist (re-readable, auditable) and are gitignored. To remove them:

```bash
./watch-video --clean <slug>            # delete one run's folder (under ./watch-video-out/)
./watch-video --clean ./path/to/dir     # delete an explicit folder (custom --out)
./watch-video --clean all               # delete all watch-video folders under ./watch-video-out/
./watch-video --clean-older-than 7      # delete watch-video folders older than 7 days
```

Cleanup **only** deletes folders carrying a valid `.watch-video.json` signature, removes
**only** watch-video's own artifacts within them, and removes the folder itself only if
it's then empty — your files are never deleted.

**Ephemeral mode** (`/watch-video:watch … --ephemeral`) is a two-step, agent-driven flow:
the agent runs the tool, reads the artifacts into context, then runs
`watch-run.py --clean <dir>` to delete them — nothing sensitive lingers on disk.

---

## Privacy

- **Local-first.** On Claude Code and Codex (your machine), transcription + OCR never
  leave the device. No cloud transcription backend is ever used.
- **Web surface caveat.** The claude.ai web bundle runs in a hosted sandbox — for
  **non-sensitive / public videos only**.
- **Output is sensitive.** Folders may contain private/financial data; they're
  `.gitignore`d — never commit one. For private Loom links, cookies are read locally;
  never copy them into output/transcripts.
- **Credential-bearing URLs are redacted.** Query strings, fragments, and HTTP userinfo
  are removed from logs, manifests, metadata, and summaries. The original URL is only
  passed in-memory to `yt-dlp`.

---

## How it works

```
probe metadata + captions (authored → automatic)
   → acquire (local file | yt-dlp)
   → extract frames (first + scene-change + periodic, via ffmpeg)
   → dedupe (perceptual hash; strict --max-frames cap)
   → transcribe only if needed (CUDA/float16 → CPU/int8 fallback)
   → OCR each frame (tesseract)                     [optional]
   → contact sheet
   → timeline.md (interleave frames + transcript + OCR)
   → SUMMARY.md + .watch-video.json manifest
```

The transcription backend is isolated in one `transcribe()` function. NVIDIA CUDA is
used automatically when visible; AMD/Apple GPU support would require a future
whisper.cpp+Vulkan/Metal backend. See
[`docs/TRANSCRIPTION-BACKENDS.md`](docs/TRANSCRIPTION-BACKENDS.md).

The plugin layer is a **thin wrapper** (`scripts/watch-run.py`) around the unchanged CLI
— one implementation of the pipeline, never duplicated.

A step-by-step user guide lives in [`docs/USER-GUIDE.md`](docs/USER-GUIDE.md).

---

## Development

```bash
python -m unittest discover -s tests -p 'test_*.py' -v  # portable unit suite
python tests/integration_smoke.py     # locked uv + ffmpeg local-file smoke test
bash tests/run_all.sh                 # existing Linux/POSIX regression suite
WV_TRANSCRIBE_TEST=1 bash tests/transcribe_test.sh   # opt-in: exercises real Whisper
python scripts/check_release.py       # version, lock, and bundle-source invariants
bash scripts/build-skill.sh dist/watch.skill         # build the distributable bundle
```

GitHub Actions runs native Ubuntu, Windows, and macOS jobs, plus Python 3.10–3.14
compatibility checks. The cross-platform job processes a synthetic local clip and a
Japanese sidecar caption through the locked CLI; the broader Bash regression suite runs
on Ubuntu. See [`docs/VERIFICATION.md`](docs/VERIFICATION.md) for the exact boundary and
honest manual checks, and [`docs/RELEASING.md`](docs/RELEASING.md) for releases.

---

## Credits

This repository is a modified distribution of
[`WebDevBar/watch-video`](https://github.com/WebDevBar/watch-video), retained under the
original MIT License. Caption-first/CUDA/SNS and Codex packaging changes in this fork are
maintained by `Agedori1811`.

Packaging modeled on, and with thanks to,
[`mathiaschu/watch`](https://github.com/mathiaschu/watch) and
[`bradautomates/claude-video`](https://github.com/bradautomates/claude-video). The OCR,
frame de-duplication, `timeline.md` interleave, and local faster-whisper backend are
watch-video's additions.

## License

MIT — see [`LICENSE`](LICENSE).
