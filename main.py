import sys

from PySide6.QtWidgets import QApplication

from src.ui.operator_window import OperatorWindow
from src.ui.public_window import PublicWindow


def main():
    app = QApplication(sys.argv)

    operator_window = OperatorWindow()
    public_window = PublicWindow()

    operator_window.participant_confirmed.connect(
        lambda participant: public_window.show_team(
            participant["nome_completo"],
            participant["squadra"],
        )
    )

    operator_window.show()
    public_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()