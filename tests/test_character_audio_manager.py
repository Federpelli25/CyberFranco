import json
import os
import random
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import QApplication

from src.audio.character_audio_manager import CharacterAudioManager


class FakeDevice:
    def __init__(self, identifier=b"device-1", name="Speakers", null=False):
        self._identifier = identifier
        self._name = name
        self._null = null

    def id(self):
        return self._identifier

    def description(self):
        return self._name

    def isNull(self):
        return self._null


class FakeMediaDevices(QObject):
    audioOutputsChanged = Signal()
    devices = [FakeDevice()]

    @classmethod
    def audioOutputs(cls):
        return cls.devices

    @classmethod
    def defaultAudioOutput(cls):
        return cls.devices[0] if cls.devices else FakeDevice(null=True)


class FakeOutput:
    def __init__(self):
        self._volume = 1.0
        self._device = FakeDevice(null=True)

    def setVolume(self, value):
        self._volume = value

    def volume(self):
        return self._volume

    def setDevice(self, device):
        self._device = device

    def device(self):
        return self._device


class FakePlayer(QObject):
    playbackStateChanged = Signal(object)
    mediaStatusChanged = Signal(object)
    errorOccurred = Signal(object, str)

    def __init__(self):
        super().__init__()
        self.source = None
        self.play_calls = 0
        self.stop_calls = 0

    def setAudioOutput(self, output):
        self.output = output

    def setSource(self, source):
        self.source = source

    def play(self):
        self.play_calls += 1
        self.playbackStateChanged.emit(QMediaPlayer.PlayingState)

    def stop(self):
        self.stop_calls += 1
        self.playbackStateChanged.emit(QMediaPlayer.StoppedState)


class CharacterAudioManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        for name in ("thinking", "awaiting", "reveal", "system"):
            (self.root / "assets" / "audio" / name).mkdir(parents=True)
        (self.root / "config").mkdir()
        (self.root / "config" / "teams.json").write_text(
            json.dumps({"BLU": {
                "slug": "blu", "display_name": "Blu",
                "audio": "assets/audio/reveal/blu.wav"
            }}),
            encoding="utf-8",
        )
        self.player = FakePlayer()
        self.output = FakeOutput()
        self.devices = FakeMediaDevices()
        self.manager = CharacterAudioManager(
            self.root,
            player=self.player,
            audio_output=self.output,
            media_devices=self.devices,
            random_source=random.Random(2),
        )

    def tearDown(self):
        self.temporary.cleanup()

    def _touch(self, relative):
        path = self.root / relative
        path.write_bytes(b"RIFF-test")
        return path

    def test_play_emits_started_and_stop_emits_finished_without_overlap(self):
        clip = self._touch("assets/audio/system/test.wav")
        events = []
        self.manager.started.connect(lambda: events.append("started"))
        self.manager.finished.connect(lambda: events.append("finished"))
        self.assertTrue(self.manager.play(clip))
        self.assertTrue(self.manager.is_playing)
        self.assertTrue(self.manager.play(clip))
        self.assertEqual(events, ["started", "finished", "started"])
        self.manager.stop()
        self.assertFalse(self.manager.is_playing)

    def test_disabled_and_missing_files_fail_safely(self):
        failures = []
        self.manager.failed.connect(failures.append)
        self.manager.set_enabled(False)
        self.assertFalse(self.manager.play("missing.wav"))
        self.manager.set_enabled(True)
        self.assertFalse(self.manager.play("missing.wav"))
        self.assertTrue(failures)

    def test_volume_and_output_device(self):
        self.manager.set_volume(0.25)
        self.assertEqual(self.manager.volume, 0.25)
        self.assertTrue(self.manager.select_output_device(b"device-1".hex()))
        self.assertEqual(self.manager.output_device_id, b"device-1".hex())

    def test_thinking_does_not_repeat_immediately(self):
        first = self._touch("assets/audio/thinking/one.wav")
        second = self._touch("assets/audio/thinking/two.wav")
        self.assertTrue(self.manager.play_thinking())
        selected_first = self.player.source.toLocalFile()
        self.assertTrue(self.manager.play_thinking())
        selected_second = self.player.source.toLocalFile()
        self.assertNotEqual(selected_first, selected_second)
        self.assertIn(Path(selected_first), (first, second))

    def test_reveal_uses_team_mapping(self):
        clip = self._touch("assets/audio/reveal/blu.wav")
        self.assertTrue(self.manager.play_reveal("blu"))
        self.assertEqual(Path(self.player.source.toLocalFile()), clip)

    def test_missing_reveal_stops_previous_thinking_clip(self):
        self._touch("assets/audio/thinking/one.wav")
        self.assertTrue(self.manager.play_thinking())
        self.assertTrue(self.manager.is_playing)
        self.assertFalse(self.manager.play_reveal("INESISTENTE"))
        self.assertFalse(self.manager.is_playing)

    def test_missing_saved_output_falls_back_to_default(self):
        warnings = []
        self.manager.warning.connect(warnings.append)
        self.assertFalse(self.manager.select_output_device("missing"))
        self.assertIsNone(self.manager.output_device_id)
        self.assertTrue(warnings)

    def test_test_audio_missing_emits_failure(self):
        failures = []
        self.manager.failed.connect(failures.append)
        self.assertFalse(self.manager.play_test())
        self.assertEqual(failures, ["TRACCIA TEST AUDIO NON DISPONIBILE"])


if __name__ == "__main__":
    unittest.main()
