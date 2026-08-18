"""Widget scenico Qt-only per il reveal di una squadra."""

import math

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.config.team_config_loader import TeamConfig


class TeamReveal(QWidget):
    """Presentazione scalabile con background cover e fallback a gradiente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._team: TeamConfig | None = None
        self._background = QPixmap()
        self._intensity = 1.0
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 50, 60, 60)
        layout.addStretch(2)
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo_label, 4)
        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label, 2)
        layout.addStretch(1)

    def configure(self, team: TeamConfig, logo: QPixmap | None = None,
                  background: QPixmap | None = None) -> None:
        self._team = team
        self._background = background or QPixmap()
        self.name_label.setText(team.display_name.upper())
        if logo is not None and not logo.isNull():
            self.logo_label.setPixmap(logo)
            self.logo_label.show()
        else:
            self.logo_label.clear()
            self.logo_label.hide()
        self._apply_text_style(1.0)
        self.update()

    def set_intensity(self, value: float) -> None:
        self._intensity = max(0.0, min(1.35, value))
        self._apply_text_style(0.8 + 0.2 * self._intensity)
        self.update()

    def _apply_text_style(self, scale: float) -> None:
        accent = self._team.secondary_color if self._team else "#8BE9FD"
        size = max(64, int(min(max(self.width(), 900) / 8.5, 150) * scale))
        self.name_label.setStyleSheet(
            f"color: white; font-size: {size}px; font-weight: 900; "
            f"letter-spacing: 8px; border-bottom: 3px solid {accent};"
        )

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_text_style(1.0)
        if self.logo_label.pixmap() and not self.logo_label.pixmap().isNull():
            source = self.logo_label.pixmap()
            side = int(min(self.width(), self.height()) * 0.36)
            self.logo_label.setPixmap(source.scaled(
                side, side, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self._background.isNull():
            scaled = self._background.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (scaled.width() - self.width()) // 2
            y = (scaled.height() - self.height()) // 2
            painter.drawPixmap(0, 0, scaled, x, y, self.width(), self.height())
            painter.fillRect(self.rect(), QColor(4, 8, 14, 90))
        else:
            primary = QColor(self._team.primary_color if self._team else "#334155")
            secondary = QColor(
                self._team.secondary_color if self._team else "#94A3B8"
            )
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor(3, 7, 13))
            gradient.setColorAt(0.48, primary.darker(170))
            gradient.setColorAt(1, secondary.darker(230))
            painter.fillRect(self.rect(), gradient)
        accent = QColor(self._team.secondary_color if self._team else "#94A3B8")
        count = max(18, min(42, self.width() // 35))
        painter.setPen(QPen(accent, 1.2))
        for index in range(count):
            x = (index * 97 + 41) % max(1, self.width())
            y = (index * 53 + int(18 * math.sin(index))) % max(1, self.height())
            radius = 1 + index % 3
            color = QColor(accent)
            color.setAlpha(int((65 + index % 4 * 28) * self._intensity))
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(x, y, radius * 2, radius * 2)
