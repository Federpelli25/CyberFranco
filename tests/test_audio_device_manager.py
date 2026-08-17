import unittest
from unittest.mock import patch

from src.audio.audio_device_manager import (
    AudioDeviceError,
    AudioDeviceManager,
)


DEVICES = [
    {
        "name": "Speakers",
        "max_input_channels": 0,
        "default_samplerate": 48000.0,
        "hostapi": 0,
    },
    {
        "name": "Microphone Array",
        "max_input_channels": 2,
        "default_samplerate": 48000.0,
        "hostapi": 1,
    },
    {
        "name": "USB Microphone",
        "max_input_channels": 1,
        "default_samplerate": 44100.0,
        "hostapi": 0,
    },
]

HOST_APIS = [
    {"name": "MME"},
    {"name": "Windows WASAPI"},
]


class AudioDeviceManagerTests(unittest.TestCase):

    def setUp(self):
        self.manager = AudioDeviceManager()

    @patch("src.audio.audio_device_manager.sd.query_hostapis")
    @patch("src.audio.audio_device_manager.sd.query_devices")
    def test_list_returns_only_input_devices(
        self,
        query_devices_mock,
        query_hostapis_mock,
    ):
        query_devices_mock.return_value = DEVICES
        query_hostapis_mock.return_value = HOST_APIS

        devices = self.manager.list_input_devices()

        self.assertEqual([device["id"] for device in devices], [1, 2])
        self.assertTrue(
            all(device["max_input_channels"] > 0 for device in devices)
        )
        self.assertEqual(devices[0]["hostapi"], "Windows WASAPI")

    @patch("src.audio.audio_device_manager.sd.query_hostapis")
    @patch("src.audio.audio_device_manager.sd.query_devices")
    def test_get_device_and_missing_id(
        self,
        query_devices_mock,
        query_hostapis_mock,
    ):
        query_devices_mock.return_value = DEVICES
        query_hostapis_mock.return_value = HOST_APIS

        self.assertEqual(self.manager.get_device(2)["name"], "USB Microphone")
        self.assertIsNone(self.manager.get_device(99))
        self.assertFalse(self.manager.is_device_available(99))

    @patch("src.audio.audio_device_manager.sd.default")
    @patch("src.audio.audio_device_manager.sd.query_hostapis")
    @patch("src.audio.audio_device_manager.sd.query_devices")
    def test_default_input_device_is_resolved(
        self,
        query_devices_mock,
        query_hostapis_mock,
        default_mock,
    ):
        query_devices_mock.return_value = DEVICES
        query_hostapis_mock.return_value = HOST_APIS
        default_mock.device = (1, 0)

        device = self.manager.get_default_input_device()

        self.assertEqual(device["id"], 1)

    @patch("src.audio.audio_device_manager.sd.default")
    def test_missing_default_is_handled(self, default_mock):
        default_mock.device = (-1, 0)

        self.assertIsNone(
            self.manager.get_default_input_device()
        )

    @patch("src.audio.audio_device_manager.sd.query_devices")
    def test_portaudio_error_is_readable(self, query_devices_mock):
        query_devices_mock.side_effect = RuntimeError(
            "PortAudio unavailable"
        )

        with self.assertRaisesRegex(
            AudioDeviceError,
            "Impossibile leggere",
        ):
            self.manager.list_input_devices()

    def test_display_name_contains_host_api(self):
        label = self.manager.format_device_name(
            {
                "name": "Microphone Array",
                "hostapi": "Windows WASAPI",
            }
        )

        self.assertIn("Microphone Array", label)
        self.assertIn("Windows WASAPI", label)
