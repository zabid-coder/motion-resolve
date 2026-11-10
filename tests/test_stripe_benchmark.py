import unittest
import json
import os
from unittest.mock import MagicMock
from core.templates.registry import TemplateRegistry
from core.templates.fusion_compiler import FusionCompiler


class TestStripeBenchmark(unittest.TestCase):
    def setUp(self):
        self.registry = TemplateRegistry()
        self.template = self.registry.get_by_id("agency_stripe_notification")

    def test_template_exists_and_loads(self):
        self.assertIsNotNone(self.template, "Template agency_stripe_notification must be registered")

    def test_all_layers_have_in_and_out_motion_tracks(self):
        layer_ids = [l.id for l in self.template.layers]
        self.assertIn("card_plate", layer_ids)
        self.assertIn("app_name", layer_ids)
        self.assertIn("msg_title", layer_ids)
        self.assertIn("amount_pill", layer_ids)

        for layer in self.template.layers:
            in_tracks = [t for t in layer.motion_tracks if t.phase == "in"]
            out_tracks = [t for t in layer.motion_tracks if t.phase == "out"]
            self.assertGreater(len(in_tracks), 0, f"Layer {layer.id} must have IN motion tracks")
            self.assertGreater(len(out_tracks), 0, f"Layer {layer.id} must have OUT motion tracks")

    def test_amount_pill_has_tactile_spring_pop(self):
        amount_layer = next(l for l in self.template.layers if l.id == "amount_pill")
        scale_track = next((t for t in amount_layer.motion_tracks if t.property == "scale" and t.phase == "in"), None)
        self.assertIsNotNone(scale_track, "amount_pill must have an IN scale motion track")
        easings = [kf.easing for kf in scale_track.keyframes]
        self.assertIn("softSpring", easings, "amount_pill scale track must utilize softSpring easing")

    def test_fusion_compiler_handles_layer_exit_keyframes(self):
        """Every layer is keyed on real splines: invisible at both clip edges,
        fully visible in the hold, and the amount pill springs past 1.0."""
        from tests.fake_fusion import make_item
        item, comp, bridge = make_item(72)
        self.assertTrue(FusionCompiler(bridge).compile_and_apply(item, self.template))
        for lid in ("card_plate", "app_name", "msg_title", "amount_pill"):
            merge = comp.FindTool(f"MR_Merge_{lid}")
            self.assertIsNotNone(merge, lid)
            self.assertAlmostEqual(merge.GetInput("Blend", 0), 0.0, places=3)
            self.assertGreater(merge.GetInput("Blend", 40), 0.99)
            self.assertAlmostEqual(merge.GetInput("Blend", 71), 0.0, places=3)
        for lid in ("app_name", "msg_title"):
            xf = comp.FindTool(f"MR_XF_{lid}")
            self.assertNotAlmostEqual(xf.GetInput("Center", 1)[1], 0.5, places=3)
            self.assertNotAlmostEqual(xf.GetInput("Center", 70)[1], 0.5, places=4)
        sizes = [comp.FindTool("MR_XF_amount_pill").GetInput("Size", f) for f in range(30)]
        self.assertGreater(max(sizes), 1.0)

    def test_canvas_area_renders_stripe_at_scrub_points(self):
        import sys
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from ui_qt.widgets.template_canvas_area import TemplateCanvasArea
        from core.templates.theme_tokens import get_theme

        canvas = TemplateCanvasArea()
        canvas.resize(600, 400)
        theme = get_theme("mono")

        for t in (0.0, 0.25, 0.50, 1.0, 3.7):
            canvas.set_state(self.template, {}, theme, t)
            pix = canvas.grab()
            self.assertFalse(pix.isNull())
            self.assertGreaterEqual(pix.width(), 600)
            self.assertGreaterEqual(pix.height(), 400)


if __name__ == "__main__":
    unittest.main()
