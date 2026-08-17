import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from src.config.settings_loader import SettingsLoader
from src.ui.operator_window import OperatorWindow


class WhisperMissingGuiTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @patch(
        "src.ui.operator_window.AudioDeviceManager"
        ".get_default_input_device"
    )
    @patch(
        "src.ui.operator_window.AudioDeviceManager"
        ".list_input_devices"
    )
    def test_manual_controls_remain_available_without_model(
        self,
        list_devices_mock,
        default_device_mock,
    ):
        device = {
            "id": 1,
            "name": "Test Microphone",
            "max_input_channels": 1,
            "default_samplerate": 48000.0,
            "hostapi": "Test API",
        }
        list_devices_mock.return_value = [device]
        default_device_mock.return_value = device

        settings_loader = SettingsLoader()
        settings = settings_loader.load()

        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_path = Path(temporary_directory) / "missing"
            settings = replace(
                settings,
                whisper_model_path=str(missing_path),
            )
            window = OperatorWindow(
                settings,
                settings_loader,
            )

            self.assertFalse(window.speech_ready)
            self.assertFalse(window.listen_button.isEnabled())
            self.assertTrue(window.search_input.isEnabled())
            self.assertTrue(window.results_list.isEnabled())
            self.assertGreaterEqual(window.display_combo.count(), 1)
            self.assertIn(
                "MODELLO WHISPER NON DISPONIBILE",
                window.process_label.text(),
            )

            window.set_processing(True)
            self.assertFalse(window.display_combo.isEnabled())
            self.assertFalse(window.apply_display_button.isEnabled())

            window.set_processing(False)
            self.assertTrue(window.display_combo.isEnabled())
            window.close()
