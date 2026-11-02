"""
Motion Resolve for DaVinci Resolve Studio - Core Unit Test Suite
Verifies paths, styles, parsing, animation math, and layout templates.
"""

import os
import tempfile
import unittest

from core.paths import get_app_dir, get_user_presets_dir
from core.style_manager import StyleManager
from core.subtitle_parser import SubtitleParser, SubtitleCue
from core.text_plus_builder import TextPlusBuilder
from core.animation_engine import AnimationEngine


class TestCore(unittest.TestCase):

    def test_paths(self):
        app_dir = get_app_dir()
        self.assertTrue(os.path.exists(app_dir))
        presets_dir = get_user_presets_dir()
        self.assertTrue(os.path.isabs(presets_dir))

    def test_style_manager(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = StyleManager(presets_dir=tmp_dir)
            presets = mgr.get_presets()
            self.assertGreaterEqual(len(presets), 15)

            # Test saving custom preset
            test_preset = {
                "id": "my_test_style",
                "name": "My Test Style",
                "font": "Impact",
                "size": 0.08
            }
            self.assertTrue(mgr.save_preset("my_test_style", test_preset))
            loaded = mgr.get_preset_by_id("my_test_style")
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded["name"], "My Test Style")

            # Test deleting custom preset
            self.assertTrue(mgr.delete_preset("my_test_style"))
            self.assertIsNone(mgr.get_preset_by_id("my_test_style"))

    def test_subtitle_parser_chunking(self):
        cue = SubtitleCue(0, 100, "THIS IS A TEST OF CAPTION CHUNKING")
        chunked = SubtitleParser.chunk_cues([cue], words_per_slide=2, remove_punctuation=True)
        self.assertEqual(len(chunked), 4)
        self.assertEqual(chunked[0].text, "THIS IS")
        self.assertEqual(chunked[1].text, "A TEST")
        self.assertEqual(chunked[2].text, "OF CAPTION")
        self.assertEqual(chunked[3].text, "CHUNKING")
        self.assertEqual(chunked[3].end_frame, 100)

    def test_subtitle_parser_word_shifting(self):
        cues = [
            SubtitleCue(0, 50, "HELLO BEAUTIFUL WORLD"),
            SubtitleCue(51, 100, "HOW ARE YOU")
        ]
        # Move 'WORLD' (index 2 of cue 0) to cue 1
        SubtitleParser.move_word(cues, from_idx=0, to_idx=1, word_idx=2)
        self.assertEqual(cues[0].text, "HELLO BEAUTIFUL")
        self.assertEqual(cues[1].text, "HOW ARE YOU WORLD")

    def test_layout_templates(self):
        builder = TextPlusBuilder(bridge=None)
        
        # Template 1: Hero word on line 2
        t1 = builder.apply_layout_template("MIGHT BE THE EASIEST", template_num=1)
        self.assertIn("\n", t1)
        missing_hero = builder.apply_layout_template("A FRESH TITLE", template_num=1, main_word="PRESET SAMPLE")
        self.assertNotIn("PRESET SAMPLE", missing_hero)
        self.assertEqual(missing_hero, "A\nFRESH\nTITLE")

        # Template 2: 2-line balanced
        t2 = builder.apply_layout_template("ONE TWO THREE FOUR", template_num=2)
        self.assertEqual(t2, "ONE TWO\nTHREE FOUR")

        # Template 3: 3-line balanced
        t3 = builder.apply_layout_template("ONE TWO THREE FOUR FIVE SIX", template_num=3)
        lines = t3.split("\n")
        self.assertEqual(len(lines), 3)

    def test_animation_engine_auto_continuity(self):
        animator = AnimationEngine()
        d1 = animator.get_auto_next_direction()
        d2 = animator.get_auto_next_direction()
        d3 = animator.get_auto_next_direction()
        d4 = animator.get_auto_next_direction()
        self.assertEqual([d1, d2, d3, d4], ["up", "right", "down", "left"])

    def test_all_presets_line_spacing_zero(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = StyleManager(presets_dir=tmp_dir)
            presets = mgr.get_presets()
            for p in presets:
                self.assertEqual(
                    p.get("line_spacing", 0.0), 0.0,
                    f"Preset {p['id']} does not have line_spacing == 0.0 (got {p.get('line_spacing')})"
                )

    def test_masked_reveal_pipeline(self):
        from unittest.mock import MagicMock
        engine = AnimationEngine()
        self.assertEqual(engine.MASK_NODE_NAME, "MR_Mask")

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

            def __eq__(self, other):
                return self._val == other

        class MockTool:
            def __init__(self, tool_type):
                self.tool_type = tool_type
                self.attrs = {"TOOLS_RegID": tool_type}
                self.Center = MockFusionInput()
                self.Size = MockFusionInput()
                self.Angle = MockFusionInput()
                self.Length = MockFusionInput()
                self.Width = None
                self.Height = None
                self.Input = MockFusionInput()
                self.Output = MockFusionInput()
                self.EffectMask = MockFusionInput()
                self.Mask = MockFusionInput()
                self.Delete = MagicMock()

            def __setattr__(self, name, val):
                if hasattr(self, name) and isinstance(getattr(self, name), MockFusionInput):
                    getattr(self, name)._val = val
                else:
                    super().__setattr__(name, val)

            def SetAttrs(self, a):
                self.attrs.update(a)

            def GetAttrs(self):
                return self.attrs

        tools = {}
        tools["Template"] = MockTool("TextPlus")
        tools["MediaOut1"] = MockTool("MediaOut")

        def mock_find_tool(name):
            return tools.get(name)

        def mock_add_tool(tool_type):
            mock_tool = MockTool(tool_type)
            return mock_tool

        def add_tool_with_name(tool_type):
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
        comp.AddTool.side_effect = add_tool_with_name

        res = engine.apply_motion_preset(timeline_item, effect_in="slide_up", effect_out="slide_down")
        self.assertTrue(res)

        # Verify MR_Mask exists and anchored
        self.assertIn("MR_Mask", tools)
        mr_mask = tools["MR_Mask"]
        self.assertEqual(mr_mask.Center, [0.5, 0.5])
        self.assertEqual(mr_mask.Width, 0.95)
        self.assertEqual(mr_mask.Height, 0.14)

        # Verify MR_Transform.EffectMask connected to MR_Mask.Mask
        mr_trans = tools["MR_Transform"]
        mr_trans.EffectMask.ConnectTo.assert_called_with(mr_mask.Mask)

        # Verify true off-screen displacement expression
        center_expr = mr_trans.Center.SetExpression.call_args[0][0]
        self.assertIn("0.55", center_expr)

        # Verify pop_in scales smoothly from zero
        engine.apply_motion_preset(timeline_item, effect_in="pop_in")
        size_expr = mr_trans.Size.SetExpression.call_args[0][0]
        self.assertIn("1.0", size_expr)

        # Verify slide_left displacement is true off-screen (0.65)
        engine.apply_motion_preset(timeline_item, effect_in="slide_left", effect_out="slide_right")
        center_expr_lr = mr_trans.Center.SetExpression.call_args[0][0]
        self.assertIn("0.65", center_expr_lr)
        self.assertNotIn("0.4", center_expr_lr)

        # Verify bounce_up displacement is 0.35
        engine.apply_motion_preset(timeline_item, effect_in="bounce_up")
        bounce_expr = mr_trans.Center.SetExpression.call_args[0][0]
        self.assertIn("0.35", bounce_expr)

        # Verify remove_effects deletes MR_Mask
        engine.remove_effects(timeline_item)
        mr_mask.Delete.assert_called_once()
        mr_trans.Delete.assert_called_once()

    def test_video_presets_exist(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mgr = StyleManager(presets_dir=tmp_dir)
            presets = mgr.get_presets()
            ids = [p["id"] for p in presets]
            for vid_id in ["em_bold", "em_bold_yellow", "nowy", "bouncy", "style_21"]:
                self.assertIn(vid_id, ids, f"Preset '{vid_id}' from reference video not found in preset catalog!")


if __name__ == "__main__":
    unittest.main()
