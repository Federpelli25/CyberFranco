import logging
import string
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel


logger = logging.getLogger(__name__)


class SpeechModelError(RuntimeError):
    """Errore leggibile relativo al modello Whisper locale."""


class SpeechToText:
    REQUIRED_MODEL_FILES = (
        "model.bin",
        "config.json",
        "tokenizer.json",
    )

    def __init__(
        self,
        model_path: str | Path,
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "it",
    ):
        self.model_path = self.validate_model_path(
            model_path
        )
        self.device = device
        self.compute_type = compute_type
        self.language = language

        logger.info("Whisper model path: %s", self.model_path)
        logger.info("Whisper model loading")

        try:
            self.model = WhisperModel(
                str(self.model_path),
                device=device,
                compute_type=compute_type,
                local_files_only=True,
            )
        except Exception as exc:
            logger.exception("Whisper model loading failed")
            raise SpeechModelError(
                "MODELLO WHISPER NON CARICABILE\n\n"
                "Percorso configurato:\n"
                f"{self.model_path}\n\n"
                f"Dettaglio: {exc}"
            ) from exc

        logger.info("Whisper model loaded")

    @classmethod
    def validate_model_path(
        cls,
        model_path: str | Path,
    ) -> Path:
        path = Path(model_path).expanduser().resolve()

        if not path.exists():
            logger.error("Whisper model path not found: %s", path)
            raise SpeechModelError(
                "MODELLO WHISPER NON TROVATO\n\n"
                "Percorso configurato:\n"
                f"{path}\n\n"
                "Preparare il modello prima di avviare CyberFranco."
            )

        if not path.is_dir():
            logger.error("Whisper model path is not a directory: %s", path)
            raise SpeechModelError(
                "PERCORSO MODELLO WHISPER NON VALIDO\n\n"
                f"'{path}' non è una directory."
            )

        missing_files = [
            file_name
            for file_name in cls.REQUIRED_MODEL_FILES
            if not (path / file_name).is_file()
        ]

        if missing_files:
            missing_text = ", ".join(missing_files)
            logger.error(
                "Whisper model incomplete: path=%s missing=%s",
                path,
                missing_text,
            )
            raise SpeechModelError(
                "MODELLO WHISPER INCOMPLETO\n\n"
                "Percorso configurato:\n"
                f"{path}\n\n"
                f"File mancanti: {missing_text}.\n\n"
                "Eseguire nuovamente lo script di preparazione."
            )

        return path

    def transcribe(
        self,
        audio: np.ndarray,
        hotwords: str | None = None,
    ) -> str:
        if audio is None:
            logger.warning("Transcription skipped: audio unavailable")
            return ""

        if len(audio) == 0:
            logger.warning("Transcription skipped: empty audio")
            return ""

        audio = np.asarray(
            audio,
            dtype=np.float32,
        ).reshape(-1)

        peak_before = float(
            np.max(np.abs(audio))
        )
        rms_before = float(
            np.sqrt(np.mean(np.square(audio)))
        )

        logger.info("Transcription started")
        logger.debug(
            "Audio metrics: samples=%d peak=%.6f rms=%.6f",
            len(audio),
            peak_before,
            rms_before,
        )

        audio = self._normalize_audio(audio)
        peak_after = float(np.max(np.abs(audio)))
        logger.debug("Normalized audio peak: %.6f", peak_after)

        initial_prompt = (
            "Verrà pronunciato solamente il nome e il cognome "
            "di una persona italiana."
        )

        segments, _ = self.model.transcribe(
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
            logger.debug(
                "Whisper segment: %.2fs-%.2fs text=%r",
                segment.start,
                segment.end,
                text,
            )

            if text:
                text_parts.append(text)

        transcription = " ".join(text_parts).strip()
        cleaned_transcription = self._clean_transcription(
            transcription
        )
        logger.info(
            "Transcription completed: characters=%d",
            len(cleaned_transcription),
        )
        return cleaned_transcription

    @staticmethod
    def _normalize_audio(
        audio: np.ndarray,
    ) -> np.ndarray:
        peak = np.max(np.abs(audio))

        if peak <= 0:
            return audio

        normalized = (audio / peak) * 0.90
        normalized = np.clip(normalized, -1.0, 1.0)
        return normalized.astype(np.float32)

    @staticmethod
    def _clean_transcription(text: str) -> str:
        if not text:
            return ""

        text = text.strip().strip(string.punctuation)
        return " ".join(text.split())
