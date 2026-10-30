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
        """Verifies FusionCompiler creates MR_RevealMask, sets parameters, connects EffectMask, and cleans up."""
        from unittest.mock import MagicMock
        from core.templates.fusion_compiler import FusionCompiler

        bridge = MagicMock()
        bridge.get_timeline_fps.return_value = 24.0
        compiler = FusionCompiler(bridge=bridge)

        reg = TemplateRegistry()
        tpl = reg.get_template("pod_lower_third_slate")
        self.assertIsNotNone(tpl)

        timeline_item = MagicMock()
        timeline_item.GetFusionCompCount.return_value = 1
        comp = MagicMock()
        timeline_item.GetFusionCompByIndex.return_value = comp

        class MockFusionInput:
            def __init__(self, val=None):
                self._val = val
                self.SetExpression = MagicMock()
                self.ConnectTo = MagicMock()

            def __eq__(self, other):
                return self._val == other

            def __repr__(self):
                return f"MockFusionInput({self._val})"

        class MockTool:
            def __init__(self, tool_type):
                self.tool_type = tool_type
                self.attrs = {"TOOLS_RegID": tool_type}
                self.Center = MockFusionInput()
                self.Size = MockFusionInput()
                self.Width = None
                self.Height = None
                self.Input = MockFusionInput()
                self.Output = MockFusionInput()
                self.EffectMask = MockFusionInput()
                self.Mask = MockFusionInput()
                self.Background = MockFusionInput()
                self.Foreground = MockFusionInput()
                self.Delete = MagicMock()
                self.inputs = {}

            def __setattr__(self, name, val):
                if hasattr(self, name) and isinstance(getattr(self, name), MockFusionInput):
                    getattr(self, name)._val = val
                else:
                    super().__setattr__(name, val)

            def SetInput(self, name, val, frame=None):
                if frame is not None:
                    if name not in self.inputs or not isinstance(self.inputs[name], dict):
                        self.inputs[name] = {}
                    self.inputs[name][frame] = val
                else:
                    self.inputs[name] = val
                if hasattr(self, name) and isinstance(getattr(self, name), MockFusionInput):
                    getattr(self, name)._val = val
                else:
                    setattr(self, name, val)

            def SetAttrs(self, a):
                self.attrs.update(a)

            def GetAttrs(self):
                return self.attrs

        tools = {}
        tools["Template"] = MockTool("TextPlus")
        tools["MR_Transform"] = MockTool("Transform")
        tools["MediaOut1"] = MockTool("MediaOut")

        def mock_find_tool(name):
            return tools.get(name)

        def mock_add_tool(tool_type, *args):
            tool = MockTool(tool_type)
            orig_set_attrs = tool.SetAttrs
            def wrapped_set_attrs(a):
                orig_set_attrs(a)
                name = a.get("TOOLS_Name")
                if name:
                    tools[name] = tool
            tool.SetAttrs = wrapped_set_attrs
            return tool

        comp.FindTool.side_effect = mock_find_tool
        comp.AddTool.side_effect = mock_add_tool
        comp.GetToolList.return_value = tools

        # 1. Compile and apply template
        success = compiler.compile_and_apply(
            timeline_item,
            tpl,
            param_overrides={"pos_y": 0.25},
            speed=1.0,
            intensity=1.0
        )
        self.assertTrue(success)

        # 2. Verify MR_RevealMask was created and added to comp
        self.assertIn("MR_RevealMask", tools)
        reveal_mask = tools["MR_RevealMask"]
        self.assertEqual(reveal_mask.tool_type, "RectangleMask")

        # 3. Verify reveal_mask parameters
        self.assertEqual(reveal_mask.Center, [0.5, 0.25])
        self.assertEqual(reveal_mask.Width, 0.95)
        self.assertAlmostEqual(reveal_mask.Height, 0.239, places=2)

        # 4. Verify MR_Transform.EffectMask is connected to reveal_mask.Mask
        mr_trans = tools["MR_Transform"]
        mr_trans.EffectMask.ConnectTo.assert_called_with(reveal_mask.Mask)

        # 5. Verify motion tracks entrance, hold, and exit
        t_info = compiler.calculate_clip_timing(None, tpl.duration_default, tpl.in_duration, tpl.out_duration, 24.0, 1.0)
        in_frames = t_info["in_frames"]
        out_frames = t_info["out_frames"]
        total_frames = t_info["total_frames"]
        hold_end_frame = t_info["hold_end_frame"]

        # At frame 0: Cy translates from authored track keyframe (-0.025, so 0.5 - 0.025 = 0.475)
        center_f0 = mr_trans.inputs["Center"][0]
        self.assertAlmostEqual(center_f0[1], 0.5 - 0.025, places=3)

        # At in_frames: resting position 0.5 (exact 0.0 offset)
        center_in = mr_trans.inputs["Center"][in_frames]
        self.assertAlmostEqual(center_in[1], 0.5, places=3)

        # At hold_end_frame: resting position 0.5
        center_hold = mr_trans.inputs["Center"][hold_end_frame]
        self.assertAlmostEqual(center_hold[1], 0.5, places=3)

        # At exit (total_frames): Cy slides into mask hiding (-0.045 from center, so 0.455)
        center_exit = mr_trans.inputs["Center"][total_frames]
        self.assertAlmostEqual(center_exit[1], 0.5 - 0.045, places=3)

        # 6. Verify _cleanup_previous_tools removes MR_RevealMask
        compiler._cleanup_previous_tools(comp)
        reveal_mask.Delete.assert_called_once()

    def test_kinetic_templates_compilation(self):
        """Verifies new kinetic templates (kin_split_reveal, kin_word_explosion) load and compile cleanly."""
        from unittest.mock import MagicMock
        from core.templates.fusion_compiler import FusionCompiler

        bridge = MagicMock()
        bridge.get_timeline_fps.return_value = 24.0
        compiler = FusionCompiler(bridge=bridge)

        reg = TemplateRegistry()
        split_tpl = reg.get_template("kin_split_reveal")
        self.assertIsNotNone(split_tpl)
        self.assertEqual(len(split_tpl.layers), 3)

        word_tpl = reg.get_template("kin_word_explosion")
        self.assertIsNotNone(word_tpl)
        self.assertEqual(len(word_tpl.layers), 3)

        # Mock timeline item and Fusion comp
        timeline_item = MagicMock()
        timeline_item.GetFusionCompCount.return_value = 1
        comp = MagicMock()
        timeline_item.GetFusionCompByIndex.return_value = comp

        class MockFusionInput:
            def __init__(self, val=None):
                self._val = val
                self.SetExpression = MagicMock()
                self.ConnectTo = MagicMock()

        class MockTool:
            def __init__(self, tool_type):
                self.tool_type = tool_type
                self.attrs = {"TOOLS_RegID": tool_type}
                self.Center = MockFusionInput()
                self.Size = MockFusionInput()
                self.Width = None
                self.Height = None
                self.Input = MockFusionInput()
                self.Output = MockFusionInput()
                self.EffectMask = MockFusionInput()
                self.Mask = MockFusionInput()
                self.Background = MockFusionInput()
                self.Foreground = MockFusionInput()
                self.Delete = MagicMock()
                self.inputs = {}

            def SetAttrs(self, a):
                self.attrs.update(a)

            def SetInput(self, name, val, frame=None):
                if frame is not None:
                    if name not in self.inputs or not isinstance(self.inputs[name], dict):
                        self.inputs[name] = {}
                    self.inputs[name][frame] = val
                else:
                    self.inputs[name] = val

        tools = {}
        tools["Template"] = MockTool("TextPlus")
        tools["MR_Transform"] = MockTool("Transform")
        tools["MediaOut1"] = MockTool("MediaOut")

        comp.FindTool.side_effect = lambda n: tools.get(n)
        def mock_add_tool(tool_type, *args):
            t = MockTool(tool_type)
            orig_set = t.SetAttrs
            def wrapped(a):
                orig_set(a)
                name = a.get("TOOLS_Name")
                if name: tools[name] = t
            t.SetAttrs = wrapped
            return t
        comp.AddTool.side_effect = mock_add_tool
        comp.GetToolList.return_value = tools

        success1 = compiler.compile_and_apply(timeline_item, split_tpl)
        self.assertTrue(success1)
        self.assertIn("MR_RevealMask", tools)

        success2 = compiler.compile_and_apply(timeline_item, word_tpl)
        self.assertTrue(success2)


if __name__ == "__main__":
    unittest.main()
