import logging

import numpy as np
from PySide6.QtCore import QObject, Signal, Slot

from src.audio.microphone import MicrophoneRecorder


logger = logging.getLogger(__name__)


class MicrophoneTestWorker(QObject):
    completed = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        microphone_device: int | None,
        duration_seconds: float = 2.0,
    ):
        super().__init__()
        self.duration_seconds = duration_seconds
        self.recorder = MicrophoneRecorder(
            sample_rate=16000,
            channels=1,
            device=microphone_device,
        )

    @Slot()
    def run(self):
        logger.info("Microphone test started")
        try:
            audio = self.recorder.record(
                self.duration_seconds
            )
            result = self.analyze_audio(audio)

            logger.info(
                "Microphone test result: status=%s peak=%.6f rms=%.6f",
                result["status"],
                result["peak"],
                result["rms"],
            )
            self.completed.emit(result)
        except Exception as exc:
            logger.exception("Microphone test failed")
            self.failed.emit(str(exc))

    @staticmethod
    def analyze_audio(audio: np.ndarray) -> dict:
        audio = np.asarray(audio, dtype=np.float32)

        if audio.size == 0:
            raise ValueError(
                "Il test microfono non ha acquisito campioni."
            )

        peak = float(np.max(np.abs(audio)))
        rms = float(
            np.sqrt(np.mean(np.square(audio)))
        )

        if rms < 0.001:
            status = "Nessun segnale rilevato"
        elif rms < 0.005:
            status = "Segnale molto basso"
        else:
            status = "Microfono OK"

        return {
            "status": status,
            "peak": peak,
            "rms": rms,
        }
