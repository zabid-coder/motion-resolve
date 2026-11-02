"""
Motion Resolve - Comprehensive Unit Tests for Audit Fixes
Covers:
1. auto_tab track selection and sample plan label preservation
2. animation_engine flicker scaling and pipeline
3. convert_drawer and In/Out subtitle filtering
4. text_plus_builder 2-Color hero text split and attribute pasting
5. template registry path resolution and theme color normalization
6. canvas_view viewport zoom and paste attributes button
7. resolve_api redo history
"""

import os
import json
import unittest
from unittest.mock import MagicMock, patch

from core.subtitle_parser import SubtitleCue
from core.templates.theme_tokens import normalize_color, color_to_hex
from core.templates.registry import TemplateRegistry
from core.resolve_api import ResolveBridge
from core.animation_engine import AnimationEngine
from core.auto_generator import AutoGenerator


class TestAuditFixes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import sys, os
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication(sys.argv)

    def test_theme_color_normalization(self):
        # 6-char hex
        c = normalize_color("#ff5500")
        self.assertAlmostEqual(c[0], 1.0, places=2)
        self.assertAlmostEqual(c[1], 0.333, places=2)
        self.assertAlmostEqual(c[2], 0.0, places=2)
        self.assertEqual(c[3], 1.0)

        # 8-char hex with alpha
        c_alpha = normalize_color("#00ff80aa")
        self.assertAlmostEqual(c_alpha[0], 0.0, places=2)
        self.assertAlmostEqual(c_alpha[1], 1.0, places=2)
        self.assertAlmostEqual(c_alpha[2], 0.502, places=2)
        self.assertAlmostEqual(c_alpha[3], 0.667, places=2)

        # Float RGBA list
        c_list = normalize_color([0.2, 0.4, 0.6, 0.8])
        self.assertEqual(c_list, [0.2, 0.4, 0.6, 0.8])

        # 0-255 int list
        c_int = normalize_color([255, 128, 0])
        self.assertAlmostEqual(c_int[0], 1.0, places=2)
        self.assertAlmostEqual(c_int[1], 0.502, places=2)
        self.assertEqual(c_int[3], 1.0)

        # Color to hex
        hex_str = color_to_hex([1.0, 0.333, 0.0, 1.0])
        self.assertEqual(hex_str, "#ff5400")

    def test_font_catalog_uses_installed_local_families(self):
        from core.font_catalog import installed_font_families, installed_font_options, resolve_available_font
        from core.templates.theme_tokens import get_theme, GLOBAL_THEMES

        installed = {name.casefold() for name in installed_font_families()}
        self.assertTrue(installed)
        self.assertIn(resolve_available_font("a definitely missing font", "display").casefold(), installed)
        self.assertIn(resolve_available_font("a definitely missing font", "bengali").casefold(), installed)
        self.assertTrue(set(name.casefold() for name in installed_font_options()).issubset(installed))

        for theme_id in GLOBAL_THEMES:
            theme = get_theme(theme_id)
            for key in ("font_heading", "font_body", "font_heading_bn", "font_body_bn"):
                self.assertIn(theme[key].casefold(), installed, f"{theme_id}.{key} must be installed")

    def test_template_registry_path_resolution(self):
        reg = TemplateRegistry()
        templates = reg.get_all()
        self.assertGreater(len(templates), 0)

        # Verify each template has a valid resolved path in its category folder
        for tpl in templates:
            path = reg.get_template_path(tpl.id)
            self.assertIsNotNone(path, f"Template {tpl.id} must have a registered path")
            self.assertTrue(path.endswith(f"{tpl.id}.json"))
            import os
            self.assertTrue(os.path.exists(path), f"Path {path} must exist on disk")

    def test_resolve_bridge_redo_reports_unsupported_without_losing_history(self):
        bridge = ResolveBridge()
        self.assertEqual(len(bridge._undo_history), 0)
        self.assertEqual(len(bridge._redo_history), 0)

        mock_tl = MagicMock()
        mock_tl.DeleteClips.return_value = True
        mock_tl.GetTrackCount.return_value = 1
        mock_tl.GetItemListInTrack.return_value = ["item1"]

        bridge.get_current_timeline = MagicMock(return_value=mock_tl)

        # Push an undo snapshot
        bridge.push_undo_snapshot(["item1", "item2"], operation_name="Create Captions", track_index=1)
        self.assertEqual(len(bridge._undo_history), 1)
        self.assertEqual(len(bridge._redo_history), 0)

        # Undo
        ok, msg = bridge.undo_last_batch()
        self.assertTrue(ok)
        self.assertIn("Undid", msg)
        self.assertEqual(len(bridge._undo_history), 0)
        self.assertEqual(len(bridge._redo_history), 1)

        # Redo
        ok_redo, msg_redo = bridge.redo_last_batch()
        self.assertFalse(ok_redo)
        self.assertIn("Redo is unavailable", msg_redo)
        self.assertEqual(len(bridge._undo_history), 0)
        self.assertEqual(len(bridge._redo_history), 1)

    def test_flicker_dynamic_scaling(self):
        engine = AnimationEngine()

        class MockExpr:
            def __init__(self):
                self.expr = None
            def SetExpression(self, val):
                self.expr = val

        class MockTool:
            def __init__(self):
                self.Alpha1 = MockExpr()
                self.attrs = {"TOOLS_RegID": "TextPlus"}
            def GetAttrs(self):
                return self.attrs
            def FindTool(self, name):
                return self if name == "Template" else None

        mock_comp = MockTool()
        mock_item = MagicMock()
        mock_item.GetFusionCompCount.return_value = 1
        mock_item.GetFusionCompByIndex.return_value = mock_comp

        # Low intensity flicker
        engine.get_or_create_pipeline = MagicMock(return_value=(MagicMock(), MagicMock(), mock_comp, MagicMock()))
        engine.apply_motion_preset(mock_item, options={"flicker": True, "flicker_frequency": 0.2, "flicker_intensity": 0.4})
        expr_low = mock_comp.Alpha1.expr
        self.assertIn("0.60", expr_low) # min_alpha = 1.0 - 0.4 = 0.60

        # High intensity flicker
        engine.apply_motion_preset(mock_item, options={"flicker": True, "flicker_frequency": 0.8, "flicker_intensity": 1.0})
        expr_high = mock_comp.Alpha1.expr
        self.assertIn("0.00", expr_high) # min_alpha = 1.0 - 1.0 = 0.00
        self.assertIn("% 2", expr_high)

    def test_motion_effects_use_independent_manual_controls(self):
        engine = AnimationEngine()
        class InputProxy:
            def __init__(self):
                self.expression = None
                self.value = None
            def SetExpression(self, expression):
                self.expression = expression

        class TransformProxy:
            def __init__(self):
                object.__setattr__(self, "Center", InputProxy())
                object.__setattr__(self, "Size", InputProxy())
                object.__setattr__(self, "Angle", InputProxy())
            def __setattr__(self, name, value):
                current = getattr(self, name, None)
                if isinstance(current, InputProxy):
                    current.value = value
                else:
                    object.__setattr__(self, name, value)

        transform, blur = TransformProxy(), TransformProxy()
        object.__setattr__(blur, "Length", InputProxy())
        comp = MagicMock()
        comp.RenderStart = 0
        comp.RenderEnd = 100
        engine.get_or_create_pipeline = MagicMock(return_value=(transform, blur, MagicMock(), MagicMock()))
        item = MagicMock()
        item.GetFusionCompCount.return_value = 1
        item.GetFusionCompByIndex.return_value = comp

        engine.apply_motion_preset(item, effect_in="slide_up", options={
            "jitter": True, "jitter_intensity": 0.4, "jitter_speed": 1.8,
            "scribble": True, "scribble_intensity": 0.7, "scribble_speed": 1.4,
            "motion_blur": True, "motion_blur_intensity": 1.6, "motion_blur_angle": 37,
        })

        center_expression = transform.Center.expression
        angle_expression = transform.Angle.expression
        blur_expression = blur.Length.expression
        self.assertIn("0.0032", center_expression)  # jitter: 0.008 * 0.4
        self.assertIn("9.54", center_expression)     # jitter rate: 5.3 * 1.8
        self.assertIn("0.0049", center_expression)  # scribble: 0.007 * 0.7
        self.assertIn("0.84", angle_expression)      # scribble amount: 1.2 * 0.7
        self.assertIn("0.08", blur_expression)      # blur amount: 0.05 * 1.6
        self.assertEqual(blur.Angle.value, 37)

    def test_motion_panel_individual_tuning_and_matching_direction_pads(self):
        from ui_qt.widgets.motion_panel import MotionEffectsControllerWidget
        panel = MotionEffectsControllerWidget()
        self.assertEqual(panel.btn_in_up.size(), panel.btn_out_up.size())
        self.assertEqual(panel.btn_in_left.size(), panel.btn_out_left.size())
        emitted = []
        panel.motionChanged.connect(emitted.append)
        panel.slider_jitter_int.setValue(45)
        self.assertAlmostEqual(emitted[-1]["jitter_intensity"], 0.45)
        panel.slider_scribble_spd.setValue(165)
        self.assertAlmostEqual(emitted[-1]["scribble_speed"], 1.65)
        panel.slider_mblur_angle.setValue(42)
        self.assertEqual(emitted[-1]["motion_blur_angle"], 42)

    def test_auto_generator_in_out_filtering(self):
        bridge = MagicMock()
        mock_tl = MagicMock()
        bridge.get_current_timeline.return_value = mock_tl
        bridge.get_in_out_range.return_value = (50, 150)

        # 3 cues: cue1 (0-40, outside), cue2 (60-100, inside), cue3 (160-200, outside)
        raw_cues = [
            SubtitleCue(0, 40, "Before range"),
            SubtitleCue(60, 100, "Inside range"),
            SubtitleCue(160, 200, "After range"),
        ]

        with patch("core.subtitle_parser.SubtitleParser.extract_from_timeline", return_value=raw_cues):
            gen = AutoGenerator(bridge)
            gen.generate_captions = MagicMock(return_value=["mock_item"])
            created = gen.convert_timeline_subtitles({"name": "Test"}, filter_in_out=True)
            self.assertEqual(len(created), 1)
            # Verify only the chunk corresponding to Inside range was passed to generate_captions
            cues_passed = gen.generate_captions.call_args[0][0]
            self.assertEqual(len(cues_passed), 1)
            self.assertIn("Inside range", cues_passed[0].text)

    def test_canvas_zoom_decoupled_from_font_size(self):
        from ui_qt.widgets.canvas_view import PhoneCanvasView
        canvas = PhoneCanvasView()
        orig_font_size = canvas.canvas_area.font_size
        self.assertEqual(canvas.current_zoom, 100)
        self.assertEqual(canvas.canvas_area.zoom_factor, 1.0)

        # Zoom in +20%
        canvas._adjust_zoom(20)
        self.assertEqual(canvas.current_zoom, 120)
        self.assertAlmostEqual(canvas.canvas_area.zoom_factor, 1.2, places=2)
        # Font size on the title must remain unmodified
        self.assertEqual(canvas.canvas_area.font_size, orig_font_size)

        # Zoom out -40%
        canvas._adjust_zoom(-40)
        self.assertEqual(canvas.current_zoom, 80)
        self.assertAlmostEqual(canvas.canvas_area.zoom_factor, 0.8, places=2)
        self.assertEqual(canvas.canvas_area.font_size, orig_font_size)

    def test_contraction_preservation_and_smart_punctuation(self):
        from core.subtitle_parser import SubtitleParser
        # Internal contractions like don't, it's, we're, can't must be preserved
        raw = "\"Don't stop, it's unbelievable! We're live, can't you see?\""
        cleaned = SubtitleParser.clean_punctuation(raw, preserve_contractions=True)
        self.assertEqual(cleaned, "Don't stop it's unbelievable We're live can't you see")

        # Strip mode
        stripped = SubtitleParser.clean_punctuation(raw, preserve_contractions=False)
        self.assertNotIn("'", stripped)

    def test_case_formatting_modes(self):
        from core.subtitle_parser import SubtitleParser
        text = "don't stop believing"
        self.assertEqual(SubtitleParser.format_case(text, "upper"), "DON'T STOP BELIEVING")
        self.assertEqual(SubtitleParser.format_case(text, "title"), "Don't Stop Believing")
        self.assertEqual(SubtitleParser.format_case(text, "sentence"), "Don't stop believing")
        self.assertEqual(SubtitleParser.format_case(text, "as_is"), "don't stop believing")

    def test_one_word_rapid_viral_punch_chunking(self):
        from core.subtitle_parser import SubtitleParser, SubtitleCue
        cues = [SubtitleCue(0, 90, "You need to see this right now")]
        # 1-word punch mode
        chunks = SubtitleParser.chunk_cues(cues, words_per_slide=1, case_mode="upper")
        self.assertEqual(len(chunks), 7)
        self.assertEqual(chunks[0].text, "YOU")
        self.assertEqual(chunks[1].text, "NEED")
        self.assertEqual(chunks[6].text, "NOW")
        self.assertEqual(chunks[0].start_frame, 0)
        self.assertEqual(chunks[-1].end_frame, 90)
        # Ensure continuity: start of next is end of prev
        for i in range(len(chunks) - 1):
            self.assertEqual(chunks[i].end_frame, chunks[i + 1].start_frame)

    def test_whisper_word_timestamp_parser(self):
        import tempfile, json, os
        from core.subtitle_parser import SubtitleParser
        data = {
            "text": "Hello world this is test",
            "words": [
                {"word": "Hello", "start": 0.0, "end": 0.4},
                {"word": "world", "start": 0.4, "end": 0.9},
                {"word": "this", "start": 1.0, "end": 1.3},
                {"word": "is", "start": 1.3, "end": 1.5},
                {"word": "test", "start": 1.5, "end": 2.0}
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fp:
            json.dump(data, fp)
            temp_path = fp.name

        try:
            parsed = SubtitleParser.parse_whisper_json(temp_path, fps=30.0)
            self.assertEqual(len(parsed), 5)
            self.assertEqual(parsed[0].text, "Hello")
            self.assertEqual(parsed[0].start_frame, 0)
            self.assertEqual(parsed[0].end_frame, 12)  # 0.4 * 30 = 12
            self.assertEqual(parsed[1].text, "world")
            self.assertEqual(parsed[1].start_frame, 12)
            self.assertEqual(parsed[1].end_frame, 27)  # 0.9 * 30 = 27
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_target_selection_playhead_vs_selected_isolation(self):
        bridge = ResolveBridge()
        tl = MagicMock()
        bridge.get_current_timeline = MagicMock(return_value=tl)
        bridge.get_playhead_frame = MagicMock(return_value=120)
        bridge.is_text_plus_item = MagicMock(return_value=True)

        # Clip A: at frame 100-200 (contains playhead 120), NOT selected
        clip_playhead = MagicMock()
        clip_playhead.GetStart.return_value = 100
        clip_playhead.GetEnd.return_value = 200
        clip_playhead.GetName.return_value = "Playhead Title"
        clip_playhead.GetFusionCompCount.return_value = 1

        # Clip B: at frame 300-400 (far from playhead), SELECTED
        clip_selected = MagicMock()
        clip_selected.GetStart.return_value = 300
        clip_selected.GetEnd.return_value = 400
        clip_selected.GetName.return_value = "Selected Title"
        clip_selected.GetFusionCompCount.return_value = 1

        tl.GetTrackCount.return_value = 1
        tl.GetItemListInTrack.return_value = [clip_playhead, clip_selected]
        bridge.get_selected_video_items = MagicMock(return_value=[clip_selected])

        # In playhead mode: MUST return clip_playhead ONLY, never clip_selected!
        playhead_targets = bridge.get_target_clips(mode="playhead")
        self.assertEqual(playhead_targets, [clip_playhead])

        # In selected mode: MUST return clip_selected ONLY
        selected_targets = bridge.get_target_clips(mode="selected")
        self.assertEqual(selected_targets, [clip_selected])

    def test_modify_snapshot_undo_and_redo(self):
        bridge = ResolveBridge()
        item = MagicMock()
        prev_style = {"text": "Original Title", "font": "Arial", "size": 0.05}
        new_style = {"text": "Updated Title", "font": "Helvetica", "size": 0.08}

        records = [{"item": item, "prev_style": prev_style, "new_style": new_style}]
        bridge.push_modify_snapshot(records, "Apply Bold Preset")

        self.assertTrue(bridge.can_undo())
        self.assertFalse(bridge.can_redo())

        # Test Undo
        with patch("core.text_plus_builder.TextPlusBuilder.apply_style") as mock_apply:
            ok, msg = bridge.undo_last_batch()
            self.assertTrue(ok)
            self.assertIn("restored previous style", msg)
            mock_apply.assert_called_once_with(item, prev_style, text_override="Original Title")

        self.assertFalse(bridge.can_undo())
        self.assertTrue(bridge.can_redo())

        # Test Redo
        with patch("core.text_plus_builder.TextPlusBuilder.apply_style") as mock_apply:
            ok, msg = bridge.redo_last_batch()
            self.assertTrue(ok)
            self.assertIn("reapplied style", msg)
            mock_apply.assert_called_once_with(item, new_style, text_override="Updated Title")

        self.assertTrue(bridge.can_undo())
        self.assertFalse(bridge.can_redo())

    def test_convert_drawer_default_look_and_scope(self):
        from ui_qt.widgets.convert_drawer import ConvertCaptionsDrawer
        drawer = ConvertCaptionsDrawer()
        drawer.populate_styles(["Viral Bold", "Clean Subtitle"])

        # Index 0 must be the default look placeholder
        self.assertEqual(drawer.combo_style.itemText(0), "Look from style... (Default Look)")
        self.assertEqual(drawer.combo_style.itemText(1), "Viral Bold")
        self.assertEqual(drawer.combo_style.itemText(2), "Clean Subtitle")

        # By default, style selected is None
        self.assertIsNone(drawer.get_selected_style_name())

        # Select a real style
        drawer.combo_style.setCurrentIndex(1)
        self.assertEqual(drawer.get_selected_style_name(), "Viral Bold")

        # By default, In/Out range is checked for safety
        self.assertTrue(drawer.chk_inout.isChecked())
        self.assertEqual(drawer.btn_convert.text(), "Convert Marked In/Out")

        # When unchecked, converts entire track
        drawer.chk_inout.setChecked(False)
        self.assertEqual(drawer.btn_convert.text(), "Convert Entire Track")

    def test_glitch_zoom_and_bounce_pop_motion_presets(self):
        engine = AnimationEngine()
        timeline_item = MagicMock()
        timeline_item.GetFusionCompCount.return_value = 1
        comp = MagicMock()
        timeline_item.GetFusionCompByIndex.return_value = comp

        class MockExpr:
            def __init__(self):
                self.expr = None
            def SetExpression(self, val):
                self.expr = val
            def ConnectTo(self, target):
                pass

        class MockTool:
            def __init__(self, name):
                self.name = name
                self.Center = MockExpr()
                self.Size = MockExpr()
                self.Angle = MockExpr()
                self.Blend = MockExpr()
                self.Length = MockExpr()
                self.Alpha1 = MockExpr()
                self.Input = MockExpr()
                self.Output = MockExpr()
                self.EffectMask = MockExpr()
                self.Mask = MockExpr()
                self.attrs = {"TOOLS_RegID": "Transform"}

            def GetAttrs(self):
                return self.attrs

            def SetAttrs(self, attrs):
                self.attrs.update(attrs)

            def SetInput(self, name, val):
                pass

            def FindTool(self, n):
                return self

        tools = {
            "MR_Transform": MockTool("MR_Transform"),
            "MR_Blur": MockTool("MR_Blur"),
            "Template": MockTool("Template"),
            "MediaOut1": MockTool("MediaOut1")
        }
        comp.FindTool.side_effect = lambda n: tools.get(n)
        comp.AddTool.side_effect = lambda t, *a: MockTool(t)

        # Test glitch_zoom
        ok1 = engine.apply_motion_preset(timeline_item, effect_in="glitch_zoom", effect_out="slide_down")
        self.assertTrue(ok1)
        self.assertIsNotNone(tools["MR_Transform"].Size.expr)
        self.assertIn("0.45", tools["MR_Transform"].Size.expr)
        self.assertIsNotNone(tools["MR_Transform"].Center.expr)
        self.assertIn("0.025", tools["MR_Transform"].Center.expr)
        self.assertIsNotNone(tools["MR_Transform"].Angle.expr)
        self.assertIn("2.50", tools["MR_Transform"].Angle.expr)

        # Test bounce_pop
        ok2 = engine.apply_motion_preset(timeline_item, effect_in="bounce_pop", effect_out="slide_down")
        self.assertTrue(ok2)
        self.assertIsNotNone(tools["MR_Transform"].Size.expr)
        self.assertIn("1.0", tools["MR_Transform"].Size.expr)
        self.assertIn("0.08", tools["MR_Transform"].Center.expr)

    def test_template_exit_clamped_to_short_clip_length(self):
        from core.templates.fusion_compiler import FusionCompiler
        # 18-frame short caption clip at 24fps
        t_info = FusionCompiler.calculate_clip_timing(
            clip_frames=18,
            template_duration_default=3.0,
            in_dur_sec=0.5,
            out_dur_sec=0.35,
            fps=24.0,
            speed=1.0
        )
        # Total frames must strictly be 18 - 1 = 17
        self.assertEqual(t_info["total_frames"], 17)
        # in_frames and out_frames must scale to at most total_frames // 3 = 5
        self.assertLessEqual(t_info["in_frames"], 5)
        self.assertLessEqual(t_info["out_frames"], 5)
        # Exit keyframes MUST complete at or before total_frames (17), never exceed!
        self.assertEqual(t_info["hold_end_frame"] + t_info["out_frames"], 17)

    def test_line_spacing_normalization_ui_and_text_plus(self):
        from ui_qt.tabs.titles_tab import TitlesTab
        from core.templates.fusion_compiler import FusionCompiler, LayerSpec

        # 1. UI SpinBox mapping
        mock_bridge = MagicMock()
        mock_bridge.resolve = None
        mock_bridge.get_current_timeline.return_value = None
        tab = TitlesTab(bridge=mock_bridge, builder=MagicMock(), animator=MagicMock())

        # Loading preset with TextPlus offset 0.0 should display 1.00 in UI
        tab.select_preset({"id": "test_norm", "name": "Test Norm", "line_spacing": 0.0})
        self.assertAlmostEqual(tab.spin_line_spacing.value(), 1.00, places=2)

        # Loading preset with positive offset 0.25 should display 1.25 in UI
        tab.select_preset({"id": "test_spaced", "name": "Test Spaced", "line_spacing": 0.25})
        self.assertAlmostEqual(tab.spin_line_spacing.value(), 1.25, places=2)

        # 2. Template Compiler line spacing mapping
        compiler = FusionCompiler(bridge=mock_bridge)
        self.assertEqual(compiler._layer_line_spacing(None), 0.0)
        self.assertEqual(compiler._layer_line_spacing(LayerSpec(id="t0", type="text", name="T0", props={})), 0.0)
        self.assertEqual(compiler._layer_line_spacing(LayerSpec(id="t0", type="text", name="T0", props={"line_spacing": 1.0})), 0.0)
        self.assertAlmostEqual(compiler._layer_line_spacing(LayerSpec(id="t0", type="text", name="T0", props={"line_spacing": 1.25})), 0.25, places=2)

    def test_extract_style_with_hero_text_attributes(self):
        from core.text_plus_builder import TextPlusBuilder

        mock_bridge = MagicMock()
        builder = TextPlusBuilder(mock_bridge)

        item = MagicMock()
        item.GetFusionCompCount.return_value = 1
        comp = MagicMock()
        item.GetFusionCompByIndex.return_value = comp

        class MockToolWithInputs:
            def __init__(self, inputs):
                self.inputs = inputs

            def GetInput(self, name):
                return self.inputs.get(name)

        base_tool = MockToolWithInputs({
            "StyledText": "BEAT\nDROP",
            "Font": "Inter",
            "Style": "Bold",
            "Size": 0.08,
            "Red1": 1.0, "Green1": 1.0, "Blue1": 1.0, "Alpha1": 1.0,
            "LineSpacingClone": 0.0,
            "CharacterSpacingClone": 1.0
        })

        hero_tool = MockToolWithInputs({
            "StyledText": " \nDROP",
            "Font": "Cinzel",
            "Style": "Black",
            "Size": 0.12,
            "Red1": 1.0, "Green1": 0.85, "Blue1": 0.0, "Alpha1": 1.0,
            "Enabled2": 1.0,
            "Thickness2": 0.045,
            "Red2": 0.1, "Green2": 0.1, "Blue2": 0.1, "Alpha2": 1.0,
            "Enabled3": 1.0,
            "Softness3": 0.035,
            "Offset3": {"1": 0.008, "2": -0.008},
            "Red3": 0.0, "Green3": 0.0, "Blue3": 0.0, "Alpha3": 0.9
        })

        def find_tool(name):
            if name in ("Template", "TextPlus"):
                return base_tool
            if name == "HeroText":
                return hero_tool
            return None

        comp.FindTool.side_effect = find_tool

        extracted = builder.extract_style_from_clip(item)
        self.assertIsNotNone(extracted)
        self.assertTrue(extracted.get("use_2color"))
        self.assertEqual(extracted.get("main_word"), "DROP")
        self.assertEqual(extracted.get("hero_font"), "Cinzel")
        self.assertEqual(extracted.get("hero_style"), "Black")
        self.assertAlmostEqual(extracted.get("hero_size_multiplier"), 1.5, places=2)
        self.assertTrue(extracted.get("hero_stroke_enabled"))
        self.assertAlmostEqual(extracted.get("hero_stroke_thickness"), 0.045, places=3)
        self.assertTrue(extracted.get("hero_shadow_enabled"))
        self.assertAlmostEqual(extracted.get("hero_shadow_softness"), 0.035, places=3)
        self.assertEqual(extracted.get("hero_shadow_offset"), [0.008, -0.008])

    def test_writable_user_storage_fallback_and_dual_loading(self):
        import tempfile
        import shutil
        from core.paths import get_user_presets_dir
        from core.style_manager import StyleManager

        # Test fallback when primary is read-only
        with patch("os.access", return_value=False):
            fb_dir = get_user_presets_dir()
            self.assertIn(".motion_resolve", fb_dir)

        # Test StyleManager dual loading
        tmp_builtin = tempfile.mkdtemp(prefix="mr_builtin_")
        tmp_user = tempfile.mkdtemp(prefix="mr_user_")
        try:
            # Built-in preset
            with open(os.path.join(tmp_builtin, "p_builtin.json"), "w", encoding="utf-8") as f:
                json.dump({"id": "p_builtin", "name": "Built-in Preset"}, f)

            # User custom preset
            with open(os.path.join(tmp_user, "p_custom.json"), "w", encoding="utf-8") as f:
                json.dump({"id": "p_custom", "name": "User Custom Preset"}, f)

            mgr = StyleManager(presets_dir=tmp_user)
            mgr.builtin_dir = tmp_builtin

            presets = mgr.get_presets()
            ids = [p["id"] for p in presets]
            self.assertIn("p_builtin", ids)
            self.assertIn("p_custom", ids)
        finally:
            shutil.rmtree(tmp_builtin, ignore_errors=True)
            shutil.rmtree(tmp_user, ignore_errors=True)

    def test_style_manager_get_all_presets_alias(self):
        from core.style_manager import StyleManager
        sm = StyleManager()
        presets = sm.get_presets()
        all_presets = sm.get_all_presets()
        self.assertEqual(len(presets), len(all_presets))
        self.assertEqual([p["id"] for p in presets], [p["id"] for p in all_presets])

    def test_workspace_tab_quick_actions_and_motion_push_undo_snapshots(self):
        from ui_qt.tabs.workspace_tab import WorkspaceTab
        from core.resolve_api import ResolveBridge
        from core.text_plus_builder import TextPlusBuilder
        from core.animation_engine import AnimationEngine

        bridge = ResolveBridge()
        bridge.push_modify_snapshot = MagicMock()
        bridge.push_fusion_snapshot = MagicMock()
        bridge.capture_fusion_comp_snapshot = MagicMock(return_value={"path": "/tmp/dummy_comp.setting"})

        mock_item = MagicMock()
        mock_item.GetFusionCompCount.return_value = 1
        bridge.get_target_clips = MagicMock(return_value=[mock_item])

        builder = TextPlusBuilder(bridge)
        animator = AnimationEngine()

        tab = WorkspaceTab(bridge, builder, animator)

        # 1. Test align_center pushes modify snapshot
        tab._on_canvas_action("align_center")
        bridge.push_modify_snapshot.assert_called()
        self.assertEqual(bridge.push_modify_snapshot.call_args[0][1], "Align Center")

        # 2. Test scale pushes modify snapshot
        bridge.push_modify_snapshot.reset_mock()
        tab._on_canvas_action("scale")
        bridge.push_modify_snapshot.assert_called()
        self.assertEqual(bridge.push_modify_snapshot.call_args[0][1], "Scale Title Size")

        # 3. Test motion preset pushes fusion snapshot
        tab.animator.apply_motion_preset = MagicMock(return_value=True)
        tab._on_motion_changed({"in": "pop_in", "out": "slide_down"})
        bridge.push_fusion_snapshot.assert_called()
        self.assertIn("Apply Motion (pop_in / slide_down)", bridge.push_fusion_snapshot.call_args[0][1])

        # 4. Test auto motion pushes fusion snapshot
        bridge.push_fusion_snapshot.reset_mock()
        tab._on_auto_motion_clicked()
        bridge.push_fusion_snapshot.assert_called()
        self.assertIn("Apply AUTO continuity", bridge.push_fusion_snapshot.call_args[0][1])

    def test_resolve_bridge_get_active_caption_metadata_generic_textplus(self):
        bridge = ResolveBridge()
        mock_tl = MagicMock()
        mock_tl.GetCurrentTimecode.return_value = "01:00:05:00"
        mock_tl.GetStartTimecode.return_value = "01:00:00:00"
        mock_tl.GetTrackCount.return_value = 1
        mock_tl.GetSelectedClips.return_value = []

        mock_item = MagicMock()
        mock_item.GetStart.return_value = 100
        mock_item.GetEnd.return_value = 200
        mock_item.GetFusionCompCount.return_value = 1

        mock_comp = MagicMock()
        # Does NOT find "Template", but tool list contains a TextPlus tool
        mock_comp.FindTool.return_value = None
        mock_tool = MagicMock()
        mock_tool.GetAttrs.return_value = {"TOOLS_RegID": "TextPlus"}
        mock_tool.GetInput.side_effect = lambda param: {
            "StyledText": "TEST TITLE",
            "Font": "Avenir Next",
            "Size": 0.09,
            "Center": [0.5, 0.3],
            "Red1": 1.0, "Green1": 0.9, "Blue1": 0.2, "Alpha1": 1.0,
            "Enabled4": 0
        }.get(param, None)
        mock_comp.GetToolList.return_value = {"CustomText1": mock_tool}
        mock_item.GetFusionCompByIndex.return_value = mock_comp

        mock_tl.GetItemListInTrack.return_value = [mock_item]
        bridge.get_current_timeline = MagicMock(return_value=mock_tl)
        bridge.get_timeline_fps = MagicMock(return_value=30.0)

        meta = bridge.get_active_caption_metadata()
        self.assertIsNotNone(meta)
        self.assertEqual(meta["text"], "TEST TITLE")
        self.assertEqual(meta["font"], "Avenir Next")
        self.assertAlmostEqual(meta["size"], 0.09)


if __name__ == "__main__":
    unittest.main()
