import unittest

import numpy as np

from src.audio.microphone_test_worker import MicrophoneTestWorker


class MicrophoneTestWorkerTests(unittest.TestCase):

    def test_no_signal_threshold(self):
        result = MicrophoneTestWorker.analyze_audio(
            np.zeros(1000, dtype=np.float32)
        )
        self.assertEqual(
            result["status"],
            "Nessun segnale rilevato",
        )

    def test_low_signal_threshold(self):
        result = MicrophoneTestWorker.analyze_audio(
            np.full(1000, 0.002, dtype=np.float32)
        )
        self.assertEqual(
            result["status"],
            "Segnale molto basso",
        )

    def test_present_signal_threshold(self):
        result = MicrophoneTestWorker.analyze_audio(
            np.full(1000, 0.01, dtype=np.float32)
        )
        self.assertEqual(result["status"], "Microfono OK")
        self.assertAlmostEqual(result["peak"], 0.01, places=5)
        self.assertAlmostEqual(result["rms"], 0.01, places=5)

    def test_empty_audio_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "non ha acquisito campioni",
        ):
            MicrophoneTestWorker.analyze_audio(
                np.array([], dtype=np.float32)
            )
