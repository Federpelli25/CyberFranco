import logging
import tempfile
import unittest
from logging.handlers import RotatingFileHandler
from pathlib import Path
from unittest.mock import patch

from src.core.logging_config import (
    HANDLER_MARKER,
    _remove_existing_handlers,
    configure_logging,
)


class LoggingConfigTests(unittest.TestCase):

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.log_file = (
            Path(self.temporary_directory.name)
            / "nested"
            / "cyberfranco.log"
        )
        self.root_logger = logging.getLogger()
        self.original_level = self.root_logger.level

    def tearDown(self):
        _remove_existing_handlers(self.root_logger)
        self.root_logger.setLevel(self.original_level)
        self.temporary_directory.cleanup()

    def cyberfranco_handlers(self):
        return [
            handler
            for handler in self.root_logger.handlers
            if getattr(handler, HANDLER_MARKER, False)
        ]

    def test_directory_file_and_message_are_created(self):
        configured = configure_logging(
            self.log_file,
            level="INFO",
        )
        logging.getLogger("test.module").info("test message")

        for handler in self.cyberfranco_handlers():
            handler.flush()

        self.assertTrue(configured)
        self.assertTrue(self.log_file.is_file())
        content = self.log_file.read_text(encoding="utf-8")
        self.assertIn("INFO | test.module | test message", content)

    def test_formatter_contains_required_fields(self):
        configure_logging(self.log_file)

        for handler in self.cyberfranco_handlers():
            format_string = handler.formatter._fmt
            self.assertIn("%(asctime)s", format_string)
            self.assertIn("%(levelname)s", format_string)
            self.assertIn("%(name)s", format_string)
            self.assertIn("%(message)s", format_string)

    def test_repeated_configuration_does_not_duplicate_handlers(self):
        configure_logging(self.log_file)
        configure_logging(self.log_file)

        handlers = self.cyberfranco_handlers()

        self.assertEqual(len(handlers), 2)
        self.assertEqual(
            sum(isinstance(h, RotatingFileHandler) for h in handlers),
            1,
        )

    def test_rotation_and_level_are_applied(self):
        configure_logging(
            self.log_file,
            level="DEBUG",
            max_bytes=2048,
            backup_count=2,
        )

        file_handler = next(
            handler
            for handler in self.cyberfranco_handlers()
            if isinstance(handler, RotatingFileHandler)
        )
        self.assertEqual(file_handler.maxBytes, 2048)
        self.assertEqual(file_handler.backupCount, 2)
        self.assertEqual(self.root_logger.level, logging.DEBUG)

    @patch(
        "src.core.logging_config.RotatingFileHandler",
        side_effect=PermissionError("access denied"),
    )
    def test_file_failure_keeps_console_logging(self, _):
        configured = configure_logging(self.log_file)

        self.assertFalse(configured)
        self.assertEqual(len(self.cyberfranco_handlers()), 1)
        self.assertIsInstance(
            self.cyberfranco_handlers()[0],
            logging.StreamHandler,
        )


if __name__ == "__main__":
    unittest.main()
