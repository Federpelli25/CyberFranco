import unittest
from unittest.mock import patch
from pathlib import Path

from src.config.settings_loader import AppSettings
from src.core.participant_tracker import ParticipantTracker
from src.core.sorting_controller import SortingController
from src.core.state_manager import AppState, StateManager


class FakeSignal:

    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)


class FakeOperatorWindow:

    def __init__(self):
        self.participant_confirmed = FakeSignal()
        self.listening_started = FakeSignal()
        self.listening_ambiguous = FakeSignal()
        self.listening_failed = FakeSignal()
        self.undo_last_requested = FakeSignal()
        self.reset_participant_requested = FakeSignal()

        self.processing = False
        self.tracking_status = None
        self.processed_participants = []
        self.tracking_messages = []
        self.already_processed = []
        self.reset_count = 0

    def set_processing(self, processing):
        self.processing = processing

    def update_tracking_status(
        self,
        total,
        processed,
        remaining,
    ):
        self.tracking_status = (
            total,
            processed,
            remaining,
        )

    def update_processed_list(self, participants):
        self.processed_participants = participants

    def show_tracking_message(self, message):
        self.tracking_messages.append(message)

    def show_already_processed(self, participant):
        self.already_processed.append(participant)

    def reset_for_next_participant(self):
        self.reset_count += 1


class FakePublicWindow:

    def __init__(self):
        self.reveal_finished = FakeSignal()
        self.idle_count = 0
        self.thinking_count = 0
        self.revealed_teams = []

    def show_idle(self):
        self.idle_count += 1

    def show_listening(self):
        pass

    def show_waiting_confirmation(self):
        pass

    def show_thinking(self):
        self.thinking_count += 1

    def show_team(self, participant_name, team):
        self.revealed_teams.append(
            (participant_name, team)
        )


def make_participant(nome, cognome, squadra):
    nome_completo = f"{nome} {cognome}"
    return {
        "nome": nome,
        "cognome": cognome,
        "squadra": squadra,
        "nome_completo": nome_completo,
        "search_name": nome_completo.lower(),
    }


class SortingControllerTrackingTests(unittest.TestCase):

    def setUp(self):
        self.mario = make_participant(
            "Mario",
            "Rossi",
            "ROSSI",
        )
        self.luca = make_participant(
            "Luca",
            "Bianchi",
            "BLU",
        )
        self.tracker = ParticipantTracker(
            [self.mario, self.luca]
        )
        self.operator = FakeOperatorWindow()
        self.public = FakePublicWindow()
        self.state_manager = StateManager()
        self.settings = AppSettings(
            project_root=Path.cwd(),
            participants_file="data/partecipanti.xlsx",
            example_participants_file=(
                "data/partecipanti_example.xlsx"
            ),
            whisper_model="small",
            whisper_model_path=(
                "models/faster-whisper-small"
            ),
            whisper_device="cpu",
            whisper_compute_type="int8",
            language="it",
            recording_duration_seconds=4.0,
            thinking_duration_ms=1200,
            microphone_device=None,
            public_display_monitor=1,
            public_display_fullscreen=False,
            logging_level="INFO",
            logging_file="logs/cyberfranco.log",
            logging_max_bytes=5242880,
            logging_backup_count=3,
        )
        self.controller = SortingController(
            operator_window=self.operator,
            public_window=self.public,
            state_manager=self.state_manager,
            participant_tracker=self.tracker,
            settings=self.settings,
        )

    def test_initial_tracking_status_is_sent_to_operator(self):
        self.assertEqual(
            self.operator.tracking_status,
            (2, 0, 2),
        )
        self.assertEqual(
            self.operator.processed_participants,
            [],
        )

    def test_participant_is_completed_only_after_reveal_finishes(self):
        with patch.object(
            SortingController,
            "_start_reveal",
        ):
            self.controller.start_sorting(self.mario)

        self.assertFalse(
            self.tracker.is_processed(self.mario)
        )
        self.assertEqual(
            self.state_manager.state,
            AppState.THINKING,
        )

        self.controller._start_reveal()

        self.assertFalse(
            self.tracker.is_processed(self.mario)
        )
        self.assertEqual(
            self.state_manager.state,
            AppState.REVEAL,
        )

        self.controller._finish_sorting()

        self.assertTrue(
            self.tracker.is_processed(self.mario)
        )
        self.assertEqual(
            self.operator.tracking_status,
            (2, 1, 1),
        )
        self.assertEqual(
            self.state_manager.state,
            AppState.IDLE,
        )
        self.assertEqual(self.operator.reset_count, 1)

    def test_processed_participant_cannot_start_second_reveal(self):
        self.tracker.mark_processed(self.mario)

        with patch.object(
            SortingController,
            "_start_reveal",
        ) as start_reveal:
            self.controller.start_sorting(self.mario)

        start_reveal.assert_not_called()
        self.assertIsNone(self.controller.current_participant)
        self.assertEqual(
            self.operator.already_processed,
            [self.mario],
        )
        self.assertEqual(self.public.idle_count, 1)

    def test_undo_is_blocked_while_application_is_busy(self):
        self.tracker.mark_processed(self.mario)
        self.state_manager.set_state(AppState.REVEAL)

        self.controller.undo_last_assignment()

        self.assertTrue(
            self.tracker.is_processed(self.mario)
        )
        self.assertEqual(self.tracker.processed_count, 1)

    def test_reset_is_blocked_while_application_is_busy(self):
        self.tracker.mark_processed(self.mario)
        self.state_manager.set_state(AppState.THINKING)

        self.controller.reset_participant(self.mario)

        self.assertTrue(
            self.tracker.is_processed(self.mario)
        )
        self.assertEqual(self.tracker.processed_count, 1)

    def test_idle_undo_and_reset_update_operator_counters(self):
        self.tracker.mark_processed(self.mario)
        self.tracker.mark_processed(self.luca)
        self.controller._update_tracking_ui()

        self.controller.undo_last_assignment()

        self.assertFalse(
            self.tracker.is_processed(self.luca)
        )
        self.assertEqual(
            self.operator.tracking_status,
            (2, 1, 1),
        )

        self.controller.reset_participant(self.mario)

        self.assertFalse(
            self.tracker.is_processed(self.mario)
        )
        self.assertEqual(
            self.operator.tracking_status,
            (2, 0, 2),
        )


if __name__ == "__main__":
    unittest.main()
