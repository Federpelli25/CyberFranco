import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.audio.speech_to_text import (
    SpeechModelError,
    SpeechToText,
)


class SpeechToTextModelPathTests(unittest.TestCase):

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def create_complete_model(self) -> Path:
        model_path = self.root / "model"
        model_path.mkdir()

        for file_name in SpeechToText.REQUIRED_MODEL_FILES:
            (model_path / file_name).write_bytes(b"test")

        return model_path

    def test_missing_model_path_is_rejected(self):
        missing_path = self.root / "missing"

        with self.assertRaisesRegex(
            SpeechModelError,
            "MODELLO WHISPER NON TROVATO",
        ):
            SpeechToText.validate_model_path(missing_path)

    def test_model_path_must_be_directory(self):
        file_path = self.root / "model.bin"
        file_path.write_bytes(b"test")

        with self.assertRaisesRegex(
            SpeechModelError,
            "NON VALIDO",
        ):
            SpeechToText.validate_model_path(file_path)

    def test_incomplete_model_lists_missing_files(self):
        model_path = self.root / "model"
        model_path.mkdir()
        (model_path / "model.bin").write_bytes(b"test")

        with self.assertRaisesRegex(
            SpeechModelError,
            "tokenizer.json",
        ):
            SpeechToText.validate_model_path(model_path)

    def test_complete_model_is_accepted(self):
        model_path = self.create_complete_model()

        self.assertEqual(
            SpeechToText.validate_model_path(model_path),
            model_path.resolve(),
        )

    def test_preprocessor_config_is_optional(self):
        model_path = self.create_complete_model()

        self.assertFalse(
            (model_path / "preprocessor_config.json").exists()
        )
        self.assertEqual(
            SpeechToText.validate_model_path(model_path),
            model_path.resolve(),
        )

    @patch("src.audio.speech_to_text.WhisperModel")
    def test_model_is_loaded_from_exact_local_path_only(
        self,
        whisper_model_mock,
    ):
        model_path = self.create_complete_model()

        speech_to_text = SpeechToText(
            model_path=model_path,
            device="cpu",
            compute_type="int8",
            language="it",
        )

        whisper_model_mock.assert_called_once_with(
            str(model_path.resolve()),
            device="cpu",
            compute_type="int8",
            local_files_only=True,
        )
        self.assertEqual(
            speech_to_text.model_path,
            model_path.resolve(),
        )

    @patch("src.audio.speech_to_text.WhisperModel")
    def test_missing_path_never_calls_whisper_model(
        self,
        whisper_model_mock,
    ):
        with self.assertRaises(SpeechModelError):
            SpeechToText(
                model_path=self.root / "missing",
            )

        whisper_model_mock.assert_not_called()

    @patch("src.audio.speech_to_text.WhisperModel")
    def test_loader_error_is_wrapped_for_operator(
        self,
        whisper_model_mock,
    ):
        model_path = self.create_complete_model()
        whisper_model_mock.side_effect = RuntimeError(
            "Invalid CTranslate2 model"
        )

        with self.assertRaisesRegex(
            SpeechModelError,
            "NON CARICABILE",
        ):
            SpeechToText(model_path=model_path)
