"""
CaptionForge for Resolve - Text+ Builder
Provides complete control over DaVinci Resolve Text+ titles:
styling, fonts, colors, strokes, drop shadows, highlight boxes,
copy/paste attributes (look, font, all), and layout templates (Hero Word, 2-line, 3-line).
"""

from core.resolve_api import ResolveBridge

class TextPlusBuilder:
    """Manages Text+ styling, extraction, template layouts, and attribute transfer."""

    DEFAULT_STYLE = {
        "text": "SAMPLE CAPTION",
        "font": "Inter",
        "style": "Bold",
        "hero_font": "Pinyon Script",
        "hero_style": "Regular",
        "hero_size_multiplier": 1.15,
        "size": 0.072,
        "character_spacing": 1.02,
        "line_spacing": 0.0,
        "horizontal_anchor": 0.0,
        "vertical_anchor": 0.0,
        "center_x": 0.5,
        "center_y": 0.28,
        "color": [1.0, 1.0, 1.0, 1.0],
        "accent_color": [0.18, 0.48, 1.0, 1.0],
        "stroke_enabled": False,
        "stroke_color": [0.0, 0.0, 0.0, 1.0],
        "stroke_thickness": 0.02,
        "shadow_enabled": True,
        "shadow_color": [0.0, 0.0, 0.0, 0.50],
        "shadow_softness": 0.045,
        "shadow_offset": [0.0, 0.0],
        "box_enabled": False,
        "box_color": [0.043, 0.059, 0.098, 0.85],
        "box_extend_x": 0.04,
        "box_extend_y": 0.025,
        "box_round": 0.25,
        "box_level": 1,
        "glow_enabled": False,
        "glow_amount": 0.0,
        "main_word": None
    }

    def __init__(self, bridge=None):
        self.bridge = bridge or ResolveBridge()
        self._clipboard = None

    def get_template_tool(self, timeline_item):
        if not timeline_item:
            return None
        try:
            if timeline_item.GetFusionCompCount() == 0:
                return None
            comp = timeline_item.GetFusionCompByIndex(1)
            if not comp:
                return None
            tool = comp.FindTool("Template")
            if not tool:
                tools = comp.GetToolList()
                for t in tools.values():
                    if t.GetAttrs().get("TOOLS_RegID") == "TextPlus":
                        return t
            return tool
        except Exception:
            return None

    def get_text_layers(self, timeline_item):
        """Return the primary Text+ tool and optional highlighted hero tool."""
        primary = self.get_template_tool(timeline_item)
        hero = None
        try:
            if timeline_item and timeline_item.GetFusionCompCount() > 0:
                comp = timeline_item.GetFusionCompByIndex(1)

                hero = comp.FindTool("HeroText") if comp else None
        except Exception:
            hero = None
        return [tool for tool in (primary, hero) if tool]

    def update_text(self, timeline_item, text):
        """Update title text while keeping a generated two-color hero line in sync."""
        primary = self.get_template_tool(timeline_item)
        if not primary:
            return False
        text = str(text)
        try:
            hero = None
            if timeline_item.GetFusionCompCount() > 0:
                comp = timeline_item.GetFusionCompByIndex(1)
                hero = comp.FindTool("HeroText") if comp else None

            if not hero:
                primary.SetInput("StyledText", text)
                return True

            old_hero_lines = str(hero.GetInput("StyledText") or "").split("\n")
            hero_index = next((i for i, line in enumerate(old_hero_lines) if line.strip()), None)
            new_lines = text.split("\n")
            if hero_index is None or len(new_lines) < 2:
                primary.SetInput("StyledText", text)
                hero.SetInput("StyledText", "")
                return True

            hero_index = min(hero_index, len(new_lines) - 1)
            primary.SetInput("StyledText", "\n".join(" " if i == hero_index else line for i, line in enumerate(new_lines)))
            hero.SetInput("StyledText", "\n".join(line if i == hero_index else " " for i, line in enumerate(new_lines)))
            return True
        except Exception:
            return False

    def apply_style(self, timeline_item, style_dict, text_override=None):
        tool = self.get_template_tool(timeline_item)
        if not tool:
            return False

        style = dict(self.DEFAULT_STYLE)
        if style_dict:
            style.update(style_dict)

        try:
            # 1. Text Content & Hero Word Layout
            final_text = text_override if text_override is not None else style.get("text", "")
            use_2color = bool(style.get("use_2color", False))
            hero_word = style.get("main_word")
            hero_req_font = style.get("hero_font")
            if use_2color and "\n" not in str(final_text):
                caption_words = [word.strip(".,!?").lower() for word in str(final_text).split()]
                requested_words = [word.strip(".,!?").lower() for word in str(hero_word or "").split()]
                if requested_words and not any(caption_words[i:i + len(requested_words)] == requested_words
                                               for i in range(len(caption_words) - len(requested_words) + 1)):
                    hero_word = max(str(final_text).split(), key=len) if str(final_text).split() else hero_word
                final_text = self.apply_layout_template(str(final_text), template_num=1, main_word=hero_word, hero_font=hero_req_font)

            # 2. Typography
            target_font = str(style.get("font", "Avenir Next"))
            try:
                from core.font_catalog import resolve_available_font, normalize_font_style
                from core.templates.bengali_engine import contains_bengali, resolve_font_for_script
                if contains_bengali(str(final_text)):
                    bn_font = style.get("font_bn") or "Kohinoor Bangla"
                    target_font = resolve_font_for_script(str(final_text), target_font, bn_font)
                else:
                    target_font = resolve_available_font(target_font, "display")
            except Exception:
                pass
            tool.SetInput("Font", target_font)
            if "style" in style:
                tool.SetInput("Style", normalize_font_style(str(style["style"]), target_font))
            # Aspect ratio adaptation (16:9 Landscape vs. 9:16 Vertical vs. 1:1 Square)
            frame_w, frame_h = (1920, 1080)
            if self.bridge:
                try:
                    frame_w, frame_h = self.bridge.get_timeline_resolution()
                except Exception:
                    frame_w, frame_h = (1920, 1080)

            ar = float(frame_w) / float(frame_h) if frame_h > 0 else 1.7778
            is_vertical = ar < 0.85
            is_square = 0.85 <= ar < 1.4

            scale_font = 1.0
            scale_h = (1080.0 / float(frame_h)) if frame_h > 0 else 1.0
            if is_vertical:
                scale_font = scale_h * 1.15
            elif is_square:
                scale_font = scale_h * 0.90

            if "size" in style:
                tool.SetInput("Size", float(style["size"]) * scale_font)

            # Line spacing in TextPlus: 1.0 is default standard spacing.
            # 0.0 collapses lines onto each other.
            raw_line_spacing = float(style.get("line_spacing", 0.0))
            if abs(raw_line_spacing) < 0.05:
                eff_line_spacing = 1.05
            elif raw_line_spacing > 0.4:
                eff_line_spacing = raw_line_spacing
            else:
                eff_line_spacing = 1.0 + raw_line_spacing

            tool.SetInput("CharacterSpacingClone", float(style.get("character_spacing", 1.0)))
            tool.SetInput("LineSpacingClone", float(eff_line_spacing))

            if "horizontal_anchor" in style:
                h_anchor = float(style["horizontal_anchor"])
                tool.SetInput("HorizontalLeftCenterRight", h_anchor)
                tool.SetInput("HorizontalJustificationNew", h_anchor)
            if "vertical_anchor" in style:
                tool.SetInput("VerticalTopCenterBottom", float(style["vertical_anchor"]))

            cx = float(style.get("center_x", 0.5))
            cy = float(style.get("center_y", 0.28))
            if is_vertical and cy < 0.28:
                cy = max(0.32, cy + 0.08)
            elif is_square and cy < 0.24:
                cy = max(0.26, cy + 0.04)
            tool.SetInput("Center", [cx, cy])

            # Auto-wrap so captions never clip the phone screen
            wrap_w = 0.88 if is_vertical else 0.84 if is_square else 0.80
            try:
                tool.SetInput("WrapWidth", wrap_w)
                tool.SetInput("WordWrap", 1)
            except Exception:
                pass

            # Dual-color text split if 2-Color is active
            comp = None
            if timeline_item and timeline_item.GetFusionCompCount() > 0:
                comp = timeline_item.GetFusionCompByIndex(1)

            tool.SetInput("StyledText", str(final_text))

            if use_2color and comp and "\n" in str(final_text):
                lines = str(final_text).split("\n")
                hero_idx = -1
                if hero_word:
                    target_words = [word.strip(".,!?").lower() for word in str(hero_word).split()]
                    for idx_l, line in enumerate(lines):
                        line_words = [word.strip(".,!?").lower() for word in line.split()]
                        if line_words == target_words:
                            hero_idx = idx_l
                            break
                if hero_idx == -1 and len(lines) > 1:
                    hero_idx = 1

                base_lines = [lines[i] if i != hero_idx else " " for i in range(len(lines))]
                hero_lines = [" " if i != hero_idx else lines[i] for i in range(len(lines))]

                tool.SetInput("StyledText", "\n".join(base_lines))

                # Resolve can collapse leading/trailing empty lines in a
                # Text+ node. Place the two-color hero and remaining text
                # block using the original line indices so neither layer
                # collapses onto the other's baseline.
                primary_center_y = cy
                hero_center_y = cy
                if len(lines) > 1:
                    size = float(style.get("size", 0.075)) * scale_font
                    raw_spacing = float(style.get("line_spacing", 0.0))
                    spacing = 1.0 if abs(raw_spacing) < 0.05 else (raw_spacing if raw_spacing > 0.3 else max(0.4, 1.0 + raw_spacing))
                    hero_scale = max(1.0, min(1.5, float(style.get("hero_size_multiplier", 1.0))))
                    line_step = max(0.045, size * 1.15 * spacing * min(1.25, hero_scale))
                    remaining_indices = [i for i in range(len(lines)) if i != hero_idx]
                    primary_mid = (remaining_indices[0] + remaining_indices[-1]) * 0.5
                    block_mid = (len(lines) - 1) * 0.5
                    primary_center_y = cy + (block_mid - primary_mid) * line_step
                    hero_center_y = cy + (block_mid - hero_idx) * line_step
                    tool.SetInput("Center", [cx, primary_center_y])

                hero_tool = comp.FindTool("HeroText")
                if not hero_tool:
                    hero_tool = comp.AddTool("TextPlus")
                    hero_tool.SetAttrs({"TOOLS_Name": "HeroText"})

                merge = comp.FindTool("MR_TextMerge")
                if not merge:
                    merge = comp.AddTool("Merge")
                    merge.SetAttrs({"TOOLS_Name": "MR_TextMerge"})

                merge.Background.ConnectTo(tool.Output)
                merge.Foreground.ConnectTo(hero_tool.Output)

                mr_trans = comp.FindTool("MR_Transform")
                media_out = comp.FindTool("MediaOut1")
                if not media_out:
                    for t in comp.GetToolList().values():
                        if t.GetAttrs().get("TOOLS_RegID") == "MediaOutput":
                            media_out = t
                            break

                if mr_trans:
                    mr_trans.Input.ConnectTo(merge.Output)
                elif media_out:
                    media_out.Input.ConnectTo(merge.Output)

                hero_tool.SetInput("StyledText", "\n".join(hero_lines))
                hero_requested_font = str(style.get("hero_font", target_font))
                try:
                    from core.templates.bengali_engine import resolve_font_for_script, contains_bengali
                    from core.font_catalog import resolve_available_font, is_script_font
                    if contains_bengali("\n".join(hero_lines)):
                        hero_font = resolve_font_for_script(
                            "\n".join(hero_lines),
                            hero_requested_font,
                            style.get("hero_font_bn") or hero_requested_font
                        )
                    else:
                        purpose = "script" if is_script_font(hero_requested_font) else ("serif" if "serif" in hero_requested_font.lower() else "display")
                        hero_font = resolve_available_font(hero_requested_font, purpose)
                except Exception:
                    hero_font = target_font
                hero_tool.SetInput("Font", hero_font)
                if "style" in style:
                    hero_tool.SetInput("Style", str(style["style"]))
                if "size" in style:
                    hero_tool.SetInput("Size", float(style["size"]) * scale_font * max(1.0, min(1.5, float(style.get("hero_size_multiplier", 1.0)))))
                if style.get("hero_style"):
                    hero_tool.SetInput("Style", str(style["hero_style"]))
                hero_tool.SetInput("CharacterSpacingClone", float(style.get("character_spacing", 1.0)))
                hero_tool.SetInput("LineSpacingClone", float(eff_line_spacing))
                try:
                    hero_tool.SetInput("WrapWidth", wrap_w)
                    hero_tool.SetInput("WordWrap", 1)
                except Exception:
                    pass
                # Optical alignment compensation for script typefaces
                optical_offset_y = 0.0
                try:
                    from core.font_catalog import is_script_font
                    if is_script_font(hero_requested_font):
                        optical_offset_y = 0.003
                except Exception:
                    pass
                if "horizontal_anchor" in style:
                    h_anchor = float(style["horizontal_anchor"])
                    hero_tool.SetInput("HorizontalLeftCenterRight", h_anchor)
                    hero_tool.SetInput("HorizontalJustificationNew", h_anchor)
                if "vertical_anchor" in style:
                    hero_tool.SetInput("VerticalTopCenterBottom", float(style["vertical_anchor"]))
                hero_tool.SetInput("Center", [cx, hero_center_y + optical_offset_y])

                accent = style.get("accent_color", [1.0, 0.85, 0.0, 1.0])
                hero_tool.SetInput("Red1", float(accent[0]))
                hero_tool.SetInput("Green1", float(accent[1]))
                hero_tool.SetInput("Blue1", float(accent[2]))
                hero_tool.SetInput("Alpha1", float(accent[3]) if len(accent) > 3 else 1.0)

                h_stroke = style.get("hero_stroke_enabled", style.get("stroke_enabled", False))
                if h_stroke:
                    hero_tool.SetInput("Enabled2", 1)
                    sc = style.get("hero_stroke_color", style.get("stroke_color", [0.0, 0.0, 0.0, 1.0]))
                    hero_tool.SetInput("Red2", float(sc[0]))
                    hero_tool.SetInput("Green2", float(sc[1]))
                    hero_tool.SetInput("Blue2", float(sc[2]))
                    hero_tool.SetInput("Alpha2", float(sc[3]) if len(sc) > 3 else 1.0)
                    th = float(style.get("hero_stroke_thickness", style.get("stroke_thickness", 0.03))) * scale_h
                    hero_tool.SetInput("Thickness2", float(th))
                else:
                    hero_tool.SetInput("Enabled2", 0)

                h_shadow = style.get("hero_shadow_enabled", style.get("shadow_enabled", False))
                if h_shadow:
                    hero_tool.SetInput("Enabled3", 1)
                    shc = style.get("hero_shadow_color", style.get("shadow_color", [0.0, 0.0, 0.0, 0.50]))
                    hero_tool.SetInput("Red3", float(shc[0]))
                    hero_tool.SetInput("Green3", float(shc[1]))
                    hero_tool.SetInput("Blue3", float(shc[2]))
                    hero_tool.SetInput("Alpha3", float(shc[3]) if len(shc) > 3 else 0.50)
                    soft = float(style.get("hero_shadow_softness", style.get("shadow_softness", 0.045)))
                    hero_tool.SetInput("Softness3", soft)
                    hero_tool.SetInput("SoftnessX3", soft)
                    hero_tool.SetInput("SoftnessY3", soft)
                    off = style.get("hero_shadow_offset", style.get("shadow_offset", [0.0, 0.0]))
                    hero_tool.SetInput("Offset3", off)
                else:
                    hero_tool.SetInput("Enabled3", 0)

            elif comp:
                # A clip can retain a hero merge from an earlier two-color
                # style application. Restore the plain Text+ route and clear
                # that old layer so changing presets cannot leave ghost text.
                hero_tool = comp.FindTool("HeroText")
                merge = comp.FindTool("MR_TextMerge")
                mr_trans = comp.FindTool("MR_Transform")
                media_out = comp.FindTool("MediaOut1")
                if not media_out:
                    for t in comp.GetToolList().values():
                        if t.GetAttrs().get("TOOLS_RegID") == "MediaOutput":
                            media_out = t
                            break

                if hero_tool:
                    hero_tool.SetInput("StyledText", "")
                if mr_trans:
                    mr_trans.Input.ConnectTo(tool.Output)
                elif media_out:
                    media_out.Input.ConnectTo(tool.Output)
                if merge and hasattr(merge, "Background"):
                    try:
                        merge.Background.ConnectTo(tool.Output)
                    except Exception:
                        pass
                if hero_tool:
                    hero_tool.Delete()
                if merge:
                    merge.Delete()
            # 3. Main Fill Color
            c = style.get("color", [1.0, 1.0, 1.0, 1.0])
            tool.SetInput("Red1", float(c[0]))
            tool.SetInput("Green1", float(c[1]))
            tool.SetInput("Blue1", float(c[2]))
            tool.SetInput("Alpha1", float(c[3]) if len(c) > 3 else 1.0)

            # Glow
            if style.get("glow_enabled", False):
                glow = float(style.get("glow_amount", 0.5))
                tool.SetInput("SoftnessGlow1", glow)
                tool.SetInput("Softness1", 0.01)
            else:
                tool.SetInput("SoftnessGlow1", 0.0)
                tool.SetInput("Softness1", 0.0)

            # 4. Stroke / Outline
            if style.get("stroke_enabled", False):
                tool.SetInput("Enabled2", 1)
                sc = style.get("stroke_color", [0.0, 0.0, 0.0, 1.0])
                tool.SetInput("Red2", float(sc[0]))
                tool.SetInput("Green2", float(sc[1]))
                tool.SetInput("Blue2", float(sc[2]))
                tool.SetInput("Alpha2", float(sc[3]) if len(sc) > 3 else 1.0)
                tool.SetInput("Thickness2", float(style.get("stroke_thickness", 0.03)) * scale_h)
            else:
                tool.SetInput("Enabled2", 0)

            # 5. Drop Shadow
            if style.get("shadow_enabled", False):
                tool.SetInput("Enabled3", 1)
                shc = style.get("shadow_color", [0.0, 0.0, 0.0, 0.8])
                tool.SetInput("Red3", float(shc[0]))
                tool.SetInput("Green3", float(shc[1]))
                tool.SetInput("Blue3", float(shc[2]))
                tool.SetInput("Alpha3", float(shc[3]) if len(shc) > 3 else 0.8)
                soft = float(style.get("shadow_softness", 0.02))
                tool.SetInput("Softness3", soft)
                tool.SetInput("SoftnessX3", soft)
                tool.SetInput("SoftnessY3", soft)
                offset = style.get("shadow_offset", [0.006, -0.006])
                tool.SetInput("Offset3", offset)
            else:
                tool.SetInput("Enabled3", 0)

            # 6. Background Box
            if style.get("box_enabled", False):
                tool.SetInput("Enabled4", 1)
                bc = style.get("box_color", [0.95, 0.25, 0.15, 0.85])
                tool.SetInput("Red4", float(bc[0]))
                tool.SetInput("Green4", float(bc[1]))
                tool.SetInput("Blue4", float(bc[2]))
                tool.SetInput("Alpha4", float(bc[3]) if len(bc) > 3 else 0.85)
                base_ext_x = float(style.get("box_extend_x", 0.04))
                base_ext_y = float(style.get("box_extend_y", 0.025))
                if is_vertical:
                    ext_x = base_ext_x * 1.35
                    ext_y = base_ext_y * scale_h * 1.15
                    round_r = float(style.get("box_round", 0.25)) * 0.85
                elif is_square:
                    ext_x = base_ext_x * 1.10
                    ext_y = base_ext_y * scale_h
                    round_r = float(style.get("box_round", 0.25))
                else:
                    ext_x = base_ext_x
                    ext_y = base_ext_y
                    round_r = float(style.get("box_round", 0.25))
                tool.SetInput("ExtendHorizontal4", ext_x)
                tool.SetInput("ExtendVertical4", ext_y)
                tool.SetInput("Round4", round_r)
                # Shading Element 4 Level: 0 = Text (single unified card for all lines), 1 = Line, 2 = Word, 3 = Character
                box_level = int(style.get("box_level", 0))
                tool.SetInput("Level4", box_level)
            else:
                tool.SetInput("Enabled4", 0)

            return True
        except Exception as e:
            print(f"[CaptionForge] Error applying style: {e}")
            return False

    def extract_style_from_clip(self, timeline_item):
        tool = self.get_template_tool(timeline_item)
        if not tool:
            return None

        style = dict(self.DEFAULT_STYLE)
        try:
            txt = tool.GetInput("StyledText")
            if txt is not None:
                style["text"] = str(txt)
            f = tool.GetInput("Font")
            if f:
                style["font"] = str(f)
            s = tool.GetInput("Style")
            if s:
                style["style"] = str(s)
            sz = tool.GetInput("Size")
            if sz is not None:
                style["size"] = float(sz)

            cnt = tool.GetInput("Center")
            if cnt and isinstance(cnt, dict):
                style["center_x"] = float(cnt.get("1", 0.5))
                style["center_y"] = float(cnt.get("2", 0.5))

            # Alignment
            h_align = tool.GetInput("HorizontalLeftCenterRight")
            if h_align is not None:
                style["horizontal_anchor"] = float(h_align)
            v_align = tool.GetInput("VerticalTopCenterBottom")
            if v_align is not None:
                style["vertical_anchor"] = float(v_align)

            # Tracking & Line spacing
            track = tool.GetInput("CharacterSpacingClone")
            if track is not None:
                style["character_spacing"] = float(track)
            l_space = tool.GetInput("LineSpacingClone")
            if l_space is not None:
                style["line_spacing"] = float(l_space)

            # Main Fill Color
            r = tool.GetInput("Red1")
            g = tool.GetInput("Green1")
            b = tool.GetInput("Blue1")
            a = tool.GetInput("Alpha1")
            style["color"] = [
                float(r) if r is not None else 1.0,
                float(g) if g is not None else 1.0,
                float(b) if b is not None else 1.0,
                float(a) if a is not None else 1.0,
            ]

            # Preserve generated two-color titles when duplicating or copying style.
            if timeline_item.GetFusionCompCount() > 0:
                comp = timeline_item.GetFusionCompByIndex(1)
                hero = comp.FindTool("HeroText") if comp else None
                if hero:
                    base_lines = str(style.get("text", "")).split("\n")
                    hero_lines = str(hero.GetInput("StyledText") or "").split("\n")
                    merged_lines = []
                    hero_line = None
                    for i in range(max(len(base_lines), len(hero_lines))):
                        base_line = base_lines[i] if i < len(base_lines) else ""
                        hero_line_text = hero_lines[i] if i < len(hero_lines) else ""
                        if hero_line_text.strip():
                            hero_line = hero_line_text.strip()
                            merged_lines.append(hero_line_text)
                        else:
                            merged_lines.append(base_line)
                    style["text"] = "\n".join(merged_lines)
                    style["use_2color"] = hero_line is not None
                    style["main_word"] = hero_line
                    style["accent_color"] = [
                        float(hero.GetInput("Red1") if hero.GetInput("Red1") is not None else 1.0),
                        float(hero.GetInput("Green1") if hero.GetInput("Green1") is not None else 0.85),
                        float(hero.GetInput("Blue1") if hero.GetInput("Blue1") is not None else 0.0),
                        float(hero.GetInput("Alpha1") if hero.GetInput("Alpha1") is not None else 1.0),
                    ]

                    hf = hero.GetInput("Font")
                    if hf:
                        style["hero_font"] = str(hf)
                    hs = hero.GetInput("Style")
                    if hs:
                        style["hero_style"] = str(hs)

                    h_sz = hero.GetInput("Size")
                    base_sz = style.get("size")
                    if h_sz is not None and base_sz:
                        try:
                            mult = round(float(h_sz) / float(base_sz), 2)
                            if mult > 1.01:
                                style["hero_size_multiplier"] = mult
                        except Exception:
                            pass

                    h_stroke = hero.GetInput("Enabled2")
                    if h_stroke is not None and float(h_stroke) > 0.5:
                        style["hero_stroke_enabled"] = True
                        th2 = hero.GetInput("Thickness2")
                        if th2 is not None:
                            style["hero_stroke_thickness"] = float(th2)
                        style["hero_stroke_color"] = [
                            float(hero.GetInput("Red2") if hero.GetInput("Red2") is not None else 0.0),
                            float(hero.GetInput("Green2") if hero.GetInput("Green2") is not None else 0.0),
                            float(hero.GetInput("Blue2") if hero.GetInput("Blue2") is not None else 0.0),
                            float(hero.GetInput("Alpha2") if hero.GetInput("Alpha2") is not None else 1.0),
                        ]

                    h_shadow = hero.GetInput("Enabled3")
                    if h_shadow is not None and float(h_shadow) > 0.5:
                        style["hero_shadow_enabled"] = True
                        soft3 = hero.GetInput("Softness3")
                        if soft3 is not None:
                            style["hero_shadow_softness"] = float(soft3)
                        off3 = hero.GetInput("Offset3")
                        if off3 and isinstance(off3, dict):
                            style["hero_shadow_offset"] = [float(off3.get("1", 0.006)), float(off3.get("2", -0.006))]
                        elif isinstance(off3, (list, tuple)) and len(off3) >= 2:
                            style["hero_shadow_offset"] = [float(off3[0]), float(off3[1])]
                        style["hero_shadow_color"] = [
                            float(hero.GetInput("Red3") if hero.GetInput("Red3") is not None else 0.0),
                            float(hero.GetInput("Green3") if hero.GetInput("Green3") is not None else 0.0),
                            float(hero.GetInput("Blue3") if hero.GetInput("Blue3") is not None else 0.0),
                            float(hero.GetInput("Alpha3") if hero.GetInput("Alpha3") is not None else 0.8),
                        ]

            # Glow
            sg = tool.GetInput("SoftnessGlow1")
            if sg is not None and float(sg) > 0.01:
                style["glow_enabled"] = True
                style["glow_amount"] = float(sg)
            else:
                style["glow_enabled"] = False

            def _is_enabled(val):
                if val is None:
                    return False
                try:
                    return float(val) > 0
                except (TypeError, ValueError):
                    return False

            # Stroke (Element 2)
            en2 = tool.GetInput("Enabled2")
            style["stroke_enabled"] = _is_enabled(en2)
            if style["stroke_enabled"]:
                style["stroke_thickness"] = float(tool.GetInput("Thickness2") or 0.03)
                r2 = tool.GetInput("Red2")
                g2 = tool.GetInput("Green2")
                b2 = tool.GetInput("Blue2")
                a2 = tool.GetInput("Alpha2")
                style["stroke_color"] = [
                    float(r2) if r2 is not None else 0.0,
                    float(g2) if g2 is not None else 0.0,
                    float(b2) if b2 is not None else 0.0,
                    float(a2) if a2 is not None else 1.0,
                ]

            # Drop Shadow (Element 3)
            en3 = tool.GetInput("Enabled3")
            style["shadow_enabled"] = _is_enabled(en3)
            if style["shadow_enabled"]:
                r3 = tool.GetInput("Red3")
                g3 = tool.GetInput("Green3")
                b3 = tool.GetInput("Blue3")
                a3 = tool.GetInput("Alpha3")
                style["shadow_color"] = [
                    float(r3) if r3 is not None else 0.0,
                    float(g3) if g3 is not None else 0.0,
                    float(b3) if b3 is not None else 0.0,
                    float(a3) if a3 is not None else 0.8,
                ]
                soft = tool.GetInput("Softness3") or tool.GetInput("SoftnessX3")
                if soft is not None:
                    style["shadow_softness"] = float(soft)
                off = tool.GetInput("Offset3")
                if isinstance(off, dict):
                    style["shadow_offset"] = [float(off.get("1", 0.006)), float(off.get("2", -0.006))]
                elif isinstance(off, (list, tuple)) and len(off) >= 2:
                    style["shadow_offset"] = [float(off[0]), float(off[1])]

            # Background Box (Element 4)
            en4 = tool.GetInput("Enabled4")
            style["box_enabled"] = _is_enabled(en4)
            if style["box_enabled"]:
                r4 = tool.GetInput("Red4")
                g4 = tool.GetInput("Green4")
                b4 = tool.GetInput("Blue4")
                a4 = tool.GetInput("Alpha4")
                style["box_color"] = [
                    float(r4) if r4 is not None else 0.95,
                    float(g4) if g4 is not None else 0.25,
                    float(b4) if b4 is not None else 0.15,
                    float(a4) if a4 is not None else 0.85,
                ]
                eh = tool.GetInput("ExtendHorizontal4")
                if eh is not None:
                    style["box_extend_x"] = float(eh)
                ev = tool.GetInput("ExtendVertical4")
                if ev is not None:
                    style["box_extend_y"] = float(ev)
                rnd = tool.GetInput("Round4")
                if rnd is not None:
                    style["box_round"] = float(rnd)

            return style
        except Exception as e:
            print(f"[CaptionForge] Error extracting style: {e}")
            return None

    def copy_clip_attributes(self, timeline_item):
        """Copy attributes from a timeline clip into clipboard."""
        style = self.extract_style_from_clip(timeline_item)
        if style:
            self._clipboard = style
            return True
        return False

    def paste_clip_attributes(self, target_items, scope="all"):
        """
        Paste attributes onto target items.
        scope can be: 'all', 'look', 'font'
        """
        if not self._clipboard or not target_items:
            return 0

        count = 0
        for item in target_items:
            tools = self.get_text_layers(item)
            if not tools:
                continue

            try:
                for index, tool in enumerate(tools):
                    if scope in ("all", "font"):
                        tool.SetInput("Font", str(self._clipboard.get("font", "Avenir Next Condensed")))
                        tool.SetInput("Style", str(self._clipboard.get("style", "Regular")))
                        tool.SetInput("Size", float(self._clipboard.get("size", 0.082)))

                    if scope in ("all", "look"):
                        base_color = self._clipboard.get("color", [1.0, 1.0, 1.0, 1.0])
                        c = self._clipboard.get("accent_color", base_color) if index == 1 else base_color
                        for channel, value in zip(("Red1", "Green1", "Blue1", "Alpha1"), c):
                            tool.SetInput(channel, float(value))

                        if self._clipboard.get("stroke_enabled"):
                            sc = self._clipboard.get("stroke_color", [0.0, 0.0, 0.0, 1.0])
                            tool.SetInput("Enabled2", 1)
                            tool.SetInput("Thickness2", float(self._clipboard.get("stroke_thickness", 0.03)))
                            for channel, value in zip(("Red2", "Green2", "Blue2", "Alpha2"), sc):
                                tool.SetInput(channel, float(value))
                        else:
                            tool.SetInput("Enabled2", 0)

                        if self._clipboard.get("shadow_enabled"):
                            sh = self._clipboard.get("shadow_color", [0.0, 0.0, 0.0, 0.8])
                            tool.SetInput("Enabled3", 1)
                            for channel, value in zip(("Red3", "Green3", "Blue3", "Alpha3"), sh):
                                tool.SetInput(channel, float(value))
                            tool.SetInput("Softness3", float(self._clipboard.get("shadow_softness", 0.02)))
                            tool.SetInput("Offset3", self._clipboard.get("shadow_offset", [0.006, -0.006]))
                        else:
                            tool.SetInput("Enabled3", 0)

                        if index == 0:
                            if self._clipboard.get("box_enabled"):
                                box = self._clipboard.get("box_color", [0.95, 0.25, 0.15, 0.85])
                                tool.SetInput("Enabled4", 1)
                                for channel, value in zip(("Red4", "Green4", "Blue4", "Alpha4"), box):
                                    tool.SetInput(channel, float(value))
                                tool.SetInput("ExtendHorizontal4", float(self._clipboard.get("box_extend_x", 0.04)))
                                tool.SetInput("ExtendVertical4", float(self._clipboard.get("box_extend_y", 0.025)))
                                tool.SetInput("Round4", float(self._clipboard.get("box_round", 0.25)))
                            else:
                                tool.SetInput("Enabled4", 0)

                count += 1
            except Exception:
                pass

        return count

    def apply_layout_template(self, text, template_num=1, main_word=None, hero_font=None, preserve_case=False):
        """
        Applies Template 1, 2, or 3 layout to text:
        - Template 1: Hero Word (Hero word stacked prominently)
        - Template 2: 2-line layout
        - Template 3: 3-line layout
        """
        words = text.replace("\n", " ").split()
        if not words:
            return text

        if template_num == 1:
            if not main_word and len(words) > 1:
                # Default hero word to the longest/accent word
                main_word = max(words, key=len)

            if main_word:
                target_words = [w.strip(".,!?").lower() for w in str(main_word).split() if w.strip(".,!?")]
                match_start = next((i for i in range(len(words) - len(target_words) + 1)
                                    if [w.strip(".,!?").lower() for w in words[i:i + len(target_words)]] == target_words), None) if target_words else None
                if match_start is None:
                    # Preset hero words can differ from an existing clip's caption.
                    # Fall back to a word already present; never inject sample copy.
                    main_word = max(words, key=len)
                    target_words = [main_word.strip(".,!?").lower()]
                    match_start = next(i for i, word in enumerate(words) if word.strip(".,!?").lower() == target_words[0])
                # Give the selected word or phrase its own line for color and size hierarchy.
                hero_words = words[match_start:match_start + len(target_words)]
                after = words[match_start + len(target_words):]
                before = words[:match_start]

                from core.font_catalog import is_script_font
                if is_script_font(hero_font) or preserve_case:
                    # Never force uppercase on cursive / script typefaces
                    hero_raw = " ".join(hero_words)
                    hero = hero_raw.title() if hero_raw.isupper() else hero_raw
                else:
                    hero = " ".join(hero_words).upper()

                lines = []
                if before:
                    lines.append(" ".join(before))
                lines.append(hero)
                if after:
                    lines.append(" ".join(after))
                return "\n".join(lines)
            return " ".join(words)

        elif template_num == 2:
            line_count = min(2, len(words))
            base, remainder = divmod(len(words), line_count)
            lines = []
            cursor = 0
            for index in range(line_count):
                count = base + (1 if index < remainder else 0)
                lines.append(" ".join(words[cursor:cursor + count]))
                cursor += count
            return "\n".join(lines)

        elif template_num == 3:
            line_count = min(3, len(words))
            base, remainder = divmod(len(words), line_count)
            lines = []
            cursor = 0
            for index in range(line_count):
                count = base + (1 if index < remainder else 0)
                lines.append(" ".join(words[cursor:cursor + count]))
                cursor += count
            return "\n".join(lines)

        return " ".join(words)
