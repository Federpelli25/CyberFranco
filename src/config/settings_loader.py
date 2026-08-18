import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.exceptions import ConfigurationError


class SettingsError(ConfigurationError, ValueError):
    """Errore di configurazione leggibile dall'operatore."""


@dataclass(frozen=True)
class AppSettings:
    project_root: Path
    participants_file: str
    example_participants_file: str
    whisper_model: str
    whisper_model_path: str
    whisper_device: str
    whisper_compute_type: str
    language: str
    recording_duration_seconds: float
    thinking_duration_ms: int
    microphone_device: int | None
    public_display_monitor: int
    public_display_fullscreen: bool
    session_file: str
    session_persistence_enabled: bool
    logging_level: str
    logging_file: str
    logging_max_bytes: int
    logging_backup_count: int
    character_audio_enabled: bool = True
    character_audio_volume: float = 0.8
    character_audio_output_device_id: str | None = None
    reveal_pre_reveal_ms: int = 500
    reveal_flash_ms: int = 180
    reveal_appear_ms: int = 500
    reveal_hold_ms: int = 2200
    reveal_fade_ms: int = 500

    def resolve_project_path(
        self,
        configured_path: str,
    ) -> Path:
        path = Path(configured_path)

        if path.is_absolute():
            return path

        return self.project_root / path

    def resolve_participants_file(self) -> Path:
        real_file = self.resolve_project_path(
            self.participants_file
        )

        if real_file.exists():
            return real_file

        example_file = self.resolve_project_path(
            self.example_participants_file
        )

        if example_file.exists():
            return example_file

        raise SettingsError(
            "Nessun file partecipanti trovato. "
            f"Controllati: '{real_file}' e "
            f"'{example_file}'."
        )

    def resolve_whisper_model_path(self) -> Path:
        return self.resolve_project_path(
            self.whisper_model_path
        )

    def resolve_log_file(self) -> Path:
        return self.resolve_project_path(
            self.logging_file
        )

    def resolve_session_file(self) -> Path:
        return self.resolve_project_path(self.session_file)


