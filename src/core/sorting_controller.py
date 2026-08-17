import logging

from PySide6.QtCore import (
    QObject,
    QTimer,
)

from src.core.participant_tracker import (
    ParticipantTracker,
)
from src.core.state_manager import (
    AppState,
    StateManager,
)
from src.config.settings_loader import AppSettings


logger = logging.getLogger(__name__)


class SortingController(QObject):

    def __init__(
        self,
        operator_window,
        public_window,
        state_manager: StateManager,
        participant_tracker: ParticipantTracker,
        settings: AppSettings,
    ):
        super().__init__()

        self.operator_window = (
            operator_window
        )

        self.public_window = (
            public_window
        )

        self.state_manager = (
            state_manager
        )

        self.participant_tracker = (
            participant_tracker
        )

        self.settings = settings

        self.current_participant = None

        self._connect_events()
        self._update_tracking_ui()

    def _connect_events(self):
        self.operator_window.participant_confirmed.connect(
            self.start_sorting
        )

        self.operator_window.listening_started.connect(
            self._start_listening
        )

        self.operator_window.listening_ambiguous.connect(
            self._await_confirmation
        )

        self.operator_window.listening_failed.connect(
            self._return_to_idle
        )

        self.operator_window.undo_last_requested.connect(
            self.undo_last_assignment
        )

        self.operator_window.reset_participant_requested.connect(
            self.reset_participant
        )

        self.public_window.reveal_finished.connect(
            self._finish_sorting
        )

    def _start_listening(self):
        if not self.state_manager.is_idle():
            return

        self.state_manager.set_state(
            AppState.LISTENING
        )
        logger.info("Listening started")

        self.public_window.show_listening()

    def _await_confirmation(self):
        logger.warning("Match ambiguous; awaiting operator confirmation")
        self.state_manager.set_state(
            AppState.AWAITING_CONFIRMATION
        )

        self.public_window.show_waiting_confirmation()

    def _return_to_idle(self):
        self.state_manager.set_state(
            AppState.IDLE
        )

        self.public_window.show_idle()

    def start_sorting(
        self,
        participant: dict,
    ):
        allowed_states = {
            AppState.IDLE,
            AppState.LISTENING,
            AppState.AWAITING_CONFIRMATION,
        }

        if (
            self.state_manager.state
            not in allowed_states
        ):
            return

        if self.participant_tracker.is_processed(
            participant
        ):
            logger.warning(
                "Participant already processed: %s",
                participant["search_name"],
            )
            self.state_manager.set_state(
                AppState.IDLE
            )

            self.public_window.show_idle()

            self.operator_window.show_already_processed(
                participant
            )

            return

        self.current_participant = (
            participant
        )
        logger.info(
            "Participant confirmed: %s",
            participant["nome_completo"],
        )

        self.operator_window.set_processing(
            True
        )

        self.state_manager.set_state(
            AppState.THINKING
        )

        self.public_window.show_thinking()
        logger.info("Thinking started")

        QTimer.singleShot(
            self.settings.thinking_duration_ms,
            self._start_reveal,
        )

    def _start_reveal(self):
        if self.current_participant is None:
            return

        participant = (
            self.current_participant
        )

        self.state_manager.set_state(
            AppState.REVEAL
        )
        logger.info(
            "Reveal started: team=%s",
            participant["squadra"],
        )

        self.public_window.show_team(
            participant["nome_completo"],
            participant["squadra"],
        )

    def _finish_sorting(self):
        if self.current_participant is None:
            return

        participant = (
            self.current_participant
        )

        self.participant_tracker.mark_processed(
            participant
        )
        logger.info(
            "Assignment completed: %s; team=%s",
            participant["nome_completo"],
            participant["squadra"],
        )

        self.current_participant = None

        self._update_tracking_ui()

        self.state_manager.set_state(
            AppState.IDLE
        )

        self.operator_window.set_processing(
            False
        )

        self.operator_window.reset_for_next_participant()

    def undo_last_assignment(self):
        if not self.state_manager.is_idle():
            return

        participant = (
            self.participant_tracker.undo_last()
        )

        if participant is None:
            self.operator_window.show_tracking_message(
                "NESSUNA ASSEGNAZIONE DA ANNULLARE"
            )

            return

        self._update_tracking_ui()

        self.operator_window.show_tracking_message(
            "ANNULLATA ULTIMA ASSEGNAZIONE: "
            f"{participant['nome_completo']}"
        )

    def reset_participant(
        self,
        participant: dict,
    ):
        if not self.state_manager.is_idle():
            return

        was_reset = (
            self.participant_tracker
            .reset_participant(participant)
        )

        if not was_reset:
            self.operator_window.show_tracking_message(
                "IL PARTECIPANTE NON RISULTA COMPLETATO: "
                f"{participant['nome_completo']}"
            )

            return

        self._update_tracking_ui()

        self.operator_window.show_tracking_message(
            "RESET PARTECIPANTE: "
            f"{participant['nome_completo']}"
        )

    def _update_tracking_ui(self):
        self.operator_window.update_tracking_status(
            total=(
                self.participant_tracker
                .total_count
            ),
            processed=(
                self.participant_tracker
                .processed_count
            ),
            remaining=(
                self.participant_tracker
                .remaining_count
            ),
        )

        self.operator_window.update_processed_list(
            self.participant_tracker
            .get_processed_participants()
        )
