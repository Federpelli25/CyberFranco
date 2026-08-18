import logging
from collections.abc import Iterable
from datetime import datetime
from typing import Any


Participant = dict[str, Any]
logger = logging.getLogger(__name__)


class ParticipantTracker:

    def __init__(
        self,
        participants: Iterable[Participant],
    ):
        self.participants = list(participants)

        self._processed: set[str] = set()
        self._history: list[Participant] = []
        self._processed_at: dict[str, str] = {}

    @staticmethod
    def _participant_key(
        participant: Participant,
    ) -> str:
        participant_id = str(participant.get("id", "")).strip()
        if not participant_id:
            raise ValueError("Il partecipante deve avere un ID valido.")
        return participant_id

    def mark_processed(
        self,
        participant: Participant,
    ) -> bool:
        key = self._participant_key(
            participant
        )

        if key in self._processed:
            logger.warning("Participant already processed: %s", key)
            return False

        self._processed.add(
            key
        )

        self._history.append(
            participant
        )
        self._processed_at[key] = (
            datetime.now().astimezone().isoformat(timespec="seconds")
        )

        logger.info("Participant marked processed: %s", key)

        return True

    def is_processed(
        self,
        participant: Participant,
    ) -> bool:
        key = self._participant_key(
            participant
        )

        return key in self._processed

    def reset_participant(
        self,
        participant: Participant,
    ) -> bool:
        key = self._participant_key(
            participant
        )

        if key not in self._processed:
            return False

        self._processed.remove(key)
        self._processed_at.pop(key, None)

        self._history = [
            item
            for item in self._history
            if self._participant_key(item)
            != key
        ]

        logger.info("Participant reset: %s", key)

        return True

    def undo_last(
        self,
    ) -> Participant | None:
        if not self._history:
            return None

        participant = (
            self._history.pop()
        )

        key = self._participant_key(
            participant
        )

        self._processed.discard(
            key
        )
        self._processed_at.pop(key, None)

        logger.info("Undo last assignment: %s", key)

        return participant

    def get_processed_participants(
        self,
    ) -> list[Participant]:
        return list(
            self._history
        )

    def get_last_processed(
        self,
    ) -> Participant | None:
        if not self._history:
            return None

        return self._history[-1]

    def reset_all(self) -> None:
        logger.info("Participant tracking reset")
        self._processed.clear()
        self._history.clear()
        self._processed_at.clear()

    def load_processed(self, entries: Iterable[dict[str, Any]]) -> None:
        """Ripristina ordine e timestamp usando solo partecipanti correnti."""
        participants_by_key = {
            self._participant_key(participant): participant
            for participant in self.participants
        }
        restored_history = []
        restored_keys = set()
        restored_timestamps = {}

        for entry in entries:
            key = str(entry.get("participant_id", "")).strip()
            participant = participants_by_key.get(key)
            if participant is None:
                raise ValueError(
                    f"Partecipante della sessione non trovato: {key}."
                )
            if key in restored_keys:
                raise ValueError(f"Partecipante duplicato nella sessione: {key}.")
            restored_keys.add(key)
            restored_history.append(participant)
            restored_timestamps[key] = str(entry["processed_at"])

        self._processed = restored_keys
        self._history = restored_history
        self._processed_at = restored_timestamps
        logger.info("Participant tracking restored: %d", len(restored_history))

    def export_state(self) -> list[dict[str, str]]:
        result = []
        for participant in self._history:
            key = self._participant_key(participant)
            result.append({
                "participant_id": key,
                "name": str(participant["nome_completo"]),
                "team": str(participant["squadra"]),
                "processed_at": self._processed_at[key],
            })
        return result

    @property
    def total_count(self) -> int:
        return len(
            self.participants
        )

    @property
    def processed_count(self) -> int:
        return len(
            self._processed
        )

    @property
    def remaining_count(self) -> int:
        return (
            self.total_count
            - self.processed_count
        )
