"""Configurazione autorevole e ricaricabile delle squadre."""

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)
COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class TeamConfig:
    key: str
    slug: str
    display_name: str
    logo_path: Path | None
    background_path: Path | None
    audio_path: Path | None
    primary_color: str = "#334155"
    secondary_color: str = "#94A3B8"
    configured: bool = True


class TeamConfigLoader:
    """Carica, valida e risolve squadre con nomi arbitrari."""

    def __init__(
        self,
        project_root: str | Path,
        config_path: str | Path = "config/teams.json",
    ):
        self.project_root = Path(project_root).resolve()
        path = Path(config_path)
        self.config_path = path if path.is_absolute() else self.project_root / path
        self._teams: dict[str, TeamConfig] = {}
        self.warnings: list[str] = []
        self.error: str | None = None
        self.reload()

    @property
    def teams(self) -> list[TeamConfig]:
        return list(self._teams.values())

    @property
    def count(self) -> int:
        return len(self._teams)

    @property
    def is_usable(self) -> bool:
        return bool(self._teams)

    def reload(self) -> list[TeamConfig]:
        self._teams.clear()
        self.warnings.clear()
        self.error = None
        try:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.error = "Configurazione squadre non trovata."
            logger.error("Team configuration missing: %s", self.config_path)
            return []
        except (OSError, json.JSONDecodeError):
            self.error = "Configurazione squadre non leggibile o non valida."
            logger.exception("Team configuration invalid: %s", self.config_path)
            return []
        if not isinstance(raw, dict) or not raw:
            self.error = "Nessuna squadra configurata."
            logger.error("Team configuration is empty")
            return []

        used_slugs: set[str] = set()
        for raw_key, value in raw.items():
            key = self.normalize_key(raw_key)
            if not key or not isinstance(value, dict):
                self.warnings.append("Ignorata una squadra con configurazione non valida.")
                continue
            display_name = value.get("display_name")
            slug = value.get("slug")
            if not isinstance(display_name, str) or not display_name.strip():
                self.warnings.append(f'Nome visualizzato mancante per "{key}".')
                continue
            if not isinstance(slug, str) or not SLUG_PATTERN.fullmatch(slug):
                self.warnings.append(f'Slug non valido per "{display_name}".')
                continue
            if slug in used_slugs:
                self.warnings.append(f'Slug duplicato "{slug}": squadra ignorata.')
                continue
            used_slugs.add(slug)

            primary = self._color(value.get("primary_color"), "#334155", display_name)
            secondary = self._color(
                value.get("secondary_color"), "#94A3B8", display_name
            )
            logo = self._optional_path(value.get("logo"))
            background = self._optional_path(value.get("background"))
            audio = self._optional_path(value.get("audio"))
            if logo is None or not logo.is_file():
                self.warnings.append(
                    f'Logo mancante per "{display_name}". Verrà usato il fallback.'
                )
                logo = None
            if background is not None and not background.is_file():
                self.warnings.append(
                    f'Background mancante per "{display_name}". Verrà usato il gradiente.'
                )
                background = None
            if audio is not None and not audio.is_file():
                self.warnings.append(
                    f'Audio reveal mancante per "{display_name}".'
                )
                audio = None
            self._teams[key] = TeamConfig(
                key=key,
                slug=slug,
                display_name=display_name.strip(),
                logo_path=logo,
                background_path=background,
                audio_path=audio,
                primary_color=primary,
                secondary_color=secondary,
            )
        if not self._teams:
            self.error = "La configurazione squadre non contiene elementi utilizzabili."
        logger.info(
            "Team configuration loaded: teams=%d warnings=%d",
            self.count,
            len(self.warnings),
        )
        return self.teams

    def get(self, team_name: str) -> TeamConfig | None:
        return self._teams.get(self.normalize_key(team_name))

    def resolve(self, team_name: str) -> TeamConfig:
        configured = self.get(team_name)
        if configured is not None:
            return configured
        display_name = str(team_name).strip() or "Squadra"
        key = self.normalize_key(display_name) or "SQUADRA"
        logger.warning("Unknown team; neutral fallback used: %s", display_name)
        return TeamConfig(
            key=key,
            slug=self.slugify(display_name),
            display_name=display_name,
            logo_path=None,
            background_path=None,
            audio_path=None,
            configured=False,
        )

    @staticmethod
    def normalize_key(value) -> str:
        return " ".join(str(value or "").strip().upper().split())

    @staticmethod
    def slugify(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
        return slug or "squadra"

    def _optional_path(self, value) -> Path | None:
        if not isinstance(value, str) or not value.strip():
            return None
        path = Path(value)
        return path if path.is_absolute() else self.project_root / path

    def _color(self, value, fallback: str, display_name: str) -> str:
        if value is None:
            return fallback
        if isinstance(value, str) and COLOR_PATTERN.fullmatch(value):
            return value.upper()
        self.warnings.append(
            f'Colore non valido per "{display_name}". Applicato il fallback.'
        )
        return fallback
