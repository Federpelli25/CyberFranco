import logging
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
    QTimer,
)
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QGraphicsOpacityEffect,
)
from src.config.settings_loader import AppSettings
from src.ui.display_manager import DisplayManager
from src.ui.face_widget import FaceWidget
from src.config.team_config_loader import TeamConfigLoader


logger = logging.getLogger(__name__)


class PublicWindow(QMainWindow):

    reveal_finished = Signal()
    team_warning = Signal(str)

    def __init__(
        self,
        settings: AppSettings,
        display_manager: DisplayManager | None = None,
        team_config_loader: TeamConfigLoader | None = None,
    ):
        super().__init__()

        self.settings = settings
        self.display_manager = display_manager or DisplayManager()
        self.team_config_loader = team_config_loader or TeamConfigLoader(
            settings.project_root
        )

        self.setWindowTitle(
            "CyberFranco - Public Display"
        )

        self.resize(
            1280,
            720,
        )

        self.face_root = settings.resolve_project_path("assets/face")

        self.reveal_animation = None
        self.size_animation = None
        self._visual_generation = 0
        self._team_pixmap_cache = {}

        self._build_ui()
        self.show_idle()
        self.reload_team_assets()

    def reload_team_assets(self):
        """Precarica logo e background senza riavviare la finestra."""
        self._team_pixmap_cache.clear()
        for team in self.team_config_loader.teams:
            for path in (team.logo_path, team.background_path):
                if path is not None:
                    pixmap = QPixmap(str(path))
                    if not pixmap.isNull():
                        self._team_pixmap_cache[path] = pixmap

    def show_configured(self):
        self.apply_display_settings(
            self.settings.public_display_monitor,
            self.settings.public_display_fullscreen,
        )

    def apply_display_settings(
        self,
        screen_identifier,
        fullscreen: bool,
    ):
        try:
            selected = self.display_manager.resolve_screen(screen_identifier)
            if selected is None:
                logger.error("Public display cannot be shown: no Qt screen")
                self.showNormal()
                return

            geometry = selected["geometry"]
            self.showNormal()
            handle = self.windowHandle()
            if handle is not None:
                handle.setScreen(selected["screen"])
            self.setGeometry(
                geometry["x"],
                geometry["y"],
                geometry["width"],
                geometry["height"],
            )

            if fullscreen:
                self.showFullScreen()
                logger.info("Fullscreen enabled")
            else:
                self.showNormal()
                self.setGeometry(
                    geometry["x"],
                    geometry["y"],
                    geometry["width"],
                    geometry["height"],
                )
                logger.info("Fullscreen disabled")

            logger.info(
                "Public display moved: screen=%s geometry=%s,%s %sx%s",
                selected["index"],
                geometry["x"],
                geometry["y"],
                geometry["width"],
                geometry["height"],
            )
        except Exception:
            logger.exception("Public display positioning failed")
            self.showNormal()
            try:
                fallback = self.display_manager.get_primary_screen()
                if fallback is None:
                    return
                geometry = fallback["geometry"]
                self.setGeometry(
                    geometry["x"],
                    geometry["y"],
                    geometry["width"],
                    geometry["height"],
                )
                handle = self.windowHandle()
                if handle is not None:
                    handle.setScreen(fallback["screen"])
                logger.warning("Public display fallback to primary screen")
            except Exception:
                logger.exception("Primary screen fallback failed")

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

        self.face_widget = FaceWidget(self.face_root, parent=self.central_widget)

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

        self.layout.addWidget(self.face_widget, 1)

        self.layout.addWidget(
            self.logo_label
        )

        self.layout.addWidget(
            self.main_label
        )

        self.layout.addStretch()

    def show_idle(self):
        self._stop_current_animation()
        self._visual_generation += 1
        if self.face_widget.state != FaceWidget.IDLE:
            self.face_widget.set_idle()
        self.face_widget.setVisible(True)

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

    def show_listening(self):
        self._stop_current_animation()
        self._visual_generation += 1
        if self.face_widget.state != FaceWidget.LISTENING:
            self.face_widget.set_listening()
        self.face_widget.setVisible(True)

        self.logo_label.clear()

        self.logo_label.setVisible(
            False
        )

        self.central_widget.setStyleSheet(
            f"""
            QWidget {{
                background:
                    qradialgradient(
                        cx: 0.5,
                        cy: 0.5,
                        radius: 0.8,
                        fx: 0.5,
                        fy: 0.5,
                        stop: 0 #10294a,
                        stop: 0.5 #091421,
                        stop: 1 #050505
                    );
            }}
            """
        )

        self.main_label.setText(
            "Ti ascolto..."
        )

        self.main_label.setStyleSheet(
            """
            QLabel {
                color: #d7eaff;
                font-size: 68px;
                font-weight: 700;
                letter-spacing: 4px;
            }
            """
        )

        self.opacity_effect.setOpacity(
            1.0
        )

    def show_waiting_confirmation(self):
        self._stop_current_animation()
        self._visual_generation += 1
        if self.face_widget.state != FaceWidget.AWAITING_CONFIRMATION:
            self.face_widget.set_awaiting_confirmation()
        self.face_widget.setVisible(True)

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
                        stop: 0 #332817,
                        stop: 0.5 #15110b,
                        stop: 1 #050505
                    );
            }
            """
        )

        self.main_label.setText(
            "Aspetta... fammi pensare."
        )

        self.main_label.setStyleSheet(
            """
            QLabel {
                color: #e8d8b5;
                font-size: 64px;
                font-weight: 700;
                letter-spacing: 3px;
            }
            """
        )

        self.opacity_effect.setOpacity(
            1.0
        )

    def show_thinking(self):
        self._stop_current_animation()
        self._visual_generation += 1
        if self.face_widget.state != FaceWidget.THINKING:
            self.face_widget.set_thinking()
        self.face_widget.setVisible(True)

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
        self._visual_generation += 1
        generation = self._visual_generation
        self.face_widget.set_reveal()
        self.face_widget.setVisible(True)

        team_config = self.team_config_loader.resolve(team)
        if not team_config.configured:
            self.team_warning.emit(
                f'La squadra "{team_config.display_name}" non è configurata. '
                "Viene usato il fallback neutro."
            )
        logger.info("Public reveal: team=%s", team_config.key)

        self._apply_team_background(
            team_config.background_path,
            team_config.primary_color,
            team_config.secondary_color,
        )

        self._load_team_logo(
            team_config.logo_path
        )

        self.main_label.setText(
            team_config.display_name
            if team_config.configured
            else team_config.display_name.upper()
        )

        self._set_team_text_style(
            font_size=95
        )

        self.opacity_effect.setOpacity(
            0.0
        )

        QTimer.singleShot(
            220,
            lambda: self._begin_team_reveal(generation),
        )

    def set_state(self, state) -> None:
        """Adatta la faccia allo stato autorevole dell'applicazione."""
        normalized = getattr(state, "value", state)
        if str(normalized).upper() == "REVEAL":
            self.face_widget.set_reveal()
            return
        self.face_widget.set_state(normalized)

    def _begin_team_reveal(self, generation: int) -> None:
        if generation != self._visual_generation:
            logger.debug("Stale public reveal transition ignored")
            return
        self.face_widget.setVisible(False)
        self._start_reveal_animation()

    def _apply_team_background(
        self,
        background_path: Path | None,
        primary_color: str = "#303030",
        secondary_color: str = "#151515",
    ):
        if background_path is not None and background_path.exists():
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

        logger.info("Team background fallback: %s", background_path or "not configured")

        self.central_widget.setStyleSheet(
            f"""
            QWidget {{
                background:
                    qradialgradient(
                        cx: 0.5,
                        cy: 0.5,
                        radius: 0.9,
                        fx: 0.5,
                        fy: 0.5,
                        stop: 0 {primary_color},
                        stop: 0.45 {secondary_color},
                        stop: 1 #050505
                    );
            }}
            """
        )

    def _load_team_logo(
        self,
        logo_path: Path | None,
    ):
        if logo_path is None or not logo_path.exists():
            logger.warning("Team logo missing: %s", logo_path)
            self.logo_label.clear()

            self.logo_label.setVisible(
                False
            )

            return

        pixmap = self._team_pixmap_cache.get(logo_path)
        if pixmap is None:
            pixmap = QPixmap(str(logo_path))

        if pixmap.isNull():
            logger.warning("Team logo is invalid: %s", logo_path)
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
        logger.info("Reveal completed")
        self.show_idle()

        self.reveal_finished.emit()

    def _stop_current_animation(self):
        if self.reveal_animation is not None:
            self.reveal_animation.stop()

    def closeEvent(self, event):
        self._visual_generation += 1
        self._stop_current_animation()
        self.face_widget.stop_animations()
        super().closeEvent(event)

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
