import os
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from src.config.team_config_loader import TeamConfig
from src.ui.team_reveal import TeamReveal


class AdvancedTeamRevealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.widget = TeamReveal()
        self.widget.resize(1280, 720)

    def tearDown(self):
        self.widget.close()

    def _team(self, configured=True):
        return TeamConfig(
            key="FENICI", slug="fenici", display_name="Le Fenici",
            logo_path=None, background_path=None, audio_path=None,
            primary_color="#D97706", secondary_color="#FBBF24",
            configured=configured,
        )

    def test_missing_assets_keep_large_team_name(self):
        self.widget.configure(self._team(), QPixmap(), QPixmap())
        self.assertEqual(self.widget.name_label.text(), "LE FENICI")
        self.assertFalse(self.widget.logo_label.isVisible())
        self.assertIn("#FBBF24", self.widget.name_label.styleSheet())

    def test_unknown_team_uses_same_safe_static_presentation(self):
        self.widget.configure(self._team(configured=False))
        self.widget.show()
        self.app.processEvents()
        self.assertEqual(self.widget.name_label.text(), "LE FENICI")
        self.assertTrue(self.widget.isVisible())

    def test_intensity_is_clamped(self):
        self.widget.configure(self._team())
        self.widget.set_intensity(99)
        self.assertEqual(self.widget._intensity, 1.35)


if __name__ == "__main__":
    unittest.main()
