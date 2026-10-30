# tests/test_theme_tokens.py
import os
import sys
import unittest
from unittest.mock import MagicMock

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

from ui_qt.styles import (
    COLOR_BG_BASE, COLOR_SURFACE_CARD, COLOR_SURFACE_ELEVATED,
    COLOR_BORDER_SUBTLE, COLOR_BORDER_CARD,
    COLOR_ACCENT_ORANGE, COLOR_ACCENT_HOVER, COLOR_ACCENT_ACTIVE,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    STYLE_PILL_ACTIVE, STYLE_PILL_INACTIVE, STYLE_DRAWER_CONTAINER,
    STYLE_OBSIDIAN_SHEET, STYLE_CANVAS_VIEWPORT, MAIN_STYLE,
    STYLE_EFFECT_ACTIVE, STYLE_EFFECT_NORMAL, STYLE_BTN_AUTO
)


class TestThemeTokens(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication(sys.argv)

    def test_easymotion_exact_color_palette(self):
        self.assertEqual(COLOR_BG_BASE.lower(), "#0d0b14")
        self.assertEqual(COLOR_SURFACE_CARD.lower(), "#13101d")
        self.assertEqual(COLOR_SURFACE_ELEVATED.lower(), "#181426")
        self.assertEqual(COLOR_BORDER_SUBTLE.lower(), "#26203a")
        self.assertEqual(COLOR_BORDER_CARD.lower(), "#1e1930")
        self.assertEqual(COLOR_ACCENT_ORANGE.lower(), "#ff5500")
        self.assertEqual(COLOR_ACCENT_HOVER.lower(), "#ff6a1a")
        self.assertEqual(COLOR_ACCENT_ACTIVE.lower(), "#e04a00")
        self.assertEqual(COLOR_TEXT_PRIMARY.lower(), "#f3f1fa")
        self.assertEqual(COLOR_TEXT_SECONDARY.lower(), "#9d93b8")
        self.assertEqual(COLOR_TEXT_MUTED.lower(), "#635b7b")

    def test_pill_stylesheets_contain_palette(self):
        self.assertIn("#ff5500", STYLE_PILL_ACTIVE)
        self.assertIn("#ff7722", STYLE_PILL_ACTIVE)
        self.assertIn("#171325", STYLE_PILL_INACTIVE)
        self.assertIn("#282140", STYLE_PILL_INACTIVE)
        self.assertIn("#9d93b8", STYLE_PILL_INACTIVE)
        self.assertIn("border: 1.5px solid #ff5500", STYLE_DRAWER_CONTAINER)
        self.assertIn("#171225", STYLE_DRAWER_CONTAINER)

    def test_main_style_and_obsidian_sheet(self):
        self.assertIn("#0d0b14", MAIN_STYLE)
        self.assertIn("#13101d", MAIN_STYLE)
        self.assertIn("#26203a", MAIN_STYLE)
        self.assertIn("#f3f1fa", MAIN_STYLE)
        self.assertEqual(MAIN_STYLE, STYLE_OBSIDIAN_SHEET)

    def test_effect_active_and_auto_button(self):
        self.assertIn("#ff5500", STYLE_EFFECT_ACTIVE)
        self.assertIn("#ffffff", STYLE_EFFECT_ACTIVE)
        self.assertIn("#13101d", STYLE_BTN_AUTO)
        self.assertIn("1.5px solid #ff5500", STYLE_BTN_AUTO)

    def test_canvas_viewport_style(self):
        self.assertIn("#000000", STYLE_CANVAS_VIEWPORT)
        self.assertIn("#26203a", STYLE_CANVAS_VIEWPORT)

    def test_convert_drawer_styling(self):
        from ui_qt.widgets.convert_drawer import ConvertCaptionsDrawer
        drawer = ConvertCaptionsDrawer()
        self.assertEqual(drawer.styleSheet(), STYLE_DRAWER_CONTAINER)
        self.assertIn("#ff5500", drawer.btn_convert.styleSheet())
        self.assertIn("#ff6a1a", drawer.btn_convert.styleSheet())

    def test_phone_canvas_view_styling(self):
        from ui_qt.widgets.phone_canvas_view import PhoneCanvasView
        canvas = PhoneCanvasView()
        self.assertIn("#000000", canvas.canvas_area.styleSheet())
        self.assertIn("#26203a", canvas.canvas_area.styleSheet())
        self.assertIn("16px", canvas.canvas_area.styleSheet())
        self.assertIn("#f3f1fa", canvas.lbl_zoom.styleSheet())

    def test_workspace_tab_segmented_buttons_and_snap_toggle(self):
        from ui_qt.tabs.workspace_tab import WorkspaceTab
        mock_bridge = MagicMock()
        mock_builder = MagicMock()
        mock_anim = MagicMock()
        tab = WorkspaceTab(mock_bridge, mock_builder, mock_anim)

        # Initial states
        self.assertEqual(tab.btn_mode_playhead.styleSheet(), STYLE_PILL_ACTIVE)
        self.assertEqual(tab.btn_mode_inout.styleSheet(), STYLE_PILL_INACTIVE)
        self.assertEqual(tab.btn_snap_to_cut.styleSheet(), STYLE_PILL_INACTIVE)

        # Switch to In/Out mode
        tab.btn_mode_inout.click()
        self.assertEqual(tab.btn_mode_inout.styleSheet(), STYLE_PILL_ACTIVE)
        self.assertEqual(tab.btn_mode_playhead.styleSheet(), STYLE_PILL_INACTIVE)

        # Toggle Snap to Cut
        tab.btn_snap_to_cut.setChecked(True)
        tab._toggle_snap_to_cut()
        self.assertEqual(tab.btn_snap_to_cut.styleSheet(), STYLE_PILL_ACTIVE)

        tab.btn_snap_to_cut.setChecked(False)
        tab._toggle_snap_to_cut()
        self.assertEqual(tab.btn_snap_to_cut.styleSheet(), STYLE_PILL_INACTIVE)

    def test_motion_panel_pills_and_effects(self):
        from ui_qt.widgets.motion_panel import MotionEffectsControllerWidget
        panel = MotionEffectsControllerWidget()

        # D-pad mode pills
        self.assertEqual(panel.btn_in_slide.styleSheet(), STYLE_PILL_ACTIVE)
        self.assertEqual(panel.btn_in_bounce.styleSheet(), STYLE_PILL_INACTIVE)

        # Effect active styling glowing orange
        panel._toggle_effect("shake")
        self.assertTrue(panel.shake_enabled)
        self.assertIn("#ff5500", panel.btn_shake.styleSheet())
        self.assertIn("#ffffff", panel.btn_shake.styleSheet())

        # Auto button styling
        self.assertEqual(panel.btn_auto.styleSheet(), STYLE_BTN_AUTO)


if __name__ == "__main__":
    unittest.main()
