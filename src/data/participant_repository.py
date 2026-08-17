from pathlib import Path

from openpyxl import load_workbook


class ParticipantRepository:

    REQUIRED_COLUMNS = {
        "Nome",
        "Cognome",
        "Squadra",
    }

    DEFAULT_REAL_FILE = Path(
        "data/partecipanti.xlsx"
    )

    DEFAULT_EXAMPLE_FILE = Path(
        "data/partecipanti_example.xlsx"
    )

    def __init__(
        self,
        file_path: str | Path | None = None,
    ):
        if file_path is None:
            self.file_path = (
                self._resolve_default_file()
            )
        else:
            self.file_path = Path(
                file_path
            )

        self.participants = []

    def load(self) -> list[dict]:
        if not self.file_path.exists():
            raise FileNotFoundError(
                "File partecipanti non trovato: "
                f"{self.file_path}"
            )

        workbook = load_workbook(
            self.file_path,
            read_only=True,
            data_only=True,
        )

        try:
            worksheet = workbook.active

            rows = worksheet.iter_rows(
                values_only=True
            )

            try:
                headers = next(
                    rows
                )
            except StopIteration:
                raise ValueError(
                    "Il file Excel è vuoto."
                )

            headers = [
                (
                    str(header).strip()
                    if header is not None
                    else ""
                )
                for header in headers
            ]

            missing_columns = (
                self.REQUIRED_COLUMNS
                - set(headers)
            )

            if missing_columns:
                missing_text = ", ".join(
                    sorted(
                        missing_columns
                    )
                )

                raise ValueError(
                    "Colonne mancanti nel file Excel: "
                    f"{missing_text}"
                )

            column_indexes = {
                column_name:
                    headers.index(
                        column_name
                    )
                for column_name
                in self.REQUIRED_COLUMNS
            }

            participants = []

            for row in rows:
                nome = row[
                    column_indexes[
                        "Nome"
                    ]
                ]

                cognome = row[
                    column_indexes[
                        "Cognome"
                    ]
                ]

                squadra = row[
                    column_indexes[
                        "Squadra"
                    ]
                ]

                if (
                    not nome
                    or not cognome
                    or not squadra
                ):
                    continue

                participant = {
                    "nome":
                        str(nome).strip(),
                    "cognome":
                        str(cognome).strip(),
                    "squadra":
                        str(squadra)
                        .strip(),
                }

                participant[
                    "nome_completo"
                ] = (
                    f"{participant['nome']} "
                    f"{participant['cognome']}"
                )

                participant[
                    "search_name"
                ] = (
                    participant[
                        "nome_completo"
                    ]
                    .lower()
                )

                participants.append(
                    participant
                )

            self.participants = (
                participants
            )

            return participants

        finally:
            workbook.close()

    @classmethod
    def _resolve_default_file(
        cls,
    ) -> Path:

        if cls.DEFAULT_REAL_FILE.exists():
            return cls.DEFAULT_REAL_FILE

        if cls.DEFAULT_EXAMPLE_FILE.exists():
            return cls.DEFAULT_EXAMPLE_FILE

        raise FileNotFoundError(
            "Nessun file partecipanti trovato. "
            "Inserire 'data/partecipanti.xlsx' "
            "oppure "
            "'data/partecipanti_example.xlsx'."
        )