"""Playback locale e non bloccante della voce del personaggio."""

import logging
import random
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import (
    QAudioDevice,
    QAudioOutput,
    QMediaDevices,
    QMediaPlayer,
)


logger = logging.getLogger(__name__)


class CharacterAudioManager(QObject):
    """Gestisce una sola clip locale alla volta e il device di uscita."""

    started = Signal()
    finished = Signal()
    failed = Signal(str)
    devices_changed = Signal()
    warning = Signal(str)

    SUPPORTED_SUFFIXES = {".wav", ".mp3"}

    def __init__(
        self,
        project_root: str | Path,
        enabled: bool = True,
        volume: float = 0.8,
        output_device_id: str | None = None,
        random_source=None,
        player=None,
        audio_output=None,
        media_devices=None,
        team_config_loader=None,
        parent=None,
    ):
        super().__init__(parent)
        self.project_root = Path(project_root)
        self.audio_root = self.project_root / "assets" / "audio"
        self.team_config_loader = team_config_loader
        self.enabled = bool(enabled)
        self._random = random_source or random.Random()
        self._last_thinking: Path | None = None
        self._playing = False
        self._finishing = False
        self._requested_output_device_id = output_device_id
        self.media_devices = media_devices or QMediaDevices(self)
        self.audio_output = audio_output or QAudioOutput(self)
        self.player = player or QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.set_volume(volume)

        self.player.playbackStateChanged.connect(self._on_playback_state)
        self.player.mediaStatusChanged.connect(self._on_media_status)
        self.player.errorOccurred.connect(self._on_error)
        outputs_changed = getattr(self.media_devices, "audioOutputsChanged", None)
        if outputs_changed is not None:
            outputs_changed.connect(self._on_devices_changed)
        self.select_output_device(output_device_id, warn=False)
        logger.info("Character audio enabled: %s", self.enabled)

    @property
    def is_playing(self) -> bool:
        return self._playing

    @property
    def volume(self) -> float:
        return float(self.audio_output.volume())

    @property
    def output_device_id(self) -> str | None:
        return self._requested_output_device_id

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)
        logger.info("Character audio enabled: %s", self.enabled)
        if not self.enabled:
            self.stop()

    def set_volume(self, volume: float) -> None:
        value = float(volume)
        if not 0.0 <= value <= 1.0:
            raise ValueError("Il volume deve essere compreso tra 0 e 1.")
        self.audio_output.setVolume(value)

    @staticmethod
    def device_id(device: QAudioDevice) -> str:
        return bytes(device.id()).hex()

    def list_output_devices(self) -> list[dict]:
        default = self.media_devices.defaultAudioOutput()
        default_id = None if default.isNull() else self.device_id(default)
        return [
            {
                "id": self.device_id(device),
                "name": device.description() or "Uscita audio",
                "default": self.device_id(device) == default_id,
                "device": device,
            }
            for device in self.media_devices.audioOutputs()
        ]

    def select_output_device(
        self, device_id: str | None, warn: bool = True
    ) -> bool:
        devices = self.list_output_devices()
        selected = next(
            (item for item in devices if item["id"] == device_id), None
        )
        fallback = device_id is not None and selected is None
        if selected is None:
            default = self.media_devices.defaultAudioOutput()
            if not default.isNull():
                self.audio_output.setDevice(default)
            self._requested_output_device_id = None
        else:
            self.audio_output.setDevice(selected["device"])
            self._requested_output_device_id = device_id
        if fallback:
            message = (
                "L'uscita audio salvata non è disponibile: "
                "uso il dispositivo predefinito."
            )
            logger.warning(message)
            if warn:
                self.warning.emit(message)
        return not fallback

    def refresh_output_devices(self) -> list[dict]:
        self.select_output_device(self._requested_output_device_id)
        self.devices_changed.emit()
        return self.list_output_devices()

    def play_thinking(self) -> bool:
        clips = self._clips_in(self.audio_root / "thinking")
        if not clips:
            logger.warning("Character audio file missing: thinking")
            return False
        choices = [clip for clip in clips if clip != self._last_thinking]
        clip = self._random.choice(choices or clips)
        self._last_thinking = clip
        logger.info("Playing thinking clip: %s", clip)
        return self.play(clip)

    def play_reveal(self, team: str) -> bool:
        # Il reveal non deve attendere una frase THINKING troppo lunga.
        self.stop()
        path = self._team_audio_path(team)
        if path is None:
            logger.warning("Character audio file missing: reveal team=%s", team)
            return False
        logger.info("Playing reveal clip for team %s: %s", team, path)
        return self.play(path)

    def play_test(self) -> bool:
        clips = self._clips_in(self.audio_root / "system")
        if not clips:
            self._fail("TRACCIA TEST AUDIO NON DISPONIBILE")
            return False
        return self.play(clips[0])

    def play(self, path: str | Path) -> bool:
        if not self.enabled:
            logger.info("Character audio skipped: disabled")
            return False
        clip = Path(path)
        if not clip.is_absolute():
            clip = self.project_root / clip
        if not clip.is_file() or clip.suffix.lower() not in self.SUPPORTED_SUFFIXES:
            self._fail(f"FILE AUDIO NON DISPONIBILE: {clip.name}")
            return False
        self.stop()
        self._finishing = False
        self.player.setSource(QUrl.fromLocalFile(str(clip.resolve())))
        self.player.play()
        return True

    def stop(self) -> None:
        was_playing = self._playing
        self._playing = False
        self._finishing = True
        self.player.stop()
        if was_playing:
            self.finished.emit()
        self._finishing = False

    def _clips_in(self, directory: Path) -> list[Path]:
        if not directory.is_dir():
            return []
        return sorted(
            path for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in self.SUPPORTED_SUFFIXES
        )

    def _team_audio_path(self, team: str) -> Path | None:
        if self.team_config_loader is not None:
            return self.team_config_loader.resolve(team).audio_path
        config_path = self.project_root / "config" / "teams.json"
        try:
            from src.config.team_config_loader import TeamConfigLoader

            loader = TeamConfigLoader(self.project_root, config_path)
            return loader.resolve(team).audio_path
        except Exception:
            logger.exception("Team audio mapping unavailable: %s", config_path)
            return None

    def _on_playback_state(self, state) -> None:
        if state == QMediaPlayer.PlayingState and not self._playing:
            self._playing = True
            self.started.emit()
        elif (
            state == QMediaPlayer.StoppedState
            and self._playing
            and not self._finishing
        ):
            self._playing = False
            logger.info("Character audio finished")
            self.finished.emit()

    def _on_media_status(self, status) -> None:
        if status == QMediaPlayer.EndOfMedia and self._playing:
            self._playing = False
            logger.info("Character audio finished")
            self.finished.emit()

    def _on_error(self, _error, message: str) -> None:
        self._playing = False
        self._fail(message or "RIPRODUZIONE AUDIO FALLITA")

    def _fail(self, message: str) -> None:
        logger.error("Character audio playback failed: %s", message)
        self.failed.emit(message)

    def _on_devices_changed(self) -> None:
        previous = self._requested_output_device_id
        if previous and not self.select_output_device(previous):
            self.stop()
        self.devices_changed.emit()
