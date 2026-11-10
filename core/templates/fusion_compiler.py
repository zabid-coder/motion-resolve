"""
Motion Resolve - Typography Template Engine: Fusion Compiler

Compiles a declarative TemplateSpec into a native DaVinci Resolve Fusion
composition on a Text+ / Fusion Title timeline item.

Node graph (one branch per layer, all fully editable in Fusion):

    MR_Base (transparent) ─┐
    Shape:  MR_Shape_<id> ─(MR_Mask_<id>)──────────────┐
    Text:   Template / MR_Text_<id> → [MR_Blur_<id>] → MR_XF_<id> ─┐
                                    each layer → MR_Merge_<id> (Blend = layer opacity)
                                                   … → MR_TemplateOut → MediaOut1

Every animated input is driven by a real Fusion BezierSpline / XYPath with
cubic-bezier handles taken from the template's easing tokens. (Calling
SetInput(name, value, time) without a spline only overwrites a static value in
Resolve - that was why earlier versions never animated per layer.)
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple

from core.templates.schema import TemplateSpec, LayerType, LayerSpec, KeyframeSpec  # noqa: F401 (re-exported)
from core.templates.theme_tokens import get_theme, normalize_color
from core.templates.motion_tokens import seconds_to_frame
from core.templates.motion_curves import (
    plan_timing, layer_channel_plan, fusion_keyframes, evaluate_keys,
)
from core.templates.scene import resolve_scene, resolve_params, resolve_value, _line_spacing, SceneLayer

TOOL_PREFIX = "MR_"


def _font_resolver(requested: str, purpose: str) -> str:
    try:
        from core.font_catalog import infer_font_purpose, resolve_available_font
        resolved_purpose = purpose if purpose == "bengali" else infer_font_purpose(requested, purpose)
        return resolve_available_font(requested, resolved_purpose)
    except Exception:
        return requested


def _font_style(weight: str, family: str) -> str:
    try:
        from core.font_catalog import resolve_font_style
        return resolve_font_style(weight, family)
    except Exception:
        from core.font_catalog import normalize_font_style
        return normalize_font_style(weight, family)


class FusionCompiler:
    """Compiles declarative template specs into DaVinci Resolve multi-layer Fusion nodes."""

    def __init__(self, bridge, animator=None):
        self.bridge = bridge
        self.animator = animator
        self.last_report: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Timing helpers
    # ------------------------------------------------------------------
    @staticmethod
    def calculate_clip_timing(clip_frames, template_duration_default, in_dur_sec, out_dur_sec, fps, speed):
        """Frame-bounded Entrance / Hold / Exit summary fitting strictly inside the clip."""
        fps = max(1.0, float(fps))
        speed = max(0.1, float(speed))
        raw_total = int(clip_frames) if (clip_frames and clip_frames > 3) else seconds_to_frame(template_duration_default, fps)
        total_frames = max(3, raw_total - 1)
        in_frames = max(2, seconds_to_frame(max(0.15, in_dur_sec / speed), fps))
        out_frames = max(2, seconds_to_frame(max(0.10, out_dur_sec / speed), fps))
        max_span = max(1, total_frames // 3)
        in_frames = min(in_frames, max_span)
        out_frames = min(out_frames, max_span)
        hold_end_frame = max(in_frames, total_frames - out_frames)
        return {
            "fps": fps, "speed": speed, "in_frames": in_frames, "out_frames": out_frames,
            "hold_end_frame": hold_end_frame, "total_frames": total_frames,
        }

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def compile_and_apply(
        self,
        timeline_item,
        template: TemplateSpec,
        param_overrides: Optional[Dict[str, Any]] = None,
        theme_id: str = "mono",
        speed: float = 1.0,
        intensity: float = 1.0,
    ) -> bool:
        if not timeline_item or not template:
            return False
        try:
            if timeline_item.GetFusionCompCount() == 0:
                return False
        except Exception:
            return False
        comp = timeline_item.GetFusionCompByIndex(1)
        if not comp:
            return False

        theme = get_theme(theme_id)
        params = resolve_params(template, param_overrides or {})
        fps = 24.0
        frame_w, frame_h = 1920, 1080
        if self.bridge:
            try:
                fps = float(self.bridge.get_timeline_fps() or 24.0)
            except Exception:
                pass
            try:
                frame_w, frame_h = self.bridge.get_timeline_resolution()
            except Exception:
                pass

        render_start, last_frame = self._comp_range(comp, timeline_item, template, fps)
        timing = plan_timing(template, last_frame, fps, speed)
        scene, fit = resolve_scene(template, params, theme, frame_w, frame_h, font_resolver=_font_resolver)

        locked = False
        try:
            if hasattr(comp, "Lock"):
                comp.Lock(); locked = True
            if hasattr(comp, "StartUndo"):
                comp.StartUndo("Motion Resolve: " + str(template.name))
            self._cleanup_previous_tools(comp)
            head = self._build_graph(comp, scene, template, timing, render_start, intensity, fit)
            out = comp.FindTool("MediaOut1") or self._find_by_regid(comp, "MediaOut")
            if out is not None and head is not None:
                out.Input.ConnectTo(head)
        finally:
            if hasattr(comp, "EndUndo"):
                try:
                    comp.EndUndo(True)
                except Exception:
                    pass
            if locked:
                comp.Unlock()

        self.last_report = {
            "template": template.id, "layers": len(scene), "fps": fps,
            "render_start": render_start, "last_frame": last_frame,
            "frame": (frame_w, frame_h), "scale": fit.scale,
        }
        if self.animator:
            try:
                self.animator.register_template_motion(template)
            except Exception:
                pass
        return True

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------
    @staticmethod
    def _comp_range(comp, item, template, fps) -> Tuple[int, int]:
        rs, re = 0, None
        try:
            attrs = comp.GetAttrs() if hasattr(comp, "GetAttrs") else {}
            if isinstance(attrs, dict):
                rs = int(attrs.get("COMPN_RenderStart", 0) or 0)
                if attrs.get("COMPN_RenderEnd") is not None:
                    re = int(attrs.get("COMPN_RenderEnd"))
        except Exception:
            pass
        last = (re - rs) if (re is not None and re > rs) else None
        if not last:
            try:
                dur = item.GetDuration()
                if isinstance(dur, (int, float)) and dur > 3:
                    last = int(round(dur)) - 1
            except Exception:
                last = None
        if not last:
            last = seconds_to_frame(template.duration_default, fps) - 1
        return rs, max(4, int(last))

    @staticmethod
    def _find_by_regid(comp, regid):
        try:
            for t in (comp.GetToolList(False) or {}).values():
                if t.GetAttrs().get("TOOLS_RegID") == regid:
                    return t
        except Exception:
            pass
        return None

    def _cleanup_previous_tools(self, comp):
        """Remove every tool generated by a previous compile (including legacy names)."""
        doomed = []
        try:
            tool_list = comp.GetToolList(False) if hasattr(comp, "GetToolList") else {}
        except TypeError:
            tool_list = comp.GetToolList()
        tools = tool_list.values() if isinstance(tool_list, dict) else (tool_list or [])
        for t in tools:
            try:
                name = t.GetAttrs().get("TOOLS_Name", "")
            except Exception:
                name = ""
            if not isinstance(name, str) or not name:
                name = getattr(t, "Name", "")
            name = name if isinstance(name, str) else ""
            if name.startswith(TOOL_PREFIX) or name in ("Template", "HeroText"):
                doomed.append(t)
        for t in doomed:
            try:
                t.Delete()
            except Exception:
                pass

    @staticmethod
    def _add(comp, regid, name, x=0, y=0):
        tool = comp.AddTool(regid, x, y)
        if tool is not None and hasattr(tool, "SetAttrs"):
            tool.SetAttrs({"TOOLS_Name": name})
        return tool

    def _build_graph(self, comp, scene: List[SceneLayer], template, timing, rs, intensity, fit):
        self._timing = timing
        self._first_follower = None
        base = self._add(comp, "Background", "MR_Base", -2, 0)
        base.SetInput("UseFrameFormatSettings", 1)
        for ch in ("TopLeftRed", "TopLeftGreen", "TopLeftBlue", "TopLeftAlpha"):
            base.SetInput(ch, 0.0)
        current = base.Output

        # plates at the back, then authored order
        ordered = sorted(scene, key=lambda l: (0 if l.is_plate else 1, l.index))
        primary_done = False
        col = 0
        for sl in ordered:
            if sl.kind == "shape" and sl.text_box:
                continue  # drawn by its text layer's Text+ background (element 4)
            col += 1
            plan = layer_channel_plan(sl.spec, timing, intensity)
            if sl.kind == "text":
                # Resolve rewrites a title's "Template" tool text when it reloads the
                # comp, which bypasses a Follower: per-letter layers therefore never
                # take that name (verified in Resolve 21).
                staggered = bool(sl.stagger) and not getattr(sl, "count", False)
                if not primary_done and not staggered:
                    name = "Template"
                    primary_done = True
                else:
                    name = f"MR_Text_{sl.id}"
                src = self._build_text(comp, sl, name, plan, rs, fit, col)
            else:
                src = self._build_shape(comp, sl, plan, rs, fit, col)
            if src is None:
                continue
            merge = self._add(comp, "Merge", f"MR_Merge_{sl.id}", col, 3)
            merge.Background.ConnectTo(current)
            merge.Foreground.ConnectTo(src)
            if sl.kind == "text" and sl.stagger and not sl.count:
                merge.SetInput("Blend", 1.0)   # opacity lives on each character
            else:
                self._animate_scalar(merge, "Blend", plan.get("opacity"), rs, 1.0)
            if sl.clip:
                clip = self._add(comp, "RectangleMask", f"MR_Clip_{sl.id}", col, 4)
                # A reveal mask only needs to limit VERTICAL travel: keep it far wider
                # than any text so long / Bengali lines are never cut horizontally.
                h = sl.line_h * 1.18 if sl.kind == "text" else sl.height * 1.02
                w = 4.0 if sl.kind == "text" else sl.width * 1.02
                clip.SetInput("Center", [float(sl.cx), float(sl.cy)])
                clip.SetInput("Width", float(w))
                clip.SetInput("Height", float(h))
                clip.SetInput("SoftEdge", 0.0)
                merge.EffectMask.ConnectTo(clip.Mask)
            current = merge.Output

        if not primary_done and self._first_follower is not None:
            # Every text layer cascades per letter: keep a hidden "Template" Text+
            # as the title's editable text source (Resolve's Inspector and the app
            # edit it) and drive the visible Follower's text from it.
            fol, text = self._first_follower
            src = self._add(comp, "TextPlus", "Template", -2, -2)
            src.SetInput("StyledText", text)
            try:
                fol.Text.SetExpression("Template.StyledText")
            except Exception as exc:
                print(f"[Motion Resolve] Could not link title text: {exc}")

        out = self._add(comp, "Transform", "MR_TemplateOut", col + 1, 3)
        out.Input.ConnectTo(current)
        return out.Output

    # ------------------------------------------------------------------
    def _build_text(self, comp, sl: SceneLayer, name, plan, rs, fit, col):
        tp = self._add(comp, "TextPlus", name, col, 0)
        tp.SetInput("StyledText", sl.text)
        tp.SetInput("Font", sl.font)
        tp.SetInput("Style", _font_style(sl.style, sl.font))
        tp.SetInput("Size", float(sl.size))
        tp.SetInput("CharacterSpacingClone", float(sl.tracking))
        tp.SetInput("LineSpacingClone", float(sl.line_spacing))
        tp.SetInput("HorizontalLeftCenterRight", float(sl.align))
        # HorizontalJustificationNew is left at its default (3 = follow anchor);
        # measured in Resolve 21: explicit 0/1/2 values do not change layout.
        tp.SetInput("VerticalTopCenterBottom", 0.0)
        tp.SetInput("Center", [float(sl.cx), float(sl.cy)])
        self._element_color(tp, 1, sl.color)

        # Outline (element 2)
        if sl.stroke:
            c = sl.stroke["color"]
            tp.SetInput("Enabled2", 1)
            self._element_color(tp, 2, c)
            tp.SetInput("Thickness2", float(sl.stroke.get("width", 0.04)))
        else:
            tp.SetInput("Enabled2", 0)

        # Soft drop shadow (element 3) - authored or a subtle premium default
        sh = sl.shadow or {}
        if sh.get("enabled", True) and not sh.get("off", False):
            col_s = normalize_color(sh.get("color", [0.0, 0.0, 0.0, 1.0]))
            tp.SetInput("Enabled3", 1)
            self._element_color(tp, 3, [col_s[0], col_s[1], col_s[2], float(sh.get("opacity", 0.38))])
            soft = float(sh.get("softness", 0.025))
            tp.SetInput("Softness3", soft); tp.SetInput("SoftnessX3", soft); tp.SetInput("SoftnessY3", soft)
            off = sh.get("offset", [0.0, -0.004])
            tp.SetInput("Offset3", [float(off[0]), float(off[1])])
        else:
            tp.SetInput("Enabled3", 0)

        # Fitted background box (element 4) for keyword boxes / pills
        if sl.text_box and "color" in sl.text_box:
            c = sl.text_box["color"]
            tp.SetInput("Enabled4", 1)
            self._element_color(tp, 4, c)
            tp.SetInput("ExtendHorizontal4", float(sl.text_box.get("pad_x", 0.35)))
            tp.SetInput("ExtendVertical4", float(sl.text_box.get("pad_y", 0.12)))
            tp.SetInput("Round4", float(sl.text_box.get("round", 0.35)))
            tp.SetInput("Level4", 1)
        else:
            tp.SetInput("Enabled4", 0)

        # Count-up: the number in the text counts from 0 (expression on StyledText,
        # verified in Resolve 21: prefixes, separators, decimals, Bengali digits).
        if getattr(sl, "count", False):
            from core.templates.counter import parse_count, count_window, lua_count_expression
            spec = parse_count(sl.text)
            if spec is not None:
                c0, c1 = count_window(plan, getattr(self, "_timing", {}), sl.count_seconds)
                try:
                    tp.StyledText.SetExpression(lua_count_expression(spec, rs + c0, rs + c1))
                except Exception as exc:
                    print(f"[Motion Resolve] Count-up unavailable: {exc}")

        # Per-character cascade: the layer's motion plays on every character with
        # a delay (Text+ Follower, verified in Resolve 21). Counters keep their
        # own text expression, so they never use the Follower.
        if sl.stagger and not getattr(sl, "count", False):
            self._apply_follower(tp, sl, plan, rs, fit)
            plan = {k: v for k, v in plan.items() if k in ("tracking", "write_on")}

        # Text-native channels
        if plan.get("tracking"):
            self._animate_scalar(tp, "CharacterSpacingClone", plan["tracking"], rs, sl.tracking)
        if plan.get("write_on"):
            self._animate_scalar(tp, "End", plan["write_on"], rs, 1.0)

        head = tp.Output
        glow = float((sl.spec.props or {}).get("glow_blur", 0) or 0)   # static glow copy
        if plan.get("blur") or glow > 0:
            blur = self._add(comp, "Blur", f"MR_Blur_{sl.id}", col, 1)
            blur.Input.ConnectTo(head)
            if plan.get("blur"):
                self._animate_scalar(blur, "XBlurSize", self._map(plan["blur"], lambda v: v + glow), rs, glow)
            else:
                blur.SetInput("XBlurSize", glow)
            head = blur.Output

        xf = self._add(comp, "Transform", f"MR_XF_{sl.id}", col, 2)
        xf.Input.ConnectTo(head)
        xf.SetInput("Pivot", [float(sl.cx), float(sl.cy)])
        self._animate_point(
            xf, "Center",
            self._map(plan.get("translate_x"), lambda v: 0.5 + fit.dx(v)),
            self._map(plan.get("translate_y"), lambda v: 0.5 + fit.dy(v)),
            rs, (0.5, 0.5),
        )
        scale = plan.get("scale") or plan.get("scale_x") or plan.get("scale_y")
        self._animate_scalar(xf, "Size", scale, rs, 1.0)
        self._animate_scalar(xf, "Angle", plan.get("rotation"), rs, 0.0)
        return xf.Output

    def _apply_follower(self, tp, sl, plan, rs, fit):
        from core.templates.motion_curves import stagger_delay, stagger_plan
        timing = getattr(self, "_timing", {})
        delay = stagger_delay(sl.stagger, sl.text, timing)
        p = stagger_plan(plan, sl.text, delay, timing)
        try:
            tp.AddModifier("StyledText", "StyledTextFollower")
            fol = tp.StyledText.GetConnectedOutput().GetTool()
        except Exception as exc:
            print(f"[Motion Resolve] Follower unavailable: {exc}")
            return
        if self._first_follower is None:
            self._first_follower = (fol, sl.text)
        fol.SetInput("Range", 0)
        fol.SetInput("Order", float(sl.stagger.get("order", 0)))
        fol.SetInput("DelayType", 1)
        fol.SetInput("Delay", float(delay))
        op = p.get("opacity")
        self._animate_scalar(fol, "Opacity1", op, rs, 1.0)
        # shadow / outline / box fade with their character (no ghost shadows)
        sh = sl.shadow or {}
        if not sh.get("off", False) and sh.get("enabled", True):
            k = float(sh.get("opacity", 0.38))
            self._animate_scalar(fol, "Opacity3", self._map(op, lambda v: v * k), rs, k)
        if sl.stroke:
            self._animate_scalar(fol, "Opacity2", op, rs, float(sl.stroke["color"][3]))
        if plan.get("translate_x") or plan.get("translate_y"):
            # Follower point inputs need a PolyPath: an XYPath silently breaks the
            # Follower's per-character timing (exit never plays) - verified in Resolve 21.
            self._key_polypath(fol, "CharacterOffset",
                               self._map(p.get("translate_x"), lambda v: fit.dx(v)),
                               self._map(p.get("translate_y"), lambda v: fit.dy(v)), rs)
        scale = p.get("scale") or p.get("scale_y")
        if scale:
            self._animate_scalar(fol, "CharacterSizeX", p.get("scale_x") or scale, rs, 1.0)
            self._animate_scalar(fol, "CharacterSizeY", scale, rs, 1.0)
        if p.get("rotation"):
            self._animate_scalar(fol, "CharacterAngleZ", p["rotation"], rs, 0.0)
        if p.get("blur"):
            fol.SetInput("SoftnessOnFillColorToo1", 1)
            soft = self._map(p["blur"], lambda v: v * 0.9)
            self._animate_scalar(fol, "SoftnessX1", soft, rs, 0.0)
            self._animate_scalar(fol, "SoftnessY1", soft, rs, 0.0)

    @staticmethod
    def _key_polypath(tool, input_name, x_keys, y_keys, rs):
        """Key a point input through a PolyPath, sampled every frame across each
        moving span so the cubic-bezier easing is reproduced exactly."""
        frames = sorted({k[0] for k in (x_keys or [])} | {k[0] for k in (y_keys or [])})
        if not frames:
            return
        dense = set(frames) | {0.0}
        for f0, f1 in zip(frames, frames[1:]):
            vx0 = evaluate_keys(x_keys, f0, 0.0) if x_keys else 0.0
            vx1 = evaluate_keys(x_keys, f1, 0.0) if x_keys else 0.0
            vy0 = evaluate_keys(y_keys, f0, 0.0) if y_keys else 0.0
            vy1 = evaluate_keys(y_keys, f1, 0.0) if y_keys else 0.0
            if abs(vx1 - vx0) + abs(vy1 - vy0) > 1e-7:
                f = f0 + 1.0
                while f < f1:
                    dense.add(round(f, 3))
                    f += 1.0
        try:
            tool.AddModifier(input_name, "PolyPath")
        except Exception:
            pass
        for f in sorted(dense):
            x = evaluate_keys(x_keys, f, 0.0) if x_keys else 0.0
            y = evaluate_keys(y_keys, f, 0.0) if y_keys else 0.0
            tool.SetInput(input_name, [float(x), float(y)], rs + f)

    @staticmethod
    def _element_color(tool, idx, rgba):
        """Text+ element colours are not premultiplied; drive transparency via
        the element Opacity like the Inspector (verified in Resolve 21)."""
        c = (list(rgba) + [1.0] * 4)[:4]
        tool.SetInput(f"Red{idx}", float(c[0])); tool.SetInput(f"Green{idx}", float(c[1]))
        tool.SetInput(f"Blue{idx}", float(c[2])); tool.SetInput(f"Alpha{idx}", 1.0)
        tool.SetInput(f"Opacity{idx}", float(c[3]))

    # ------------------------------------------------------------------
    def _build_shape(self, comp, sl: SceneLayer, plan, rs, fit, col):
        fill = self._shape_branch(comp, sl, f"MR_Shape_{sl.id}", f"MR_Mask_{sl.id}", sl.color,
                                  sl.width, sl.height, plan, rs, fit, col, gradient=sl.gradient)
        if not sl.border:
            return fill
        # Border: a slightly larger rounded rect behind the fill, animated identically.
        px = float(sl.border["px"])
        bw = px / float(fit.width)
        bh = px / float(fit.height)
        border = self._shape_branch(comp, sl, f"MR_Border_{sl.id}", f"MR_BorderMask_{sl.id}", sl.border["color"],
                                    sl.width + 2 * bw, sl.height + 2 * bh, plan, rs, fit, col, row=-1)
        m = self._add(comp, "Merge", f"MR_Card_{sl.id}", col, 2)
        m.Background.ConnectTo(border)
        m.Foreground.ConnectTo(fill)
        return m.Output

    def _shape_branch(self, comp, sl, bg_name, mask_name, color, width, height, plan, rs, fit, col, gradient=None, row=0):
        bg = self._add(comp, "Background", bg_name, col, row - 2)
        bg.SetInput("UseFrameFormatSettings", 1)
        # Fusion's Background colour is NOT premultiplied, while Merge expects
        # premultiplied foregrounds: premultiply so translucent plates/borders
        # composite correctly (otherwise a 12% white border renders near-solid).
        def premul(cc):
            cc = (list(cc) + [1.0] * 4)[:4]
            return [cc[0] * cc[3], cc[1] * cc[3], cc[2] * cc[3], cc[3]]
        c = premul(color)
        if gradient:
            g0, g1 = premul(gradient[0]), premul(gradient[1])
            bg.SetInput("Type", 1)  # horizontal gradient
            for pre, cc in (("TopLeft", g0), ("TopRight", g1)):
                bg.SetInput(pre + "Red", cc[0]); bg.SetInput(pre + "Green", cc[1])
                bg.SetInput(pre + "Blue", cc[2]); bg.SetInput(pre + "Alpha", cc[3])
        else:
            bg.SetInput("TopLeftRed", c[0]); bg.SetInput("TopLeftGreen", c[1])
            bg.SetInput("TopLeftBlue", c[2]); bg.SetInput("TopLeftAlpha", c[3])
        mask = self._add(comp, "RectangleMask", mask_name, col, row - 1)
        mask.SetInput("CornerRadius", float(sl.corner))
        mask.SetInput("SoftEdge", 0.0006)

        sx_keys = plan.get("scale_x") or plan.get("scale")
        sy_keys = plan.get("scale_y") or plan.get("scale")
        self._animate_scalar(mask, "Width", self._map(sx_keys, lambda v: max(0.0, width * v)), rs, width)
        self._animate_scalar(mask, "Height", self._map(sy_keys, lambda v: max(0.0, height * v)), rs, height)

        # Centre: translation plus origin compensation for directional wipes.
        side_x = {"left": -1.0, "right": 1.0}.get(sl.origin, 0.0)
        side_y = {"bottom": -1.0, "top": 1.0}.get(sl.origin, 0.0)
        x_keys = self._compose(plan.get("translate_x"), sx_keys if side_x else None,
                               lambda dx, s: sl.cx + fit.dx(dx) + side_x * (1.0 - s) * width / 2.0)
        y_keys = self._compose(plan.get("translate_y"), sy_keys if side_y else None,
                               lambda dy, s: sl.cy + fit.dy(dy) + side_y * (1.0 - s) * height / 2.0)
        self._animate_point(mask, "Center", x_keys, y_keys, rs, (sl.cx, sl.cy))
        bg.EffectMask.ConnectTo(mask.Mask)
        return bg.Output

    # ------------------------------------------------------------------
    # Keyframe writers (real Fusion splines)
    # ------------------------------------------------------------------
    @staticmethod
    def _map(keys, fn):
        if not keys:
            return None
        return [(f, fn(v), e) for f, v, e in keys]

    @staticmethod
    def _compose(a_keys, b_keys, fn):
        """Combine two channels (translate + scale) into one: fn(a, b) on the union of frames."""
        if not a_keys and not b_keys:
            return None
        if a_keys and not b_keys:
            return [(f, fn(v, 1.0), e) for f, v, e in a_keys]
        if b_keys and not a_keys:
            return [(f, fn(0.0, v), e) for f, v, e in b_keys]
        frames = sorted({k[0] for k in a_keys} | {k[0] for k in b_keys})
        dense = []
        for f0, f1 in zip(frames, frames[1:] + [None]):
            dense.append(f0)
            if f1 is not None:
                f = f0 + 1.0
                while f < f1:
                    dense.append(f)
                    f += 1.0
        return [(f, fn(evaluate_keys(a_keys, f, 0.0), evaluate_keys(b_keys, f, 1.0)), "linear") for f in dense]

    @staticmethod
    def _is_animated(keys) -> bool:
        return bool(keys) and len(keys) > 1 and any(abs(k[1] - keys[0][1]) > 1e-7 for k in keys)

    def _spline_for(self, tool, input_name, modifier="BezierSpline"):
        try:
            tool.AddModifier(input_name, modifier)
            inp = getattr(tool, input_name)
            out = inp.GetConnectedOutput()
            return out.GetTool() if out else None
        except Exception as exc:
            print(f"[Motion Resolve] Could not animate {input_name}: {exc}")
            return None

    def _animate_scalar(self, tool, input_name, keys, rs, rest):
        if not self._is_animated(keys):
            value = keys[0][1] if keys else rest
            if keys or input_name not in ("Blend",):
                tool.SetInput(input_name, float(value))
            return
        spline = self._spline_for(tool, input_name)
        if spline is None:
            tool.SetInput(input_name, float(keys[-1][1]))
            return
        self._write_keys(spline, keys, rs)

    @staticmethod
    def _write_keys(spline, keys, rs):
        """Make the spline hold EXACTLY these keys.

        AddModifier seeds a key at the comp's current time and a Fusion spline
        never drops its last key, so: write our keys first, then delete every
        stray key that is not ours (verified in Resolve 21).
        """
        keys = list(keys)
        if keys and keys[0][0] > 0.0:
            keys.insert(0, (0.0, keys[0][1], "linear"))  # pins the seed key at comp start
        table = fusion_keyframes([(rs + f, v, e) for f, v, e in keys])
        spline.SetKeyFrames(table, True)
        try:
            existing = spline.GetKeyFrames() or {}
            ours = {round(float(t), 4) for t in table}
            for t in list(existing.keys()):
                if round(float(t), 4) not in ours:
                    spline.DeleteKeyFrames(float(t) - 0.001, float(t) + 0.001)
        except Exception:
            pass

    def _animate_point(self, tool, input_name, x_keys, y_keys, rs, rest):
        ax, ay = self._is_animated(x_keys), self._is_animated(y_keys)
        x_static = x_keys[0][1] if x_keys else rest[0]
        y_static = y_keys[0][1] if y_keys else rest[1]
        if not ax and not ay:
            tool.SetInput(input_name, [float(x_static), float(y_static)])
            return
        path = self._spline_for(tool, input_name, "XYPath")
        if path is None:
            tool.SetInput(input_name, [float(x_static), float(y_static)])
            return
        for axis, keys, animated, static in (("X", x_keys, ax, x_static), ("Y", y_keys, ay, y_static)):
            # XYPath connects splines to BOTH axes, so a static axis must also be
            # written as a key (a plain SetInput is ignored - verified in Resolve 21).
            spline = self._spline_for(path, axis)
            if spline is not None:
                self._write_keys(spline, keys if animated else [(0.0, float(static), "linear")], rs)
            else:
                path.SetInput(axis, float(static))

    # ------------------------------------------------------------------
    # Back-compat helpers (used by UI and tests)
    # ------------------------------------------------------------------
    def _resolve_parameters(self, template: TemplateSpec, overrides: Dict[str, Any]) -> Dict[str, Any]:
        return {p.id: overrides.get(p.id, p.default) for p in template.parameters}

    def _resolve_value(self, val: Any, params: Dict[str, Any], theme: Dict[str, Any]) -> Any:
        return resolve_value(val, params, theme)

    def _layer_line_spacing(self, layer):
        return _line_spacing((layer.props if layer else {}).get("line_spacing", 0.0))

    @staticmethod
    def calculate_icon_layout(text_size: float, line_spacing: float = 0.0) -> Dict[str, float]:
        icon_size = round(text_size * 0.5, 4)
        gap = round(text_size * 0.32, 4) if abs(line_spacing) < 0.01 else round(abs(line_spacing) * 2.0, 4)
        return {"icon_size": icon_size, "gap": gap, "line_step": round(text_size * 1.15 + gap, 4)}

    @staticmethod
    def calculate_squircle_padding(text_width: float, text_height: float, pad_ratio: float = 0.03) -> Dict[str, float]:
        pad_x = max(0.03, text_width * pad_ratio + 0.02)
        pad_y = max(0.02, text_height * pad_ratio + 0.015)
        return {
            "width": round(text_width + pad_x * 2.0, 4), "height": round(text_height + pad_y * 2.0, 4),
            "pad_x": round(pad_x, 4), "pad_y": round(pad_y, 4), "corner_radius": 14,
        }

    @staticmethod
    def calculate_lower_third_clamping(line_count: int, font_size: float, default_y: float = 0.28) -> float:
        if line_count <= 1:
            return round(default_y, 3)
        return round(max(0.18, min(0.35, default_y)), 3)

    @staticmethod
    def calculate_trailing_icon_overlap(text_end_x: float, icon_size: float, overlap_pct: float = 0.20) -> float:
        overlap = icon_size * overlap_pct
        return round(text_end_x + icon_size * 0.5 - overlap, 4)
