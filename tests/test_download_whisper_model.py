import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import download_whisper_model
from src.audio.speech_to_text import SpeechToText


class DownloadWhisperModelScriptTests(unittest.TestCase):

    def test_script_prepares_and_validates_requested_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "local-model"

            def fake_download(
                model_name,
                output_dir,
                local_files_only,
            ):
                self.assertEqual(model_name, "small")
                self.assertFalse(local_files_only)
                model_path = Path(output_dir)
                model_path.mkdir(parents=True, exist_ok=True)

                for file_name in SpeechToText.REQUIRED_MODEL_FILES:
                    (model_path / file_name).write_bytes(b"test")

                return str(model_path)

            with patch.object(
                download_whisper_model,
                "download_model",
                side_effect=fake_download,
            ) as download_mock, patch(
                "sys.argv",
                [
                    "download_whisper_model.py",
                    "--model",
                    "small",
                    "--output",
                    str(output_path),
                ],
            ):
                exit_code = download_whisper_model.main()

            self.assertEqual(exit_code, 0)
            download_mock.assert_called_once()

    def test_script_reports_download_failure(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch.object(
                download_whisper_model,
                "download_model",
                side_effect=RuntimeError("network unavailable"),
            ), patch(
                "sys.argv",
                [
                    "download_whisper_model.py",
                    "--output",
                    temporary_directory,
                ],
            ):
                exit_code = download_whisper_model.main()

            self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
