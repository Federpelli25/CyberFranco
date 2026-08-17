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
from src.core.exceptions import ParticipantDataError
from src.core.sorting_controller import SortingController
from src.core.state_manager import StateManager
from src.ui.operator_window import OperatorWindow
from src.ui.public_window import PublicWindow
from src.ui.display_manager import DisplayManager


def install_exception_handler() -> None:
    """Registra e comunica le eccezioni Qt/Python non intercettate."""
    def handle_exception(exception_type, exception, traceback):
        if issubclass(exception_type, KeyboardInterrupt):
            sys.__excepthook__(exception_type, exception, traceback)
            return

        logging.getLogger(__name__).critical(
            "Unhandled application exception",
            exc_info=(exception_type, exception, traceback),
        )
        QMessageBox.critical(
            None,
            "Errore inatteso",
            "ERRORE INATTESO\n\n"
            "Consulta il file di log e riavvia il flusso.",
        )

    sys.excepthook = handle_exception


def main() -> int:
    app = QApplication(sys.argv)
    install_exception_handler()

    try:
        settings_loader = SettingsLoader()
        settings = settings_loader.load()
    except SettingsError as exc:
        logging.getLogger(__name__).exception(
            "Application startup blocked by invalid settings"
        )
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
    display_manager = DisplayManager(app)
    try:
        operator_window = OperatorWindow(
            settings,
            settings_loader,
            display_manager,
        )
        public_window = PublicWindow(settings, display_manager)
    except ParticipantDataError as exc:
        logger.exception("Application startup blocked by participant data")
        QMessageBox.critical(
            None,
            "Errore partecipanti",
            str(exc),
        )
        return 1
    except Exception:
        logger.exception("Application startup failed")
        QMessageBox.critical(
            None,
            "Errore di avvio",
            "IMPOSSIBILE AVVIARE CYBERFRANCO\n\n"
            "Consulta il file di log per il dettaglio tecnico.",
        )
        return 1
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

    operator_window.public_display_changed.connect(
        public_window.apply_display_settings
    )

    primary_screen = display_manager.get_primary_screen()
    if primary_screen is not None:
        primary_geometry = primary_screen["geometry"]
        operator_window.move(
            primary_geometry["x"] + 40,
            primary_geometry["y"] + 40,
        )

    operator_window.show()
    public_window.show_configured()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
