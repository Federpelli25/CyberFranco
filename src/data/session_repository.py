import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.exceptions import SessionError, SessionValidationError


logger = logging.getLogger(__name__)


class SessionRepository:
    VERSION = 1

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

    def exists(self) -> bool:
        return self.file_path.is_file()

    def load(self) -> dict[str, Any] | None:
        if not self.exists():
            logger.info("Session file not found; starting empty")
            return None

        logger.info("Loading session file: %s", self.file_path)
        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeError) as exc:
            logger.exception("Session JSON is corrupted")
            raise SessionValidationError(
                "SESSIONE CORROTTA: JSON non valido."
            ) from exc
        except OSError as exc:
            logger.exception("Session file cannot be read")
            raise SessionError("Impossibile leggere la sessione locale.") from exc

        self.validate(data)
        return data

    def save(self, session: dict[str, Any]) -> None:
        payload = dict(session)
        payload["updated_at"] = self.now_iso()
        self.validate(payload)
        temporary_path = self.file_path.with_name(
            f"{self.file_path.name}.tmp"
        )

        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with temporary_path.open("w", encoding="utf-8", newline="\n") as file:
                json.dump(payload, file, ensure_ascii=False, indent=2)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.file_path)
        except OSError as exc:
            logger.exception("Session save failed: %s", self.file_path)
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                logger.warning("Unable to remove temporary session file")
            raise SessionError("Impossibile salvare la sessione locale.") from exc

        session["updated_at"] = payload["updated_at"]
        logger.info("Session saved: processed=%d", len(payload["processed"]))

    def delete(self) -> None:
        try:
            self.file_path.unlink(missing_ok=True)
        except OSError as exc:
            logger.exception("Session delete failed")
            raise SessionError("Impossibile eliminare la sessione locale.") from exc

    def quarantine_corrupted(self) -> Path | None:
        if not self.exists():
            return None
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        destination = self.file_path.with_name(
            f"{self.file_path.stem}.corrupted.{timestamp}{self.file_path.suffix}"
        )
        try:
            os.replace(self.file_path, destination)
        except OSError as exc:
            logger.exception("Corrupted session could not be preserved")
            raise SessionError(
                "Impossibile preservare la sessione corrotta."
            ) from exc
        logger.warning("Session corrupted; preserved at: %s", destination)
        return destination

    @classmethod
    def create_empty(
        cls,
        participants_file: str,
        participants_fingerprint: str,
    ) -> dict[str, Any]:
        now = cls.now_iso()
        return {
            "version": cls.VERSION,
            "created_at": now,
            "updated_at": now,
            "participants_file": participants_file,
            "participants_fingerprint": participants_fingerprint,
            "processed": [],
        }

    @classmethod
    def validate(cls, data: Any) -> None:
        if not isinstance(data, dict):
            raise SessionValidationError("La sessione deve essere un oggetto JSON.")
        if data.get("version") != cls.VERSION:
            raise SessionValidationError(
                f"Versione sessione non supportata: {data.get('version')!r}."
            )
        for field in (
            "created_at", "updated_at", "participants_file",
            "participants_fingerprint", "processed",
        ):
            if field not in data:
                raise SessionValidationError(
                    f"Campo sessione obbligatorio mancante: {field}."
                )
        for field in (
            "created_at", "updated_at", "participants_file",
            "participants_fingerprint",
        ):
            if not isinstance(data[field], str) or not data[field].strip():
                raise SessionValidationError(f"Campo sessione non valido: {field}.")
        cls._validate_timestamp(data["created_at"])
        cls._validate_timestamp(data["updated_at"])
        if not isinstance(data["processed"], list):
            raise SessionValidationError("'processed' deve essere una lista.")
        seen = set()
        for entry in data["processed"]:
            if not isinstance(entry, dict):
                raise SessionValidationError("Entry processata non valida.")
            for field in ("key", "name", "team", "processed_at"):
                if not isinstance(entry.get(field), str) or not entry[field].strip():
                    raise SessionValidationError(
                        f"Campo processed non valido: {field}."
                    )
            cls._validate_timestamp(entry["processed_at"])
            if entry["key"] in seen:
                raise SessionValidationError(
                    f"Chiave processata duplicata: {entry['key']}."
                )
            seen.add(entry["key"])

    @staticmethod
    def participants_fingerprint(participants: list[dict]) -> str:
        stable_rows = sorted(
            f"{str(item.get('search_name', '')).strip().casefold()}|"
            f"{str(item.get('squadra', '')).strip().casefold()}"
            for item in participants
        )
        payload = "\n".join(stable_rows).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def now_iso() -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    @staticmethod
    def _validate_timestamp(value: str) -> None:
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise SessionValidationError("Timestamp sessione non valido.") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise SessionValidationError(
                "I timestamp della sessione devono includere il timezone."
            )
