import numpy as np
import sounddevice as sd


class MicrophoneRecorder:

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        device: int | str | None = None,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device

    def record(
        self,
        duration_seconds: float,
    ) -> np.ndarray:

        if duration_seconds <= 0:
            raise ValueError(
                "La durata della registrazione deve essere maggiore di zero."
            )

        frames = int(
            duration_seconds * self.sample_rate
        )

        print(
            f"Registrazione avviata "
            f"({duration_seconds:.1f} secondi)..."
        )

        audio = sd.rec(
            frames,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            blocking=True,
            device=self.device,
        )

        print("Registrazione completata.")

        if self.channels == 1:
            audio = audio.reshape(-1)

        return audio
