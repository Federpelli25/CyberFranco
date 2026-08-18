"""Orchestrazione non bloccante delle fasi del reveal pubblico."""

import logging
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QObject, QTimer, Signal


logger = logging.getLogger(__name__)


class RevealPhase(str, Enum):
    PRE_REVEAL = "PRE_REVEAL"
    FLASH_IN = "FLASH_IN"
    TEAM_APPEAR = "TEAM_APPEAR"
    HOLD = "HOLD"
    FADE_OUT = "FADE_OUT"


@dataclass(frozen=True)
class RevealTimings:
    pre_reveal_ms: int = 500
    flash_ms: int = 180
    appear_ms: int = 500
    hold_ms: int = 2200
    fade_ms: int = 500


class RevealController(QObject):
    """Esegue la sequenza visuale senza conoscere o scegliere la squadra."""

    phase_changed = Signal(object)
    completed = Signal()
    aborted = Signal()

    def __init__(self, timings: RevealTimings | None = None, parent=None):
        super().__init__(parent)
        self.timings = timings or RevealTimings()
        self._generation = 0
        self._active = False

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def active(self) -> bool:
        return self._active

    def start(self) -> int:
        self.abort(emit_signal=False)
        self._active = True
        token = self._generation
        logger.info("Pre-reveal started")
        self._emit_phase(token, RevealPhase.PRE_REVEAL)
        self._schedule(token, self.timings.pre_reveal_ms, RevealPhase.FLASH_IN)
        return token

    def abort(self, emit_signal: bool = True) -> None:
        was_active = self._active
        self._generation += 1
        self._active = False
        if was_active:
            logger.info("Reveal aborted")
            if emit_signal:
                self.aborted.emit()

    def complete_now(self) -> None:
        if not self._active:
            return
        self._finish(self._generation)

    def _schedule(self, token: int, delay: int, phase: RevealPhase) -> None:
        QTimer.singleShot(delay, lambda: self._advance(token, phase))

    def _advance(self, token: int, phase: RevealPhase) -> None:
        if token != self._generation or not self._active:
            logger.debug("Stale reveal callback ignored: phase=%s", phase.value)
            return
        self._emit_phase(token, phase)
        delays = {
            RevealPhase.FLASH_IN: self.timings.flash_ms,
            RevealPhase.TEAM_APPEAR: self.timings.appear_ms,
            RevealPhase.HOLD: self.timings.hold_ms,
            RevealPhase.FADE_OUT: self.timings.fade_ms,
        }
        next_phases = {
            RevealPhase.FLASH_IN: RevealPhase.TEAM_APPEAR,
            RevealPhase.TEAM_APPEAR: RevealPhase.HOLD,
            RevealPhase.HOLD: RevealPhase.FADE_OUT,
        }
        if phase == RevealPhase.FADE_OUT:
            QTimer.singleShot(delays[phase], lambda: self._finish(token))
        else:
            self._schedule(token, delays[phase], next_phases[phase])

    def _emit_phase(self, token: int, phase: RevealPhase) -> None:
        if token == self._generation and self._active:
            self.phase_changed.emit(phase)

    def _finish(self, token: int) -> None:
        if token != self._generation or not self._active:
            return
        self._active = False
        logger.info("Reveal completed")
        self.completed.emit()
