import logging
import math
import random
from pathlib import Path

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPointF,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QRectF,
    QSequentialAnimationGroup,
    QTimer,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget


logger = logging.getLogger(__name__)


class FaceWidget(QWidget):
    """Volto pubblico scalabile, animato e indipendente dalla business logic."""

    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    REVEAL = "REVEAL"

    ASSET_NAMES = {
        IDLE: "idle.png",
        "BLINK": "blink.png",
        LISTENING: "listening.png",
        THINKING: "thinking_01.png",
        AWAITING_CONFIRMATION: "thinking_02.png",
        REVEAL: "reveal.png",
    }

    def __init__(
        self,
        assets_root: str | Path | None = None,
        blink_min_ms: int = 3000,
        blink_max_ms: int = 6500,
        random_source=None,
        parent=None,
    ):
        super().__init__(parent)
        self.assets_root = Path(assets_root or "assets/face")
        self.blink_min_ms = max(100, int(blink_min_ms))
        self.blink_max_ms = max(self.blink_min_ms, int(blink_max_ms))
        self._random = random_source or random.Random()
        self._state = self.IDLE
        self._generation = 0
        self._using_fallback = True
        self._assets: dict[str, QPixmap] = {}
        self._gaze = 0.0
        self._float_offset = 0.0
        self._glow = 0.15
        self._eye_openness = 1.0
        self._face_scale = 1.0
        self._head_tilt = 0.0
        self._brow_raise = 0.0
        self._mouth_expression = 0.15
        self._mesh_phase = 0.0
        self._talking = False
        self.thinking_variant = 0

        self.setMinimumSize(320, 240)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self._load_assets()

        self.blink_timer = QTimer(self)
        self.blink_timer.setSingleShot(True)
        self.blink_timer.timeout.connect(self._blink)
        self.thinking_timer = QTimer(self)
        self.thinking_timer.timeout.connect(self._advance_thinking)

        self._animations = []
        self.set_idle()

    @property
    def state(self) -> str:
        return self._state

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def using_fallback(self) -> bool:
        return self._using_fallback

    def set_state(self, state) -> None:
        normalized = getattr(state, "value", state)
        normalized = str(normalized).upper()
        handlers = {
            self.IDLE: self.set_idle,
            self.LISTENING: self.set_listening,
            self.THINKING: self.set_thinking,
            self.AWAITING_CONFIRMATION: self.set_awaiting_confirmation,
            self.REVEAL: self.set_reveal,
        }
        if normalized not in handlers:
            logger.warning("Unknown face state ignored: %s", normalized)
            return
        if normalized == self._state:
            return
        handlers[normalized]()

    def set_idle(self) -> None:
        self._begin_state(self.IDLE)
        self._set_visual_values(
            gaze=0.0, glow=0.15, openness=0.92, scale=1.0,
            tilt=0.0, brow=0.0, mouth=0.18,
        )
        self._start_float_animation(amplitude=5.0, duration=2400)
        self._start_mesh_animation(duration=7200)
        self._schedule_blink()

    def set_listening(self) -> None:
        self._begin_state(self.LISTENING)
        self._set_visual_values(
            gaze=0.0, glow=0.72, openness=1.28, scale=1.04,
            tilt=7.0, brow=0.78, mouth=0.62,
        )
        self._start_float_animation(amplitude=3.0, duration=1300)
        self._start_pulse_animation(0.45, 0.95, 850)
        self._start_mesh_animation(duration=2300)

    def set_thinking(self) -> None:
        self._begin_state(self.THINKING)
        self.thinking_variant = self._random.randint(1, 4)
        logger.info("Face thinking variant selected: %d", self.thinking_variant)
        pose = self._thinking_pose(self.thinking_variant)
        self._set_visual_values(
            gaze=pose[0], glow=0.42, openness=pose[1], scale=1.0,
            tilt=pose[2], brow=pose[3], mouth=pose[4],
        )
        self._start_float_animation(amplitude=7.0, duration=1800)
        self._start_mesh_animation(duration=1400)
        self.thinking_timer.start(420 + (self.thinking_variant * 70))

    def set_awaiting_confirmation(self) -> None:
        if self._state == self.THINKING:
            self._state = self.AWAITING_CONFIRMATION
            self._glow = 0.55
            self._head_tilt = -3.0
            self._brow_raise = 0.38
            self._mouth_expression = 0.42
            self._eye_openness = 1.02
            self.thinking_timer.setInterval(1100)
            logger.info("Face state changed: %s (continuous)", self._state)
            self.update()
            return
        self._begin_state(self.AWAITING_CONFIRMATION)
        self._set_visual_values(
            gaze=0.2, glow=0.55, openness=1.02, scale=1.0,
            tilt=-3.0, brow=0.38, mouth=0.42,
        )
        self._start_float_animation(amplitude=6.0, duration=1800)
        self._start_mesh_animation(duration=3200)
        self.thinking_timer.start(650)

    def set_reveal(self) -> None:
        self._begin_state(self.REVEAL)
        self._set_visual_values(
            gaze=0.0, glow=1.0, openness=1.42, scale=1.0,
            tilt=0.0, brow=0.9, mouth=1.0,
        )
        animation = QPropertyAnimation(self, b"faceScale", self)
        animation.setDuration(260)
        animation.setStartValue(1.0)
        animation.setEndValue(1.12)
        animation.setEasingCurve(QEasingCurve.OutBack)
        self._start_animation(animation)
        flash = QPropertyAnimation(self, b"glow", self)
        flash.setDuration(260)
        flash.setStartValue(1.0)
        flash.setEndValue(0.58)
        flash.setEasingCurve(QEasingCurve.OutCubic)
        self._start_animation(flash)
        self._start_mesh_animation(duration=520)

    def set_talking(self, talking: bool) -> None:
        """API predisposta per la futura fase voce, senza collegamenti audio."""
        self._talking = bool(talking)
        self.update()

    def stop_animations(self) -> None:
        self.blink_timer.stop()
        self.thinking_timer.stop()
        for animation in self._animations:
            animation.stop()
        self._animations.clear()

    def is_callback_current(self, generation: int) -> bool:
        return generation == self._generation

    def closeEvent(self, event) -> None:
        self.stop_animations()
        self._generation += 1
        super().closeEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#05070b"))
        pixmap = self._asset_for_current_state()
        if pixmap is not None:
            self._paint_asset(painter, pixmap)
        else:
            self._paint_fallback(painter)

    def _load_assets(self) -> None:
        for state, filename in self.ASSET_NAMES.items():
            path = self.assets_root / filename
            pixmap = QPixmap(str(path))
            if path.is_file() and not pixmap.isNull():
                self._assets[state] = pixmap
                logger.info("Face asset loaded: state=%s path=%s", state, path)
            else:
                logger.warning("Face asset missing; fallback enabled: %s", path)
        self._using_fallback = not bool(self._assets)
        if self._using_fallback:
            logger.info("Digital face using Qt painted fallback")

    def _asset_for_current_state(self) -> QPixmap | None:
        if self._eye_openness < 0.3 and "BLINK" in self._assets:
            return self._assets["BLINK"]
        return self._assets.get(self._state) or self._assets.get(self.IDLE)

    def _paint_asset(self, painter: QPainter, pixmap: QPixmap) -> None:
        available = self.rect().adjusted(40, 40, -40, -40)
        scaled = pixmap.scaled(
            available.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        x = available.center().x() - scaled.width() / 2
        y = available.center().y() - scaled.height() / 2 + self._float_offset
        painter.save()
        painter.translate(self.rect().center())
        painter.scale(self._face_scale, self._face_scale)
        painter.translate(-self.rect().center())
        painter.drawPixmap(QPointF(x, y), scaled)
        painter.restore()

    def _paint_fallback(self, painter: QPainter) -> None:
        side = min(self.width(), self.height()) * 0.70 * self._face_scale
        center = QPointF(
            self.width() / 2,
            self.height() / 2 + self._float_offset - side * 0.02,
        )
        accent = self._accent_color()
        painter.save()
        painter.translate(center)
        painter.rotate(self._head_tilt)
        painter.translate(-center)
        painter.setCompositionMode(QPainter.CompositionMode_Plus)

        aura = QRadialGradient(center, side * 0.72)
        aura_color = QColor(accent)
        aura_color.setAlphaF(0.08 + self._glow * 0.13)
        aura.setColorAt(0.0, aura_color)
        aura.setColorAt(1.0, QColor(5, 7, 11, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(aura)
        painter.drawEllipse(center, side * 0.74, side * 0.74)

        face = QPainterPath()
        face.moveTo(center.x(), center.y() - side * 0.48)
        face.cubicTo(
            center.x() - side * 0.31, center.y() - side * 0.48,
            center.x() - side * 0.39, center.y() - side * 0.25,
            center.x() - side * 0.34, center.y() + side * 0.05,
        )
        face.cubicTo(
            center.x() - side * 0.30, center.y() + side * 0.31,
            center.x() - side * 0.13, center.y() + side * 0.43,
            center.x(), center.y() + side * 0.46,
        )
        face.cubicTo(
            center.x() + side * 0.13, center.y() + side * 0.43,
            center.x() + side * 0.30, center.y() + side * 0.31,
            center.x() + side * 0.34, center.y() + side * 0.05,
        )
        face.cubicTo(
            center.x() + side * 0.39, center.y() - side * 0.25,
            center.x() + side * 0.31, center.y() - side * 0.48,
            center.x(), center.y() - side * 0.48,
        )
        face.closeSubpath()
        painter.setBrush(Qt.NoBrush)
        painter.setPen(self._glow_pen(accent, side * 0.030, 0.12 + self._glow * 0.18))
        painter.drawPath(face)
        painter.setPen(self._glow_pen(accent, side * 0.006, 0.90))
        painter.drawPath(face)

        self._paint_mesh(painter, center, side, accent)
        self._paint_orbiting_particles(painter, center, side, accent)

        eye_y = center.y() - side * 0.075
        eye_dx = side * 0.16
        eye_w = side * 0.16
        eye_h = max(3.0, side * 0.078 * self._eye_openness)
        gaze_shift = self._gaze * side * 0.042
        for direction in (-1, 1):
            eye_center = QPointF(center.x() + direction * eye_dx, eye_y)
            self._paint_holographic_eye(
                painter, eye_center, eye_w, eye_h, gaze_shift, accent, side
            )

            brow_y = eye_y - side * (0.105 + self._brow_raise * 0.025)
            brow_tilt = (
                direction * side * 0.025 * self._brow_raise
                if self._state != self.THINKING
                else direction * side * 0.035 * (self.thinking_variant - 2.5)
            )
            brow = QPainterPath()
            brow.moveTo(eye_center.x() - eye_w * 0.58, brow_y + brow_tilt)
            brow.quadTo(
                eye_center.x(), brow_y - side * 0.018,
                eye_center.x() + eye_w * 0.58, brow_y - brow_tilt,
            )
            painter.setPen(self._glow_pen(accent, side * 0.012, 0.78))
            painter.drawPath(brow)

        nose = QPainterPath()
        nose.moveTo(center.x() + side * 0.012, center.y() - side * 0.015)
        nose.quadTo(
            center.x() + side * 0.045, center.y() + side * 0.095,
            center.x() - side * 0.015, center.y() + side * 0.105,
        )
        painter.setBrush(Qt.NoBrush)
        painter.setPen(self._glow_pen(accent, side * 0.005, 0.48))
        painter.drawPath(nose)

        self._paint_mouth(painter, center, side, accent)
        painter.restore()

    def _paint_mesh(self, painter, center, side, accent) -> None:
        rows = []
        for row_index, normalized_y in enumerate(
            (-0.39, -0.30, -0.20, -0.10, 0.0, 0.10, 0.20, 0.30, 0.38)
        ):
            half_width = side * 0.32 * math.sqrt(
                max(0.0, 1.0 - (normalized_y / 0.46) ** 2)
            )
            row = []
            for column in range(7):
                horizontal = (column - 3) / 3
                phase = self._mesh_phase + row_index * 0.63 + column * 0.91
                jitter_x = math.sin(phase) * side * 0.006 * self._mesh_activity()
                jitter_y = math.cos(phase * 1.17) * side * 0.005 * self._mesh_activity()
                row.append(QPointF(
                    center.x() + half_width * horizontal + jitter_x,
                    center.y() + side * normalized_y + jitter_y,
                ))
            rows.append(row)

        line_alpha = 0.16 + self._glow * 0.18
        painter.setBrush(Qt.NoBrush)
        painter.setPen(self._glow_pen(accent, side * 0.0022, line_alpha))
        for row_index, row in enumerate(rows):
            for column in range(6):
                painter.drawLine(row[column], row[column + 1])
            if row_index == 0:
                continue
            previous = rows[row_index - 1]
            for column in range(7):
                painter.drawLine(previous[column], row[column])
                if column < 6 and (column + row_index + self.thinking_variant) % 2:
                    painter.drawLine(previous[column], row[column + 1])

        for row_index, row in enumerate(rows):
            for column, point in enumerate(row):
                pulse = 0.55 + 0.45 * math.sin(
                    self._mesh_phase * 1.4 + row_index + column * 0.7
                )
                color = QColor(accent)
                color.setAlphaF(min(1.0, 0.38 + pulse * (0.30 + self._glow * 0.18)))
                painter.setPen(Qt.NoPen)
                painter.setBrush(color)
                radius = side * (0.0032 + pulse * 0.0028)
                painter.drawEllipse(point, radius, radius)

    def _paint_orbiting_particles(self, painter, center, side, accent) -> None:
        count = 22 if self._state == self.IDLE else 34
        if self._state in (self.THINKING, self.REVEAL):
            count = 46
        painter.setPen(Qt.NoPen)
        for index in range(count):
            angle = index * 2.399 + self._mesh_phase * (0.08 + index % 3 * 0.025)
            radius = side * (0.43 + (index % 7) * 0.027)
            point = QPointF(
                center.x() + math.cos(angle) * radius,
                center.y() + math.sin(angle) * radius * 0.88,
            )
            color = QColor(accent)
            color.setAlphaF(0.20 + (index % 5) * 0.10)
            painter.setBrush(color)
            dot = side * (0.0025 + (index % 4) * 0.0012)
            painter.drawEllipse(point, dot, dot)

    def _paint_holographic_eye(
        self, painter, eye_center, eye_w, eye_h, gaze_shift, accent, side
    ) -> None:
        eye = QPainterPath()
        eye.moveTo(eye_center.x() - eye_w / 2, eye_center.y())
        eye.quadTo(
            eye_center.x(), eye_center.y() - eye_h,
            eye_center.x() + eye_w / 2, eye_center.y(),
        )
        eye.quadTo(
            eye_center.x(), eye_center.y() + eye_h,
            eye_center.x() - eye_w / 2, eye_center.y(),
        )
        painter.setBrush(Qt.NoBrush)
        painter.setPen(self._glow_pen(accent, side * 0.010, 0.92))
        painter.drawPath(eye)
        iris_center = QPointF(eye_center.x() + gaze_shift, eye_center.y())
        iris_radius = min(eye_w, eye_h * 2) * 0.27
        painter.setPen(self._glow_pen(QColor("#e9ffff"), side * 0.007, 0.95))
        painter.drawEllipse(iris_center, iris_radius, iris_radius)
        painter.setPen(self._glow_pen(accent, side * 0.003, 0.70))
        for spoke in range(8):
            angle = spoke * math.pi / 4 + self._mesh_phase * 0.04
            painter.drawLine(
                iris_center,
                QPointF(
                    iris_center.x() + math.cos(angle) * iris_radius,
                    iris_center.y() + math.sin(angle) * iris_radius,
                ),
            )
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#eaffff"))
        pupil = side * (0.008 if self._state != self.REVEAL else 0.011)
        painter.drawEllipse(iris_center, pupil, pupil)

    def _paint_mouth(self, painter, center, side, accent) -> None:
        mouth_y = center.y() + side * 0.215
        width = side * (0.12 + 0.055 * abs(self._mouth_expression))
        if self._state == self.LISTENING:
            painter.setPen(self._glow_pen(accent, side * 0.008, 0.82))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(
                QPointF(center.x(), mouth_y), side * 0.055, side * 0.072
            )
            return
        if self._state == self.REVEAL:
            mouth = QRectF(
                center.x() - side * 0.16, mouth_y - side * 0.025,
                side * 0.32, side * 0.15,
            )
            painter.setPen(self._glow_pen(accent, side * 0.010, 0.95))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(mouth, side * 0.07, side * 0.07)
            painter.setPen(self._glow_pen(QColor("#f2ffff"), side * 0.005, 0.88))
            painter.drawLine(
                QPointF(mouth.left() + side * 0.035, mouth.center().y()),
                QPointF(mouth.right() - side * 0.035, mouth.center().y()),
            )
            return

        curve = side * 0.075 * self._mouth_expression
        if self._state == self.THINKING and self.thinking_variant == 2:
            curve *= -1.0
        mouth = QPainterPath()
        mouth.moveTo(center.x() - width, mouth_y)
        mouth.quadTo(center.x(), mouth_y + curve, center.x() + width, mouth_y)
        painter.setPen(self._glow_pen(accent, side * 0.009, 0.80))
        painter.drawPath(mouth)

    def _mesh_activity(self) -> float:
        return {
            self.IDLE: 0.35,
            self.LISTENING: 0.75,
            self.THINKING: 1.35,
            self.AWAITING_CONFIRMATION: 0.65,
            self.REVEAL: 1.6,
        }.get(self._state, 0.35)

    @staticmethod
    def _glow_pen(color, width, alpha):
        glow = QColor(color)
        glow.setAlphaF(max(0.0, min(1.0, alpha)))
        return QPen(glow, max(1.0, width), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

    def _accent_color(self) -> QColor:
        return {
            self.IDLE: QColor("#68e1fd"),
            self.LISTENING: QColor("#38bdf8"),
            self.THINKING: QColor("#c4b5fd"),
            self.AWAITING_CONFIRMATION: QColor("#5eead4"),
            self.REVEAL: QColor("#ffffff"),
        }.get(self._state, QColor("#68e1fd"))

    def _begin_state(self, state: str) -> None:
        self.stop_animations()
        self._generation += 1
        self._state = state
        logger.info("Face state changed: %s", state)

    def _set_visual_values(
        self, gaze, glow, openness, scale, tilt, brow, mouth
    ) -> None:
        self._gaze = gaze
        self._glow = glow
        self._eye_openness = openness
        self._face_scale = scale
        self._head_tilt = tilt
        self._brow_raise = brow
        self._mouth_expression = mouth
        self._float_offset = 0.0
        self.update()

    def _schedule_blink(self) -> None:
        if self._state != self.IDLE:
            return
        self.blink_timer.start(
            self._random.randint(self.blink_min_ms, self.blink_max_ms)
        )

    def _blink(self) -> None:
        generation = self._generation
        if self._state != self.IDLE or not self.is_callback_current(generation):
            return
        group = QSequentialAnimationGroup(self)
        close = QPropertyAnimation(self, b"eyeOpenness", group)
        close.setDuration(90)
        close.setStartValue(self._eye_openness)
        close.setEndValue(0.08)
        reopen = QPropertyAnimation(self, b"eyeOpenness", group)
        reopen.setDuration(120)
        reopen.setStartValue(0.08)
        reopen.setEndValue(1.0)
        group.addAnimation(close)
        group.addAnimation(reopen)
        group.finished.connect(
            lambda: self._schedule_blink()
            if self.is_callback_current(generation) else None
        )
        self._start_animation(group)

    def _advance_thinking(self) -> None:
        if self._state not in (self.THINKING, self.AWAITING_CONFIRMATION):
            return
        self.thinking_variant = (self.thinking_variant % 4) + 1
        pose = self._thinking_pose(self.thinking_variant)
        if self._state == self.AWAITING_CONFIRMATION:
            pose = (pose[0] * 0.45, 1.02, -3.0, 0.38, 0.42)
        group = QParallelAnimationGroup(self)
        for property_name, start, end in (
            (b"gaze", self._gaze, pose[0]),
            (b"eyeOpenness", self._eye_openness, pose[1]),
            (b"headTilt", self._head_tilt, pose[2]),
            (b"browRaise", self._brow_raise, pose[3]),
            (b"mouthExpression", self._mouth_expression, pose[4]),
        ):
            animation = QPropertyAnimation(self, property_name, group)
            animation.setDuration(360)
            animation.setStartValue(start)
            animation.setEndValue(end)
            animation.setEasingCurve(QEasingCurve.InOutSine)
            group.addAnimation(animation)
        self._start_animation(group)

    @staticmethod
    def _thinking_pose(variant: int):
        return {
            1: (-0.72, 0.82, -8.0, -0.18, -0.10),
            2: (0.68, 0.92, 9.0, 0.32, -0.55),
            3: (-0.18, 0.70, 4.0, -0.42, 0.05),
            4: (0.35, 1.08, -5.0, 0.58, 0.48),
        }[variant]

    def _start_float_animation(self, amplitude: float, duration: int) -> None:
        animation = QPropertyAnimation(self, b"floatOffset", self)
        animation.setDuration(duration)
        animation.setStartValue(-amplitude)
        animation.setKeyValueAt(0.5, amplitude)
        animation.setEndValue(-amplitude)
        animation.setLoopCount(-1)
        animation.setEasingCurve(QEasingCurve.InOutSine)
        self._start_animation(animation)

    def _start_pulse_animation(self, low: float, high: float, duration: int) -> None:
        animation = QPropertyAnimation(self, b"glow", self)
        animation.setDuration(duration)
        animation.setStartValue(low)
        animation.setKeyValueAt(0.5, high)
        animation.setEndValue(low)
        animation.setLoopCount(-1)
        animation.setEasingCurve(QEasingCurve.InOutSine)
        self._start_animation(animation)

    def _start_mesh_animation(self, duration: int) -> None:
        animation = QPropertyAnimation(self, b"meshPhase", self)
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(math.tau)
        animation.setLoopCount(-1)
        animation.setEasingCurve(QEasingCurve.Linear)
        self._start_animation(animation)

    def _start_animation(self, animation) -> None:
        self._animations.append(animation)
        animation.finished.connect(
            lambda current=animation: self._discard_animation(current)
        )
        animation.start()

    def _discard_animation(self, animation) -> None:
        if animation in self._animations:
            self._animations.remove(animation)

    def _get_gaze(self):
        return self._gaze

    def _set_gaze(self, value):
        self._gaze = float(value)
        self.update()

    def _get_float_offset(self):
        return self._float_offset

    def _set_float_offset(self, value):
        self._float_offset = float(value)
        self.update()

    def _get_glow(self):
        return self._glow

    def _set_glow(self, value):
        self._glow = float(value)
        self.update()

    def _get_eye_openness(self):
        return self._eye_openness

    def _set_eye_openness(self, value):
        self._eye_openness = float(value)
        self.update()

    def _get_face_scale(self):
        return self._face_scale

    def _set_face_scale(self, value):
        self._face_scale = float(value)
        self.update()

    def _get_head_tilt(self):
        return self._head_tilt

    def _set_head_tilt(self, value):
        self._head_tilt = float(value)
        self.update()

    def _get_brow_raise(self):
        return self._brow_raise

    def _set_brow_raise(self, value):
        self._brow_raise = float(value)
        self.update()

    def _get_mouth_expression(self):
        return self._mouth_expression

    def _set_mouth_expression(self, value):
        self._mouth_expression = float(value)
        self.update()

    def _get_mesh_phase(self):
        return self._mesh_phase

    def _set_mesh_phase(self, value):
        self._mesh_phase = float(value)
        self.update()

    gaze = Property(float, _get_gaze, _set_gaze)
    floatOffset = Property(float, _get_float_offset, _set_float_offset)
    glow = Property(float, _get_glow, _set_glow)
    eyeOpenness = Property(float, _get_eye_openness, _set_eye_openness)
    faceScale = Property(float, _get_face_scale, _set_face_scale)
    headTilt = Property(float, _get_head_tilt, _set_head_tilt)
    browRaise = Property(float, _get_brow_raise, _set_brow_raise)
    mouthExpression = Property(
        float, _get_mouth_expression, _set_mouth_expression
    )
    meshPhase = Property(float, _get_mesh_phase, _set_mesh_phase)
