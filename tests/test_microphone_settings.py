import unittest
from unittest.mock import patch

import numpy as np

from src.audio.microphone import (
    MicrophoneError,
    MicrophoneRecorder,
)
from src.audio.voice_recognition_worker import (
    VoiceRecognitionWorker,
)


class MicrophoneSettingsTests(unittest.TestCase):

    def test_voice_worker_uses_selected_device(self):
        worker = VoiceRecognitionWorker(
            speech_to_text=object(),
            hotwords="Mario Rossi",
            microphone_device=12,
        )

        self.assertEqual(worker.recorder.device, 12)

    @patch("src.audio.microphone.sd.query_devices")
    @patch("src.audio.microphone.sd.rec")
    def test_configured_device_is_passed_to_sounddevice(
        self,
        record_mock,
        query_devices_mock,
    ):
        query_devices_mock.return_value = {
            "name": "USB Microphone",
            "max_input_channels": 1,
            "default_samplerate": 48000.0,
        }
        record_mock.return_value = np.zeros(
            (16000, 1),
            dtype=np.float32,
        )
        recorder = MicrophoneRecorder(
            sample_rate=16000,
            channels=1,
            device=3,
        )

        audio = recorder.record(1.0)

        record_mock.assert_called_once_with(
            16000,
            samplerate=16000,
            channels=1,
            dtype="float32",
            blocking=True,
            device=3,
        )
        self.assertEqual(audio.shape, (16000,))
        self.assertEqual(
            recorder.get_last_device_info()["id"],
            3,
        )
        self.assertEqual(
            recorder.get_last_device_info()["name"],
            "USB Microphone",
        )

    @patch("src.audio.microphone.sd.query_devices")
    def test_missing_device_has_readable_error(
        self,
        query_devices_mock,
    ):
        query_devices_mock.side_effect = RuntimeError(
            "Invalid device"
        )
        recorder = MicrophoneRecorder(device=99)

        with self.assertRaisesRegex(
            MicrophoneError,
            "Microfono non disponibile",
        ):
            recorder.record(1.0)

    @patch("src.audio.microphone.sd.query_devices")
    def test_output_only_device_is_rejected(
        self,
        query_devices_mock,
    ):
        query_devices_mock.return_value = {
            "name": "Speakers",
            "max_input_channels": 0,
            "default_samplerate": 48000.0,
        }
        recorder = MicrophoneRecorder(device=4)

        with self.assertRaisesRegex(
            MicrophoneError,
            "non supporta l'acquisizione",
        ):
            recorder.record(1.0)


if __name__ == "__main__":
    unittest.main()
