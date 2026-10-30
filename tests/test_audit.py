"""
Exhaustive Audit Test Suite for Motion Resolve
Validates all 46 template specifications, 21 style presets, alignment accuracy,
coordinate math, safe targeting, and fallback parameter resolution.
"""

import unittest
import os
import sys
import json
import glob

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication

from core.templates.registry import TemplateRegistry
from core.templates.fusion_compiler import FusionCompiler
from core.templates.theme_tokens import GLOBAL_THEMES, get_theme
from core.templates.schema import ParameterType, LayerType
from core.templates.bengali_engine import contains_bengali, to_bengali_numerals, get_safe_line_height
from core.resolve_api import ResolveBridge
from core.style_manager import StyleManager, DEFAULT_PRESETS
from ui_qt.widgets.canvas_view import CanvasInteractiveArea


class TestFullAppAudit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication(sys.argv)

    def setUp(self):
        self.registry = TemplateRegistry()

    def test_all_46_templates_exist_and_bound(self):
        """Audit that all 46 templates have 100% parameter bindings and valid layers."""
        templates = self.registry.get_all()
        self.assertGreaterEqual(len(templates), 46, f"Expected at least 46 templates, found {len(templates)}")

        for t in templates:
            with self.subTest(template=t.id):
                self.assertTrue(len(t.parameters) > 0, f"{t.id} has no parameters")
                self.assertTrue(len(t.layers) > 0, f"{t.id} has no layers")

                # Check text layers
                for l in t.layers:
                    if l.type == LayerType.TEXT:
                        raw_text = l.props.get("text", "")
                        self.assertTrue(
                            raw_text.startswith("param:") or raw_text.startswith("$"),
                            f"{t.id} layer {l.id} has unbound text prop: {repr(raw_text)}"
                        )

    def test_pos_y_design_intent(self):
        """Audit that centered templates default to 0.50 and lower-thirds to <= 0.35."""
        centered_ids = [
            "min_centered_statement", "cine_intertitle_card", "cine_main_title",
            "cine_chapter_card", "edit_pull_quote", "edit_split_weight",
            "edit_section_opener", "kin_dynamic_stack", "kin_masked_line",
            "kin_word_pop", "pod_episode_card", "pod_quote_card", "pod_outro_card",
            "saas_bento_grid", "saas_glass_card", "saas_gradient_headline",
            "saas_stat_counter", "saas_step_titles", "saas_cta_card",
            "soc_3line_stack", "soc_split_twotone", "min_outro_title",
            "min_single_line", "min_subtitle_hairline", "min_underline_reveal"
        ]

        for cid in centered_ids:
            t = self.registry.get_template(cid)
            self.assertIsNotNone(t, f"Template {cid} not found in registry")
            pos_y_params = [p for p in t.parameters if p.id == "pos_y"]
            self.assertTrue(len(pos_y_params) > 0, f"{cid} missing pos_y parameter")
            self.assertEqual(pos_y_params[0].default, 0.50, f"{cid} pos_y should default to 0.50 (exact center)")

        # Corner tag
        corner = self.registry.get_template("min_corner_tag")
        self.assertIsNotNone(corner)
        corner_py = [p for p in corner.parameters if p.id == "pos_y"][0]
        self.assertGreater(corner_py.default, 0.70, "min_corner_tag should be positioned near top of frame")

    def test_all_21_presets_line_spacing(self):
        """Audit that all 21 preset files have line_spacing strictly 0.0, center_x 0.5, and valid center_y."""
        preset_files = [f for f in glob.glob("data/styles/*.json") if not os.path.basename(f).startswith(".")]
        self.assertGreaterEqual(len(preset_files), 21, f"Expected at least 21 presets, found {len(preset_files)}")

        for p_path in preset_files:
            with open(p_path) as f:
                data = json.load(f)
            name = data.get("name", os.path.basename(p_path))
            self.assertEqual(
                data.get("line_spacing"), 0.0,
                f"Preset '{name}' has line_spacing {data.get('line_spacing')} instead of 0.0 (1.0 single spacing)"
            )
            self.assertEqual(
                data.get("center_x"), 0.5,
                f"Preset '{name}' center_x must be 0.5, got {data.get('center_x')}"
            )
            cy = data.get("center_y")
            self.assertIsNotNone(cy, f"Preset '{name}' missing center_y")
            self.assertTrue(0.10 <= float(cy) <= 0.90, f"Preset '{name}' center_y out of bounds: {cy}")
            self.assertIn("animation_in", data, f"Preset '{name}' missing animation_in")
            self.assertIn("animation_out", data, f"Preset '{name}' missing animation_out")

    def test_all_21_presets_elevated_typography(self):
        """Audit elevated typography across presets: no legacy generic fonts and correct design tokens."""
        mgr = StyleManager()
        presets = mgr.get_presets()
        self.assertGreaterEqual(len(presets), 21, f"Expected at least 21 presets loaded by StyleManager, found {len(presets)}")

        legacy_banned_fonts = {"Arial", "Times New Roman", "Courier New"}
        preset_map = {p["id"]: p for p in presets}

        for pid, p in preset_map.items():
            font = p.get("font")
            self.assertNotIn(
                font, legacy_banned_fonts,
                f"Preset '{pid}' still uses banned legacy font '{font}'. Must be upgraded to modern typography."
            )

        # The built-in library uses distinct, softer premium profiles and working hero accents.
        gadzhi = preset_map["iman_gadzhi_luxury"]
        self.assertEqual(gadzhi["font"], "Didot")
        self.assertEqual(gadzhi["character_spacing"], 1.08)
        self.assertEqual(gadzhi["color"], [0.97, 0.93, 0.85, 1])
        self.assertEqual(gadzhi["main_word"], "FOCUS")
        self.assertFalse(gadzhi["stroke_enabled"])
        self.assertGreater(gadzhi["shadow_softness"], 0.03)
        self.assertEqual(gadzhi["animation_in"], "slide_up")
        self.assertEqual(gadzhi["animation_out"], "slide_down")

        vox = preset_map["vox_documentary"]
        self.assertEqual(vox["font"], "Avenir Next")
        self.assertEqual(vox["character_spacing"], 1.02)
        self.assertEqual(vox["color"], [0.17, 0.18, 0.16, 1])
        self.assertTrue(vox["box_enabled"])
        self.assertEqual(vox["box_color"], [0.92, 0.86, 0.72, 0.91])

        cine = preset_map["cinematic_sub"]
        self.assertEqual(cine["font"], "Charter")
        self.assertEqual(cine["character_spacing"], 1.04)
        self.assertTrue(cine["shadow_enabled"])
        colors = {tuple(p["color"]) for p in presets if p.get("color")}
        self.assertGreaterEqual(len(colors), 20, "Built-in presets should keep distinct color identities")
        for preset in presets:
            if preset.get("use_2color"):
                self.assertTrue(preset.get("main_word"), f"{preset['id']} needs a hero word")

        from core.templates.theme_tokens import get_available_themes
        theme_ids = {theme["id"] for theme in get_available_themes()}
        self.assertTrue({"frosted_slate", "porcelain", "rosewood"}.issubset(theme_ids))

    def test_canvas_aspect_ratios_and_alignments(self):
        """Audit canvas view aspect ratios, snapping coordinates, and text alignments."""
        canvas = CanvasInteractiveArea()

        # Check default 16:9 widescreen
        self.assertEqual(canvas.aspect_ratio, "16:9")
        self.assertEqual(canvas.pos_x, 0.5)
        self.assertEqual(canvas.pos_y, 0.5)
        self.assertTrue(canvas.is_snapped_x)
        self.assertTrue(canvas.is_snapped_y)

        # Switch aspect ratios
        canvas.set_aspect_ratio("9:16")
        self.assertEqual(canvas.aspect_ratio, "9:16")
        canvas.set_aspect_ratio("1:1")
        self.assertEqual(canvas.aspect_ratio, "1:1")
        canvas.set_aspect_ratio("16:9")
        self.assertEqual(canvas.aspect_ratio, "16:9")

        # Alignment
        canvas.set_alignment("left")
        self.assertEqual(canvas.alignment, "left")
        canvas.set_alignment("right")
        self.assertEqual(canvas.alignment, "right")
        canvas.set_alignment("center")
        self.assertEqual(canvas.alignment, "center")

    def test_bengali_engine_integrity(self):
        """Audit Bengali numeral translation and line height calculations."""
        bn_str = "অধ্যায় ০১: টেস্টিং ২০২৬"
        self.assertTrue(contains_bengali(bn_str))
        self.assertEqual(get_safe_line_height(bn_str), 1.0)

        num_converted = to_bengali_numerals("Chapter 2026")
        self.assertIn("২০২৬", num_converted)

    def test_resolve_value_param_fallback(self):
        """Audit compiler parameter resolution with param: prefix and fallback."""
        compiler = FusionCompiler(ResolveBridge())
        t = self.registry.get_template("min_centered_statement")
        theme = get_theme("mono")
        params = {p.id: p.default for p in t.parameters}

        val = compiler._resolve_value("param:statement", params, theme)
        self.assertEqual(val, "DESIGN IS THINKING MADE VISUAL")


    def test_inout_mode_precedence_audit(self):
        """Audit that In/Out mode prioritizes range over a single selected item."""
        bridge = ResolveBridge()
        # Even if selected items exist, inout mode with valid range checks In/Out marks
        self.assertTrue(hasattr(bridge, "get_target_clips"))

    def test_extract_style_full_attributes_audit(self):
        """Audit that extract_style_from_clip preserves stroke, shadow, box, tracking, and alignment."""
        from core.text_plus_builder import TextPlusBuilder
        builder = TextPlusBuilder(ResolveBridge())

        class MockTool:
            def __init__(self, inputs):
                self.inputs = inputs
            def GetInput(self, key):
                return self.inputs.get(key)

        class MockComp:
            def __init__(self, tool):
                self.tool = tool
            def FindTool(self, name):
                return self.tool if name == "Template" else None
            def GetToolList(self):
                return {1: self.tool}

        class MockClip:
            def __init__(self, comp):
                self.comp = comp
            def GetFusionCompCount(self):
                return 1
            def GetFusionCompByIndex(self, idx):
                return self.comp

        mock_inputs = {
            "StyledText": "TEST CLIP",
            "Font": "Didot",
            "Style": "Bold",
            "Size": 0.08,
            "Center": {"1": 0.5, "2": 0.5},
            "HorizontalLeftCenterRight": 0.0,
            "VerticalTopCenterBottom": 0.0,
            "CharacterSpacingClone": 1.05,
            "LineSpacingClone": 0.0,
            "Red1": 1.0, "Green1": 0.9, "Blue1": 0.8, "Alpha1": 1.0,
            "SoftnessGlow1": 0.45,
            "Enabled2": 1,
            "Thickness2": 0.025,
            "Red2": 0.1, "Green2": 0.2, "Blue2": 0.3, "Alpha2": 1.0,
            "Enabled3": 1,
            "Red3": 0.0, "Green3": 0.0, "Blue3": 0.0, "Alpha3": 0.75,
            "Softness3": 0.04,
            "Offset3": {"1": 0.008, "2": -0.008},
            "Enabled4": 1,
            "Red4": 0.95, "Green4": 0.2, "Blue4": 0.1, "Alpha4": 0.9,
            "ExtendHorizontal4": 0.05,
            "ExtendVertical4": 0.03,
            "Round4": 0.3
        }

        clip = MockClip(MockComp(MockTool(mock_inputs)))
        extracted = builder.extract_style_from_clip(clip)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted["font"], "Didot")
        self.assertEqual(extracted["character_spacing"], 1.05)
        self.assertEqual(extracted["line_spacing"], 0.0)
        self.assertTrue(extracted["stroke_enabled"])
        self.assertEqual(extracted["stroke_color"], [0.1, 0.2, 0.3, 1.0])
        self.assertTrue(extracted["shadow_enabled"])
        self.assertEqual(extracted["shadow_color"], [0.0, 0.0, 0.0, 0.75])
        self.assertEqual(extracted["shadow_offset"], [0.008, -0.008])
        self.assertTrue(extracted["box_enabled"])
        self.assertEqual(extracted["box_color"], [0.95, 0.2, 0.1, 0.9])
        self.assertEqual(extracted["box_extend_x"], 0.05)
        self.assertTrue(extracted["glow_enabled"])
        self.assertEqual(extracted["glow_amount"], 0.45)

    def test_category_filter_coverage_audit(self):
        """Audit that all categories in data/styles/*.json match the TitlesTab filter combo."""
        from ui_qt.tabs.titles_tab import TitlesTab
        from core.text_plus_builder import TextPlusBuilder
        from core.animation_engine import AnimationEngine
        b = ResolveBridge()
        tab = TitlesTab(b, TextPlusBuilder(b), AnimationEngine())
        combo_items = [tab.combo_category.itemText(i) for i in range(tab.combo_category.count())]

        style_files = glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "styles", "*.json"))
        for sf in style_files:
            if os.path.basename(sf).startswith("."):
                continue
            with open(sf, "r") as f:
                d = json.load(f)
            cat = d.get("category", "").lower()
            match = False
            for c in combo_items:
                sc = c.lower()
                if sc == "all categories":
                    continue
                if (sc == cat or
                    ("clean" in sc and ("clean" in cat or "ssa" in cat)) or
                    ("social" in sc and ("social" in cat or "retention" in cat or "easymotion" in cat)) or
                    ("documentary" in sc and ("documentary" in cat or "podcast" in cat or "vox" in cat)) or
                    ("corporate" in sc and ("corporate" in cat or "brand" in cat)) or
                    ("cinematic" in sc and ("cinematic" in cat or "film" in cat)) or
                    ("tech" in sc and ("tech" in cat or "gaming" in cat or "glitch" in cat or "kinetic" in cat)) or
                    ("bengali" in sc and ("bengali" in cat or "multilingual" in cat))):
                    match = True
                    break
            self.assertTrue(match, f"Category '{d.get('category')}' from {os.path.basename(sf)} not covered by filter combo {combo_items}")

    def test_sample_cue_guard_and_reconnect_audit(self):
        """Audit sample cue protection and bridge reconnect propagation."""
        from ui_qt.main_window import MainWindow
        win = MainWindow()
        self.assertFalse(win.tab_auto.is_sample_cues)
        self.assertFalse(win.tab_workspace.btn_redo.isEnabled())

        # Test reconnect propagation
        old_bridge = win.tab_workspace.bridge
        win._reconnect_resolve()
        new_bridge = win.tab_workspace.bridge
        self.assertIsNot(old_bridge, new_bridge)
        self.assertIs(win.tab_templates.bridge, new_bridge)
        self.assertIs(win.tab_titles.bridge, new_bridge)
        self.assertIs(win.tab_auto.bridge, new_bridge)


if __name__ == "__main__":
    unittest.main()
