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
from src.core.exceptions import SessionError


logger = logging.getLogger(__name__)


class SortingController(QObject):

    def __init__(
        self,
        operator_window,
        public_window,
        state_manager: StateManager,
        participant_tracker: ParticipantTracker,
        settings: AppSettings,
        session_repository=None,
        session_context: dict | None = None,
        session_blocked: bool = False,
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
        self.session_repository = session_repository
        self.session_context = session_context
        self.session_blocked = session_blocked

        self.current_participant = None
        self._flow_token = 0

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
            self.recover_to_idle
        )

        self.operator_window.undo_last_requested.connect(
            self.undo_last_assignment
        )

        self.operator_window.reset_participant_requested.connect(
            self.reset_participant
        )

        self.operator_window.new_event_requested.connect(
            self.start_new_event
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
        self.recover_to_idle()

    def recover_to_idle(self, message: str | None = None):
        """Invalida il flusso corrente e ripristina una UI utilizzabile."""
        previous_state = self.state_manager.state
        self._flow_token += 1
        self.current_participant = None
        self.state_manager.set_state(AppState.IDLE)

        try:
            self.public_window.show_idle()
        except Exception:
            logger.exception("Public display recovery failed")

        self.operator_window.set_processing(False)
        if message:
            self.operator_window.show_error(message)

        logger.warning(
            "Application recovered to IDLE: previous_state=%s message=%s",
            previous_state.value,
            message or "-",
        )

    def start_sorting(
        self,
        participant: dict,
    ):
        if self.session_blocked:
            self.operator_window.show_warning(
                "SESSIONE NON COMPATIBILE — AVVIA UN NUOVO EVENTO"
            )
            return

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
        self._flow_token += 1
        flow_token = self._flow_token
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

        try:
            self.public_window.show_thinking()
        except Exception:
            logger.exception("Thinking display failed")
            self.recover_to_idle("ERRORE DISPLAY PUBBLICO")
            return
        logger.info("Thinking started")

        QTimer.singleShot(
            self.settings.thinking_duration_ms,
            lambda: self._start_reveal(flow_token),
        )

    def _start_reveal(self, flow_token: int | None = None):
        if (
            self.current_participant is None
            or self.state_manager.state != AppState.THINKING
            or (
                flow_token is not None
                and flow_token != self._flow_token
            )
        ):
            logger.warning("Stale reveal callback ignored")
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

        try:
            self.public_window.show_team(
                participant["nome_completo"],
                participant["squadra"],
            )
        except Exception:
            logger.exception("Team reveal failed")
            self.recover_to_idle("ERRORE DISPLAY PUBBLICO")

    def _finish_sorting(self):
        if self.current_participant is None:
            return

        participant = (
            self.current_participant
        )

        try:
            self.participant_tracker.mark_processed(participant)
        except Exception:
            logger.exception("Unable to complete participant assignment")
            self.recover_to_idle("ERRORE ASSEGNAZIONE")
            return
        logger.info(
            "Assignment completed: %s; team=%s",
            participant["nome_completo"],
            participant["squadra"],
        )

        self.current_participant = None
        self._flow_token += 1

        self._update_tracking_ui()

        self.state_manager.set_state(
            AppState.IDLE
        )

        self.operator_window.set_processing(
            False
        )

        self.operator_window.reset_for_next_participant()
        self._persist_session("Participant assignment persisted")

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
        if self._persist_session("Undo persisted"):
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
        if self._persist_session("Participant reset persisted"):
            self.operator_window.show_tracking_message(
                "RESET PARTECIPANTE: "
                f"{participant['nome_completo']}"
            )

    def start_new_event(self):
        if not self.state_manager.is_idle():
            return
        self.participant_tracker.reset_all()
        self.session_blocked = False
        self._update_tracking_ui()
        if self._persist_session("New event started"):
            self.operator_window.show_tracking_message(
                "NUOVO EVENTO AVVIATO — COMPLETATI: 0"
            )
        logger.info("New event started")

    def _persist_session(self, event: str) -> bool:
        if self.session_repository is None or self.session_context is None:
            return True
        self.session_context["processed"] = (
            self.participant_tracker.export_state()
        )
        try:
            self.session_repository.save(self.session_context)
        except SessionError:
            logger.exception("Session persistence failed: %s", event)
            self.operator_window.show_warning(
                "SESSIONE NON SALVATA — RIPROVA PRIMA DI CHIUDERE"
            )
            return False
        logger.info(event)
        return True

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
