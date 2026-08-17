import logging
from enum import Enum

from PySide6.QtCore import QObject, Signal


logger = logging.getLogger(__name__)


class AppState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    THINKING = "THINKING"
    REVEAL = "REVEAL"


class StateManager(QObject):

    state_changed = Signal(str)

    def __init__(self):
        super().__init__()

        self._state = AppState.IDLE

    @property
    def state(self) -> AppState:
        return self._state

    def set_state(
        self,
        state: AppState,
    ):
        if self._state == state:
            return

        self._state = state

        logger.info("Application state changed: %s", state.value)

        self.state_changed.emit(
            state.value
        )

    def is_idle(self) -> bool:
        return (
            self._state
            == AppState.IDLE
        )

    def is_busy(self) -> bool:
        return (
            self._state
            != AppState.IDLE
        )
