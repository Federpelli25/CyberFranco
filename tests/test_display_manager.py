import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.config.settings_loader import SettingsLoader
from src.ui.display_manager import DisplayManager
from src.ui.public_window import PublicWindow
from PySide6.QtWidgets import QApplication


class FakeGeometry:
    def __init__(self, x, y, width, height):
        self.values = x, y, width, height

    def x(self): return self.values[0]
    def y(self): return self.values[1]
    def width(self): return self.values[2]
    def height(self): return self.values[3]


class FakeScreen:
    def __init__(self, name, geometry):
        self._name = name
        self._geometry = geometry

    def name(self): return self._name
    def geometry(self): return self._geometry


class DisplayManagerTests(unittest.TestCase):

    def setUp(self):
        self.primary = FakeScreen("Internal", FakeGeometry(0, 0, 1920, 1080))
        self.secondary = FakeScreen("Projector", FakeGeometry(-1280, 0, 1280, 720))
        self.application = Mock()
        self.application.screens.return_value = [self.primary, self.secondary]
        self.application.primaryScreen.return_value = self.primary
        self.manager = DisplayManager(self.application)

    def test_list_screens_exposes_geometry_and_primary(self):
        screens = self.manager.list_screens()
        self.assertEqual(screens[0]["geometry"]["width"], 1920)
        self.assertTrue(screens[0]["is_primary"])
        self.assertEqual(screens[1]["geometry"]["x"], -1280)

    def test_valid_index_resolves_secondary(self):
        self.assertEqual(self.manager.resolve_screen(1)["name"], "Projector")

    def test_name_can_be_used_as_identifier(self):
        self.assertEqual(
            self.manager.resolve_screen("Projector")["index"],
            1,
        )

    def test_invalid_identifier_falls_back_to_primary(self):
        resolved = self.manager.resolve_screen(99)
        self.assertEqual(resolved["index"], 0)
        self.assertTrue(resolved["is_primary"])

    def test_no_screens_returns_none(self):
        self.application.screens.return_value = []
        self.application.primaryScreen.return_value = None
        self.assertIsNone(self.manager.resolve_screen(0))

    def test_format_contains_size_and_primary_marker(self):
        label = self.manager.format_screen(self.manager.list_screens()[0])
        self.assertIn("1920x1080", label)
        self.assertIn("Principale", label)


class PublicDisplaySettingsTests(unittest.TestCase):

    def test_display_preferences_are_saved_without_losing_other_values(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config"
            config.mkdir()
            path = config / "settings.json"
            path.write_text(
                '{"language": "it", "public_display_monitor": 0, '
                '"public_display_fullscreen": false}',
                encoding="utf-8",
            )
            loader = SettingsLoader(root)

            loader.save_public_display(2, True)
            settings = loader.load()

            self.assertEqual(settings.public_display_monitor, 2)
            self.assertTrue(settings.public_display_fullscreen)
            self.assertEqual(settings.language, "it")

    def test_invalid_display_preferences_are_rejected(self):
        loader = SettingsLoader()
        with self.assertRaisesRegex(ValueError, "public_display_monitor"):
            loader.save_public_display(-1, False)


class PublicWindowPositioningTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_window_uses_selected_geometry_and_fullscreen(self):
        screen = self.app.primaryScreen()
        manager = Mock()
        manager.resolve_screen.return_value = {
            "index": 0,
            "screen": screen,
            "geometry": {
                "x": -1280,
                "y": 100,
                "width": 1280,
                "height": 720,
            },
        }
        window = PublicWindow(SettingsLoader().load(), manager)
        window.showNormal = Mock()
        window.showFullScreen = Mock()
        window.setGeometry = Mock()
        handle = Mock()
        window.windowHandle = Mock(return_value=handle)

        window.apply_display_settings(1, True)

        window.setGeometry.assert_called_with(-1280, 100, 1280, 720)
        handle.setScreen.assert_called_once_with(screen)
        window.showFullScreen.assert_called_once()
        window.close()


if __name__ == "__main__":
    unittest.main()
