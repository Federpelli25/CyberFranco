import os
import tempfile
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from src.config.settings_loader import SettingsLoader
from src.ui.operator_window import OperatorWindow


def create_operator_window():
    app = QApplication.instance() or QApplication([])
    temporary = tempfile.TemporaryDirectory()
    loader = SettingsLoader()
    settings = replace(
        loader.load(),
        whisper_model_path=str(Path(temporary.name) / "missing-model"),
    )
    device = {
        "id": 1,
        "name": "Test Microphone",
        "max_input_channels": 1,
        "default_samplerate": 48000.0,
        "hostapi": "Test API",
    }
    list_patch = patch(
        "src.ui.operator_window.AudioDeviceManager.list_input_devices",
        return_value=[device],
    )
    default_patch = patch(
        "src.ui.operator_window.AudioDeviceManager.get_default_input_device",
        return_value=device,
    )
    list_patch.start()
    default_patch.start()
    window = OperatorWindow(settings, loader)
    window.show()
    app.processEvents()
    return app, window, temporary, (list_patch, default_patch)


def close_operator_window(window, temporary, patches):
    window.close()
    for active_patch in patches:
        active_patch.stop()
    temporary.cleanup()
