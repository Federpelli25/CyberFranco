import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class SettingsError(ValueError):
    """Errore di configurazione leggibile dall'operatore."""


@dataclass(frozen=True)
class AppSettings:
    project_root: Path
    participants_file: str
    example_participants_file: str
    whisper_model: str
    whisper_device: str
    whisper_compute_type: str
    language: str
    recording_duration_seconds: float
    thinking_duration_ms: int
    microphone_device: int | str | None
    public_display_monitor: int
    public_display_fullscreen: bool

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


class SettingsLoader:
    DEFAULTS: dict[str, Any] = {
        "participants_file": "data/partecipanti.xlsx",
        "example_participants_file": (
            "data/partecipanti_example.xlsx"
        ),
        "whisper_model": "small",
        "whisper_device": "cpu",
        "whisper_compute_type": "int8",
        "language": "it",
        "recording_duration_seconds": 4.0,
        "thinking_duration_ms": 1200,
        "microphone_device": None,
        "public_display_monitor": 1,
        "public_display_fullscreen": False,
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

        self._validate(values)

        return AppSettings(
            project_root=self.project_root,
            participants_file=values["participants_file"],
            example_participants_file=(
                values["example_participants_file"]
            ),
            whisper_model=values["whisper_model"],
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
        )

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
                or not isinstance(microphone, (int, str))
            )
        ):
            raise SettingsError(
                "'microphone_device' deve essere null, "
                "un indice intero o il nome di un dispositivo."
            )

        if isinstance(microphone, str) and not microphone.strip():
            raise SettingsError(
                "'microphone_device' non può essere una "
                "stringa vuota."
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
