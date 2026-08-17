import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
HANDLER_MARKER = "_cyberfranco_handler"


def configure_logging(
    log_file: str | Path,
    level: str = "INFO",
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> bool:
    """Configura logging console/file e degrada alla console se necessario."""
    numeric_level = getattr(
        logging,
        str(level).upper(),
        logging.INFO,
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    _remove_existing_handlers(root_logger)

    formatter = logging.Formatter(
        LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    setattr(console_handler, HANDLER_MARKER, True)
    root_logger.addHandler(console_handler)

    path = Path(log_file)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        setattr(file_handler, HANDLER_MARKER, True)
        root_logger.addHandler(file_handler)
    except OSError as exc:
        root_logger.warning(
            "File logging unavailable; continuing with console only: %s",
            exc,
        )
        return False

    return True


def _remove_existing_handlers(
    logger: logging.Logger,
) -> None:
    for handler in list(logger.handlers):
        if not getattr(handler, HANDLER_MARKER, False):
            continue

        logger.removeHandler(handler)
        handler.close()
