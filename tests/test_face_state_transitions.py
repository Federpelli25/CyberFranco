import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from src.core.state_manager import AppState, StateManager
from src.ui.face_widget import FaceWidget


class FaceStateTransitionTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.widget = FaceWidget(Path("missing-assets-for-test"))
        self.manager = StateManager()
        self.manager.state_changed.connect(self.widget.set_state)

    def tearDown(self):
        self.widget.close()

    def test_idle_listening_thinking_transition(self):
        self.manager.set_state(AppState.LISTENING)
        self.assertEqual(self.widget.state, FaceWidget.LISTENING)
        self.manager.set_state(AppState.THINKING)
        self.assertEqual(self.widget.state, FaceWidget.THINKING)
        self.assertTrue(self.widget.thinking_timer.isActive())
        self.assertNotEqual(self.widget._head_tilt, 7.0)

    def test_awaiting_confirmation_keeps_thinking_animation_continuous(self):
        self.manager.set_state(AppState.THINKING)
        generation = self.widget.generation
        animations = list(self.widget._animations)
        self.manager.set_state(AppState.AWAITING_CONFIRMATION)
        self.assertEqual(self.widget.state, FaceWidget.AWAITING_CONFIRMATION)
        self.assertEqual(self.widget.generation, generation)
        self.assertEqual(self.widget._animations, animations)
        self.assertTrue(self.widget.thinking_timer.isActive())
        self.assertEqual(self.widget.thinking_timer.interval(), 1100)
        self.assertEqual(self.widget._mouth_expression, 0.42)

    def test_thinking_to_reveal_stops_thinking_timer(self):
        self.manager.set_state(AppState.THINKING)
        self.manager.set_state(AppState.REVEAL)
        self.assertEqual(self.widget.state, FaceWidget.REVEAL)
        self.assertFalse(self.widget.thinking_timer.isActive())
        self.assertEqual(self.widget._mouth_expression, 1.0)
        self.assertGreaterEqual(len(self.widget._animations), 2)

    def test_callback_from_previous_generation_is_stale(self):
        generation = self.widget.generation
        self.manager.set_state(AppState.LISTENING)
        self.assertFalse(self.widget.is_callback_current(generation))
        self.assertTrue(self.widget.is_callback_current(self.widget.generation))

    def test_repeated_ten_cycles_leave_only_current_state_resources(self):
        for _ in range(10):
            self.manager.set_state(AppState.LISTENING)
            self.manager.set_state(AppState.THINKING)
            self.manager.set_state(AppState.REVEAL)
            self.manager.set_state(AppState.IDLE)
        self.assertEqual(self.widget.state, FaceWidget.IDLE)
        self.assertTrue(self.widget.blink_timer.isActive())
        self.assertFalse(self.widget.thinking_timer.isActive())
        self.assertEqual(len(self.widget._animations), 2)


if __name__ == "__main__":
    unittest.main()
