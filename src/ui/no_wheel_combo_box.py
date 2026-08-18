"""Combo box che non intercetta lo scroll della pagina quando è chiusa."""

from PySide6.QtWidgets import QComboBox


class NoWheelComboBox(QComboBox):
    """Accetta la rotellina solo mentre il popup delle opzioni è aperto."""

    def wheelEvent(self, event) -> None:
        if self.view().isVisible():
            super().wheelEvent(event)
            return
        event.ignore()
