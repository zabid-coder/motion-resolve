"""
CaptionForge for Resolve - Animation Engine
Implements physics-based animations, continuous effects, customize distance/duration,
and AUTO direction continuity tracking between successive titles.
"""

class AnimationEngine:
    """Manages motion effects and directional continuity matching."""

    TRANSFORM_NODE_NAME = "MR_Transform"
    CHAR_EFFECTS_IN = ("write_on", "char_cascade", "char_pop", "char_blur")
    CHAR_EFFECTS_OUT = ("char_cascade_out", "char_fade_out")
    BLUR_NODE_NAME = "MR_Blur"
    MASK_NODE_NAME = "MR_Mask"
    MATTE_NODE_NAME = "MR_Matte"

    def __init__(self):
        self._dir_index = 0
        self._directions = ["up", "right", "down", "left"]
        self._last_exit_direction = None

    def get_or_create_pipeline(self, comp):
        template = comp.FindTool("Template")
        if not template:
            for t in comp.GetToolList().values():
                if t.GetAttrs().get("TOOLS_RegID") == "TextPlus":
                    template = t
                    break

        media_out = comp.FindTool("MediaOut1")
        if not media_out:
            for t in comp.GetToolList().values():
                if t.GetAttrs().get("TOOLS_RegID") == "MediaOut":
                    media_out = t
                    break

        if not template or not media_out:
            return None, None, None, None

        # Source to animate: a compiled template's output, a dual-text merge
        # (HeroText + Template), or the plain Text+ tool.
        text_source = comp.FindTool("MR_TemplateOut") or comp.FindTool("MR_TextMerge") or template

        mr_trans = comp.FindTool(self.TRANSFORM_NODE_NAME)
        if not mr_trans:
            mr_trans = comp.AddTool("Transform")
            mr_trans.SetAttrs({"TOOLS_Name": self.TRANSFORM_NODE_NAME})

        mr_blur = comp.FindTool(self.BLUR_NODE_NAME)
        if not mr_blur:
            mr_blur = comp.AddTool("DirectionalBlur")
            mr_blur.SetAttrs({"TOOLS_Name": self.BLUR_NODE_NAME})
            mr_blur.Length = 0.0

        mr_mask = comp.FindTool(self.MASK_NODE_NAME)
        if not mr_mask:
            mr_mask = comp.AddTool("RectangleMask")
            mr_mask.SetAttrs({"TOOLS_Name": self.MASK_NODE_NAME})

        # Fit the reveal mask around every visible text layer. Two-color
        # titles use separate Text+ nodes with a small vertical offset, so a
        # fixed 0.14 mask clips the top/bottom of the stack during entry/exit.
        centers_y = []
        font_sizes = []
        cx_values = []
        for text_node in (template, comp.FindTool("HeroText")):
            if not text_node:
                continue
            try:
                center = text_node.GetInput("Center")
                if isinstance(center, dict):
                    cx_val = center.get(1) if center.get(1) is not None else (center.get(1.0) if center.get(1.0) is not None else center.get("1", 0.5))
                    cy_val = center.get(2) if center.get(2) is not None else (center.get(2.0) if center.get(2.0) is not None else center.get("2", 0.5))
                    cx_values.append(float(cx_val))
                    centers_y.append(float(cy_val))
                elif isinstance(center, (list, tuple)) and len(center) >= 2:
                    cx_values.append(float(center[0]))
                    centers_y.append(float(center[1]))
                size = text_node.GetInput("Size")
                if size is not None:
                    font_sizes.append(float(size))
            except Exception:
                continue

        cx = sum(cx_values) / len(cx_values) if cx_values else 0.5
        cy = (min(centers_y) + max(centers_y)) * 0.5 if centers_y else 0.5
        text_size = max(font_sizes) if font_sizes else 0.075
        stack_span = max(centers_y) - min(centers_y) if len(centers_y) > 1 else 0.0
        mr_mask.Center = [cx, cy]
        mr_mask.Width = 0.95
        mr_mask.Height = min(0.65, max(0.14, stack_span + text_size * 1.25 + 0.02))

        mr_trans.Input.ConnectTo(text_source.Output)
        if hasattr(mr_trans, "EffectMask") and hasattr(mr_trans.EffectMask, "ConnectTo"):
            mr_trans.EffectMask.ConnectTo(mr_mask.Mask)
        mr_blur.Input.ConnectTo(mr_trans.Output)

        # If MatteControl is available in Fusion, route through studio matte control
        mr_matte = comp.FindTool(self.MATTE_NODE_NAME)
        if not mr_matte:
            mr_matte = comp.AddTool("MatteControl")
            if mr_matte:
                mr_matte.SetAttrs({"TOOLS_Name": self.MATTE_NODE_NAME})

        if mr_matte and hasattr(mr_matte, "Background") and hasattr(mr_matte.Background, "ConnectTo"):
            mr_matte.Background.ConnectTo(mr_blur.Output)
            if hasattr(mr_matte, "EffectMask") and hasattr(mr_matte.EffectMask, "ConnectTo"):
                mr_matte.EffectMask.ConnectTo(mr_mask.Mask)
            head = mr_matte.Output
        else:
            head = mr_blur.Output

        # True opacity: Merge(transparent BG, title FG).Blend. A Transform's
        # Blend only mixes back to the UNtransformed input (at 0 the title is
        # fully visible at rest), so it can never fade a title out.
        mr_fade = self._get_fade(comp)
        if mr_fade is not None:
            mr_fade.Foreground.ConnectTo(head)
            head = mr_fade.Output
        media_out.Input.ConnectTo(head)

        return mr_trans, mr_blur, template, media_out

    FADE_NODE_NAME = "MR_Fade"
    CLEAR_NODE_NAME = "MR_Clear"

    def _get_fade(self, comp):
        fade = comp.FindTool(self.FADE_NODE_NAME)
        if fade:
            return fade
        try:
            clear = comp.FindTool(self.CLEAR_NODE_NAME) or comp.AddTool("Background")
            clear.SetAttrs({"TOOLS_Name": self.CLEAR_NODE_NAME})
            clear.SetInput("UseFrameFormatSettings", 1)
            for chn in ("TopLeftRed", "TopLeftGreen", "TopLeftBlue", "TopLeftAlpha"):
                clear.SetInput(chn, 0.0)
            fade = comp.AddTool("Merge")
            fade.SetAttrs({"TOOLS_Name": self.FADE_NODE_NAME})
            fade.Background.ConnectTo(clear.Output)
            return fade
        except Exception:
            return None

    def remove_effects(self, timeline_item):
        if not timeline_item or timeline_item.GetFusionCompCount() == 0:
            return False
        try:
            comp = timeline_item.GetFusionCompByIndex(1)
            template = comp.FindTool("Template")
            media_out = comp.FindTool("MediaOut1")

            source = comp.FindTool("MR_TemplateOut") or comp.FindTool("MR_TextMerge") or template
            for node_name in [self.TRANSFORM_NODE_NAME, self.BLUR_NODE_NAME, self.MASK_NODE_NAME,
                              self.MATTE_NODE_NAME, self.FADE_NODE_NAME, self.CLEAR_NODE_NAME]:
                t = comp.FindTool(node_name)
                if t:
                    t.Delete()

            if source and media_out:
                media_out.Input.ConnectTo(source.Output)
            return True
        except Exception as e:
            print(f"[CaptionForge] Error removing effects: {e}")
            return False

    def get_auto_next_direction(self, continuity=True):
        """Return a direction that follows the last applied motion when known."""
        if continuity and self._last_exit_direction in self._directions:
            return self._last_exit_direction
        next_dir = self._directions[self._dir_index % len(self._directions)]
        self._dir_index += 1
        return next_dir

    def has_motion_continuity(self):
        return self._last_exit_direction in self._directions

    def register_template_motion(self, template):
        """Remember the actual authored template exit direction for the next title."""
        for layer in getattr(template, "layers", []):
            for track in getattr(layer, "motion_tracks", []):
                if getattr(track, "phase", None) != "out" or not getattr(track, "keyframes", None):
                    continue
                prop = getattr(track, "property", "")
                try:
                    value = float(track.keyframes[-1].value) - float(track.keyframes[0].value)
                    if prop == "translate_y" and abs(value) > 1e-5:
                        # Fusion's normalized Y axis increases upward.
                        self._last_exit_direction = "up" if value > 0 else "down"
                        return self._last_exit_direction
                    if prop == "translate_x" and abs(value) > 1e-5:
                        self._last_exit_direction = "right" if value > 0 else "left"
                        return self._last_exit_direction
                except (TypeError, ValueError):
                    continue
        # Templates without an authored translation use the compiler's subtle
        # default exit, which moves down from the title's resting position.
        self._last_exit_direction = "down"
        return self._last_exit_direction

    def resolve_auto_effect(self, effect_in, effect_out=None):
        """Resolve AUTO into a concrete direction while retaining bounce/slide style."""
        value = str(effect_in or "").lower()
        if value == "auto":
            value = "slide"
        if value in ("slide", "bounce"):
            direction = self.get_auto_next_direction()
            effect_in = f"{value}_{direction}"
            self._last_direction = direction
        elif value.endswith(("_up", "_down", "_left", "_right")):
            self._last_direction = value.rsplit("_", 1)[-1]

        out_value = str(effect_out or "").lower()
        if out_value.endswith(("_up", "_down", "_left", "_right")):
            self._last_exit_direction = out_value.rsplit("_", 1)[-1]
        elif out_value in ("fade", "off", "none") and getattr(self, "_last_direction", None):
            self._last_exit_direction = self._last_direction
        return effect_in

    def get_motion_curve_expression(self, effect_name: str, phase: str = "in", duration: int = 15, distance: float = 1.0) -> str:
        dur = max(1, int(duration))
        dist = float(distance)
        if phase == "in":
            p = f"math.max(0, math.min(1, (time - comp.RenderStart) / {dur}))"
            if effect_name == "slide_up":
                return f"- Point(0.0, {0.65 * dist:.3f} * (1 - (1 - math.pow(2, -10 * ({p})))))"
            elif effect_name == "slide_down":
                return f"+ Point(0.0, {0.65 * dist:.3f} * (1 - (1 - math.pow(2, -10 * ({p})))))"
            elif effect_name == "slide_left":
                return f"+ Point({0.75 * dist:.3f} * (1 - (1 - math.pow(2, -10 * ({p})))), 0.0)"
            elif effect_name == "slide_right":
                return f"- Point({0.75 * dist:.3f} * (1 - (1 - math.pow(2, -10 * ({p})))), 0.0)"
            elif effect_name == "bounce_up":
                return f"- Point(0.0, {0.45 * dist:.3f} * (1 - (1 + math.pow(2, -9 * ({p})) * math.sin((({p}) * 9.5 - 0.75) * 2.094) * 0.065)))"
            elif effect_name == "bounce_down":
                return f"+ Point(0.0, {0.45 * dist:.3f} * (1 - (1 + math.pow(2, -9 * ({p})) * math.sin((({p}) * 9.5 - 0.75) * 2.094) * 0.065)))"
            elif effect_name == "bounce_left":
                return f"+ Point({0.55 * dist:.3f} * (1 - (1 + math.pow(2, -9 * ({p})) * math.sin((({p}) * 9.5 - 0.75) * 2.094) * 0.065)), 0.0)"
            elif effect_name == "bounce_right":
                return f"- Point({0.55 * dist:.3f} * (1 - (1 + math.pow(2, -9 * ({p})) * math.sin((({p}) * 9.5 - 0.75) * 2.094) * 0.065)), 0.0)"
        else:
            # Exit phase: cubic acceleration offscreen
            p_out = f"math.max(0, math.min(1, (comp.RenderEnd - time) / {dur}))"
            if effect_name in ("slide_down", "default"):
                return f"- Point(0.0, {0.65 * dist:.3f} * (1 - math.pow({p_out}, 3)))"
            elif effect_name == "slide_up":
                return f"+ Point(0.0, {0.65 * dist:.3f} * (1 - math.pow({p_out}, 3)))"
            elif effect_name == "slide_left":
                return f"- Point({0.75 * dist:.3f} * (1 - math.pow({p_out}, 3)), 0.0)"
            elif effect_name == "slide_right":
                return f"+ Point({0.75 * dist:.3f} * (1 - math.pow({p_out}, 3)), 0.0)"
            elif effect_name == "bounce_down":
                return f"- Point(0.0, {0.65 * dist:.3f} * (1 - math.pow({p_out}, 3)))"
            elif effect_name == "bounce_up":
                return f"+ Point(0.0, {0.65 * dist:.3f} * (1 - math.pow({p_out}, 3)))"
            elif effect_name == "bounce_left":
                return f"- Point({0.75 * dist:.3f} * (1 - math.pow({p_out}, 3)), 0.0)"
            elif effect_name == "bounce_right":
                return f"+ Point({0.75 * dist:.3f} * (1 - math.pow({p_out}, 3)), 0.0)"
        return ""

    def apply_motion_preset(self, timeline_item, effect_in=None, effect_out=None, options=None):
        if not timeline_item or timeline_item.GetFusionCompCount() == 0:
            return False

        effect_in = self.resolve_auto_effect(effect_in, effect_out)
        opts = dict(options or {})
        # Preset motion names that used to fall through to a plain fade.
        if effect_in == "fade_in_slow":
            opts["duration"] = int(opts.get("duration", 10)) * 2
            effect_in = "fade"
        elif effect_in == "fade_in":
            effect_in = "fade"
        if effect_out in ("fade_out",):
            effect_out = "fade"
        char_in = effect_in if effect_in in self.CHAR_EFFECTS_IN else None
        char_out = effect_out if effect_out in self.CHAR_EFFECTS_OUT else None
        comp = timeline_item.GetFusionCompByIndex(1)
        mr_trans, mr_blur, template, media_out = self.get_or_create_pipeline(comp)
        if not mr_trans:
            return False

        dur = max(1, int(opts.get("duration", 10)))
        dist = float(opts.get("distance", 1.0))
        intensity = float(opts.get("intensity", 1.0))

        # Reset base values
        if hasattr(mr_trans.Center, "SetExpression"):
            mr_trans.Center.SetExpression(None)
        if hasattr(mr_trans.Size, "SetExpression"):
            mr_trans.Size.SetExpression(None)
        if hasattr(mr_trans.Angle, "SetExpression"):
            mr_trans.Angle.SetExpression(None)
        if hasattr(mr_trans, "Blend") and hasattr(mr_trans.Blend, "SetExpression"):
            mr_trans.Blend.SetExpression(None)

        if hasattr(mr_trans, "SetInput"):
            mr_trans.SetInput("Center", [0.5, 0.5])
            mr_trans.SetInput("Size", 1.0)
            mr_trans.SetInput("Angle", 0.0)
            if hasattr(mr_trans, "Blend"):
                mr_trans.SetInput("Blend", 1.0)
        else:
            mr_trans.Center = [0.5, 0.5]
            mr_trans.Size = 1.0
            mr_trans.Angle = 0.0
            if hasattr(mr_trans, "Blend"):
                mr_trans.Blend = 1.0

        if mr_blur:
            if hasattr(mr_blur.Length, "SetExpression"):
                mr_blur.Length.SetExpression(None)
            mr_blur.Length = 0.0

        center_expr_parts = []
        size_expr_parts = []
        blend_expr_parts = []

        # 1. IN Effects
        curve_in = self.get_motion_curve_expression(effect_in, phase="in", duration=dur, distance=dist)
        if curve_in:
            center_expr_parts.append(curve_in)
            if effect_in.endswith("_up"):
                self._last_direction = "up"
            elif effect_in.endswith("_down"):
                self._last_direction = "down"
            elif effect_in.endswith("_left"):
                self._last_direction = "left"
            elif effect_in.endswith("_right"):
                self._last_direction = "right"
        elif effect_in == "pop_in":
            size_expr_parts.append(
                f"- (1.0 * math.exp(-math.max(0, time - comp.RenderStart) * 0.40) * math.cos(math.max(0, time - comp.RenderStart) * 0.65))"
            )
        elif effect_in == "bounce_pop":
            size_expr_parts.append(
                f"- (1.0 * math.exp(-math.max(0, time - comp.RenderStart) * 0.32) * math.cos(math.max(0, time - comp.RenderStart) * 0.55))"
            )
            center_expr_parts.append(
                f"- Point(0.0, {0.08 * dist} * math.exp(-math.max(0, time - comp.RenderStart) * 0.40) * math.sin(math.max(0, time - comp.RenderStart) * 0.70))"
            )
            self._last_direction = "up"
        elif effect_in == "glitch_zoom":
            size_expr_parts.append(
                f"+ ({0.45 * intensity} * math.exp(-math.max(0, time - comp.RenderStart) * 0.45) * math.cos(math.max(0, time - comp.RenderStart) * 0.80))"
            )
            center_expr_parts.append(
                f"+ Point(({0.025 * intensity} * math.sin(time * 35.0) * math.max(0, 1 - (time - comp.RenderStart) / {dur})), 0.0)"
            )
            if hasattr(mr_trans.Angle, "SetExpression"):
                mr_trans.Angle.SetExpression(
                    f"{2.5 * intensity:.2f} * math.sin(time * 42.0) * math.max(0, 1 - (time - comp.RenderStart) / {dur})"
                )
        elif effect_in == "fade":
            blend_expr_parts.append(f"min(1, max(0, (time - comp.RenderStart) / {dur}))")
        elif effect_in in ("scale_fade", "zoom_punch", "slam_drop", "slide_up_blur"):
            fast = max(4, int(dur * (0.7 if effect_in == "slam_drop" else 1.2)))
            p_in = f"math.max(0, math.min(1, (time - comp.RenderStart) / {fast}))"
            ease = f"(1 - math.pow(1 - {p_in}, 4))"   # quart-out: readable, not a snap
            if effect_in == "scale_fade":
                size_expr_parts.append(f"- ({0.14 * intensity:.3f} * (1 - {ease}))")
            elif effect_in == "zoom_punch":
                size_expr_parts.append(f"+ ({0.38 * intensity:.3f} * (1 - {ease}))")
            elif effect_in == "slam_drop":
                center_expr_parts.append(f"+ Point(0.0, {0.2 * dist:.3f} * math.pow(1 - {p_in}, 3))")
                # squash on landing, settling with a damped wobble
                size_expr_parts.append(
                    f"+ ({0.1 * intensity:.3f} * math.exp(-math.max(0, time - comp.RenderStart - {fast}) * 0.35)"
                    f" * math.cos(math.max(0, time - comp.RenderStart - {fast}) * 0.9) * ({p_in} >= 1 and 1 or 0))")
                opts["motion_blur"] = True
                opts.setdefault("motion_blur_angle", 90.0)
            elif effect_in == "slide_up_blur":
                center_expr_parts.append(f"- Point(0.0, {0.06 * dist:.3f} * (1 - {ease}))")
                opts["blur_in"] = True
            blend_expr_parts.append(f"min(1, max(0, (time - comp.RenderStart) / {max(2, fast // 2)}))")
            self._last_direction = "up"

        # 2. OUT Effects
        eff_out = effect_out
        if eff_out is None and effect_in:
            eff_out = "slide_down"

        curve_out = self.get_motion_curve_expression(eff_out, phase="out", duration=dur, distance=dist)
        if curve_out:
            center_expr_parts.append(curve_out)
        elif eff_out == "fade":
            blend_expr_parts.append(f"min(1, max(0, (comp.RenderEnd - time) / {dur}))")
        elif eff_out == "scale_out":
            p_out = f"math.max(0, math.min(1, (comp.RenderEnd - time) / {dur}))"
            size_expr_parts.append(f"- ({0.12 * intensity:.3f} * (1 - math.pow({p_out}, 3)))")
            blend_expr_parts.append(f"min(1, max(0, (comp.RenderEnd - time) / {dur}))")
        elif eff_out == "blur_out":
            blend_expr_parts.append(f"min(1, max(0, (comp.RenderEnd - time) / {dur}))")
            opts["blur_out"] = True

        # Guarantee transparent first and last frames. The previous motion
        # offsets were small enough to leave titles partially visible at both
        # ends, particularly on short slide presets.
        edge = 2 if (char_in or char_out) else dur
        fade_span = f"math.max(1, math.min({edge}, (comp.RenderEnd - comp.RenderStart) / 3))"
        blend_expr_parts.append(
            f"min(1, max(0, (time - comp.RenderStart) / ({fade_span})), "
            f"max(0, (comp.RenderEnd - time) / ({fade_span})))"
        )

        # Continuous Effects (Persist across entire clip)
        shake_speed = float(opts.get("shake_speed", 1.0))
        shake_intensity = float(opts.get("shake_intensity", intensity))

        if opts.get("shake", False) or effect_in == "shake":
            freq1 = 3.7 * shake_speed
            freq2 = 1.9 * shake_speed
            freq3 = 2.8 * shake_speed
            freq4 = 4.1 * shake_speed
            amp = 0.012 * shake_intensity
            center_expr_parts.append(
                f"+ Point({amp:.4f} * math.sin(time * {freq1:.2f}) * math.cos(time * {freq2:.2f}), {amp:.4f} * math.cos(time * {freq3:.2f}) * math.sin(time * {freq4:.2f}))"
            )
        if effect_in == "jitter" or opts.get("jitter", False):
            jitter_intensity = float(opts.get("jitter_intensity", shake_intensity))
            jitter_speed = float(opts.get("jitter_speed", shake_speed))
            amp_j = 0.008 * jitter_intensity
            freq_j1 = 5.3 * jitter_speed
            freq_j2 = 6.7 * jitter_speed
            center_expr_parts.append(
                f"+ Point({amp_j:.4f} * math.sin(time * {freq_j1:.2f}), {amp_j:.4f} * math.cos(time * {freq_j2:.2f}))"
            )
        if effect_in == "scribble" or opts.get("scribble", False):
            scribble_intensity = float(opts.get("scribble_intensity", shake_intensity))
            scribble_speed = float(opts.get("scribble_speed", shake_speed))
            amp_s = 0.007 * scribble_intensity
            freq_s = 0.7 * scribble_speed
            center_expr_parts.append(
                f"+ Point({amp_s:.4f} * math.sin(math.floor(time * {freq_s:.2f}) * 12.3), {amp_s:.4f} * math.cos(math.floor(time * {freq_s:.2f}) * 7.9))"
            )
            mr_trans.Angle.SetExpression(f"{1.2 * scribble_intensity:.2f} * math.sin(math.floor(time * {freq_s:.2f}) * 5.1)")

        if center_expr_parts:
            mr_trans.Center.SetExpression("Point(0.5, 0.5) " + " ".join(center_expr_parts))

        if size_expr_parts:
            mr_trans.Size.SetExpression("1.0 " + " ".join(size_expr_parts))
        elif hasattr(mr_trans.Size, "SetExpression"):
            # Override stale template keyframes when reusing this Text+ clip.
            mr_trans.Size.SetExpression("1.0")

        fade_tool = self._get_fade(comp)
        if blend_expr_parts:
            expr = " * ".join(f"({part})" for part in blend_expr_parts)
            target = fade_tool if fade_tool is not None else mr_trans
            if hasattr(target, "Blend") and hasattr(target.Blend, "SetExpression"):
                target.Blend.SetExpression(expr)

        # 3. Blur & Motion Blur
        if mr_blur:
            if opts.get("motion_blur", False) or effect_in == "motion_blur":
                blur_intensity = float(opts.get("motion_blur_intensity", intensity))
                blur_angle = max(0.0, min(180.0, float(opts.get("motion_blur_angle", 90.0))))
                mr_blur.Length.SetExpression(f"{0.05 * blur_intensity} * math.exp(-math.max(0, time - comp.RenderStart) * 0.40)")
                mr_blur.Angle = blur_angle
            elif opts.get("blur_out", False):
                mr_blur.Length.SetExpression(f"{0.04 * intensity} * math.exp(-math.max(0, comp.RenderEnd - time) * 0.35)")
                mr_blur.Angle = 90.0
            elif effect_in == "blur_in" or opts.get("blur_in", False):
                blur_intensity = float(opts.get("motion_blur_intensity", intensity))
                blur_angle = max(0.0, min(180.0, float(opts.get("motion_blur_angle", 90.0))))
                mr_blur.Length.SetExpression(f"{0.04 * blur_intensity} * math.exp(-math.max(0, time - comp.RenderStart) * 0.35)")
                mr_blur.Angle = blur_angle

        # 4. Per-character motion (Text+ Follower) - or a neutral Follower
        self._apply_char_motion(comp, char_in, char_out, opts)

        # 4. Flicker
        flicker_enabled = opts.get("flicker", False) or effect_in == "flicker"
        text_layers = [comp.FindTool("Template"), comp.FindTool("HeroText")]
        freq = float(opts.get("flicker_frequency", 0.5))
        amp = float(opts.get("flicker_intensity", 1.0))
        flicker_dur = max(4, int(5 + freq * 15))
        rate = 2 if freq > 0.4 else 3
        min_alpha = max(0.0, 1.0 - amp)
        for text_layer in text_layers:
            if text_layer:
                try:
                    if flicker_enabled:
                        text_layer.Alpha1.SetExpression(
                            f"(time - comp.RenderStart < {flicker_dur} and (math.floor(time) % {rate} == 0)) and {min_alpha:.2f} or 1.0"
                        )
                    else:
                        text_layer.Alpha1.SetExpression(None)
                except Exception:
                    pass

        return True


    # ------------------------------------------------------------------
    # Per-character motion
    # ------------------------------------------------------------------
    @staticmethod
    def _key(tool, inp, keys, rs):
        """Write cubic-bezier keys (frame offsets from comp start) on a Follower input."""
        from core.templates.motion_curves import fusion_keyframes, expand_springs
        keys = expand_springs(list(keys))
        if keys and keys[0][0] > 0:
            keys.insert(0, (0.0, keys[0][1], "linear"))
        try:
            tool.AddModifier(inp, "BezierSpline")
            sp = getattr(tool, inp).GetConnectedOutput().GetTool()
            table = fusion_keyframes([(rs + f, v, e) for f, v, e in keys])
            sp.SetKeyFrames(table, True)
            ours = {round(float(t), 4) for t in table}
            for t in list((sp.GetKeyFrames() or {}).keys()):
                if round(float(t), 4) not in ours:
                    sp.DeleteKeyFrames(float(t) - 0.001, float(t) + 0.001)
        except Exception as exc:
            print(f"[Motion Resolve] Could not key {inp}: {exc}")

    def _apply_char_motion(self, comp, char_in, char_out, opts):
        try:
            attrs = comp.GetAttrs()
            rs = float(attrs.get("COMPN_RenderStart", 0) or 0)
            last = float(attrs.get("COMPN_RenderEnd", rs + 72)) - rs
        except Exception:
            rs, last = 0.0, 72.0
        for name in ("Template", "HeroText"):
            tool = comp.FindTool(name)
            if not tool:
                continue
            try:
                if tool.StyledText.GetExpression():
                    continue  # a count-up drives this text
            except Exception:
                pass
            try:
                out = tool.StyledText.GetConnectedOutput()
                fol = out.GetTool() if out else None
            except Exception:
                continue  # not a Fusion Text+ (or Resolve refused): leave text motion as is
            if fol is None or fol.GetAttrs().get("TOOLS_RegID") != "StyledTextFollower":
                if not (char_in or char_out):
                    continue
                tool.AddModifier("StyledText", "StyledTextFollower")
                fol = tool.StyledText.GetConnectedOutput().GetTool()
            text = str(tool.GetInput("StyledText") or "")
            n = max(1, len(text.replace("\n", "").strip()))
            if not (char_in or char_out):
                # neutral: keep the modifier (it holds the text) but no motion
                for inp, v in (("Opacity1", 1.0), ("CharacterSizeX", 1.0), ("CharacterSizeY", 1.0),
                               ("SoftnessX1", 0.0), ("SoftnessY1", 0.0)):
                    self._key(fol, inp, [(0.0, v, "linear")], rs)
                fol.SetInput("Delay", 0.0)
                continue
            delay = 1.6 if char_in == "write_on" else float(opts.get("char_delay", 1.2))
            delay = min(delay, max(0.2, last * 0.18 / max(1, n - 1)))
            span = max(3.0, float(opts.get("duration", 10)))
            shift = (n - 1) * delay
            out0 = max(span, last - span - shift)
            fol.SetInput("Order", 0)
            fol.SetInput("DelayType", 1)
            fol.SetInput("Delay", delay)
            op_in = {"write_on": [(0, 0, "hold"), (1, 1, "linear")]}.get(char_in, [(0, 0, "quartInOut"), (span * 0.6, 1, "linear")])
            op = list(op_in) if char_in else [(0, 1, "linear")]
            if char_out:
                op += [(out0, 1, "cubicIn"), (out0 + span * 0.7, 0, "linear")]
            self._key(fol, "Opacity1", op, rs)
            if tool.GetInput("Enabled3"):
                k = float(tool.GetInput("Opacity3") or 0.5)
                self._key(fol, "Opacity3", [(f, v * k, e) for f, v, e in op], rs)
            size = [(0, 1, "linear")]
            if char_in == "char_pop":
                size = [(0, 0.2, "spring"), (span, 1, "linear")]
            elif char_in == "char_cascade":
                size = [(0, 0.85, "expoOut"), (span, 1, "linear")]
            self._key(fol, "CharacterSizeX", size, rs)
            self._key(fol, "CharacterSizeY", size, rs)
            soft = [(0, 0, "linear")]
            if char_in in ("char_blur", "char_cascade"):
                soft = [(0, 6.0, "expoOut"), (span, 0, "linear")]
            if char_out:
                soft = soft + [(out0, 0, "cubicIn"), (out0 + span * 0.7, 4.0, "linear")]
            fol.SetInput("SoftnessOnFillColorToo1", 1)
            self._key(fol, "SoftnessX1", soft, rs)
            self._key(fol, "SoftnessY1", soft, rs)
