import os
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from src.ui.no_wheel_combo_box import NoWheelComboBox


class NoWheelComboBoxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_closed_combo_ignores_wheel_without_changing_selection(self):
        combo = NoWheelComboBox()
        combo.addItems(["Primo", "Secondo", "Terzo"])
        combo.setCurrentIndex(1)
        event = Mock()
        combo.wheelEvent(event)
        self.assertEqual(combo.currentIndex(), 1)
        event.ignore.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
