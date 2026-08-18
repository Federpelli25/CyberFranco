import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.config.settings_loader import AppSettings
from src.core.exceptions import SessionError
from src.core.participant_tracker import ParticipantTracker
from src.core.sorting_controller import SortingController
from src.core.state_manager import StateManager
from src.data.session_repository import SessionRepository
from tests.test_sorting_controller_tracking import (
    FakeOperatorWindow,
    FakePublicWindow,
    make_participant,
)


class SessionPersistenceTests(unittest.TestCase):

    def setUp(self):
        self.mario = make_participant("Mario", "Rossi", "BLU")
        self.luca = make_participant("Luca", "Bianchi", "ROSSA")
        self.participants = [self.mario, self.luca]
        self.tracker = ParticipantTracker(self.participants)
        self.operator = FakeOperatorWindow()
        self.public = FakePublicWindow()
        self.repository = Mock()
        self.context = SessionRepository.create_empty(
            "data/partecipanti.xlsx",
            SessionRepository.participants_fingerprint(self.participants),
        )
        self.settings = AppSettings(
            project_root=Path.cwd(),
            participants_file="data/partecipanti.xlsx",
            example_participants_file="data/partecipanti_example.xlsx",
            whisper_model="small",
            whisper_model_path="models/faster-whisper-small",
            whisper_device="cpu",
            whisper_compute_type="int8",
            language="it",
            recording_duration_seconds=4.0,
            thinking_duration_ms=1200,
            microphone_device=None,
            public_display_monitor=0,
            public_display_fullscreen=False,
            session_file="data/session.json",
            session_persistence_enabled=True,
            logging_level="INFO",
            logging_file="logs/cyberfranco.log",
            logging_max_bytes=5242880,
            logging_backup_count=3,
        )
        self.controller = SortingController(
            self.operator,
            self.public,
            StateManager(),
            self.tracker,
            self.settings,
            self.repository,
            self.context,
        )

    def test_tracker_restore_preserves_history_and_timestamp(self):
        timestamp = "2026-08-17T15:00:00+02:00"
        self.tracker.load_processed([{
            "participant_id": self.mario["id"],
            "name": "Mario Rossi",
            "team": "BLU",
            "processed_at": timestamp,
        }])
        self.assertTrue(self.tracker.is_processed(self.mario))
        self.assertEqual(self.tracker.export_state()[0]["processed_at"], timestamp)

    def test_restore_distinguishes_duplicate_names_by_id(self):
        first = make_participant("Mario", "Rossi", "BLU", "001")
        second = make_participant("Mario", "Rossi", "ROSSA", "002")
        tracker = ParticipantTracker([first, second])
        tracker.load_processed([{
            "participant_id": "002",
            "name": "Mario Rossi",
            "team": "ROSSA",
            "processed_at": "2026-08-17T15:00:00+02:00",
        }])
        self.assertFalse(tracker.is_processed(first))
        self.assertTrue(tracker.is_processed(second))

    def test_reveal_completion_persists_processed_participant(self):
        with patch.object(SortingController, "_start_reveal"):
            self.controller.start_sorting(self.mario)
        self.controller._finish_sorting()

        self.repository.save.assert_called_once_with(self.context)
        self.assertEqual(
            self.context["processed"][0]["participant_id"], self.mario["id"]
        )

    def test_undo_and_reset_are_persisted(self):
        self.tracker.mark_processed(self.mario)
        self.tracker.mark_processed(self.luca)
        self.controller.undo_last_assignment()
        self.controller.reset_participant(self.mario)

        self.assertEqual(self.repository.save.call_count, 2)
        self.assertEqual(self.context["processed"], [])

    def test_new_event_clears_and_persists(self):
        self.tracker.mark_processed(self.mario)
        self.controller.start_new_event()

        self.assertEqual(self.tracker.processed_count, 0)
        self.assertEqual(self.context["processed"], [])
        self.repository.save.assert_called_once()

    def test_mismatch_blocks_sorting_until_new_event(self):
        self.controller.session_blocked = True
        self.controller.start_sorting(self.mario)
        self.assertIsNone(self.controller.current_participant)
        self.assertIn("SESSIONE NON COMPATIBILE", self.operator.errors[-1])

        self.controller.start_new_event()
        self.controller.start_sorting(self.mario)
        self.assertIs(self.controller.current_participant, self.mario)

    def test_write_failure_does_not_rollback_tracking(self):
        self.repository.save.side_effect = SessionError("disk full")
        self.tracker.mark_processed(self.mario)

        self.controller.undo_last_assignment()

        self.assertFalse(self.tracker.is_processed(self.mario))
        self.assertIn("SESSIONE NON SALVATA", self.operator.errors[-1])


if __name__ == "__main__":
    unittest.main()
