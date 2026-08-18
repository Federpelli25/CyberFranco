import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from src.ui.reveal_controller import RevealController, RevealPhase, RevealTimings


class RevealControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_complete_sequence_has_stable_order(self):
        controller = RevealController(RevealTimings(0, 0, 0, 0, 0))
        phases = []
        completed = []
        controller.phase_changed.connect(phases.append)
        controller.completed.connect(lambda: completed.append(True))
        controller.start()
        for _ in range(8):
            self.app.processEvents()
        self.assertEqual(phases, list(RevealPhase))
        self.assertEqual(completed, [True])

    def test_old_generation_cannot_advance_new_flow(self):
        controller = RevealController(RevealTimings(9999, 0, 0, 0, 0))
        phases = []
        controller.phase_changed.connect(phases.append)
        stale = controller.start()
        controller.abort()
        controller._advance(stale, RevealPhase.FLASH_IN)
        self.assertEqual(phases, [RevealPhase.PRE_REVEAL])
        self.assertFalse(controller.active)

    def test_complete_now_emits_once(self):
        controller = RevealController(RevealTimings(9999, 0, 0, 0, 0))
        completed = []
        controller.completed.connect(lambda: completed.append(True))
        controller.start()
        controller.complete_now()
        controller.complete_now()
        self.assertEqual(completed, [True])


if __name__ == "__main__":
    unittest.main()
