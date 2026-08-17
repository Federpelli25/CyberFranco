from PySide6.QtCore import (
    QObject,
    QTimer,
)

from src.core.state_manager import (
    AppState,
    StateManager,
)


class SortingController(QObject):

    THINKING_DURATION_MS = 1200

    def __init__(
        self,
        operator_window,
        public_window,
        state_manager: StateManager,
    ):
        super().__init__()

        self.operator_window = operator_window
        self.public_window = public_window
        self.state_manager = state_manager

        self.current_participant = None

        self._connect_events()

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

        self.public_window.reveal_finished.connect(
            self._finish_sorting
        )

    def _start_listening(self):
        if not self.state_manager.is_idle():
            return

        self.state_manager.set_state(
            AppState.LISTENING
        )

        self.public_window.show_listening()

    def _await_confirmation(self):
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
            print(
                "Assegnazione ignorata: "
                "applicazione occupata."
            )

            return

        self.current_participant = (
            participant
        )

        print(
            f"INIZIO ASSEGNAZIONE: "
            f"{participant['nome_completo']}"
        )

        self.operator_window.set_processing(
            True
        )

        self.state_manager.set_state(
            AppState.THINKING
        )

        self.public_window.show_thinking()

        QTimer.singleShot(
            self.THINKING_DURATION_MS,
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

        self.public_window.show_team(
            participant["nome_completo"],
            participant["squadra"],
        )

    def _finish_sorting(self):
        if self.current_participant is not None:
            print(
                f"ASSEGNAZIONE COMPLETATA: "
                f"{self.current_participant['nome_completo']} "
                f"-> "
                f"{self.current_participant['squadra']}"
            )

        self.current_participant = None

        self.state_manager.set_state(
            AppState.IDLE
        )

        self.operator_window.set_processing(
            False
        )

        self.operator_window.reset_for_next_participant()