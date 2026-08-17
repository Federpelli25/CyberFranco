"""Tema scuro centralizzato della console amministratore."""

from PySide6.QtGui import QColor, QPalette


COLORS = {
    "background": "#0d1117",
    "surface": "#161b22",
    "surface_raised": "#21262d",
    "border": "#4b5563",
    "text": "#f0f6fc",
    "text_secondary": "#c4ccd6",
    "text_muted": "#9da7b3",
    "accent": "#2f81f7",
    "accent_hover": "#58a6ff",
    "accent_pressed": "#1f6feb",
    "selection": "#1f6feb",
    "danger": "#cf4455",
}


def apply_operator_theme(window) -> None:
    """Applica palette di fallback e stylesheet completo alla console."""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(COLORS["background"]))
    palette.setColor(QPalette.WindowText, QColor(COLORS["text"]))
    palette.setColor(QPalette.Base, QColor(COLORS["background"]))
    palette.setColor(QPalette.AlternateBase, QColor(COLORS["surface_raised"]))
    palette.setColor(QPalette.Text, QColor(COLORS["text"]))
    palette.setColor(QPalette.Button, QColor(COLORS["surface_raised"]))
    palette.setColor(QPalette.ButtonText, QColor(COLORS["text"]))
    palette.setColor(QPalette.Highlight, QColor(COLORS["selection"]))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.PlaceholderText, QColor(COLORS["text_muted"]))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(COLORS["text_muted"]))
    palette.setColor(
        QPalette.Disabled,
        QPalette.ButtonText,
        QColor(COLORS["text_muted"]),
    )
    window.setPalette(palette)
    window.setStyleSheet(OPERATOR_STYLE_SHEET)


