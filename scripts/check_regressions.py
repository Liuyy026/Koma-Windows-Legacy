"""Check the Windows legacy backend and optionally PySide6 without model downloads."""
import argparse
from contextlib import contextmanager, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend import worker
from backend.translation_service import API_KEY_ENV, TranslationService, TranslationServiceError


SAMPLE = ROOT / "samples" / "01.webp"
SOURCE = "ここで少し休みましょう。"
TRANSLATION = "我们在这里休息一下吧。"
MODEL = "regression-model"


def fixture_page():
    return {
        "version": 2,
        "width": 320,
        "height": 320,
        "model": "",
        "blocks": [
            {"id": "1", "box": [20, 30, 160, 65], "vertical": False, "source": SOURCE,
             "translation": "", "error": "", "edited": False},
        ],
    }


@contextmanager
def mock_service(provider):
    """Record requests at the service boundary and return provider-shaped replies."""
    calls = []

    def respond(service, route, payload=None, timeout=300):
        calls.append((route, payload, timeout))
        if route == "/api/tags":
            return {"models": [{"name": MODEL}, {"name": MODEL}, {"name": "example:cloud"},
                               {"name": "remote", "remote_model": "remote/model"}]}
        if route == "/models":
            return {"data": [{"id": MODEL}, {"id": MODEL}]}
        content = json.dumps({"translations": {"1": TRANSLATION}}, ensure_ascii=False)
        if provider == "ollama" and route == "/api/chat":
            return {"message": {"content": content}, "done_reason": "stop"}
        if provider == "omlx" and route == "/chat/completions":
            return {"choices": [{"message": {"content": content}, "finish_reason": "stop"}]}
        raise AssertionError(f"Unexpected request {route}")

    with patch.object(TranslationService, "request", respond):
        yield calls


class BackendChecks(unittest.TestCase):
    def test_launch_and_model_setup_cli_help(self):
        for script, argument in (("backend/worker.py", "--image"),
                                 ("scripts/migrate_structure.py", "--dry-run")):
            with self.subTest(script=script):
                result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(ROOT / script), "--help"],
                                        capture_output=True, text=True, encoding="utf-8", timeout=15, check=True)
                self.assertIn(argument, result.stdout)
        self.assertTrue((ROOT / "scripts" / "prepare_models.py").is_file())
        self.assertTrue((ROOT / "windows" / "启动Windows.bat").is_file())

    def test_provider_model_listing(self):
        for provider, expected_route in (("ollama", "/api/tags"), ("omlx", "/models")):
            with self.subTest(provider=provider), mock_service(provider) as calls:
                with patch.object(sys, "argv", ["worker.py", "--provider", provider, "--list-models"]):
                    output = io.StringIO()
                    with redirect_stdout(output):
                        worker.main()
                self.assertEqual(json.loads(output.getvalue()), {"ok": True, "models": [MODEL]})
                self.assertEqual(calls, [(expected_route, None, 5)])

    def test_provider_payload_and_translations(self):
        for provider, expected_route in (("ollama", "/api/chat"), ("omlx", "/chat/completions")):
            with self.subTest(provider=provider), mock_service(provider) as calls:
                page = fixture_page()
                worker.translate(page, MODEL, lambda message: None, lambda result: None, provider=provider)
                self.assertEqual(page["blocks"][0]["translation"], TRANSLATION)
                self.assertEqual(page["translation_config"]["provider"], provider)
                route, payload, _ = calls[-1]
                self.assertEqual(route, expected_route)
                self.assertFalse(payload["stream"])
                schema = (payload["format"] if provider == "ollama"
                          else payload["response_format"]["json_schema"]["schema"])
                self.assertEqual(schema["properties"]["translations"]["required"], ["1"])

    def test_partial_response_rejects_echo_without_losing_valid_translation(self):
        translated, errors = worker.parse_translations(
            json.dumps({"translations": {"1": TRANSLATION, "2": SOURCE}}),
            {"1", "2", "3"}, {"1": SOURCE, "2": SOURCE},
        )
        self.assertEqual(translated, {"1": TRANSLATION})
        self.assertEqual(set(errors), {"2", "3"})

    def test_provider_change_regenerates_machine_translation_and_preserves_edit(self):
        page = fixture_page()
        page["blocks"].append({"id": "2", "box": [205, 30, 295, 65], "vertical": False,
                               "source": "こんにちは。", "translation": "人工保留", "edited": True, "error": ""})
        for provider in ("ollama", "omlx"):
            with mock_service(provider) as calls:
                worker.translate(page, MODEL, lambda message: None, lambda result: None, provider=provider)
            self.assertEqual(page["translation_config"]["provider"], provider)
            self.assertEqual(page["blocks"][1]["translation"], "人工保留")
            self.assertEqual(len(calls), 2)
        with mock_service("omlx") as calls:
            worker.translate(page, MODEL, lambda message: None, lambda result: None, provider="omlx")
        self.assertEqual(calls, [("/models", None, 5)])

    def test_url_validation_and_key_redaction(self):
        with patch.dict(os.environ, {API_KEY_ENV: "regression-token"}):
            service = TranslationService("omlx", "https://LOCALHOST:443/")
            self.assertEqual(service.identity, {"provider": "omlx", "base_url": "https://localhost/v1"})
            self.assertEqual(service.safe_error(ValueError("failed: regression-token")), "failed: [已隐藏]")
        with self.assertRaises(TranslationServiceError):
            TranslationService("ollama", "http://user:pass@localhost:11439")

    def test_ocr_cache_is_reused_for_identical_content(self):
        with tempfile.TemporaryDirectory(prefix="koma-检查-") as temporary:
            folder = Path(temporary)
            relocated = folder / "同一页.webp"
            relocated.write_bytes(SAMPLE.read_bytes())
            with patch.object(worker, "CACHE", folder / "缓存"), patch.object(
                worker, "recognize", return_value=fixture_page(),
            ) as recognize:
                result_cache_paths = []
                for image in (SAMPLE, relocated):
                    arguments = ["worker.py", "--image", str(image), "--operation", "ocr",
                                 "--status", str(folder / "进度.json")]
                    output = io.StringIO()
                    with patch.object(sys, "argv", arguments), redirect_stdout(output):
                        worker.main()
                    result = json.loads(output.getvalue())
                    self.assertTrue(result.get("ok"), result)
                    result_cache_paths.append(Path(result["cache"]))
                recognize.assert_called_once()
                self.assertEqual(result_cache_paths[0], result_cache_paths[1])
                self.assertEqual(json.loads(result_cache_paths[0].read_text(encoding="utf-8"))["blocks"][0]["source"], SOURCE)


class QtChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_open_sample_folder_shows_cached_translation(self):
        from PySide6.QtCore import QSettings
        from PySide6.QtWidgets import QFileDialog
        from windows.windows_app import Reader

        with tempfile.TemporaryDirectory(prefix="koma-qt-") as temporary:
            folder = Path(temporary)
            settings = QSettings(str(folder / "settings.ini"), QSettings.Format.IniFormat)
            reader = Reader(settings)
            try:
                page = fixture_page()
                page["blocks"][0]["translation"] = TRANSLATION
                cache = folder / "缓存.json"
                worker.atomic_json(cache, page)
                before = cache.read_bytes()
                with patch.object(QFileDialog, "getExistingDirectory", return_value=str(SAMPLE.parent)), patch.object(
                    reader, "cache_for_image", return_value=cache,
                ):
                    reader.open_folder()
                self.assertEqual(reader.current, SAMPLE)
                self.assertEqual(reader.list.count(), 2)
                self.assertFalse(reader.preview.pixmap.isNull())
                self.assertIn("1 处已翻译", reader.results.toPlainText())
                self.assertIn(TRANSLATION, reader.results.toPlainText())
                self.assertTrue(reader.results.isReadOnly())
                self.assertEqual(reader.display.currentText(), "中文")
                self.assertEqual(cache.read_bytes(), before)
            finally:
                reader.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qt", action="store_true", help="also check the reader with PySide6 offscreen")
    args = parser.parse_args()
    loader = unittest.defaultTestLoader
    suite = loader.loadTestsFromTestCase(BackendChecks)
    if args.qt:
        suite.addTests(loader.loadTestsFromTestCase(QtChecks))
    with patch.dict(os.environ, {API_KEY_ENV: "", "KOMA_BENCHMARK_METRICS": ""}):
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
