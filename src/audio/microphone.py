import logging
from typing import Any

import numpy as np
import sounddevice as sd

from src.core.exceptions import AudioDeviceError


logger = logging.getLogger(__name__)


class MicrophoneError(AudioDeviceError):
    """Errore di acquisizione audio leggibile dall'operatore."""


class MicrophoneRecorder:

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        device: int | None = None,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.last_device_info: dict[str, Any] | None = None

    def get_device_info(self) -> dict[str, Any]:
        try:
            info = sd.query_devices(
                self.device,
                kind="input",
            )
        except Exception as exc:
            logger.exception("Unable to query selected microphone")
            raise MicrophoneError(
                "Microfono non disponibile. "
                "Seleziona un altro dispositivo."
            ) from exc

        max_input_channels = int(
            info.get("max_input_channels", 0)
        )

        if max_input_channels <= 0:
            raise MicrophoneError(
                "Il dispositivo selezionato non supporta "
                "l'acquisizione audio."
            )

        if self.channels > max_input_channels:
            raise MicrophoneError(
                "Il microfono selezionato non supporta "
                f"{self.channels} canali di input."
            )

        self.last_device_info = {
            "id": self._resolved_device_id(),
            "name": str(info.get("name", "Microfono sconosciuto")),
            "max_input_channels": max_input_channels,
            "default_samplerate": float(
                info.get("default_samplerate", 0.0)
            ),
        }

        return dict(self.last_device_info)

    def get_last_device_info(self) -> dict[str, Any] | None:
        if self.last_device_info is None:
            return None

        return dict(self.last_device_info)

    def _resolved_device_id(self) -> int | None:
        if self.device is not None:
            return self.device

        try:
            default_device = sd.default.device
            return int(default_device[0])
        except (IndexError, TypeError, ValueError):
            return None

    def record(
        self,
        duration_seconds: float,
    ) -> np.ndarray:
        if duration_seconds <= 0:
            raise ValueError(
                "La durata della registrazione deve essere "
                "maggiore di zero."
            )

        device_info = self.get_device_info()
        frames = int(duration_seconds * self.sample_rate)

        logger.info(
            "Recording started: device=%s duration=%.1fs",
            device_info["name"],
            duration_seconds,
        )

        try:
            audio = sd.rec(
                frames,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                blocking=True,
                device=self.device,
            )
        except Exception as exc:
            logger.exception("Microphone recording failed")
            raise MicrophoneError(
                "Microfono non disponibile o acquisizione fallita. "
                "Seleziona un altro dispositivo e aggiorna la lista."
            ) from exc

        logger.info("Recording completed: frames=%d", frames)
        audio = np.asarray(audio, dtype=np.float32)

        if self.channels == 1:
            audio = audio.reshape(-1)

        return audio
