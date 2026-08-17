import logging
from typing import Any

from PySide6.QtGui import QGuiApplication


logger = logging.getLogger(__name__)


class DisplayManager:
    """Interroga Qt e risolve un display con fallback sul principale."""

    def __init__(self, application=None):
        self.application = application or QGuiApplication.instance()

    def list_screens(self) -> list[dict[str, Any]]:
        screens = list(self.application.screens()) if self.application else []
        primary = self.application.primaryScreen() if self.application else None
        result = [self._screen_entry(screen, index, screen is primary)
                  for index, screen in enumerate(screens)]
        logger.info("Screens detected: %d", len(result))
        return result

    def get_primary_screen(self) -> dict[str, Any] | None:
        screens = self.list_screens()
        return next((screen for screen in screens if screen["is_primary"]),
                    screens[0] if screens else None)

    def resolve_screen(self, saved_identifier) -> dict[str, Any] | None:
        screens = self.list_screens()
        if not screens:
            logger.error("No screens detected by Qt")
            return None

        for screen in screens:
            if saved_identifier in (screen["index"], screen["identifier"]):
                return screen

        fallback = next(
            (screen for screen in screens if screen["is_primary"]),
            screens[0],
        )
        logger.warning(
            "Saved public display unavailable; fallback to primary: %r",
            saved_identifier,
        )
        return fallback

    @staticmethod
    def format_screen(screen: dict[str, Any]) -> str:
        geometry = screen["geometry"]
        primary = " — Principale" if screen["is_primary"] else ""
        name = f" — {screen['name']}" if screen["name"] else ""
        return (
            f"Display {screen['index'] + 1}{name} — "
            f"{geometry['width']}x{geometry['height']}{primary}"
        )

    @staticmethod
    def _screen_entry(screen, index: int, is_primary: bool) -> dict[str, Any]:
        geometry = screen.geometry()
        name = str(screen.name() or "")
        return {
            "index": index,
            "identifier": name or index,
            "name": name,
            "geometry": {
                "x": geometry.x(),
                "y": geometry.y(),
                "width": geometry.width(),
                "height": geometry.height(),
            },
            "is_primary": is_primary,
            "screen": screen,
        }
