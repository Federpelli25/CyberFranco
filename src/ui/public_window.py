from pathlib import Path

from PySide6.QtCore import (
    Qt,
    Signal,
    QPropertyAnimation,
    QVariantAnimation,
    QSequentialAnimationGroup,
    QParallelAnimationGroup,
    QPauseAnimation,
    QEasingCurve,
)
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QGraphicsOpacityEffect,
)


class PublicWindow(QMainWindow):

    reveal_finished = Signal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "CyberFranco - Public Display"
        )

        self.resize(
            1280,
            720,
        )

        self.teams_root = Path(
            "assets/teams"
        )

        self.reveal_animation = None
        self.size_animation = None

        self._build_ui()
        self.show_idle()

    def _build_ui(self):
        self.central_widget = QWidget()

        self.setCentralWidget(
            self.central_widget
        )

        self.layout = QVBoxLayout(
            self.central_widget
        )

        self.layout.setContentsMargins(
            40,
            40,
            40,
            40,
        )

        self.logo_label = QLabel()

        self.logo_label.setAlignment(
            Qt.AlignCenter
        )

        self.logo_label.setVisible(
            False
        )

        self.main_label = QLabel()

        self.main_label.setAlignment(
            Qt.AlignCenter
        )

        self.opacity_effect = (
            QGraphicsOpacityEffect(
                self.main_label
            )
        )

        self.main_label.setGraphicsEffect(
            self.opacity_effect
        )

        self.layout.addStretch()

        self.layout.addWidget(
            self.logo_label
        )

        self.layout.addWidget(
            self.main_label
        )

        self.layout.addStretch()

    def show_idle(self):
        self._stop_current_animation()

        self.central_widget.setStyleSheet(
            """
            QWidget {
                background-color: #080808;
            }
            """
        )

        self.logo_label.clear()

        self.logo_label.setVisible(
            False
        )

        self.main_label.setText(
            "Dimmi il tuo nome..."
        )

        self.main_label.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 54px;
                font-weight: 600;
            }
            """
        )

        self.opacity_effect.setOpacity(
            1.0
        )

    def show_thinking(self):
        self._stop_current_animation()

        self.logo_label.clear()

        self.logo_label.setVisible(
            False
        )

        self.central_widget.setStyleSheet(
            """
            QWidget {
                background:
                    qradialgradient(
                        cx: 0.5,
                        cy: 0.5,
                        radius: 0.8,
                        fx: 0.5,
                        fy: 0.5,
                        stop: 0 #252525,
                        stop: 0.45 #111111,
                        stop: 1 #050505
                    );
            }
            """
        )

        self.main_label.setText(
            "Mmmh..."
        )

        self.main_label.setStyleSheet(
            """
            QLabel {
                color: #dddddd;
                font-size: 72px;
                font-weight: 700;
                letter-spacing: 4px;
            }
            """
        )

        self.opacity_effect.setOpacity(
            1.0
        )

    def show_team(
        self,
        participant_name: str,
        team: str,
    ):
        self._stop_current_animation()

        team = team.strip()

        if not team:
            team = "SQUADRA"

        team_slug = (
            self._slugify_team_name(
                team
            )
        )

        team_directory = (
            self.teams_root
            / team_slug
        )

        logo_path = (
            team_directory
            / "logo.png"
        )

        background_path = (
            team_directory
            / "background.png"
        )

        self._apply_team_background(
            background_path
        )

        self._load_team_logo(
            logo_path
        )

        self.main_label.setText(
            team.upper()
        )

        self._set_team_text_style(
            font_size=95
        )

        self.opacity_effect.setOpacity(
            0.0
        )

        self._start_reveal_animation()

    def _apply_team_background(
        self,
        background_path: Path,
    ):
        if background_path.exists():
            normalized_path = (
                background_path
                .resolve()
                .as_posix()
            )

            self.central_widget.setStyleSheet(
                f"""
                QWidget {{
                    background-image:
                        url("{normalized_path}");
                    background-position: center;
                    background-repeat: no-repeat;
                    background-color: #080808;
                }}
                """
            )

            return

        self.central_widget.setStyleSheet(
            """
            QWidget {
                background:
                    qradialgradient(
                        cx: 0.5,
                        cy: 0.5,
                        radius: 0.9,
                        fx: 0.5,
                        fy: 0.5,
                        stop: 0 #303030,
                        stop: 0.45 #151515,
                        stop: 1 #050505
                    );
            }
            """
        )

    def _load_team_logo(
        self,
        logo_path: Path,
    ):
        if not logo_path.exists():
            self.logo_label.clear()

            self.logo_label.setVisible(
                False
            )

            return

        pixmap = QPixmap(
            str(logo_path)
        )

        if pixmap.isNull():
            self.logo_label.clear()

            self.logo_label.setVisible(
                False
            )

            return

        scaled_pixmap = pixmap.scaled(
            320,
            320,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.logo_label.setPixmap(
            scaled_pixmap
        )

        self.logo_label.setVisible(
            True
        )

    def _start_reveal_animation(self):
        fade_in = QPropertyAnimation(
            self.opacity_effect,
            b"opacity",
        )

        fade_in.setDuration(
            400
        )

        fade_in.setStartValue(
            0.0
        )

        fade_in.setEndValue(
            1.0
        )

        fade_in.setEasingCurve(
            QEasingCurve.OutCubic
        )

        self.size_animation = (
            QVariantAnimation()
        )

        self.size_animation.setDuration(
            600
        )

        self.size_animation.setStartValue(
            95
        )

        self.size_animation.setEndValue(
            145
        )

        self.size_animation.setEasingCurve(
            QEasingCurve.OutBack
        )

        self.size_animation.valueChanged.connect(
            lambda value:
                self._set_team_text_style(
                    int(value)
                )
        )

        entrance = (
            QParallelAnimationGroup()
        )

        entrance.addAnimation(
            fade_in
        )

        entrance.addAnimation(
            self.size_animation
        )

        pause = QPauseAnimation(
            1800
        )

        fade_out = QPropertyAnimation(
            self.opacity_effect,
            b"opacity",
        )

        fade_out.setDuration(
            500
        )

        fade_out.setStartValue(
            1.0
        )

        fade_out.setEndValue(
            0.0
        )

        fade_out.setEasingCurve(
            QEasingCurve.InCubic
        )

        self.reveal_animation = (
            QSequentialAnimationGroup()
        )

        self.reveal_animation.addAnimation(
            entrance
        )

        self.reveal_animation.addAnimation(
            pause
        )

        self.reveal_animation.addAnimation(
            fade_out
        )

        self.reveal_animation.finished.connect(
            self._reset_after_reveal
        )

        self.reveal_animation.start()

    def _set_team_text_style(
        self,
        font_size: int,
    ):
        self.main_label.setStyleSheet(
            f"""
            QLabel {{
                color: white;
                font-size: {font_size}px;
                font-weight: 900;
                letter-spacing: 10px;
            }}
            """
        )

    def _reset_after_reveal(self):
        self.show_idle()

        self.reveal_finished.emit()

    def _stop_current_animation(self):
        if self.reveal_animation is not None:
            if (
                self.reveal_animation.state()
                !=
                self.reveal_animation.State.Stopped
            ):
                self.reveal_animation.stop()

    @staticmethod
    def _slugify_team_name(
        team: str,
    ) -> str:
        return (
            team.strip()
            .lower()
            .replace(
                " ",
                "_",
            )
        )