from collections.abc import Iterable
from typing import Any


Participant = dict[str, Any]


class ParticipantTracker:

    def __init__(
        self,
        participants: Iterable[Participant],
    ):
        self.participants = list(participants)

        self._processed: set[str] = set()
        self._history: list[Participant] = []

    @staticmethod
    def _participant_key(
        participant: Participant,
    ) -> str:
        participant_id = participant.get("id")

        if participant_id is not None:
            normalized_id = str(participant_id).strip()

            if normalized_id:
                return f"id:{normalized_id}"

        search_name = str(
            participant.get("search_name", "")
        ).strip().lower()

        if not search_name:
            raise ValueError(
                "Il partecipante deve avere un ID "
                "oppure un search_name valido."
            )

        return f"name:{search_name}"

    def mark_processed(
        self,
        participant: Participant,
    ) -> bool:
        key = self._participant_key(
            participant
        )

        if key in self._processed:
            return False

        self._processed.add(
            key
        )

        self._history.append(
            participant
        )

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

        self._history = [
            item
            for item in self._history
            if self._participant_key(item)
            != key
        ]

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
        self._processed.clear()
        self._history.clear()

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
