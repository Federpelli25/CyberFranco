import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QAbstractAnimation, Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication

from src.ui.face_widget import FaceWidget


class FaceWidgetTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_initial_state_is_animated_idle_with_missing_asset_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            widget = FaceWidget(Path(directory) / "missing")
            self.assertEqual(widget.state, FaceWidget.IDLE)
            self.assertTrue(widget.using_fallback)
            self.assertTrue(widget.blink_timer.isActive())
            self.assertGreater(len(widget._animations), 0)
            widget.close()

    def test_assets_are_preloaded_and_keep_source_aspect_ratio(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pixmap = QPixmap(200, 100)
            pixmap.fill(QColor("cyan"))
            self.assertTrue(pixmap.save(str(root / "idle.png")))
            widget = FaceWidget(root)
            loaded = widget._assets[FaceWidget.IDLE]
            scaled = loaded.scaled(300, 300, Qt.KeepAspectRatio)
            self.assertEqual((loaded.width(), loaded.height()), (200, 100))
            self.assertEqual((scaled.width(), scaled.height()), (300, 150))
            self.assertFalse(widget.using_fallback)
            widget.close()

    def test_state_change_stops_old_animations_and_idle_timer(self):
        widget = FaceWidget(Path("missing-assets-for-test"))
        old_animations = list(widget._animations)
        self.assertTrue(widget.blink_timer.isActive())
        widget.set_listening()
        self.assertFalse(widget.blink_timer.isActive())
        self.assertTrue(all(
            item.state() == QAbstractAnimation.Stopped for item in old_animations
        ))
        widget.close()

    def test_listening_pose_is_visibly_distinct_from_idle(self):
        widget = FaceWidget(Path("missing-assets-for-test"))
        idle_pose = (
            widget._eye_openness, widget._head_tilt,
            widget._brow_raise, widget._mouth_expression,
        )
        widget.set_listening()
        listening_pose = (
            widget._eye_openness, widget._head_tilt,
            widget._brow_raise, widget._mouth_expression,
        )
        self.assertNotEqual(idle_pose, listening_pose)
        self.assertGreater(widget._eye_openness, idle_pose[0])
        self.assertGreater(widget._brow_raise, idle_pose[2])
        self.assertNotEqual(widget._head_tilt, 0.0)
        widget.close()

    def test_four_thinking_variants_define_distinct_expressive_poses(self):
        poses = {FaceWidget._thinking_pose(index) for index in range(1, 5)}
        self.assertEqual(len(poses), 4)
        self.assertEqual({pose[2] for pose in poses}, {-8.0, 9.0, 4.0, -5.0})

    def test_mesh_activity_is_strongest_during_reveal_and_thinking(self):
        widget = FaceWidget(Path("missing-assets-for-test"))
        widget.set_idle()
        idle = widget._mesh_activity()
        widget.set_listening()
        listening = widget._mesh_activity()
        widget.set_thinking()
        thinking = widget._mesh_activity()
        widget.set_reveal()
        reveal = widget._mesh_activity()
        self.assertLess(idle, listening)
        self.assertLess(listening, thinking)
        self.assertLess(thinking, reveal)
        widget.close()

    def test_close_cleans_timers_and_animations(self):
        widget = FaceWidget(Path("missing-assets-for-test"))
        widget.set_thinking()
        self.assertTrue(widget.thinking_timer.isActive())
        widget.close()
        self.assertFalse(widget.thinking_timer.isActive())
        self.assertFalse(widget.blink_timer.isActive())
        self.assertEqual(widget._animations, [])


if __name__ == "__main__":
    unittest.main()
