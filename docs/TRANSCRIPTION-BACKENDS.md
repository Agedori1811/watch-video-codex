# Transcription backend — caveats & upgrade paths

v1.2 uses **`faster-whisper` with automatic device selection** after trying captions.
Run `uv run --locked --script watch-video --diagnose` to see what the process can use.

- **CPU:** `cpu/int8`; hardware-aware `--model auto` selects `small`.
- **NVIDIA / CUDA:** `cuda/float16`; `--model auto` selects `medium`. Current
  faster-whisper packages require CUDA 12 cuBLAS and cuDNN 9. Auto mode retries on
  CPU if CUDA libraries are visible enough to probe but fail during inference.
- **AMD (ROCm) / Apple Silicon / cross-vendor GPU:** `faster-whisper`
  (CTranslate2) has **no ROCm or Metal** path — it runs CPU-only on AMD/Mac.
  For GPU there, swap the backend to **`whisper.cpp` with Vulkan** (works on AMD
  RDNA, Intel, NVIDIA) or Metal (Apple). This is why the backend is kept
  isolated in `transcribe()` — it's a drop-in swap, not a rewrite. On AMD/Apple today
  the pipeline runs on CPU; whisper.cpp+Vulkan/Metal is the future GPU path.

## Why this is isolated

Keeping all transcription behind a single `transcribe()` function means the
backend can be swapped without touching the download / frame-extraction / OCR /
dedupe pipeline. The reference plugins do the same thing differently
(`mlx-whisper` vs `openai-whisper` vs cloud Whisper) — see
[REFERENCE-PLUGINS.md](REFERENCE-PLUGINS.md). Our isolation point is the seam
where we'd pick up `whisper.cpp + Vulkan` for AMD GPU support.
