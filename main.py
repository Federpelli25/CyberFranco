import logging
import sys

from PySide6.QtWidgets import (
    QApplication,
    QMessageBox,
)

from src.config.settings_loader import (
    SettingsError,
    SettingsLoader,
)
from src.core.participant_tracker import ParticipantTracker
from src.core.logging_config import configure_logging
from src.core.sorting_controller import SortingController
from src.core.state_manager import StateManager
from src.ui.operator_window import OperatorWindow
from src.ui.public_window import PublicWindow


def main() -> int:
    app = QApplication(sys.argv)

    try:
        settings_loader = SettingsLoader()
        settings = settings_loader.load()
    except SettingsError as exc:
        QMessageBox.critical(
            None,
            "Errore configurazione",
            str(exc),
        )
        return 1

    configure_logging(
        log_file=settings.resolve_log_file(),
        level=settings.logging_level,
        max_bytes=settings.logging_max_bytes,
        backup_count=settings.logging_backup_count,
    )
    logger = logging.getLogger(__name__)
    logger.info("Application starting")
    logger.info("Settings loaded")

    state_manager = StateManager()
    operator_window = OperatorWindow(
        settings,
        settings_loader,
    )
    public_window = PublicWindow(settings)
    participant_tracker = ParticipantTracker(
        operator_window.participants
    )
    logger.info(
        "Participants file: %s",
        operator_window.repository.file_path,
    )
    logger.info(
        "Participants loaded: %d",
        len(operator_window.participants),
    )

    sorting_controller = SortingController(
        operator_window=operator_window,
        public_window=public_window,
        state_manager=state_manager,
        participant_tracker=participant_tracker,
        settings=settings,
    )

    operator_window.show()
    public_window.show_configured()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
