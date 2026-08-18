import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from src.core.exceptions import ParticipantDataError
from src.data.participant_repository import ParticipantRepository


class ParticipantRepositoryTests(unittest.TestCase):

    def _load(self, rows):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "participants.xlsx"
        workbook = Workbook()
        sheet = workbook.active
        for row in rows:
            sheet.append(row)
        workbook.save(path)
        workbook.close()
        return temporary, ParticipantRepository(path)

    def test_string_ids_and_leading_zeroes_are_preserved(self):
        temporary, repository = self._load([
            ["ID", "Nome", "Cognome", "Squadra"],
            ["001", "Mario", "Rossi", "ROSSI"],
            [" A017 ", "Luca", "Bianchi", "BLU"],
        ])
        with temporary:
            participants = repository.load()
        self.assertEqual([item["id"] for item in participants], ["001", "A017"])

    def test_duplicate_names_with_distinct_ids_are_supported(self):
        temporary, repository = self._load([
            ["ID", "Nome", "Cognome", "Squadra"],
            ["001", "Mario", "Rossi", "ROSSI"],
            ["002", "Mario", "Rossi", "BLU"],
        ])
        with temporary:
            participants = repository.load()
        self.assertEqual(len(participants), 2)
        self.assertEqual(participants[0]["search_name"], participants[1]["search_name"])

    def test_duplicate_id_is_blocking(self):
        temporary, repository = self._load([
            ["ID", "Nome", "Cognome", "Squadra"],
            ["001", "Mario", "Rossi", "ROSSI"],
            ["001", "Luca", "Bianchi", "BLU"],
        ])
        with temporary, self.assertRaisesRegex(
            ParticipantDataError, "ID PARTECIPANTE DUPLICATO"
        ):
            repository.load()

    def test_empty_id_is_rejected(self):
        temporary, repository = self._load([
            ["ID", "Nome", "Cognome", "Squadra"],
            [None, "Mario", "Rossi", "ROSSI"],
        ])
        with temporary, self.assertRaisesRegex(ParticipantDataError, "riga 2"):
            repository.load()

    def test_missing_id_column_is_rejected(self):
        temporary, repository = self._load([
            ["Nome", "Cognome", "Squadra"],
            ["Mario", "Rossi", "ROSSI"],
        ])
        with temporary, self.assertRaisesRegex(ParticipantDataError, "ID"):
            repository.load()


if __name__ == "__main__":
    unittest.main()
