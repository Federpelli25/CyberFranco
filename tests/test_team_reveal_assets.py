import json
import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from src.config.settings_loader import SettingsLoader
from src.config.team_config_loader import TeamConfigLoader
from src.ui.public_window import PublicWindow


class TeamRevealAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "config").mkdir()
        (self.root / "assets" / "face").mkdir(parents=True)
        (self.root / "config" / "teams.json").write_text(json.dumps({
            "FENICI": {
                "slug": "fenici", "display_name": "Le Fenici",
                "primary_color": "#D97706",
                "secondary_color": "#FBBF24",
            }
        }), encoding="utf-8")
        base = SettingsLoader().load()
        self.settings = replace(base, project_root=self.root)
        self.loader = TeamConfigLoader(self.root)
        self.window = PublicWindow(self.settings, team_config_loader=self.loader)

    def tearDown(self):
        self.window.close()
        self.temporary.cleanup()

    def test_reveal_uses_display_name_and_gradient_fallback(self):
        self.window.show_team("Partecipante", "fenici")
        self.assertEqual(self.window.main_label.text(), "Le Fenici")
        style = self.window.central_widget.styleSheet()
        self.assertIn("#D97706", style)
        self.assertIn("#FBBF24", style)
        self.assertFalse(self.window.logo_label.isVisible())

    def test_unknown_team_warns_and_continues(self):
        warnings = []
        self.window.team_warning.connect(warnings.append)
        self.window.show_team("Partecipante", "Leoni")
        self.assertEqual(self.window.main_label.text(), "LEONI")
        self.assertTrue(warnings)

    def test_reload_clears_preloaded_asset_cache(self):
        self.window._team_pixmap_cache[Path("fake.png")] = object()
        self.window.reload_team_assets()
        self.assertNotIn(Path("fake.png"), self.window._team_pixmap_cache)


if __name__ == "__main__":
    unittest.main()
