"""
Motion Resolve - 2026 Commercial Design System & Viral Agency Suite Tests
Verifies dual-font typography, 60-30-10 color proportions, ambient 360 diffusion shadows,
the 6 new viral agency templates, and mathematical spacing engine formulas.
"""

import unittest
from unittest.mock import MagicMock
from core.text_plus_builder import TextPlusBuilder
from core.font_catalog import is_script_font, resolve_available_font
from core.style_manager import StyleManager
from core.templates.registry import TemplateRegistry
from core.templates.fusion_compiler import FusionCompiler
from core.templates.schema import LayerType


class TestAgencyDesignSystem(unittest.TestCase):
    """Test suite for the 2026 Commercial Design System and Viral Agency Upgrade."""

    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        import sys
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.mock_bridge = MagicMock()
        self.mock_bridge.get_timeline_fps.return_value = 30.0
        self.builder = TextPlusBuilder(bridge=self.mock_bridge)
        self.compiler = FusionCompiler(bridge=self.mock_bridge)
        self.registry = TemplateRegistry()
        self.style_mgr = StyleManager()

    def test_script_font_detection(self):
        """Audit that script and cursive typefaces are accurately identified."""
        self.assertTrue(is_script_font("Pinyon Script"))
        self.assertTrue(is_script_font("Snell Roundhand"))
        self.assertTrue(is_script_font("Brush Script MT"))
        self.assertTrue(is_script_font("Zapfino"))
        self.assertFalse(is_script_font("Inter"))
        self.assertFalse(is_script_font("Montserrat"))
        self.assertFalse(is_script_font("DM Serif Display"))

    def test_dual_font_hero_preserves_case_for_script(self):
        """Verifies apply_layout_template avoids ugly all-caps on script/cursive fonts."""
        text = "This will elevate your retention"
        # 1. Non-script font: Hero word forced uppercase for bold punch
        out_bold = self.builder.apply_layout_template(text, template_num=1, main_word="elevate", hero_font="Montserrat")
        self.assertIn("ELEVATE", out_bold)

        # 2. Script font: Hero word preserves natural casing / title case
        out_script = self.builder.apply_layout_template(text, template_num=1, main_word="elevate", hero_font="Pinyon Script")
        self.assertIn("elevate", out_script.lower())
        self.assertNotIn("ELEVATE", out_script)

    def test_all_33_presets_have_dual_font_pairings(self):
        """Audit that all presets have curated hero_font pairings and ambient diffusion shadows."""
        presets = self.style_mgr.get_presets()
        self.assertEqual(len(presets), 33)

        for p in presets:
            pid = p["id"]
            self.assertIn("hero_font", p, f"Preset '{pid}' missing hero_font")
            self.assertIn("hero_style", p, f"Preset '{pid}' missing hero_style")
            self.assertIn("hero_size_multiplier", p, f"Preset '{pid}' missing hero_size_multiplier")
            self.assertGreaterEqual(p["hero_size_multiplier"], 1.05)
            self.assertEqual(p["line_spacing"], 0.0)

            # Ambient 360-degree diffusion shadow check
            if p.get("shadow_enabled"):
                self.assertEqual(p.get("shadow_offset"), [0.0, 0.0], f"Preset '{pid}' must use zero-distance ambient shadow")
                self.assertGreaterEqual(p.get("shadow_softness", 0), 0.04, f"Preset '{pid}' must use wide diffuse softness")

    def test_all_6_viral_agency_templates_exist_and_validate(self):
        """Audit that all 6 2026 Viral Agency templates load and adhere to schema."""
        expected_agency_ids = [
            "agency_stripe_notification",
            "agency_price_strikethrough",
            "agency_testimonial_proof",
            "agency_one_object_focus",
            "agency_diagonal_stat_split",
            "agency_side_by_side_thirds"
        ]

        for tid in expected_agency_ids:
            tpl = self.registry.get_template(tid)
            self.assertIsNotNone(tpl, f"Agency template '{tid}' failed to load from registry")
            self.assertEqual(tpl.category, "Agency / Social")
            self.assertGreaterEqual(len(tpl.parameters), 5)
            self.assertGreaterEqual(len(tpl.layers), 3)

            # Check that all text layers are properly parameter-bound
            for l in tpl.layers:
                if l.type == LayerType.TEXT:
                    raw_text = l.props.get("text", "")
                    self.assertTrue(
                        raw_text.startswith("param:") or raw_text.startswith("$"),
                        f"Template '{tid}' layer '{l.id}' has unbound text prop: {raw_text}"
                    )

    def test_agency_template_compilation_smoke(self):
        """Verifies that an agency template compiles without error through FusionCompiler."""
        tpl = self.registry.get_template("agency_stripe_notification")
        self.assertIsNotNone(tpl)

        mock_item = MagicMock()
        mock_item.GetFusionCompCount.return_value = 1
        mock_comp = MagicMock()
        mock_item.GetFusionCompByIndex.return_value = mock_comp
        mock_comp.GetToolList.return_value = {}

        success = self.compiler.compile_and_apply(
            mock_item,
            tpl,
            param_overrides={"brand": "Stripe • now", "amount": "+$5,000.00"},
            theme_id="mono"
        )
        self.assertTrue(success)

    def test_mathematical_spacing_formulas(self):
        """Audit exact mathematical layout formulas: Icon = 0.5x Text, Gap = 2.0x LineSpacing."""
        layout = FusionCompiler.calculate_icon_layout(text_size=0.072, line_spacing=0.0)
        self.assertAlmostEqual(layout["icon_size"], 0.036, places=3)
        self.assertGreater(layout["gap"], 0.0)

        layout_custom = FusionCompiler.calculate_icon_layout(text_size=0.080, line_spacing=0.025)
        self.assertAlmostEqual(layout_custom["icon_size"], 0.040, places=3)
        self.assertAlmostEqual(layout_custom["gap"], 0.050, places=3)

    def test_squircle_padding_and_clamping(self):
        """Audit squircle padding and lower-third midpoint clamping."""
        padding = FusionCompiler.calculate_squircle_padding(text_width=0.42, text_height=0.12)
        self.assertGreater(padding["width"], 0.42)
        self.assertGreater(padding["height"], 0.12)
        self.assertEqual(padding["corner_radius"], 14)

        # Multi-line subtitle midpoint centered at lower third
        clamp_1 = FusionCompiler.calculate_lower_third_clamping(line_count=1, font_size=0.072, default_y=0.28)
        self.assertEqual(clamp_1, 0.28)

        clamp_2 = FusionCompiler.calculate_lower_third_clamping(line_count=2, font_size=0.072, default_y=0.28)
        self.assertEqual(clamp_2, 0.28)

        # Trailing icon overlap (20% overlap onto text end)
        trailing_x = FusionCompiler.calculate_trailing_icon_overlap(text_end_x=0.65, icon_size=0.04, overlap_pct=0.20)
        # Expected: 0.65 + 0.04 * 0.5 - 0.04 * 0.20 = 0.65 + 0.02 - 0.008 = 0.662
        self.assertAlmostEqual(trailing_x, 0.662, places=3)


if __name__ == "__main__":
    unittest.main()
