"""Count-up numbers, per-letter stagger and preset motion coverage."""
import json
import glob
import unittest

from tests.fake_fusion import make_item
from core.templates.counter import parse_count, lua_count_expression
from core.templates.motion_curves import plan_timing, layer_channel_plan, stagger_delay, stagger_plan
from core.templates.registry import TemplateRegistry
from core.templates.fusion_compiler import FusionCompiler
from core.animation_engine import AnimationEngine

REG = TemplateRegistry()


class TestCounter(unittest.TestCase):
    def test_formats_are_preserved(self):
        cases = {
            "87%": "87%", "+$2,000.00": "+$2,000.00", "94.8%": "94.8%",
            "1,000,000 SUBSCRIBERS": "1,000,000 SUBSCRIBERS", "১৪ জুলাই": "১৪ জুলাই",
        }
        for text, final in cases.items():
            spec = parse_count(text)
            self.assertIsNotNone(spec, text)
            self.assertEqual(spec.render(1.0), final)
            self.assertEqual(len(spec.render(0.0)) <= len(final), True)
        self.assertEqual(parse_count("+$2,000.00").render(0.0), "+$0.00")
        self.assertIsNone(parse_count("no digits here"))

    def test_lua_escapes_line_breaks(self):
        expr = lua_count_expression(parse_count(" \n100 HOURS"), 0, 30)
        self.assertNotIn("\n", expr)
        self.assertIn("\\n", expr)

    def test_compiler_sets_count_expression(self):
        item, comp, bridge = make_item(120)
        FusionCompiler(bridge).compile_and_apply(item, REG.get_template("sig_stat_reveal"))
        tool = comp.FindTool("Template")
        self.assertIn("Text(", tool.expressions.get("StyledText", ""))

    def test_count_switch_off(self):
        item, comp, bridge = make_item(120)
        FusionCompiler(bridge).compile_and_apply(item, REG.get_template("sig_stat_reveal"), {"count_up": False})
        self.assertFalse(comp.FindTool("Template").expressions.get("StyledText"))


class TestStagger(unittest.TestCase):
    def test_last_character_finishes_on_last_frame(self):
        tpl = REG.get_template("trend_role_chip")
        layer = next(l for l in tpl.layers if l.id == "name")
        timing = plan_timing(tpl, 95, 24.0)
        plan = layer_channel_plan(layer, timing)
        d = stagger_delay({"delay": 1.0}, "Nusrat Jahan", timing)
        sp = stagger_plan(plan, "Nusrat Jahan", d, timing)
        last_char_end = sp["opacity"][-1][0] + (len("Nusrat Jahan") - 1) * d
        self.assertAlmostEqual(last_char_end, 95.0, places=3)

    def test_follower_drives_per_character_opacity(self):
        item, comp, bridge = make_item(96)
        FusionCompiler(bridge).compile_and_apply(item, REG.get_template("trend_role_chip"))
        # Resolve rewrites a title's "Template" tool on reload, bypassing a Follower,
        # so per-letter layers must live on their own Text+ tool.
        self.assertIsNone(comp.FindTool("Template").modifiers.get("StyledText") if comp.FindTool("Template") else None)
        fol = comp.FindTool("MR_Text_name").modifiers.get("StyledText")
        self.assertEqual(getattr(fol, "regid", ""), "StyledTextFollower")
        self.assertAlmostEqual(fol.GetInput("Opacity1", 0), 0.0, places=3)
        self.assertGreater(fol.GetInput("Opacity1", 40), 0.99)

    def test_bengali_never_split_into_letters(self):
        item, comp, bridge = make_item(96)
        FusionCompiler(bridge).compile_and_apply(item, REG.get_template("trend_role_chip"), {"name": "নুসরাত জাহান"})
        name_tool = comp.FindTool("Template") or comp.FindTool("MR_Text_name")
        self.assertIsNone(name_tool.modifiers.get("StyledText"))


class TestPresetMotion(unittest.TestCase):
    def test_every_preset_motion_is_implemented(self):
        known_in = {"fade", "fade_in", "fade_in_slow", "pop_in", "bounce_pop", "glitch_zoom", "scale_fade",
                    "zoom_punch", "slam_drop", "slide_up_blur", "jitter", "scribble", "flicker", "shake",
                    "bounce_up", "bounce_down", "slide_up", "slide_down"} | set(AnimationEngine.CHAR_EFFECTS_IN)
        known_out = {"fade", "fade_out", "slide_down", "slide_up", "scale_out", "blur_out"} | set(AnimationEngine.CHAR_EFFECTS_OUT)
        entrances = set()
        for p in glob.glob("data/styles/*.json"):
            d = json.load(open(p, encoding="utf-8"))
            self.assertIn(d["animation_in"], known_in, d["id"])
            self.assertIn(d["animation_out"], known_out, d["id"])
            entrances.add(d["animation_in"])
        self.assertGreaterEqual(len(entrances), 12, "presets should not all share one motion")

    def test_bengali_presets_avoid_letter_motion(self):
        for p in glob.glob("data/styles/*bengali*.json") + glob.glob("data/styles/*bangla*.json"):
            d = json.load(open(p, encoding="utf-8"))
            self.assertNotIn(d["animation_in"], AnimationEngine.CHAR_EFFECTS_IN, d["id"])


if __name__ == "__main__":
    unittest.main()