class SettingsLoader:
    DEFAULTS: dict[str, Any] = {
        "participants_file": "data/partecipanti.xlsx",
        "example_participants_file": (
            "data/partecipanti_example.xlsx"
        ),
        "whisper_model": "small",
        "whisper_model_path": "models/faster-whisper-small",
        "whisper_device": "cpu",
        "whisper_compute_type": "int8",
        "language": "it",
        "recording_duration_seconds": 4.0,
        "thinking_duration_ms": 1200,
        "microphone_device": None,
        "public_display_monitor": 1,
        "public_display_fullscreen": False,
        "session_file": "data/session.json",
        "session_persistence_enabled": True,
        "logging": {
            "level": "INFO",
            "file": "logs/cyberfranco.log",
            "max_bytes": 5 * 1024 * 1024,
            "backup_count": 3,
        },
        "character_audio": {
            "enabled": True,
            "volume": 0.8,
            "output_device_id": None,
        },
        "reveal": {
            "pre_reveal_ms": 500,
            "flash_ms": 180,
            "appear_ms": 500,
            "hold_ms": 2200,
            "fade_ms": 500,
        },
    }

    def __init__(
        self,
        project_root: str | Path | None = None,
    ):
        if project_root is None:
            project_root = Path(__file__).resolve().parents[2]

        self.project_root = Path(project_root).resolve()

    def load(
        self,
        settings_path: str | Path | None = None,
    ) -> AppSettings:
        path = self._resolve_settings_path(settings_path)
        raw_settings = self._read_json(path)
        values = {
            **self.DEFAULTS,
            **raw_settings,
        }
        raw_logging = raw_settings.get("logging", {})

        if isinstance(raw_logging, dict):
            values["logging"] = {
                **self.DEFAULTS["logging"],
                **raw_logging,
            }
        else:
            values["logging"] = raw_logging
        raw_character_audio = raw_settings.get("character_audio", {})
        if isinstance(raw_character_audio, dict):
            values["character_audio"] = {
                **self.DEFAULTS["character_audio"],
                **raw_character_audio,
            }
        else:
            values["character_audio"] = raw_character_audio
        raw_reveal = raw_settings.get("reveal", {})
        if isinstance(raw_reveal, dict):
            values["reveal"] = {
                **self.DEFAULTS["reveal"],
                **raw_reveal,
            }
        else:
            values["reveal"] = raw_reveal

        self._validate(values)

        return AppSettings(
            project_root=self.project_root,
            participants_file=values["participants_file"],
            example_participants_file=(
                values["example_participants_file"]
            ),
            whisper_model=values["whisper_model"],
            whisper_model_path=values["whisper_model_path"],
            whisper_device=values["whisper_device"],
            whisper_compute_type=(
                values["whisper_compute_type"]
            ),
            language=values["language"],
            recording_duration_seconds=float(
                values["recording_duration_seconds"]
            ),
            thinking_duration_ms=values[
                "thinking_duration_ms"
            ],
            microphone_device=values["microphone_device"],
            public_display_monitor=values[
                "public_display_monitor"
            ],
            public_display_fullscreen=values[
                "public_display_fullscreen"
            ],
            session_file=values["session_file"],
            session_persistence_enabled=values[
                "session_persistence_enabled"
            ],
            logging_level=values["logging"]["level"],
            logging_file=values["logging"]["file"],
            logging_max_bytes=values["logging"]["max_bytes"],
            logging_backup_count=(
                values["logging"]["backup_count"]
            ),
            character_audio_enabled=values["character_audio"]["enabled"],
            character_audio_volume=float(values["character_audio"]["volume"]),
            character_audio_output_device_id=(
                values["character_audio"]["output_device_id"]
            ),
            reveal_pre_reveal_ms=values["reveal"]["pre_reveal_ms"],
            reveal_flash_ms=values["reveal"]["flash_ms"],
            reveal_appear_ms=values["reveal"]["appear_ms"],
            reveal_hold_ms=values["reveal"]["hold_ms"],
            reveal_fade_ms=values["reveal"]["fade_ms"],
        )

    def save_character_audio(
        self,
        enabled: bool,
        volume: float,
        output_device_id: str | None,
        settings_path: str | Path | None = None,
    ) -> None:
        candidate = {
            **self.DEFAULTS,
            "character_audio": {
                "enabled": enabled,
                "volume": volume,
                "output_device_id": output_device_id,
            },
        }
        self._validate(candidate)
        path = self._resolve_settings_path(settings_path)
        values = self._read_json(path)
        values["character_audio"] = candidate["character_audio"]
        temporary_path = path.with_suffix(f"{path.suffix}.tmp")
        try:
            temporary_path.write_text(
                json.dumps(values, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary_path.replace(path)
        except OSError as exc:
            temporary_path.unlink(missing_ok=True)
            raise SettingsError(
                "Impossibile salvare le impostazioni della voce."
            ) from exc

    def save_microphone_device(
        self,
        device_id: int | None,
        settings_path: str | Path | None = None,
    ) -> None:
        if (
            device_id is not None
            and (
                isinstance(device_id, bool)
                or not isinstance(device_id, int)
                or device_id < 0
            )
        ):
            raise SettingsError(
                "'microphone_device' deve essere null "
                "oppure un ID intero maggiore o uguale a zero."
            )

        path = self._resolve_settings_path(settings_path)
        values = self._read_json(path)
        values["microphone_device"] = device_id
        temporary_path = path.with_suffix(
            f"{path.suffix}.tmp"
        )

        try:
            temporary_path.write_text(
                json.dumps(
                    values,
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            temporary_path.replace(path)
        except OSError as exc:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass

            raise SettingsError(
                "Impossibile salvare il microfono nel file "
                f"di configurazione '{path}': {exc}"
            ) from exc

    def save_public_display(
        self,
        screen_index: int,
        fullscreen: bool,
        settings_path: str | Path | None = None,
    ) -> None:
        values_to_validate = {**self.DEFAULTS}
        values_to_validate["public_display_monitor"] = screen_index
        values_to_validate["public_display_fullscreen"] = fullscreen
        self._validate(values_to_validate)

        path = self._resolve_settings_path(settings_path)
        values = self._read_json(path)
        values["public_display_monitor"] = screen_index
        values["public_display_fullscreen"] = fullscreen
        temporary_path = path.with_suffix(f"{path.suffix}.tmp")

        try:
            temporary_path.write_text(
                json.dumps(values, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary_path.replace(path)
        except OSError as exc:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise SettingsError(
                "Impossibile salvare le impostazioni del display pubblico."
            ) from exc

    def _resolve_settings_path(
        self,
        settings_path: str | Path | None,
    ) -> Path:
        if settings_path is None:
            return self.project_root / "config" / "settings.json"

        path = Path(settings_path)

        if path.is_absolute():
            return path

        return self.project_root / path

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        try:
            content = path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise SettingsError(
                f"File di configurazione non trovato: '{path}'."
            ) from exc
        except OSError as exc:
            raise SettingsError(
                "Impossibile leggere il file di configurazione "
                f"'{path}': {exc}"
            ) from exc

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise SettingsError(
                "JSON non valido in "
                f"'{path}', riga {exc.lineno}, "
                f"colonna {exc.colno}: {exc.msg}."
            ) from exc

        if not isinstance(data, dict):
            raise SettingsError(
                "La configurazione deve essere un oggetto JSON."
            )

        return data

    @classmethod
    def _validate(cls, values: dict[str, Any]) -> None:
        cls._require_non_empty_string(
            values,
            "participants_file",
        )
        cls._require_non_empty_string(
            values,
            "example_participants_file",
        )
        cls._require_non_empty_string(values, "whisper_model")
        cls._require_non_empty_string(
            values,
            "whisper_model_path",
        )
        cls._require_non_empty_string(values, "whisper_device")
        cls._require_non_empty_string(
            values,
            "whisper_compute_type",
        )
        cls._require_non_empty_string(values, "language")

        duration = values["recording_duration_seconds"]

        if (
            isinstance(duration, bool)
            or not isinstance(duration, (int, float))
            or duration <= 0
        ):
            raise SettingsError(
                "'recording_duration_seconds' deve essere "
                "un numero maggiore di zero."
            )

        thinking_duration = values["thinking_duration_ms"]

        if (
            isinstance(thinking_duration, bool)
            or not isinstance(thinking_duration, int)
            or thinking_duration < 0
        ):
            raise SettingsError(
                "'thinking_duration_ms' deve essere "
                "un intero maggiore o uguale a zero."
            )

        microphone = values["microphone_device"]

        if (
            microphone is not None
            and (
                isinstance(microphone, bool)
                or not isinstance(microphone, int)
                or microphone < 0
            )
        ):
            raise SettingsError(
                "'microphone_device' deve essere null, "
                "oppure un ID intero maggiore o uguale a zero."
            )

        monitor = values["public_display_monitor"]

        if (
            isinstance(monitor, bool)
            or not isinstance(monitor, int)
            or monitor < 0
        ):
            raise SettingsError(
                "'public_display_monitor' deve essere "
                "un indice intero maggiore o uguale a zero."
            )

        if not isinstance(
            values["public_display_fullscreen"],
            bool,
        ):
            raise SettingsError(
                "'public_display_fullscreen' deve essere "
                "true oppure false."
            )

        cls._require_non_empty_string(values, "session_file")

        if not isinstance(values["session_persistence_enabled"], bool):
            raise SettingsError(
                "'session_persistence_enabled' deve essere true oppure false."
            )

        logging_settings = values["logging"]

        if not isinstance(logging_settings, dict):
            raise SettingsError(
                "'logging' deve essere un oggetto JSON."
            )

        cls._require_non_empty_string(
            logging_settings,
            "level",
        )
        cls._require_non_empty_string(
            logging_settings,
            "file",
        )

        level = logging_settings["level"].upper()

        if level not in {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }:
            raise SettingsError(
                "'logging.level' deve essere DEBUG, INFO, "
                "WARNING, ERROR oppure CRITICAL."
            )

        for key in ("max_bytes", "backup_count"):
            value = logging_settings[key]

            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 0
            ):
                raise SettingsError(
                    f"'logging.{key}' deve essere un intero "
                    "maggiore o uguale a zero."
                )

        character_audio = values["character_audio"]
        if not isinstance(character_audio, dict):
            raise SettingsError("'character_audio' deve essere un oggetto JSON.")
        if not isinstance(character_audio.get("enabled"), bool):
            raise SettingsError("'character_audio.enabled' deve essere true o false.")
        volume = character_audio.get("volume")
        if (
            isinstance(volume, bool)
            or not isinstance(volume, (int, float))
            or not 0.0 <= volume <= 1.0
        ):
            raise SettingsError(
                "'character_audio.volume' deve essere compreso tra 0 e 1."
            )
        device_id = character_audio.get("output_device_id")
        if device_id is not None and (
            not isinstance(device_id, str) or not device_id.strip()
        ):
            raise SettingsError(
                "'character_audio.output_device_id' deve essere null o una stringa."
            )

        reveal = values.get("reveal")
        if not isinstance(reveal, dict):
            raise SettingsError("'reveal' deve essere un oggetto JSON.")
        for key in (
            "pre_reveal_ms", "flash_ms", "appear_ms", "hold_ms", "fade_ms"
        ):
            duration = reveal.get(key)
            if isinstance(duration, bool) or not isinstance(duration, int) or duration < 0:
                raise SettingsError(
                    f"'reveal.{key}' deve essere un intero maggiore o uguale a zero."
                )

    @staticmethod
    def _require_non_empty_string(
        values: dict[str, Any],
        key: str,
    ) -> None:
        value = values[key]

        if not isinstance(value, str) or not value.strip():
            raise SettingsError(
                f"'{key}' deve essere una stringa non vuota."
            )
