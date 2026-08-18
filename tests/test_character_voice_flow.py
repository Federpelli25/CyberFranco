import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from src.core.participant_tracker import ParticipantTracker
from src.core.sorting_controller import SortingController
from src.core.state_manager import AppState, StateManager


class FakeAudio(QObject):
    started = Signal()
    finished = Signal()
    failed = Signal(str)

    def __init__(self):
        super().__init__()
        self.is_playing = False
        self.play_thinking = Mock(return_value=True)
        self.play_reveal = Mock(return_value=True)
        self.stop = Mock()


class CharacterVoiceFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.participant = {
            "id": "001", "nome_completo": "Mario Rossi", "squadra": "BLU"
        }
        self.operator = Mock()
        for name in (
            "participant_confirmed", "listening_started", "listening_ambiguous",
            "listening_failed", "undo_last_requested", "reset_participant_requested",
            "new_event_requested",
        ):
            setattr(self.operator, name, Mock())
        self.public = Mock()
        self.public.face_widget = Mock()
        self.public.reveal_finished = Mock()
        self.state = StateManager()
        self.audio = FakeAudio()
        self.controller = SortingController(
            self.operator, self.public, self.state,
            ParticipantTracker([self.participant]),
            SimpleNamespace(thinking_duration_ms=999999),
            character_audio_manager=self.audio,
        )

    def test_thinking_reveal_and_talking_signals(self):
        self.controller.start_sorting(self.participant)
        self.audio.play_thinking.assert_called_once_with()
        self.controller._start_reveal(self.controller._flow_token)
        self.audio.play_reveal.assert_called_once_with("BLU")
        self.audio.started.emit()
        self.public.face_widget.set_talking.assert_called_with(True)
        self.audio.finished.emit()
        self.public.face_widget.set_talking.assert_called_with(False)

    def test_recovery_stops_audio_and_clears_talking(self):
        self.state.set_state(AppState.THINKING)
        self.controller.recover_to_idle()
        self.audio.stop.assert_called()
        self.public.face_widget.set_talking.assert_called_with(False)

    def test_listening_is_blocked_while_character_speaks(self):
        self.audio.is_playing = True
        self.controller._start_listening()
        self.assertEqual(self.state.state, AppState.IDLE)
        self.public.show_listening.assert_not_called()


if __name__ == "__main__":
    unittest.main()
