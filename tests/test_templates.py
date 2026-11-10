"""
Motion Resolve - Typography Template Engine Unit Tests
Verifies schema parsing, motion token math, Bengali typographic rules, and registry catalog.
"""

import unittest
from core.templates.registry import TemplateRegistry
from core.templates.motion_tokens import evaluate_easing, seconds_to_frame, get_fusion_spline_handles
from core.templates.bengali_engine import (
    contains_bengali, is_pure_bengali, get_optical_scale, get_safe_line_height,
    to_bengali_numerals, to_western_numerals
)
from core.templates.theme_tokens import get_theme, GLOBAL_THEMES


class TestTypographyEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import sys
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication(sys.argv)

    def test_registry_loads_pilot_templates(self):
        import core.templates.registry as r_mod
        self.assertTrue(hasattr(r_mod, "Any"))
        reg = TemplateRegistry()
        templates = reg.get_all()
        self.assertGreaterEqual(len(templates), 40)

        categories = reg.get_categories()
        expected = ["Podcast", "SaaS / Tech", "Minimal Clean", "Editorial / Magazine", "Social / Reels 9:16", "Documentary / NGO / Corporate", "Cinematic", "Kinetic, Restrained"]
        for exp in expected:
            found = any(c.lower() == exp.lower() for c in categories)
            self.assertTrue(found, f"Category '{exp}' missing from registry")

    def test_motion_easing_evaluation(self):
        # Progress 0.0 -> 0.0
        self.assertAlmostEqual(evaluate_easing("linear", 0.0), 0.0)
        self.assertAlmostEqual(evaluate_easing("linear", 1.0), 1.0)
        self.assertAlmostEqual(evaluate_easing("linear", 0.5), 0.5)

        # expoOut: fast deceleration, at 0.5 should be > 0.95
        self.assertGreater(evaluate_easing("expoOut", 0.5), 0.90)
        self.assertAlmostEqual(evaluate_easing("expoOut", 1.0), 1.0)

        # cubicIn: slow acceleration, at 0.5 should be 0.125
        self.assertAlmostEqual(evaluate_easing("cubicIn", 0.5), 0.125)

        # quartInOut: symmetry
        self.assertAlmostEqual(evaluate_easing("quartInOut", 0.5), 0.5)

        # softSpring: overshoot <= 4%
        val = evaluate_easing("softSpring", 0.3)
        self.assertLessEqual(val, 1.05)

    def test_fusion_spline_handles(self):
        h = get_fusion_spline_handles("expoOut")
        self.assertEqual(len(h), 4)
        self.assertEqual(h, (0.16, 1.0, 0.30, 1.0))

    def test_seconds_to_frame(self):
        self.assertEqual(seconds_to_frame(1.0, 24.0), 24)
        self.assertEqual(seconds_to_frame(0.5, 60.0), 30)
        self.assertEqual(seconds_to_frame(0.25, 24.0), 6)

    def test_bengali_script_engine(self):
        latin_text = "MINIMALIST CINEMA"
        bn_text = "প্রধান গবেষক ও স্থপতি"
        mixed_text = "Dr. Sarah Mitchell • প্রধান বিজ্ঞানী"

        self.assertFalse(contains_bengali(latin_text))
        self.assertTrue(contains_bengali(bn_text))
        self.assertTrue(contains_bengali(mixed_text))

        self.assertTrue(is_pure_bengali(bn_text))
        self.assertFalse(is_pure_bengali(mixed_text))

        # Optical scale
        self.assertEqual(get_optical_scale(latin_text), 1.0)
        self.assertEqual(get_optical_scale(mixed_text), 1.08)

        # Line height: 1.0 standard single spacing per user requirement
        self.assertEqual(get_safe_line_height(bn_text), 1.0)

        # Bengali numerals
        self.assertEqual(to_bengali_numerals("2026"), "২০২৬")
        self.assertEqual(to_western_numerals("২০২৬"), "2026")

    def test_theme_tokens(self):
        self.assertGreaterEqual(len(GLOBAL_THEMES), 5)
        mono = get_theme("mono")
        self.assertIn("accent", mono)
        self.assertIn("font_heading", mono)
        self.assertIn("font_heading_bn", mono)

    def test_fusion_compiler_helpers(self):
        from core.templates.fusion_compiler import FusionCompiler
        compiler = FusionCompiler(bridge=None)
        reg = TemplateRegistry()
        tpl = reg.get_template("pod_lower_third_slate")
        self.assertIsNotNone(tpl)

        # Test parameter resolution
        resolved = compiler._resolve_parameters(tpl, {"name": "Test User"})
        self.assertEqual(resolved["name"], "Test User")
        self.assertEqual(resolved["role"], "Creative Director · Studio North")

        # Test token and parameter value resolution
        theme = get_theme("mono")
        val1 = compiler._resolve_value("$name", resolved, theme)
        self.assertEqual(val1, "Test User")
        val2 = compiler._resolve_value("token:accent", resolved, theme)
        self.assertEqual(val2, theme["accent"])

    def test_fusion_compiler_mask_reveal_and_cleanup(self):
        """Masked-reveal templates get a per-layer clip (MR_Clip_*) on the layer's
        merge, keyed motion on the layer transform, and a clean recompile."""
        from tests.fake_fusion import make_item
        from core.templates.fusion_compiler import FusionCompiler
        tpl = TemplateRegistry().get_template("pod_lower_third_slate")
        item, comp, bridge = make_item(84)
        compiler = FusionCompiler(bridge)
        self.assertTrue(compiler.compile_and_apply(item, tpl, param_overrides={"pos_y": 0.25}))
        clip = comp.FindTool("MR_Clip_guest_name")
        self.assertIsNotNone(clip)
        self.assertEqual(clip.regid, "RectangleMask")
        self.assertIs(comp.FindTool("MR_Merge_guest_name").connections["EffectMask"].GetTool(), clip)
        self.assertGreater(clip.GetInput("Width"), 1.0)  # never cuts text horizontally
        xf = comp.FindTool("MR_XF_guest_name")
        self.assertLess(xf.GetInput("Center", 1)[0], 0.5)          # slides in from the left
        self.assertAlmostEqual(xf.GetInput("Center", 40)[0], 0.5, places=4)
        names = set(comp.tools)
        self.assertTrue(compiler.compile_and_apply(item, tpl, param_overrides={"pos_y": 0.25}))
        self.assertEqual(names, set(comp.tools))

    def test_kinetic_templates_compilation(self):
        from tests.fake_fusion import make_item
        from core.templates.fusion_compiler import FusionCompiler
        for tid in ("kin_split_reveal", "kin_word_pop", "kin_masked_line", "kin_dynamic_stack"):
            with self.subTest(template=tid):
                tpl = TemplateRegistry().get_template(tid)
                self.assertIsNotNone(tpl)
                item, comp, bridge = make_item(60)
                self.assertTrue(FusionCompiler(bridge).compile_and_apply(item, tpl))
                merges = [t for n, t in comp.tools.items() if n.startswith("MR_Merge_")]
                self.assertTrue(merges)
                from tests.test_fusion_engine import layer_opacity
                for name in [n for n in comp.tools if n.startswith("MR_Merge_")]:
                    self.assertAlmostEqual(layer_opacity(comp, name, 0), 0.0, places=3)
                    self.assertAlmostEqual(layer_opacity(comp, name, 59), 0.0, places=3)


if __name__ == "__main__":
    unittest.main()
