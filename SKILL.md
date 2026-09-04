---
name: watch-video
description: Inspect a YouTube, X, TikTok, Instagram, Vimeo, Loom, Reddit, other yt-dlp-supported video URL, or local video using caption-first transcription, source metadata, key frames, and OCR. Use when the user wants the actual contents, claims, visuals, captions, editing, or on-screen text of a video analyzed.
---

# watch-video

Turn a video into agent-readable artifacts. For remote sources, preserve sanitized post
metadata and use this transcript order: **authored caption → automatic caption → local
Whisper**. CUDA is selected automatically when CTranslate2 can see an NVIDIA GPU;
otherwise CPU/int8 is used. Everything runs **locally**.

## ⚠️ Privacy (read first)
On **Claude Code** and **Codex** (local machines) transcription + OCR never leave
the machine. **The claude.ai web surface runs in a hosted sandbox — it is for
NON-SENSITIVE / PUBLIC videos only. Never send a sensitive video to the web
surface.** Output folders may contain private/financial data — never commit or
upload them.

## Dependencies
Required: `uv`, `ffmpeg` (including `ffprobe`). Optional: `tesseract` (OCR). Run
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup.py"` once to install them (it attempts the
official `uv` installer + your OS package manager for ffmpeg; tesseract is best-effort),
or preinstall manually. On **Windows** use `python` or `py` if `python3` isn't found. If
`uv`'s installer lands it outside your `PATH`, add its dir to `PATH` and re-run.
(Once `uv` is present, the wrapper above is run via `uv run`, which works on
Linux/macOS/Windows without assuming a `python3` on PATH.)

## Invocation
Installed as a Claude Code plugin, this is invoked **namespaced** as
`/watch-video:watch`. The command resolves the wrapper via the plugin-root env var
`${CLAUDE_PLUGIN_ROOT}` (set by Claude Code to the installed plugin directory). On
Codex / manual skill installs, run the wrapper from the skill's own directory.

## How to run
The command runs the wrapper (which runs the bundled CLI and prints the output dir):

```
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/watch-run.py" <url|file> [--caption-language ja] [--device auto] [--ephemeral]
```

The wrapper prints exactly one line: the **output directory**.

## How to read the result (in order, skip any file not present)
1. `SUMMARY.md` — lists exactly what this run produced and transcript provenance.
2. `metadata.md` — title/post text/uploader/date/chapters and source-platform context.
3. `timeline.md` — frames interleaved with transcript + OCR (read this first for meaning).
4. `transcript.md` — full timestamped transcript.
5. `frames/*.jpg` — open individual frames; cross-check exact numbers against
   `frames/ocr-combined.md` (OCR can misread; the image is ground truth).

Do not claim the full video was inspected merely because the command succeeded. Read the
artifacts above, inspect the relevant frames, state whether the transcript came from
manual captions, automatic captions, or Whisper, and identify any unverified gaps.

## Useful controls
- `--diagnose`: report CUDA visibility and dependencies without processing a video.
- `--captions FILE`: prefer a supplied `.vtt`/`.srt`; local same-name sidecars are automatic.
- `--captions-only`: do not fall back to Whisper. `--no-captions`: force local Whisper.
- `--device cuda`: require CUDA; `--device auto` (default) falls back safely to CPU.
- `--model auto` (default): `medium` on CUDA and `small` on CPU.
- Login-gated SNS URLs may need `--cookies-from-browser edge` or `chrome`. Never copy
  cookie files or credentials into the output.

## Ephemeral mode (two steps — delete after reading)
`--ephemeral` does NOT auto-delete (the CLI exits before you read). Do this:
1. Run `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/watch-run.py" <src> --ephemeral` → note the printed output dir.
2. After you have read the artifacts, run
   `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/watch-run.py" --clean <output-dir>` to delete them.

## Cleanup
- `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/watch-run.py" --clean <slug|path>` — delete one run's folder.
- `... --clean all` — delete all watch-video folders under `./watch-video-out/`.
- `... --clean-older-than 7` — delete folders older than 7 days.
Cleanup only deletes folders carrying a valid `.watch-video.json` marker.
