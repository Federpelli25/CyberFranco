import unittest
from unittest.mock import patch

import numpy as np

from src.audio.microphone import MicrophoneRecorder


class MicrophoneSettingsTests(unittest.TestCase):

    @patch("src.audio.microphone.sd.rec")
    def test_configured_device_is_passed_to_sounddevice(
        self,
        record_mock,
    ):
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


if __name__ == "__main__":
    unittest.main()
