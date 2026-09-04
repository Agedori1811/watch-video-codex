import contextlib
import io
import json
import runpy
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = ROOT / "watch-video"


def load(path):
    return runpy.run_path(str(path))


class PortableCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = load(CLI_PATH)

    def test_sensitive_url_is_redacted(self):
        raw = "https://user:password@example.com:8443/video?id=7&token=secret#fragment"
        safe = self.ns["safe_source"](raw)
        self.assertEqual(safe, "https://example.com:8443/video?redacted")
        self.assertNotIn("password", safe)
        self.assertNotIn("secret", safe)

    def test_sensitive_url_slug_is_redacted(self):
        raw = "https://user:password@example.com:8443/video?id=7&token=secret#fragment"
        slug = self.ns["slugify"](raw)
        self.assertEqual(slug, "example.com-8443-video-redacted")
        self.assertNotIn("password", slug)
        self.assertNotIn("secret", slug)

    def test_stdio_is_reconfigured_for_utf8_when_supported(self):
        class Stream:
            def __init__(self):
                self.calls = []

            def reconfigure(self, **kwargs):
                self.calls.append(kwargs)

        stdout, stderr = Stream(), Stream()
        with mock.patch.object(self.ns["sys"], "stdout", stdout), mock.patch.object(
            self.ns["sys"], "stderr", stderr
        ):
            self.ns["configure_stdio"]()
        expected = [{"encoding": "utf-8", "errors": "replace"}]
        self.assertEqual(stdout.calls, expected)
        self.assertEqual(stderr.calls, expected)

    def test_remote_acquire_does_not_overwrite_user_source_file(self):
        acquire = self.ns["acquire"]
        globals_ = acquire.__globals__
        old_have, old_run = globals_["have"], globals_["run"]

        def fake_run(command, label):
            template = Path(command[command.index("-o") + 1])
            Path(str(template).replace("%(ext)s", "mp4")).write_bytes(b"downloaded")

        try:
            globals_["have"] = lambda binary: True
            globals_["run"] = fake_run
            with tempfile.TemporaryDirectory() as directory:
                out = Path(directory)
                user_file = out / "source.mp4"
                user_file.write_bytes(b"user data")
                self.ns["write_manifest"](out, "previous local run")
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    downloaded, was_downloaded = acquire(
                        "https://example.com/watch?token=secret", out, None, None
                    )
                self.assertTrue(was_downloaded)
                self.assertEqual(user_file.read_bytes(), b"user data")
                self.assertEqual(downloaded.name, "source-watch-video-1.mp4")
                self.assertEqual(downloaded.read_bytes(), b"downloaded")
                self.assertNotIn("secret", stderr.getvalue())
        finally:
            globals_["have"], globals_["run"] = old_have, old_run

    def test_manifest_and_metadata_are_utf8_and_redacted(self):
        raw = "https://example.com/動画?token=secret#fragment"
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            self.ns["write_manifest"](out, raw)
            clean = self.ns["write_metadata"](
                out,
                {"title": "日本語", "webpage_url": raw, "original_url": raw},
                raw,
            )
            manifest = json.loads((out / ".watch-video.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["source"], "https://example.com/動画?redacted")
            self.assertEqual(clean["webpage_url"], "https://example.com/動画?redacted")
            self.assertIn("日本語", (out / "metadata.md").read_text(encoding="utf-8"))
            self.assertNotIn(b"secret", (out / "metadata.json").read_bytes())

    def test_caption_first_parser_and_utf8_output(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            caption = out / "入力.ja.vtt"
            caption.write_text(
                "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\n字幕を優先します。\n",
                encoding="utf-8",
            )
            segments = self.ns["write_caption_transcript"](
                out, {"path": caption, "kind": "sidecar-caption", "language": "ja"}
            )
            self.assertEqual(segments, [(0.0, "字幕を優先します。")])
            self.assertIn("字幕を優先", (out / "transcript.md").read_text(encoding="utf-8"))

    def test_invalid_numeric_options_fail_before_processing(self):
        cases = (
            (["sample.mp4", "--periodic", "0"], "--periodic SECONDS must be > 0"),
            (["sample.mp4", "--scene-threshold", "2"], "between 0 and 1"),
            (["sample.mp4", "--max-frames", "0"], "--max-frames must be >= 1"),
            (["sample.mp4", "--dedupe-distance", "-1"], "--dedupe-distance must be >= 0"),
        )
        for args, message in cases:
            with self.subTest(args=args):
                proc = subprocess.run(
                    [sys.executable, str(CLI_PATH), *args],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                self.assertEqual(proc.returncode, 2)
                self.assertIn(message, proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)

    def test_remote_mp4_url_is_not_mistaken_for_a_local_path(self):
        args = types.SimpleNamespace(
            periodic=4,
            scene_threshold=0.08,
            max_frames=200,
            dedupe_distance=6,
            cookies=None,
            source="https://cdn.example.com/video.mp4?token=secret",
        )

        class Parser:
            @staticmethod
            def error(message):
                raise AssertionError(message)

        self.ns["validate_processing_args"](Parser(), args)

    def test_missing_local_file_has_actionable_error(self):
        proc = subprocess.run(
            [sys.executable, str(CLI_PATH), "definitely-missing.mp4"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("local source file not found", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_expected_failure_has_no_traceback_or_secret(self):
        namespace = dict(self.ns)
        function = namespace["cli_entrypoint"]
        function.__globals__["main"] = lambda: (_ for _ in ()).throw(
            namespace["WatchVideoError"]("failed https://example.com/v?token=secret")
        )
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            function()
        self.assertEqual(raised.exception.code, 1)
        self.assertNotIn("secret", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertIn("?redacted", stderr.getvalue())

    def test_external_command_failure_redacts_url(self):
        failed = subprocess.CompletedProcess(
            [], 1, stdout="", stderr="download failed https://example.com/v?token=secret"
        )
        with mock.patch.object(self.ns["subprocess"], "run", return_value=failed):
            with self.assertRaises(self.ns["WatchVideoError"]) as raised:
                self.ns["run"](["yt-dlp", "sensitive-url"], "download")
        self.assertNotIn("secret", str(raised.exception))
        self.assertIn("?redacted", str(raised.exception))

    def test_cuda_auto_falls_back_to_cpu(self):
        calls = []

        class Segment:
            start = 1.0
            text = " test "

        class Info:
            language = "en"

        class Model:
            def __init__(self, name, device, compute_type):
                calls.append((name, device, compute_type))
                if device == "cuda":
                    raise RuntimeError("CUDA unavailable")

            def transcribe(self, *args, **kwargs):
                return iter([Segment()]), Info()

        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            sys.modules,
            {
                "ctranslate2": types.SimpleNamespace(get_cuda_device_count=lambda: 1),
                "faster_whisper": types.SimpleNamespace(WhisperModel=Model),
            },
        ):
            result = self.ns["transcribe"]("input.mp4", Path(directory), "auto", None)
        self.assertEqual(result[2:], ("cpu", "int8", "small"))
        self.assertEqual(calls, [("medium", "cuda", "float16"), ("small", "cpu", "int8")])


class SetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = load(ROOT / "scripts" / "setup.py")

    def test_windows_package_ids_are_explicit_and_noninteractive(self):
        with mock.patch.object(self.ns["platform"], "system", return_value="Windows"), mock.patch.object(
            self.ns["shutil"], "which", side_effect=lambda name: "winget.exe" if name == "winget" else None
        ):
            ffmpeg = self.ns["pkg_install"]("ffmpeg")
            tesseract = self.ns["pkg_install"]("tesseract")
        self.assertIn("Gyan.FFmpeg", ffmpeg)
        self.assertIn("UB-Mannheim.TesseractOCR", tesseract)
        self.assertIn("--accept-source-agreements", ffmpeg)

    def test_linux_tesseract_package_name(self):
        with mock.patch.object(self.ns["platform"], "system", return_value="Linux"), mock.patch.object(
            self.ns["shutil"], "which", side_effect=lambda name: "/usr/bin/apt-get" if name == "apt-get" else None
        ):
            command = self.ns["pkg_install"]("tesseract")
        self.assertEqual(command[-1], "tesseract-ocr")


class WrapperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = load(ROOT / "scripts" / "watch-run.py")

    def test_wrapper_adds_default_ocr_and_returns_output_directory(self):
        completed = subprocess.CompletedProcess([], 0, stdout=str(ROOT / "out" / "SUMMARY.md") + "\n")
        function = self.ns["run_cli"]
        function.__globals__["command_prefix"] = lambda: ["uv", "run", "--script", "watch-video"]
        with mock.patch.object(self.ns["subprocess"], "run", return_value=completed) as called:
            result = function(["video.mp4", "--no-transcribe"], default_ocr_tuned=True)
        self.assertEqual(Path(result), (ROOT / "out").resolve())
        self.assertIn("--ocr-tuned", called.call_args.args[0])
        self.assertEqual(called.call_args.kwargs["encoding"], "utf-8")


if __name__ == "__main__":
    unittest.main()
