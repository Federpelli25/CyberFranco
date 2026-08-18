import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from openpyxl import Workbook
from PySide6.QtWidgets import QApplication

from src.audio.speech_to_text import SpeechToText
from src.audio.voice_recognition_worker import VoiceRecognitionWorker
from src.core.exceptions import (
    ParticipantDataError,
    SpeechRecognitionError,
)
from src.data.participant_repository import ParticipantRepository
from src.config.settings_loader import SettingsLoader
from src.ui.public_window import PublicWindow


class ParticipantErrorHandlingTests(unittest.TestCase):

    def _workbook(self, rows):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "participants.xlsx"
        workbook = Workbook()
        sheet = workbook.active
        for row in rows:
            sheet.append(row)
        workbook.save(path)
        workbook.close()
        return temporary, path

    def test_missing_excel_raises_application_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.xlsx"
            with self.assertRaisesRegex(
                ParticipantDataError,
                "FILE PARTECIPANTI NON TROVATO",
            ):
                ParticipantRepository(path).load()

    def test_missing_required_column_is_readable(self):
        temporary, path = self._workbook([
            ["Nome", "Cognome"],
            ["Mario", "Rossi"],
        ])
        with temporary:
            with self.assertRaisesRegex(ParticipantDataError, "Squadra"):
                ParticipantRepository(path).load()

    def test_duplicate_participant_is_rejected(self):
        temporary, path = self._workbook([
            ["ID", "Nome", "Cognome", "Squadra"],
            ["001", "Mario", "Rossi", "Blu"],
            ["001", "Luca", "Bianchi", "Rossa"],
        ])
        with temporary:
            with self.assertRaisesRegex(
                ParticipantDataError,
                "ID PARTECIPANTE DUPLICATO",
            ):
                ParticipantRepository(path).load()

    def test_incomplete_row_is_rejected(self):
        temporary, path = self._workbook([
            ["ID", "Nome", "Cognome", "Squadra"],
            ["001", "Mario", None, "Blu"],
        ])
        with temporary:
            with self.assertRaisesRegex(ParticipantDataError, "riga 2"):
                ParticipantRepository(path).load()


class RuntimeErrorHandlingTests(unittest.TestCase):

    def test_whisper_runtime_error_is_wrapped(self):
        service = object.__new__(SpeechToText)
        service.language = "it"
        service.model = Mock()
        service.model.transcribe.side_effect = RuntimeError("ctranslate2")

        with self.assertRaises(SpeechRecognitionError):
            service.transcribe(np.ones(100, dtype=np.float32))

    def test_voice_worker_failure_emits_failed_once(self):
        speech = Mock()
        worker = VoiceRecognitionWorker(speech, "Mario Rossi")
        worker.recorder = Mock()
        worker.recorder.record.side_effect = RuntimeError("device lost")
        failures = []
        completed = []
        worker.failed.connect(failures.append)
        worker.completed.connect(completed.append)

        worker.run()

        self.assertEqual(failures, ["device lost"])
        self.assertEqual(completed, [])


class PublicDisplayFallbackTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_missing_team_assets_use_graphic_fallback(self):
        settings = SettingsLoader().load()
        window = PublicWindow(settings)
        with tempfile.TemporaryDirectory() as directory:
            window.teams_root = Path(directory)
            window.show_team("Mario Rossi", "Squadra inesistente")

            self.assertFalse(window.logo_label.isVisible())
            self.assertIn("qradialgradient", window.central_widget.styleSheet())
            self.assertEqual(window.main_label.text(), "SQUADRA INESISTENTE")

        window._stop_current_animation()
        window.close()
