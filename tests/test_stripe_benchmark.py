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
        compiler = FusionCompiler(bridge=None)
        timing = compiler.calculate_clip_timing(
            72, self.template.duration_default, self.template.in_duration, self.template.out_duration, 24.0, 1.0
        )
        timing["intensity"] = 1.0

        amount_pill = next(l for l in self.template.layers if l.id == "amount_pill")
        card_plate = next(l for l in self.template.layers if l.id == "card_plate")
        app_name = next(l for l in self.template.layers if l.id == "app_name")

        # 1. amount_pill: verifies SetInput for Size and Alpha1 across in, hold, and out frames
        mock_tool_pill = MagicMock()
        compiler._compile_layer_motion(mock_tool_pill, amount_pill, [0.86, 0.28], timing, base_size=0.056)

        pill_calls = mock_tool_pill.SetInput.call_args_list
        size_frames = {c[0][2] for c in pill_calls if c[0][0] == "Size" and len(c[0]) > 2}
        alpha_frames = {c[0][2] for c in pill_calls if c[0][0] == "Alpha1" and len(c[0]) > 2}

        self.assertTrue(any(0 <= f <= timing["in_frames"] for f in size_frames), "Size must be keyframed in 'in' phase")
        self.assertTrue(any(timing["in_frames"] < f < timing["hold_end_frame"] for f in size_frames), "Size must be set during hold phase")
        self.assertTrue(any(timing["hold_end_frame"] <= f <= timing["total_frames"] for f in size_frames), "Size must be keyframed in 'out' phase")

        self.assertTrue(any(0 <= f <= timing["in_frames"] for f in alpha_frames), "Alpha1 must be keyframed in 'in' phase")
        self.assertTrue(any(timing["in_frames"] < f < timing["hold_end_frame"] for f in alpha_frames), "Alpha1 must be set during hold phase")
        self.assertTrue(any(timing["hold_end_frame"] <= f <= timing["total_frames"] for f in alpha_frames), "Alpha1 must be keyframed in 'out' phase")

        # 2. card_plate and app_name: verifies SetInput for Center during both in and out frames
        for layer_spec in (card_plate, app_name):
            mock_layer_tool = MagicMock()
            compiler._compile_layer_motion(mock_layer_tool, layer_spec, [0.5, 0.28], timing)
            center_calls = [c for c in mock_layer_tool.SetInput.call_args_list if c[0][0] == "Center"]
            center_frames = {c[0][2] for c in center_calls if len(c[0]) > 2}
            self.assertTrue(any(0 <= f <= timing["in_frames"] for f in center_frames), f"{layer_spec.id} Center must be keyframed in 'in' phase")
            self.assertTrue(any(timing["hold_end_frame"] <= f <= timing["total_frames"] for f in center_frames), f"{layer_spec.id} Center must be keyframed in 'out' phase")

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
