import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from src.core.exceptions import SessionError, SessionValidationError
from src.data.session_repository import SessionRepository


class SessionRepositoryTests(unittest.TestCase):

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "data" / "session.json"
        self.repository = SessionRepository(self.path)
        self.session = self.repository.create_empty(
            "data/partecipanti.xlsx",
            "a" * 64,
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_missing_file_returns_none(self):
        self.assertFalse(self.repository.exists())
        self.assertIsNone(self.repository.load())

    def test_empty_session_save_and_load(self):
        self.repository.save(self.session)
        loaded = self.repository.load()
        self.assertEqual(loaded["version"], 1)
        self.assertEqual(loaded["processed"], [])

    def test_save_uses_temporary_file_before_atomic_replace(self):
        real_replace = os.replace
        observed = []

        def replace(source, destination):
            observed.append((Path(source).name, Path(source).is_file()))
            real_replace(source, destination)

        with patch("src.data.session_repository.os.replace", side_effect=replace):
            self.repository.save(self.session)

        self.assertEqual(observed, [("session.json.tmp", True)])
        self.assertFalse(self.path.with_name("session.json.tmp").exists())

    def test_corrupted_json_is_preserved(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{invalid", encoding="utf-8")
        with self.assertRaises(SessionValidationError):
            self.repository.load()

        preserved = self.repository.quarantine_corrupted()

        self.assertIsNotNone(preserved)
        self.assertTrue(preserved.exists())
        self.assertFalse(self.path.exists())
        self.assertIn("session.corrupted.", preserved.name)

    def test_invalid_utf8_is_treated_as_corrupted(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(b"\xff\xfe\x00")
        with self.assertRaises(SessionValidationError):
            self.repository.load()

    def test_unknown_version_is_rejected(self):
        self.session["version"] = 99
        self.path.parent.mkdir(parents=True)
        self.path.write_text(json.dumps(self.session), encoding="utf-8")
        with self.assertRaisesRegex(SessionValidationError, "non supportata"):
            self.repository.load()

    def test_timestamps_are_timezone_aware(self):
        created = datetime.fromisoformat(self.session["created_at"])
        self.assertIsNotNone(created.utcoffset())

    def test_fingerprint_is_deterministic_but_detects_changes(self):
        first = [
            {"search_name": "mario rossi", "squadra": "Blu"},
            {"search_name": "luca bianchi", "squadra": "Rossa"},
        ]
        reordered = list(reversed(first))
        changed = [*first[:-1], {"search_name": "luca bianchi", "squadra": "Verde"}]
        self.assertEqual(
            self.repository.participants_fingerprint(first),
            self.repository.participants_fingerprint(reordered),
        )
        self.assertNotEqual(
            self.repository.participants_fingerprint(first),
            self.repository.participants_fingerprint(changed),
        )

    def test_write_failure_is_wrapped_and_temp_removed(self):
        with patch(
            "src.data.session_repository.os.replace",
            side_effect=PermissionError("denied"),
        ):
            with self.assertRaises(SessionError):
                self.repository.save(self.session)
        self.assertFalse(self.path.with_name("session.json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
