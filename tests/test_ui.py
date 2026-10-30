"""
Motion Resolve for DaVinci Resolve Studio - UI Unit Test Suite
Headless verification of PyQt6 widgets, tabs, signals, and window controls.
"""

import os
import sys
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from ui_qt.main_window import MainWindow
from ui_qt.widgets.canvas_view import PhoneCanvasView


class TestUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from PyQt6.QtGui import QFont
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication(sys.argv)
        cls.app.setFont(QFont("Arial", 10))

    def test_main_window_creation(self):
        win = MainWindow()
        self.assertEqual(win.tab_bar.count(), 4)
        self.assertEqual(win.windowTitle(), "Motion Resolve for DaVinci Resolve Studio")

    def test_tab_navigation(self):
        win = MainWindow()

        # Workspace Tab
        win.tab_bar.setCurrentIndex(0)
        self.assertEqual(win.stack.currentIndex(), 0)

        # Templates Tab
        win.tab_bar.setCurrentIndex(1)
        self.assertEqual(win.stack.currentIndex(), 1)

        # Presets Tab
        win.tab_bar.setCurrentIndex(2)
        self.assertEqual(win.stack.currentIndex(), 2)

        # Auto Tab
        win.tab_bar.setCurrentIndex(3)
        self.assertEqual(win.stack.currentIndex(), 3)

    def test_titles_filter_and_select(self):
        win = MainWindow()
        win.tab_bar.setCurrentIndex(2) # Presets Tab

        win.tab_titles.txt_search.setText("Hormozi")
        win.tab_titles.txt_search.setText("")

        # Select preset
        presets = win.tab_titles.style_mgr.get_presets()
        self.assertGreaterEqual(len(presets), 15)
        win.tab_titles.select_preset(presets[0])
        self.assertIsNotNone(win.tab_titles.active_style)

    def test_templates_preview_player(self):
        win = MainWindow()
        win.tab_bar.setCurrentIndex(1) # Templates tab
        self.assertIsNotNone(win.tab_templates.preview_player)
        self.assertGreaterEqual(len(win.tab_templates.cards), 40)

        # Test playback toggle
        self.assertFalse(win.tab_templates.preview_player.is_playing)
        win.tab_templates.preview_player._toggle_playback()
        self.assertTrue(win.tab_templates.preview_player.is_playing)
        win.tab_templates.preview_player._toggle_playback()
        self.assertFalse(win.tab_templates.preview_player.is_playing)

        # Test scrubbing
        win.tab_templates.preview_player._on_slider_scrubbed(1500)
        self.assertAlmostEqual(win.tab_templates.preview_player.playback_time, 1.5)

    def test_mini_playback_mode(self):
        win = MainWindow()
        self.assertFalse(win.is_minimized_bar)
        win._toggle_minimize_playback()
        self.assertTrue(win.is_minimized_bar)
        self.assertEqual(win.height(), 50)
        win._toggle_minimize_playback()
        self.assertFalse(win.is_minimized_bar)

    def test_template_canvas_mask_clipping(self):
        """Verifies TemplateCanvasArea renders with mask clipping at t=0, t=1.0, and t=total_dur."""
        from ui_qt.widgets.template_preview_canvas import TemplateCanvasArea
        from core.templates.registry import TemplateRegistry

        canvas = TemplateCanvasArea()
        canvas.resize(640, 360)
        reg = TemplateRegistry()
        tpl = reg.get_template("pod_lower_third_slate")
        self.assertIsNotNone(tpl)
        total_dur = tpl.duration_default

        # 1. Test Entrance (t=0): displacement > 0 (slid into mask)
        canvas.set_state(tpl, {"name": "Test Speaker", "role": "Principal Engineer"}, {}, 0.0)
        pix_0 = canvas.grab()
        self.assertFalse(pix_0.isNull())
        self.assertEqual(pix_0.width(), 640)
        self.assertEqual(pix_0.height(), 360)
        self.assertGreater(canvas.last_text_dy, 0.0)
        self.assertIsNotNone(canvas.last_mask_rect)
        self.assertAlmostEqual(canvas.last_mask_rect.height(), 99.45, places=1)

        # 2. Test Hold (t=1.0): displacement = 0.0
        canvas.set_state(tpl, {"name": "Test Speaker", "role": "Principal Engineer"}, {}, 1.0)
        pix_hold = canvas.grab()
        self.assertFalse(pix_hold.isNull())
        self.assertEqual(pix_hold.width(), 640)
        self.assertEqual(pix_hold.height(), 360)
        self.assertAlmostEqual(canvas.last_text_dy, 0.0, places=2)

        # 3. Test Exit (t=total_dur): displacement > 0 (slid down into mask hiding)
        canvas.set_state(tpl, {"name": "Test Speaker", "role": "Principal Engineer"}, {}, total_dur)
        pix_exit = canvas.grab()
        self.assertFalse(pix_exit.isNull())
        self.assertEqual(pix_exit.width(), 640)
        self.assertEqual(pix_exit.height(), 360)
        self.assertGreater(canvas.last_text_dy, 0.0)

    def test_template_inspector_rich_controls(self):
        """Verifies Template Inspector builds Color, Font, and Select input controls."""
        from core.templates.schema import TemplateSpec, TemplateParameter, ParameterType
        win = MainWindow()
        tab = win.tab_templates

        # Create dummy template with all parameter types
        dummy_params = [
            TemplateParameter(id="title", name="Title Text", type=ParameterType.STRING, default="Test Title"),
            TemplateParameter(id="scale", name="Scale Factor", type=ParameterType.NUMBER, default=1.0, min_val=0.5, max_val=2.0),
            TemplateParameter(id="accent_color", name="Accent Color", type=ParameterType.COLOR, default="#ffe500"),
            TemplateParameter(id="heading_font", name="Heading Font", type=ParameterType.FONT, default="Montserrat"),
            TemplateParameter(id="mode_select", name="Display Mode", type=ParameterType.SELECT, default="Dark", options=["Dark", "Light"]),
            TemplateParameter(id="glow_on", name="Enable Glow", type=ParameterType.BOOLEAN, default=True),
        ]
        dummy_tpl = TemplateSpec(
            id="test_dummy_inspector",
            name="Dummy Inspector Template",
            category="Test",
            description="Testing rich controls",
            tags=[],
            aspect_ratios=["16:9"],
            duration_default=3.0,
            min_hold=1.0,
            in_duration=0.5,
            out_duration=0.3,
            parameters=dummy_params,
            layers=[]
        )

        tab.select_template(dummy_tpl)
        self.assertEqual(tab.active_template.id, "test_dummy_inspector")
        self.assertIn("accent_color", tab.active_params)
        self.assertIn("heading_font", tab.active_params)
        self.assertIn("mode_select", tab.active_params)

        # Check export and import buttons exist
        self.assertTrue(hasattr(tab, "btn_export_template"))
        self.assertTrue(hasattr(tab, "btn_import_template"))

    def test_preset_preview_canvas_rendering(self):
        """Verifies PresetPreviewCanvas renders accurate Text+ elements to pixmap."""
        from ui_qt.tabs.titles_tab import PresetPreviewCanvas

        preset_data = {
            "name": "Test Glow Style",
            "text": "VOX DOCUMENTARY",
            "font": "DIN Alternate",
            "character_spacing": 1.05,
            "color": [1.0, 1.0, 1.0, 1.0],
            "stroke_enabled": True,
            "stroke_color": [0.0, 0.0, 0.0, 1.0],
            "stroke_thickness": 0.03,
            "shadow_enabled": True,
            "shadow_color": [0.0, 0.0, 0.0, 0.8],
            "shadow_offset": [0.006, -0.006],
            "box_enabled": True,
            "box_color": [1.0, 0.88, 0.0, 0.95],
        }

        canvas = PresetPreviewCanvas(preset_data)
        canvas.resize(240, 84)
        pix = canvas.grab()
        self.assertFalse(pix.isNull())
        self.assertEqual(pix.width(), 240)
        self.assertEqual(pix.height(), 84)

    def test_platform_safe_zones_switching(self):
        """Verifies platform safe zone switching (TikTok, Reels, Shorts, SMPTE) and painting."""
        canvas_view = PhoneCanvasView()
        canvas_view.resize(360, 640)
        canvas_area = canvas_view.canvas_area

        for platform in ["TikTok", "Instagram Reels", "YouTube Shorts", "Broadcast (SMPTE)"]:
            canvas_view.combo_safe_platform.setCurrentText(platform)
            self.assertEqual(canvas_area.safe_zone_platform, platform)
            pix = canvas_area.grab()
            self.assertFalse(pix.isNull())

    def test_motion_preview_scrub_loop(self):
        """Verifies motion preview scrub loop toggling, timer ticking, and reset."""
        canvas_view = PhoneCanvasView()
        canvas_view.resize(360, 640)
        canvas_area = canvas_view.canvas_area

        # Initially stopped
        self.assertFalse(canvas_area.is_playing)
        self.assertEqual(canvas_area.anim_progress, 1.0)

        # Toggle play
        playing = canvas_view._toggle_motion_play()
        self.assertTrue(canvas_area.is_playing)
        self.assertTrue(canvas_area.anim_timer.isActive())
        self.assertEqual(canvas_area.anim_progress, 0.0)

        # Advance tick
        canvas_area._on_anim_tick()
        self.assertGreater(canvas_area.anim_progress, 0.0)

        # Paint during animation
        pix = canvas_area.grab()
        self.assertFalse(pix.isNull())

        # Toggle pause
        canvas_view._toggle_motion_play()
        self.assertFalse(canvas_area.is_playing)
        self.assertFalse(canvas_area.anim_timer.isActive())
        self.assertEqual(canvas_area.anim_progress, 1.0)


if __name__ == "__main__":
    unittest.main()
