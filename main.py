import sys

from PySide6.QtWidgets import QApplication

from src.core.participant_tracker import ParticipantTracker
from src.core.sorting_controller import SortingController
from src.core.state_manager import StateManager
from src.ui.operator_window import OperatorWindow
from src.ui.public_window import PublicWindow


def main():
    app = QApplication(sys.argv)

    state_manager = StateManager()
    operator_window = OperatorWindow()
    public_window = PublicWindow()
    participant_tracker = ParticipantTracker(
        operator_window.participants
    )

    sorting_controller = SortingController(
        operator_window=operator_window,
        public_window=public_window,
        state_manager=state_manager,
        participant_tracker=participant_tracker,
    )

    operator_window.show()
    public_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
