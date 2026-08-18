import json
import tempfile
import unittest
from pathlib import Path

from src.config.team_config_loader import TeamConfigLoader


class TeamConfigTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "config").mkdir()
        (self.root / "assets" / "teams" / "fenici").mkdir(parents=True)
        (self.root / "assets" / "audio" / "reveal").mkdir(parents=True)
        self.logo = self.root / "assets" / "teams" / "fenici" / "logo.png"
        self.logo.write_bytes(b"placeholder")
        self.audio = self.root / "assets" / "audio" / "reveal" / "fenici.wav"
        self.audio.write_bytes(b"RIFF")
        self.path = self.root / "config" / "teams.json"

    def tearDown(self):
        self.temporary.cleanup()

    def _write(self, data):
        self.path.write_text(json.dumps(data), encoding="utf-8")

    def test_arbitrary_name_and_optional_assets_are_resolved(self):
        self._write({
            "LE FENICI": {
                "slug": "le-fenici",
                "display_name": "Le Fenici",
                "logo": "assets/teams/fenici/logo.png",
                "background": None,
                "audio": "assets/audio/reveal/fenici.wav",
                "primary_color": "#D97706",
            }
        })
        loader = TeamConfigLoader(self.root)
        team = loader.resolve("  le fenici ")
        self.assertTrue(team.configured)
        self.assertEqual(team.display_name, "Le Fenici")
        self.assertEqual(team.slug, "le-fenici")
        self.assertEqual(team.logo_path, self.logo)
        self.assertIsNone(team.background_path)
        self.assertEqual(team.audio_path, self.audio)
        self.assertEqual(team.secondary_color, "#94A3B8")

    def test_unknown_team_uses_neutral_fallback(self):
        self._write({"FENICI": {"slug": "fenici", "display_name": "Fenici"}})
        team = TeamConfigLoader(self.root).resolve("Leoni")
        self.assertFalse(team.configured)
        self.assertEqual(team.display_name, "Leoni")
        self.assertEqual(team.slug, "leoni")

    def test_invalid_color_and_missing_assets_are_warnings(self):
        self._write({"DRAGHI": {
            "slug": "draghi", "display_name": "Draghi",
            "logo": "missing.png", "background": "missing-bg.png",
            "audio": "missing.wav", "primary_color": "purple"
        }})
        loader = TeamConfigLoader(self.root)
        self.assertEqual(loader.count, 1)
        self.assertGreaterEqual(len(loader.warnings), 4)
        self.assertEqual(loader.resolve("Draghi").primary_color, "#334155")

    def test_duplicate_slug_is_ignored_and_reload_invalidates_config(self):
        self._write({
            "FENICI": {"slug": "volanti", "display_name": "Fenici"},
            "GRIFONI": {"slug": "volanti", "display_name": "Grifoni"},
        })
        loader = TeamConfigLoader(self.root)
        self.assertEqual(loader.count, 1)
        self._write({"TITANI": {"slug": "titani", "display_name": "Titani"}})
        loader.reload()
        self.assertIsNone(loader.get("Fenici"))
        self.assertEqual(loader.get("Titani").display_name, "Titani")

    def test_missing_or_invalid_file_is_non_crashing(self):
        loader = TeamConfigLoader(self.root, "config/missing.json")
        self.assertFalse(loader.is_usable)
        self.path.write_text("{invalid", encoding="utf-8")
        loader = TeamConfigLoader(self.root)
        self.assertFalse(loader.is_usable)


if __name__ == "__main__":
    unittest.main()
