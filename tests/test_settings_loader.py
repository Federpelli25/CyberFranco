import json
import tempfile
import unittest
from pathlib import Path

from src.config.settings_loader import (
    SettingsError,
    SettingsLoader,
)


class SettingsLoaderTests(unittest.TestCase):

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project_root = Path(
            self.temporary_directory.name
        )
        self.config_directory = self.project_root / "config"
        self.config_directory.mkdir()
        self.settings_path = (
            self.config_directory / "settings.json"
        )
        self.loader = SettingsLoader(self.project_root)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write_settings(self, values):
        self.settings_path.write_text(
            json.dumps(values),
            encoding="utf-8",
        )

    def test_missing_optional_values_use_defaults(self):
        self.write_settings({})

        settings = self.loader.load()

        self.assertEqual(settings.whisper_model, "small")
        self.assertEqual(
            settings.whisper_model_path,
            "models/faster-whisper-small",
        )
        self.assertEqual(
            settings.recording_duration_seconds,
            4.0,
        )
        self.assertEqual(settings.thinking_duration_ms, 1200)
        self.assertIsNone(settings.microphone_device)
        self.assertEqual(settings.public_display_monitor, 1)
        self.assertFalse(settings.public_display_fullscreen)
        self.assertEqual(settings.session_file, "data/session.json")
        self.assertTrue(settings.session_persistence_enabled)
        self.assertEqual(
            settings.resolve_session_file(),
            self.project_root / "data" / "session.json",
        )
        self.assertEqual(settings.logging_level, "INFO")
        self.assertEqual(
            settings.logging_file,
            "logs/cyberfranco.log",
        )
        self.assertEqual(settings.logging_max_bytes, 5242880)
        self.assertEqual(settings.logging_backup_count, 3)

    def test_values_override_defaults(self):
        self.write_settings(
            {
                "whisper_model": "medium",
                "recording_duration_seconds": 3.5,
                "thinking_duration_ms": 2500,
                "microphone_device": 4,
                "public_display_monitor": 2,
                "public_display_fullscreen": True,
                "session_file": "runtime/event.json",
                "session_persistence_enabled": False,
            }
        )

        settings = self.loader.load()

        self.assertEqual(settings.whisper_model, "medium")
        self.assertEqual(
            settings.recording_duration_seconds,
            3.5,
        )
        self.assertEqual(settings.thinking_duration_ms, 2500)
        self.assertEqual(settings.microphone_device, 4)
        self.assertEqual(settings.public_display_monitor, 2)
        self.assertTrue(settings.public_display_fullscreen)
        self.assertEqual(settings.session_file, "runtime/event.json")
        self.assertFalse(settings.session_persistence_enabled)

    def test_invalid_session_persistence_flag_is_rejected(self):
        self.write_settings({"session_persistence_enabled": "yes"})
        with self.assertRaisesRegex(SettingsError, "session_persistence_enabled"):
            self.loader.load()

    def test_relative_paths_are_resolved_from_project_root(self):
        self.write_settings({})
        settings = self.loader.load()

        self.assertEqual(
            settings.resolve_project_path("assets/teams"),
            self.project_root / "assets" / "teams",
        )
        self.assertEqual(
            settings.resolve_whisper_model_path(),
            self.project_root
            / "models"
            / "faster-whisper-small",
        )

    def test_whisper_model_path_can_be_overridden(self):
        self.write_settings(
            {"whisper_model_path": "custom/whisper"}
        )

        settings = self.loader.load()

        self.assertEqual(
            settings.resolve_whisper_model_path(),
            self.project_root / "custom" / "whisper",
        )

    def test_logging_settings_override_defaults(self):
        self.write_settings(
            {
                "logging": {
                    "level": "DEBUG",
                    "file": "custom/app.log",
                    "max_bytes": 1024,
                    "backup_count": 1,
                }
            }
        )

        settings = self.loader.load()

        self.assertEqual(settings.logging_level, "DEBUG")
        self.assertEqual(settings.logging_max_bytes, 1024)
        self.assertEqual(settings.logging_backup_count, 1)
        self.assertEqual(
            settings.resolve_log_file(),
            self.project_root / "custom" / "app.log",
        )

    def test_partial_logging_settings_keep_defaults(self):
        self.write_settings(
            {"logging": {"level": "ERROR"}}
        )

        settings = self.loader.load()

        self.assertEqual(settings.logging_level, "ERROR")
        self.assertEqual(
            settings.logging_file,
            "logs/cyberfranco.log",
        )

    def test_invalid_logging_level_is_rejected(self):
        self.write_settings(
            {"logging": {"level": "VERBOSE"}}
        )

        with self.assertRaisesRegex(
            SettingsError,
            "logging.level",
        ):
            self.loader.load()

    def test_logging_must_be_object(self):
        self.write_settings({"logging": "INFO"})

        with self.assertRaisesRegex(
            SettingsError,
            "oggetto JSON",
        ):
            self.loader.load()

    def test_negative_logging_rotation_value_is_rejected(self):
        self.write_settings(
            {"logging": {"max_bytes": -1}}
        )

        with self.assertRaisesRegex(
            SettingsError,
            "logging.max_bytes",
        ):
            self.loader.load()

    def test_real_participants_file_has_priority(self):
        data_directory = self.project_root / "data"
        data_directory.mkdir()
        real_file = data_directory / "partecipanti.xlsx"
        example_file = data_directory / "partecipanti_example.xlsx"
        real_file.touch()
        example_file.touch()
        self.write_settings({})

        settings = self.loader.load()

        self.assertEqual(
            settings.resolve_participants_file(),
            real_file,
        )

    def test_example_file_is_used_as_fallback(self):
        data_directory = self.project_root / "data"
        data_directory.mkdir()
        example_file = data_directory / "partecipanti_example.xlsx"
        example_file.touch()
        self.write_settings({})

        settings = self.loader.load()

        self.assertEqual(
            settings.resolve_participants_file(),
            example_file,
        )

    def test_missing_participant_files_have_readable_error(self):
        self.write_settings({})
        settings = self.loader.load()

        with self.assertRaisesRegex(
            SettingsError,
            "Nessun file partecipanti",
        ):
            settings.resolve_participants_file()

    def test_malformed_json_has_line_and_column(self):
        self.settings_path.write_text(
            '{"whisper_model": }',
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            SettingsError,
            "riga 1, colonna",
        ):
            self.loader.load()

    def test_missing_settings_file_has_readable_error(self):
        with self.assertRaisesRegex(
            SettingsError,
            "File di configurazione non trovato",
        ):
            self.loader.load()

    def test_invalid_recording_duration_is_rejected(self):
        self.write_settings(
            {"recording_duration_seconds": 0}
        )

        with self.assertRaisesRegex(
            SettingsError,
            "recording_duration_seconds",
        ):
            self.loader.load()

    def test_invalid_microphone_device_is_rejected(self):
        self.write_settings(
            {"microphone_device": []}
        )

        with self.assertRaisesRegex(
            SettingsError,
            "microphone_device",
        ):
            self.loader.load()

    def test_boolean_microphone_device_is_rejected(self):
        self.write_settings(
            {"microphone_device": True}
        )

        with self.assertRaisesRegex(
            SettingsError,
            "microphone_device",
        ):
            self.loader.load()

    def test_invalid_monitor_is_rejected(self):
        self.write_settings(
            {"public_display_monitor": -1}
        )

        with self.assertRaisesRegex(
            SettingsError,
            "public_display_monitor",
        ):
            self.loader.load()

    def test_invalid_fullscreen_value_is_rejected(self):
        self.write_settings(
            {"public_display_fullscreen": "yes"}
        )

        with self.assertRaisesRegex(
            SettingsError,
            "public_display_fullscreen",
        ):
            self.loader.load()

    def test_microphone_device_is_saved_preserving_settings(self):
        self.write_settings(
            {
                "whisper_model": "small",
                "microphone_device": None,
            }
        )

        self.loader.save_microphone_device(18)

        saved = json.loads(
            self.settings_path.read_text(encoding="utf-8")
        )
        self.assertEqual(saved["microphone_device"], 18)
        self.assertEqual(saved["whisper_model"], "small")

    def test_default_microphone_selection_is_saved_as_null(self):
        self.write_settings({"microphone_device": 7})

        self.loader.save_microphone_device(None)

        saved = json.loads(
            self.settings_path.read_text(encoding="utf-8")
        )
        self.assertIsNone(saved["microphone_device"])

    def test_negative_microphone_id_is_rejected(self):
        self.write_settings({})

        with self.assertRaisesRegex(
            SettingsError,
            "microphone_device",
        ):
            self.loader.save_microphone_device(-1)

    def test_microphone_name_is_no_longer_accepted_as_id(self):
        self.write_settings(
            {"microphone_device": "USB microphone"}
        )

        with self.assertRaisesRegex(
            SettingsError,
            "microphone_device",
        ):
            self.loader.load()


if __name__ == "__main__":
    unittest.main()
