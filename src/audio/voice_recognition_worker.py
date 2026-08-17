from PySide6.QtCore import QObject, Signal, Slot

from src.audio.microphone import MicrophoneRecorder
from src.audio.speech_to_text import SpeechToText


class VoiceRecognitionWorker(QObject):

    completed = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        speech_to_text: SpeechToText,
        hotwords: str,
        duration_seconds: float = 4.0,
        microphone_device: int | None = None,
    ):
        super().__init__()

        self.speech_to_text = speech_to_text
        self.hotwords = hotwords
        self.duration_seconds = duration_seconds

        self.recorder = MicrophoneRecorder(
            sample_rate=16000,
            channels=1,
            device=microphone_device,
        )

    @Slot()
    def run(self):
        try:
            audio = self.recorder.record(
                duration_seconds=self.duration_seconds
            )

            transcription = (
                self.speech_to_text.transcribe(
                    audio,
                    hotwords=self.hotwords,
                )
            )

            self.completed.emit(
                transcription
            )

        except Exception as exc:
            self.failed.emit(
                str(exc)
            )
