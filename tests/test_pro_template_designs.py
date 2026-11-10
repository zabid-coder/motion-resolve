"""
Motion Resolve - Pro Template & Preset Redesign Suite Tests
Tests curated typography pairings, 360° ambient diffusion shadows, zero line-spacing,
and schema integrity across all presets and declarative templates.
"""

import unittest
from core.templates.registry import TemplateRegistry
from core.templates.schema import LayerType
from core.style_manager import StyleManager


class TestProTemplateDesigns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        import sys
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_all_templates_have_curated_typography(self):
        """All declarative templates must use curated typography without amateur fonts."""
        reg = TemplateRegistry()
        templates = reg.get_all()
        self.assertGreaterEqual(len(templates), 50, "Expected at least 50 templates loaded")

        banned_fonts = {"Comic Sans", "Comic Sans MS", "Papyrus", "Times New Roman"}

        for t in templates:
            for layer in t.layers:
                if layer.type == LayerType.TEXT:
                    # LayerSpec supports .typography property returning TypographySpec
                    self.assertIsNotNone(layer.typography, f"Template '{t.id}' text layer '{layer.id}' missing typography")
                    font = layer.typography.font_family or layer.props.get("font", "")
                    self.assertTrue(bool(font), f"Template '{t.id}' text layer '{layer.id}' has empty font")
                    for banned in banned_fonts:
                        self.assertNotIn(banned.lower(), font.lower(),
                                         f"Template '{t.id}' uses banned font: {font}")

        # Category-specific typography checks
        # Minimal Clean: must use luxury editorial typography (Didot, Bodoni, Avenir, token:font_heading)
        minimal_templates = reg.get_by_category("Minimal Clean")
        self.assertGreaterEqual(len(minimal_templates), 6)
        for t in minimal_templates:
            for layer in t.layers:
                if layer.type == LayerType.TEXT:
                    font = layer.typography.font_family
                    self.assertTrue(
                        any(f in font for f in ["Didot", "Bodoni", "Avenir", "token:font_heading", "token:font_body", "Pinyon Script", "Cormorant", "Baskerville"]),
                        f"Minimal template '{t.id}' layer '{layer.id}' should use luxury editorial font, got: {font}"
                    )

        # SaaS / Tech: must use tech/monospace stats (JetBrains Mono / token:font_mono) or modern sans
        saas_templates = reg.get_by_category("SaaS / Tech")
        self.assertGreaterEqual(len(saas_templates), 10)
        has_mono_stat = False
        for t in saas_templates:
            for layer in t.layers:
                if layer.type == LayerType.TEXT:
                    font = layer.typography.font_family
                    from core.font_catalog import infer_font_purpose
                    if infer_font_purpose(font) == "mono" or "jetbrains" in font.lower():
                        has_mono_stat = True
        self.assertTrue(has_mono_stat, "SaaS category must feature monospace typography for stats / keys")

    def test_presets_have_ambient_diffusion_shadows(self):
        """Audit that all 33 presets with shadows enabled use 360° ambient diffusion glow."""
        mgr = StyleManager()
        presets = mgr.get_presets()
        self.assertGreaterEqual(len(presets), 33, f"Expected at least 33 presets, found {len(presets)}")

        for p in presets:
            pid = p.get("id")
            # Premium shadow: soft and subtle (ambient or lightly lifted), never a hard drop.
            if p.get("shadow_enabled"):
                off = p.get("shadow_offset", [0.0, 0.0])
                self.assertLessEqual(abs(off[0]) + abs(off[1]), 0.015, f"Preset '{pid}' shadow offset too hard: {off}")
                self.assertGreaterEqual(p.get("shadow_softness", 0), 0.015, f"Preset '{pid}' shadow too sharp")
                shadow_col = p.get("shadow_color", [0, 0, 0, 0])
                alpha = shadow_col[3] if len(shadow_col) > 3 else 1.0
                self.assertGreaterEqual(alpha, 0.30, f"Preset '{pid}' shadow alpha {alpha} too faint")
                self.assertLessEqual(alpha, 0.90, f"Preset '{pid}' shadow alpha {alpha} too heavy")

    def test_presets_zero_line_spacing(self):
        """All 33 presets must enforce zero line_spacing and high-end typography pairings."""
        mgr = StyleManager()
        presets = mgr.get_presets()
        self.assertGreaterEqual(len(presets), 33)

        for p in presets:
            pid = p.get("id")
            self.assertEqual(p.get("line_spacing"), 0.0, f"Preset '{pid}' must have line_spacing == 0.0")
            if p.get("use_2color"):
                self.assertTrue(p.get("hero_font"), f"Preset '{pid}' missing hero_font pairing")
                self.assertTrue(p.get("hero_style"), f"Preset '{pid}' missing hero_style")

        # Curated pairings: a hero word must contrast with its base face
        # (different family or different style), otherwise two-colour is pointless.
        for p in presets:
            if p.get("use_2color"):
                self.assertTrue(
                    p.get("hero_font") != p.get("font") or p.get("hero_style") != p.get("style")
                    or p.get("hero_size_multiplier", 1.0) >= 1.08,
                    f"Preset '{p['id']}' hero pairing does not contrast with the base face")

    def test_all_templates_valid_schema_and_categories(self):
        """All declarative templates must satisfy schema constraints and standard categories."""
        reg = TemplateRegistry()
        templates = reg.get_all()

        curated_categories = {
            "Agency / Social",
            "Cinematic",
            "Signature",
            "Documentary / NGO / Corporate",
            "Editorial / Magazine",
            "Kinetic, Restrained",
            "Minimal Clean",
            "Podcast",
            "SaaS / Tech",
            "Social / Reels 9:16"
        }

        for t in templates:
            self.assertTrue(bool(t.id), "Template missing id")
            self.assertTrue(bool(t.name), f"Template '{t.id}' missing name")
            self.assertIn(t.category, curated_categories,
                          f"Template '{t.id}' has uncurated category '{t.category}'")
            self.assertGreater(t.duration_default, 0.0, f"Template '{t.id}' invalid duration_default")
            self.assertGreater(t.min_hold, 0.0, f"Template '{t.id}' invalid min_hold")
            self.assertGreaterEqual(len(t.layers), 1, f"Template '{t.id}' has no layers")
            self.assertGreaterEqual(len(t.aspect_ratios), 1, f"Template '{t.id}' has no aspect_ratios")


if __name__ == "__main__":
    unittest.main()
