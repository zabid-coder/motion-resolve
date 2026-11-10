"""
Behavioural tests for the Fusion compiler against a Fusion stand-in that
reproduces DaVinci Resolve 21 semantics (see tests/fake_fusion.py).
"""

import unittest

from tests.fake_fusion import make_item
from core.templates.registry import TemplateRegistry
from core.templates.fusion_compiler import FusionCompiler
from core.templates.motion_curves import cubic_bezier, fusion_keyframes, expand_springs, plan_timing
from tests.fake_fusion import FakeSpline


REG = TemplateRegistry()
SIGNATURE = [t for t in REG.get_all() if t.category == "Signature"]


def merges(comp):
    return {n: t for n, t in comp.tools.items() if n.startswith("MR_Merge_")}


def layer_opacity(comp, merge_name, frame):
    """Visible opacity of a layer: its merge Blend, or - for per-letter layers -
    the Follower's per-character opacity (the merge then stays at 1)."""
    m = comp.tools[merge_name]
    lid = merge_name[len("MR_Merge_"):]
    for tname in ("MR_Text_" + lid, "Template"):
        t = comp.tools.get(tname)
        fol = t.modifiers.get("StyledText") if t is not None else None
        if fol is not None and getattr(fol, "regid", "") == "StyledTextFollower":
            if m.connections.get("Foreground") and m.connections["Foreground"].GetTool().connections.get("Input"):
                src = m.connections["Foreground"].GetTool().connections["Input"].GetTool()
                if src is t:
                    return fol.GetInput("Opacity1", frame) * m.GetInput("Blend", frame)
    return m.GetInput("Blend", frame)


def compile_on(tid, frames=72, res=(1920, 1080), render_start=0, **kw):
    item, comp, bridge = make_item(frames, render_start, res)
    ok = FusionCompiler(bridge).compile_and_apply(item, REG.get_template(tid), **kw)
    return ok, comp


class TestMotionCurves(unittest.TestCase):
    def test_easing_endpoints_and_shape(self):
        for token in ("expoOut", "quintOut", "quartInOut", "cubicIn", "expoInOut", "linear"):
            self.assertAlmostEqual(cubic_bezier(token, 0.0), 0.0, places=6)
            self.assertAlmostEqual(cubic_bezier(token, 1.0), 1.0, places=6)
        self.assertGreater(cubic_bezier("expoOut", 0.25), 0.6)       # decelerating
        self.assertLess(cubic_bezier("cubicIn", 0.25), 0.1)          # accelerating
        self.assertGreater(max(cubic_bezier("softSpring", x / 50) for x in range(51)), 1.0)  # overshoot

    def test_spring_expands_to_damped_oscillation(self):
        keys = expand_springs([(0.0, 0.5, "spring"), (10.0, 1.0, "linear")])
        values = [v for _, v, _ in keys]
        self.assertGreater(max(values), 1.0)      # overshoot
        self.assertLess(min(values[2:]), 1.0)     # undershoot after it
        self.assertEqual(keys[-1][1], 1.0)        # settles

    def test_fusion_handles_reproduce_easing(self):
        """Relative Fusion handles written by the compiler must evaluate to the token curve."""
        sp = FakeSpline(0, 0)
        sp.SetKeyFrames(fusion_keyframes([(0.0, 0.0, "expoOut"), (20.0, 1.0, "linear")]))
        for f in (2, 5, 10, 15):
            self.assertAlmostEqual(sp.value(f), cubic_bezier("expoOut", f / 20.0), places=3)

    def test_short_clip_timing_fits(self):
        tpl = REG.get_template("sig_cinematic_title")  # 2s entrance, 1s exit
        t = plan_timing(tpl, 17, 24.0)
        self.assertLessEqual(t["in_end"], t["out_start"])
        self.assertAlmostEqual(t["out_start"] + 1.0 * t["out_scale"], 17.0, places=3)


