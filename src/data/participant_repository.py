from pathlib import Path

from openpyxl import load_workbook


class ParticipantRepository:
    REQUIRED_COLUMNS = {"Nome", "Cognome", "Squadra"}

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.participants = []

    def load(self) -> list[dict]:
        if not self.file_path.exists():
            raise FileNotFoundError(
                f"File partecipanti non trovato: {self.file_path}"
            )

        workbook = load_workbook(self.file_path, read_only=True, data_only=True)
        worksheet = workbook.active

        rows = worksheet.iter_rows(values_only=True)

        try:
            headers = next(rows)
        except StopIteration:
            raise ValueError("Il file Excel è vuoto.")

        headers = [
            str(header).strip() if header is not None else ""
            for header in headers
        ]

        missing_columns = self.REQUIRED_COLUMNS - set(headers)

        if missing_columns:
            raise ValueError(
                f"Colonne mancanti nel file Excel: {', '.join(missing_columns)}"
            )

        column_indexes = {
            column_name: headers.index(column_name)
            for column_name in self.REQUIRED_COLUMNS
        }

        participants = []

        for row in rows:
            nome = row[column_indexes["Nome"]]
            cognome = row[column_indexes["Cognome"]]
            squadra = row[column_indexes["Squadra"]]

            if not nome or not cognome or not squadra:
                continue

            participant = {
                "nome": str(nome).strip(),
                "cognome": str(cognome).strip(),
                "squadra": str(squadra).strip().upper(),
            }

            participant["nome_completo"] = (
                f"{participant['nome']} {participant['cognome']}"
            )

            participant["search_name"] = (
                participant["nome_completo"].lower()
            )

            participants.append(participant)

        workbook.close()

        self.participants = participants

        return participants