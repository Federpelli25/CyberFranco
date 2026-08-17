import string

import numpy as np

from faster_whisper import WhisperModel


class SpeechToText:

    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "it",
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language

        print(
            f"Caricamento modello Whisper '{model_size}'..."
        )

        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )

        print(
            "Modello Whisper caricato."
        )

    def transcribe(
        self,
        audio: np.ndarray,
        hotwords: str | None = None,
    ) -> str:

        if audio is None:
            print(
                "Audio non disponibile."
            )
            return ""

        if len(audio) == 0:
            print(
                "Audio vuoto."
            )
            return ""

        audio = np.asarray(
            audio,
            dtype=np.float32,
        ).reshape(-1)

        peak_before = float(
            np.max(
                np.abs(audio)
            )
        )

        rms_before = float(
            np.sqrt(
                np.mean(
                    np.square(audio)
                )
            )
        )

        print(
            "Audio ricevuto da Whisper:"
        )

        print(
            f"- campioni: {len(audio)}"
        )

        print(
            f"- peak originale: "
            f"{peak_before:.6f}"
        )

        print(
            f"- RMS originale: "
            f"{rms_before:.6f}"
        )

        audio = self._normalize_audio(
            audio
        )

        peak_after = float(
            np.max(
                np.abs(audio)
            )
        )

        print(
            f"- peak normalizzato: "
            f"{peak_after:.6f}"
        )

        initial_prompt = (
            "Verrà pronunciato solamente "
            "il nome e il cognome di una persona italiana."
        )

        segments, info = self.model.transcribe(
            audio,
            language=self.language,
            task="transcribe",
            beam_size=5,
            temperature=0.0,
            vad_filter=True,
            vad_parameters={
                "threshold": 0.35,
                "min_speech_duration_ms": 150,
                "min_silence_duration_ms": 250,
            },
            condition_on_previous_text=False,
            initial_prompt=initial_prompt,
            hotwords=hotwords,
        )

        text_parts = []

        for segment in segments:
            text = segment.text.strip()

            print(
                f"Segmento Whisper: "
                f"{segment.start:.2f}s - "
                f"{segment.end:.2f}s -> "
                f"'{text}'"
            )

            if text:
                text_parts.append(
                    text
                )

        transcription = " ".join(
            text_parts
        ).strip()

        return self._clean_transcription(
            transcription
        )

    @staticmethod
    def _normalize_audio(
        audio: np.ndarray,
    ) -> np.ndarray:

        peak = np.max(
            np.abs(audio)
        )

        if peak <= 0:
            return audio

        target_peak = 0.90

        normalized = (
            audio / peak
        ) * target_peak

        normalized = np.clip(
            normalized,
            -1.0,
            1.0,
        )

        return normalized.astype(
            np.float32
        )

    @staticmethod
    def _clean_transcription(
        text: str,
    ) -> str:

        if not text:
            return ""

        text = text.strip()

        text = text.strip(
            string.punctuation
        )

        text = " ".join(
            text.split()
        )

        return text