class TestCompiledTimeline(unittest.TestCase):
    def assert_clean_edges(self, comp, last):
        ms = merges(comp)
        self.assertTrue(ms, "no layer merges were built")
        for name, m in ms.items():
            self.assertAlmostEqual(layer_opacity(comp, name, 0), 0.0, places=3, msg=f"{name} visible on first frame")
            self.assertAlmostEqual(layer_opacity(comp, name, last), 0.0, places=3, msg=f"{name} visible on last frame")

    def test_every_signature_template_animates_cleanly(self):
        self.assertGreaterEqual(len(SIGNATURE), 11)
        for tpl in SIGNATURE:
            with self.subTest(template=tpl.id):
                ok, comp = compile_on(tpl.id, 120)
                self.assertTrue(ok)
                self.assert_clean_edges(comp, 119)
                for name, m in merges(comp).items():
                    self.assertGreater(layer_opacity(comp, name, 70), 0.99, f"{name} not fully visible during hold")
                out = comp.FindTool("MediaOut1")
                self.assertIs(out.connections["Input"].GetTool(), comp.FindTool("MR_TemplateOut"))

    def test_legacy_templates_now_fade_per_layer(self):
        for tid in ("pod_lower_third_slate", "agency_stripe_notification", "kin_masked_line", "saas_glass_card"):
            with self.subTest(template=tid):
                ok, comp = compile_on(tid, 72)
                self.assertTrue(ok)
                self.assert_clean_edges(comp, 71)

    def test_staggered_entrance(self):
        ok, comp = compile_on("pod_lower_third_slate", 72)
        name = comp.FindTool("MR_Merge_guest_name").GetInput("Blend", 9)
        role = comp.FindTool("MR_Merge_guest_role").GetInput("Blend", 9)
        self.assertGreater(name, role + 0.1, "role should enter after the name")

    def test_masked_rise_is_keyed_on_layer_transform(self):
        ok, comp = compile_on("sig_editorial_lower_third", 120)
        xf = comp.FindTool("MR_XF_name")
        y_start, y_hold = xf.GetInput("Center", 3)[1], xf.GetInput("Center", 60)[1]
        self.assertLess(y_start, 0.49)
        self.assertAlmostEqual(y_hold, 0.5, places=4)
        clip = comp.FindTool("MR_Clip_name")
        self.assertIsNotNone(clip)
        self.assertIs(comp.FindTool("MR_Merge_name").connections["EffectMask"].GetTool(), clip)

    def test_short_18_frame_clip_exits_on_last_frame(self):
        ok, comp = compile_on("pod_lower_third_slate", 18)
        self.assertTrue(ok)
        self.assert_clean_edges(comp, 17)
        self.assertGreater(max(comp.FindTool("MR_Merge_guest_name").GetInput("Blend", f) for f in range(18)), 0.9)

    def test_render_start_offset(self):
        item, comp, bridge = make_item(72, render_start=100)
        FusionCompiler(bridge).compile_and_apply(item, REG.get_template("sig_doc_locator"))
        m = comp.FindTool("MR_Merge_place")
        self.assertAlmostEqual(m.GetInput("Blend", 100), 0.0, places=3)
        self.assertGreater(m.GetInput("Blend", 140), 0.99)
        self.assertAlmostEqual(m.GetInput("Blend", 171), 0.0, places=3)

    def test_spring_pop_overshoots(self):
        ok, comp = compile_on("agency_stripe_notification", 96)
        xf = comp.FindTool("MR_XF_amount_pill")
        sizes = [xf.GetInput("Size", f) for f in range(0, 30)]
        self.assertLess(sizes[0], 0.8)
        self.assertGreater(max(sizes), 1.0)

    def test_translucent_shapes_are_premultiplied(self):
        ok, comp = compile_on("sig_glass_quote", 120)
        border = comp.FindTool("MR_Border_card")
        self.assertAlmostEqual(border.GetInput("TopLeftRed"), 0.14, places=3)
        self.assertAlmostEqual(border.GetInput("TopLeftAlpha"), 0.14, places=3)

    def test_vertical_timeline_scales_design_up(self):
        ok, comp = compile_on("sig_social_hook", 72, res=(1080, 1920))
        self.assertGreater(comp.FindTool("Template").GetInput("Size"), 0.046 * 1.5)

    def test_recompile_replaces_previous_graph(self):
        item, comp, bridge = make_item(72)
        c = FusionCompiler(bridge)
        c.compile_and_apply(item, REG.get_template("sig_news_tag"))
        first = set(comp.tools)
        c.compile_and_apply(item, REG.get_template("sig_news_tag"))
        self.assertEqual(first, set(comp.tools))
        c.compile_and_apply(item, REG.get_template("sig_cinematic_title"))
        self.assertFalse(any(n.endswith("tag_block") for n in comp.tools))

    def test_text_line_spacing_is_a_multiplier(self):
        ok, comp = compile_on("sig_stat_reveal", 72)
        self.assertAlmostEqual(comp.FindTool("MR_Text_label").GetInput("LineSpacingClone"), 1.0, places=3)


if __name__ == "__main__":
    unittest.main()
