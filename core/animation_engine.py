"""
CaptionForge for Resolve - Animation Engine
Implements physics-based animations, continuous effects, customize distance/duration,
and AUTO direction continuity tracking between successive titles.
"""

class AnimationEngine:
    """Manages motion effects and directional continuity matching."""

    TRANSFORM_NODE_NAME = "MR_Transform"
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

        # Check if comp has dual-text merge (HeroText + Template)
        text_source = comp.FindTool("MR_TextMerge") or template

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
            media_out.Input.ConnectTo(mr_matte.Output)
        else:
            media_out.Input.ConnectTo(mr_blur.Output)

        return mr_trans, mr_blur, template, media_out

    def remove_effects(self, timeline_item):
        if not timeline_item or timeline_item.GetFusionCompCount() == 0:
            return False
        try:
            comp = timeline_item.GetFusionCompByIndex(1)
            template = comp.FindTool("Template")
            media_out = comp.FindTool("MediaOut1")

            for node_name in [self.TRANSFORM_NODE_NAME, self.BLUR_NODE_NAME, self.MASK_NODE_NAME, self.MATTE_NODE_NAME]:
                t = comp.FindTool(node_name)
                if t:
                    t.Delete()

            if template and media_out:
                media_out.Input.ConnectTo(template.Output)
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
        opts = options or {}
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

        # 2. OUT Effects
        eff_out = effect_out
        if eff_out is None and effect_in:
            eff_out = "slide_down"

        curve_out = self.get_motion_curve_expression(eff_out, phase="out", duration=dur, distance=dist)
        if curve_out:
            center_expr_parts.append(curve_out)
        elif eff_out == "fade":
            blend_expr_parts.append(f"min(1, max(0, (comp.RenderEnd - time) / {dur}))")

        # Guarantee transparent first and last frames. The previous motion
        # offsets were small enough to leave titles partially visible at both
        # ends, particularly on short slide presets.
        fade_span = f"math.max(1, math.min({dur}, (comp.RenderEnd - comp.RenderStart) / 3))"
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
            mr_trans.Center.SetExpression("Point(0.5, 0.5) " + " ".join(center_expr_parts) + " -- [safe 0.55 0.65 0.35]")

        if size_expr_parts:
            mr_trans.Size.SetExpression("1.0 " + " ".join(size_expr_parts))
        elif hasattr(mr_trans.Size, "SetExpression"):
            # Override stale template keyframes when reusing this Text+ clip.
            mr_trans.Size.SetExpression("1.0")

        if blend_expr_parts and hasattr(mr_trans, "Blend") and hasattr(mr_trans.Blend, "SetExpression"):
            mr_trans.Blend.SetExpression(" * ".join(f"({part})" for part in blend_expr_parts))

        # 3. Blur & Motion Blur
        if mr_blur:
            if opts.get("motion_blur", False) or effect_in == "motion_blur":
                blur_intensity = float(opts.get("motion_blur_intensity", intensity))
                blur_angle = max(0.0, min(180.0, float(opts.get("motion_blur_angle", 90.0))))
                mr_blur.Length.SetExpression(f"{0.05 * blur_intensity} * math.exp(-math.max(0, time - comp.RenderStart) * 0.40)")
                mr_blur.Angle = blur_angle
            elif effect_in == "blur_in" or opts.get("blur_in", False):
                blur_intensity = float(opts.get("motion_blur_intensity", intensity))
                blur_angle = max(0.0, min(180.0, float(opts.get("motion_blur_angle", 90.0))))
                mr_blur.Length.SetExpression(f"{0.04 * blur_intensity} * math.exp(-math.max(0, time - comp.RenderStart) * 0.35)")
                mr_blur.Angle = blur_angle

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