OPERATOR_STYLE_SHEET = """
    QMainWindow, QWidget {
        background-color: #0d1117;
        color: #f0f6fc;
    }
    QScrollArea, QScrollArea QWidget, QScrollArea::viewport,
    QStackedWidget, QStackedWidget > QWidget {
        background-color: #0d1117;
        color: #f0f6fc;
        border: none;
    }
    QWidget#adminHeader {
        background-color: #161b22;
        border-bottom: 1px solid #30363d;
    }
    QLabel {
        background-color: transparent;
        color: #f0f6fc;
    }
    QLabel[secondary="true"] { color: #c4ccd6; }
    QLabel#headerTitle {
        color: #ffffff;
        font-size: 26px;
        font-weight: 800;
    }
    QLabel#pageTitle {
        color: #ffffff;
        font-size: 25px;
        font-weight: 700;
    }
    QLabel#progressLabel {
        color: #dbe7f3;
        font-size: 17px;
        font-weight: 600;
    }
    QLabel#operatorMessage {
        color: #f0f6fc;
        background-color: #21262d;
        border: 1px solid #4b5563;
        border-radius: 7px;
        padding: 9px;
        font-weight: 650;
    }
    QLabel#stateReady, QLabel#stateListening, QLabel#stateConfirm,
    QLabel#stateProcessing, QLabel#stateReveal, QLabel#stateError,
    QLabel#stateProcessed {
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 90);
        border-radius: 8px;
        padding: 7px 14px;
        font-weight: 800;
    }
    QLabel#stateReady { background-color: #1f6f43; }
    QLabel#stateListening { background-color: #1158a7; }
    QLabel#stateConfirm { background-color: #9a4d00; }
    QLabel#stateProcessing { background-color: #7a5b00; }
    QLabel#stateReveal { background-color: #5a3eaa; }
    QLabel#stateError { background-color: #9e2636; }
    QLabel#stateProcessed { background-color: #0f6b63; }

    QPushButton {
        color: #f0f6fc;
        background-color: #2d3744;
        border: 1px solid #566273;
        border-radius: 6px;
        padding: 9px 14px;
        font-weight: 600;
    }
    QPushButton:hover {
        color: #ffffff;
        background-color: #3b4756;
        border-color: #8b98aa;
    }
    QPushButton:focus {
        border: 2px solid #58a6ff;
    }
    QPushButton:pressed, QPushButton:checked {
        color: #ffffff;
        background-color: #1f6feb;
        border-color: #79b8ff;
    }
    QPushButton:disabled {
        color: #9da7b3;
        background-color: #21262d;
        border-color: #3d4652;
    }
    QWidget#adminHeader QPushButton {
        color: #c4ccd6;
        background-color: transparent;
        border: 1px solid transparent;
    }
    QWidget#adminHeader QPushButton:hover {
        color: #ffffff;
        background-color: #2d3744;
        border-color: #566273;
    }
    QWidget#adminHeader QPushButton:checked {
        color: #ffffff;
        background-color: #1f6feb;
        border-color: #79b8ff;
    }
    QPushButton#primaryActionButton {
        color: #ffffff;
        background-color: #1f6feb;
        border-color: #79b8ff;
        font-size: 24px;
        font-weight: 800;
        padding: 15px;
    }
    QPushButton#primaryActionButton:hover { background-color: #388bfd; }
    QPushButton#primaryActionButton:disabled {
        color: #aab4c0;
        background-color: #27313d;
        border-color: #4b5563;
    }
    QPushButton#dangerActionButton {
        color: #ffffff;
        background-color: #9e2636;
        border-color: #e06c75;
        font-weight: 800;
    }
    QPushButton#dangerActionButton:hover { background-color: #b83243; }
    QPushButton#dangerActionButton:disabled {
        color: #b6bec8;
        background-color: #35262b;
        border-color: #574047;
    }

    QLineEdit, QComboBox, QListWidget, QListView {
        color: #f0f6fc;
        background-color: #111820;
        border: 1px solid #566273;
        border-radius: 5px;
        padding: 7px;
        selection-color: #ffffff;
        selection-background-color: #1f6feb;
    }
    QLineEdit { placeholder-text-color: #9da7b3; }
    QLineEdit:focus, QComboBox:focus, QListWidget:focus, QListView:focus {
        color: #ffffff;
        border: 2px solid #58a6ff;
    }
    QLineEdit:disabled, QComboBox:disabled, QListWidget:disabled,
    QListView:disabled {
        color: #9da7b3;
        background-color: #20262e;
        border-color: #3d4652;
    }
    QListWidget::item, QListView::item {
        color: #f0f6fc;
        background-color: transparent;
        padding: 7px;
    }
    QListWidget::item:hover, QListView::item:hover {
        color: #ffffff;
        background-color: #283545;
    }
    QListWidget::item:selected, QListView::item:selected {
        color: #ffffff;
        background-color: #1f6feb;
        border: 1px solid #79b8ff;
    }
    QComboBox QAbstractItemView {
        color: #f0f6fc;
        background-color: #161b22;
        selection-color: #ffffff;
        selection-background-color: #1f6feb;
        border: 1px solid #566273;
    }
    QCheckBox {
        color: #f0f6fc;
        background-color: transparent;
        spacing: 8px;
    }
    QCheckBox:disabled { color: #9da7b3; }
    QCheckBox::indicator {
        width: 17px;
        height: 17px;
        border: 1px solid #8b98aa;
        border-radius: 3px;
        background-color: #111820;
    }
    QCheckBox::indicator:checked {
        background-color: #1f6feb;
        border-color: #79b8ff;
    }
    QGroupBox {
        color: #f0f6fc;
        background-color: #161b22;
        border: 1px solid #4b5563;
        border-radius: 8px;
        margin-top: 14px;
        padding: 16px 14px 14px 14px;
        font-weight: 700;
    }
    QGroupBox::title {
        color: #ffffff;
        background-color: #161b22;
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
    }
    QScrollBar:vertical, QScrollBar:horizontal {
        background-color: #161b22;
        border: none;
    }
    QScrollBar::handle {
        background-color: #566273;
        border-radius: 4px;
        min-height: 24px;
        min-width: 24px;
    }
"""
