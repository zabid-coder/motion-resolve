"""
Motion Resolve - Template Canvas Area (PyQt6)
Renders declarative typography template layers with 60fps scrubbable timeline,
playback phase lifecycle (Entrance 0.0-0.35, Hold 0.35-0.75, Exit 0.75-1.0),
and live dynamic layer transformations.
"""

from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QFrame
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QFontMetricsF

from core.templates.schema import TemplateSpec, LayerType, ParameterType
from core.templates.motion_tokens import evaluate_easing
from core.templates.theme_tokens import get_theme
from core.templates.bengali_engine import (
    contains_bengali, get_optical_scale, to_bengali_numerals
)


class TemplateCanvasArea(QFrame):
    """Drawing area for animated template layers at playback phase (0.0 - 1.0) or time t."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(240)
        self.setStyleSheet("""
            QFrame {
                background-color: #0a0814;
                border: 1px solid #231b38;
                border-radius: 10px;
            }
        """)
        self.template: Optional[TemplateSpec] = None
        self.params: Dict[str, Any] = {}
        self.theme: Dict[str, Any] = get_theme("mono")
        self.current_time: float = 0.8
        self.playback_phase: float = 0.0
        self.last_mask_rect: Optional[QRectF] = None
        self.last_text_dy: float = 0.0

    def set_playback_phase(self, phase: float):
        """Set normalized playback phase in range [0.0, 1.0] and update canvas."""
        self.playback_phase = max(0.0, min(1.0, float(phase)))
        total_dur = max(0.1, self.template.duration_default if self.template else 3.0)
        in_dur = max(0.1, self.template.in_duration if self.template else 0.5)
        out_dur = max(0.1, self.template.out_duration if self.template else 0.5)
        hold_end = max(in_dur, total_dur - out_dur)

        if self.playback_phase <= 0.35:
            self.current_time = (self.playback_phase / 0.35) * in_dur
        elif self.playback_phase >= 0.75:
            p = (self.playback_phase - 0.75) / 0.25
            self.current_time = hold_end + p * out_dur
        else:
            p = (self.playback_phase - 0.35) / 0.40
            self.current_time = in_dur + p * max(0.01, hold_end - in_dur)
        self.update()

    def set_state(self, template: Optional[TemplateSpec], params: Dict[str, Any], theme: Dict[str, Any], t_sec: float):
        """Update template, params, theme, and time, calculating matching playback_phase."""
        self.template = template
        self.params = params
        self.theme = theme
        self.current_time = float(t_sec)

        total_dur = max(0.1, template.duration_default if template else 3.0)
        in_dur = max(0.1, template.in_duration if template else 0.5)
        out_dur = max(0.1, template.out_duration if template else 0.5)
        hold_end = max(in_dur, total_dur - out_dur)

        if self.current_time <= in_dur:
            progress = max(0.0, min(1.0, self.current_time / in_dur))
            self.playback_phase = progress * 0.35
        elif self.current_time >= hold_end:
            progress = max(0.0, min(1.0, (self.current_time - hold_end) / out_dur))
            self.playback_phase = 0.75 + progress * 0.25
        else:
            span = max(0.01, hold_end - in_dur)
            progress = max(0.0, min(1.0, (self.current_time - in_dur) / span))
            self.playback_phase = 0.35 + progress * 0.40

        self.playback_phase = max(0.0, min(1.0, self.playback_phase))
        self.update()

    def _resolve_val(self, val: Any) -> Any:
        if isinstance(val, str):
            if val.startswith("param:"):
                pid = val[6:]
                if pid in self.params:
                    return self.params[pid]
                if self.template and hasattr(self.template, "parameters") and self.template.parameters:
                    for p in self.template.parameters:
                        if getattr(p, "id", None) == pid:
                            return p.default
                return self.params.get(pid, val)
            elif val.startswith("$"):
                pid = val[1:]
                if pid in self.params:
                    return self.params[pid]
                if self.template and hasattr(self.template, "parameters") and self.template.parameters:
                    for p in self.template.parameters:
                        if getattr(p, "id", None) == pid:
                            return p.default
                return self.params.get(pid, val)
            elif val.startswith("token:"):
                tid = val[6:]
                return self.theme.get(tid, [1.0, 1.0, 1.0, 1.0])
        return val

    def _layer_center_px(self, layer, w, h, default_x, default_y):
        props = layer.props if layer else {}
        try:
            x = float(self._resolve_val(props.get("center_x", default_x / max(1, w))))
        except (TypeError, ValueError):
            x = default_x / max(1, w)
        try:
            y_norm = float(self._resolve_val(props.get("center_y", 1.0 - default_y / max(1, h))))
        except (TypeError, ValueError):
            y_norm = 1.0 - default_y / max(1, h)
        try:
            y_norm += float(self._resolve_val(props.get("offset_y", 0.0)))
        except (TypeError, ValueError):
            pass
        return w * max(0.0, min(1.0, x)), h * (1.0 - max(0.0, min(1.0, y_norm)))

    def _layer_text_rect(self, layer, w, h, default_x, default_y, rect_height):
        props = layer.props if layer else {}
        cx, cy = self._layer_center_px(layer, w, h, default_x, default_y)
        rect_width = w * max(0.15, min(0.95, float(props.get("text_width", 0.9))))
        alignment = str(props.get("alignment", "center")).lower()
        if alignment == "left":
            left = cx
        elif alignment == "right":
            left = cx - rect_width
        else:
            left = cx - rect_width * 0.5
        return QRectF(left, cy - rect_height * 0.5, rect_width, rect_height), alignment

    def _layer_color(self, layer, fallback_token):
        raw = layer.props.get("color", f"token:{fallback_token}") if layer else f"token:{fallback_token}"
        value = self._resolve_val(raw)
        if not isinstance(value, (list, tuple)) or len(value) < 3:
            value = self.theme.get(fallback_token, [0.95, 0.93, 0.90, 1.0])
        rgba = list(value[:4])
        while len(rgba) < 4:
            rgba.append(1.0)
        return QColor(*(int(max(0.0, min(1.0, float(c))) * 255) for c in rgba[:3]), int(max(0.0, min(1.0, float(rgba[3]))) * 255))

    def _layer_font_name(self, layer, fallback, purpose="display"):
        from core.font_catalog import resolve_available_font, is_script_font
        requested = self._resolve_val(layer.props.get("font", fallback)) if layer else fallback
        if is_script_font(requested):
            purpose = "script"
        elif str(requested).lower() in {"baskerville", "didot", "bodoni", "bodoni 72", "georgia", "dm serif display", "instrument serif", "playfair display"}:
            purpose = "editorial"
        return resolve_available_font(requested, purpose)

    def _layer_style_color(self, layer, key, default):
        """Resolve an optional styling color prop (shadow/glow/stroke color)."""
        raw = layer.props.get(key) if layer else None
        if raw is None:
            return QColor(default)
        value = self._resolve_val(raw)
        if isinstance(value, str):
            return QColor(value)
        if isinstance(value, (list, tuple)) and len(value) >= 3:
            rgba = list(value[:4])
            while len(rgba) < 4:
                rgba.append(1.0)
            return QColor(*(int(max(0.0, min(1.0, float(c))) * 255) for c in rgba[:3]),
                          int(max(0.0, min(1.0, float(rgba[3]))) * 255))
        return QColor(default)

    def _draw_styled_text(self, painter, layer, rect, align_flag, text, base_color, preview_scale=1.0):
        """
        Professional WYSIWYG text renderer honoring authored depth props on the layer:
          - shadow: {"offset_x": px@1080, "offset_y": ..., "blur": ..., "color": [r,g,b,a] or "#hex"}
          - stroke / outline: {"width": px@1080, "color": ...} or stroke_color prop
          - glow: {"radius": px@1080, "color": ..., "intensity": 0..1}
        Falls back to a subtle soft drop shadow so every template renders with depth.
        """
        props = layer.props if layer else {}
        s = max(0.4, preview_scale)

        # --- Glow (drawn first, behind everything) ---
        glow = props.get("glow")
        if isinstance(glow, dict) and glow:
            radius = float(glow.get("radius", glow.get("size", 6.0))) * s
            intensity = max(0.05, min(1.0, float(glow.get("intensity", 0.55))))
            glow_color = self._layer_style_color(layer, "glow_color", "#ffffff")
            steps = max(3, min(8, int(radius // 1.5) + 3))
            painter.save()
            for i in range(steps, 0, -1):
                alpha = int(255 * intensity * (1.0 - i / (steps + 1)) * 0.5)
                pen = QPen(QColor(glow_color.red(), glow_color.green(), glow_color.blue(), max(8, alpha)))
                pen.setWidthF(max(1.0, (radius / steps) * i * 1.6))
                painter.setPen(pen)
                painter.drawText(rect, align_flag, text)
            painter.restore()

        # --- Drop shadow (360° ambient diffusion approximation) ---
        shadow = props.get("shadow")
        if isinstance(shadow, dict) and shadow:
            ox = float(shadow.get("offset_x", 0.0)) * s
            oy = float(shadow.get("offset_y", 2.5)) * s
            blur = max(0.0, float(shadow.get("blur", 3.0))) * s
            shadow_color = self._layer_style_color(layer, "shadow_color", "#000000")
            base_alpha = float(shadow.get("opacity", shadow_color.alpha() / 255.0))
            steps = max(1, int(round(blur / 1.5)))
            painter.save()
            for i in range(steps, -1, -1):
                frac = i / steps if steps else 0.0
                alpha = int(max(0.0, min(1.0, base_alpha * (1.0 - frac * 0.75))) * 255)
                painter.setPen(QColor(shadow_color.red(), shadow_color.green(), shadow_color.blue(), alpha))
                painter.drawText(QRectF(rect.x() + ox + frac * blur * 0.35,
                                        rect.y() + oy + frac * blur * 0.35,
                                        rect.width(), rect.height()), align_flag, text)
            painter.restore()
        elif shadow is None:
            # Default professional soft shadow when nothing authored
            painter.save()
            painter.setPen(QColor(0, 0, 0, 120))
            painter.drawText(QRectF(rect.x() + 1.2 * s, rect.y() + 1.6 * s, rect.width(), rect.height()),
                             align_flag, text)
            painter.restore()

        # --- Stroke / outline under fill ---
        stroke = props.get("stroke") if isinstance(props.get("stroke"), dict) else None
        stroke_width = float((stroke or {}).get("width", props.get("stroke_width", props.get("outline_width", 0.0))))
        stroke_raw = (stroke or {}).get("color") or props.get("stroke_color") or props.get("outline_color")
        if stroke_width > 0.01 and stroke_raw is not None:
            if isinstance(stroke_raw, dict):
                stroke_color = QColor(str(stroke_raw.get("color", "#000000")))
            else:
                resolved = self._resolve_val(stroke_raw)
                if isinstance(resolved, str):
                    stroke_color = QColor(resolved)
                elif isinstance(resolved, (list, tuple)) and len(resolved) >= 3:
                    rgba = list(resolved[:4])
                    while len(rgba) < 4:
                        rgba.append(1.0)
                    stroke_color = QColor(*(int(max(0.0, min(1.0, float(c))) * 255) for c in rgba[:3]),
                                          int(max(0.0, min(1.0, float(rgba[3]))) * 255))
                else:
                    stroke_color = QColor("#000000")
            pen = QPen(stroke_color)
            pen.setWidthF(max(0.8, stroke_width * s * 2.0))
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.save()
            painter.setPen(pen)
            painter.drawText(rect, align_flag, text)
            painter.restore()

        # --- Fill pass ---
        painter.setPen(base_color)
        painter.drawText(rect, align_flag, text)

    @staticmethod
    def _sample_keyframes(keyframes, phase_time, default_value=0.0):
        if not keyframes:
            return float(default_value)
        if phase_time <= float(keyframes[0].time):
            return float(keyframes[0].value)
        if phase_time >= float(keyframes[-1].time):
            return float(keyframes[-1].value)
        for first, second in zip(keyframes, keyframes[1:]):
            if float(first.time) <= phase_time <= float(second.time):
                span = float(second.time) - float(first.time)
                if span <= 0:
                    return float(second.value)
                fraction = (phase_time - float(first.time)) / span
                easing = second.easing.value if hasattr(second.easing, "value") else str(second.easing)
                fraction = evaluate_easing(easing, fraction)
                return float(first.value) + (float(second.value) - float(first.value)) * fraction
        return float(default_value)

    def _layer_motion_state(self, layer):
        """Evaluate authored motion for one layer at the current preview time."""
        state = {"opacity": 1.0, "translate_x": 0.0, "translate_y": 0.0,
                 "scale": 1.0, "scale_x": 1.0, "scale_y": 1.0}
        if not layer or not getattr(layer, "motion_tracks", None):
            return state

        in_dur = max(0.01, getattr(self.template, "in_duration", 0.5))
        out_dur = max(0.01, getattr(self.template, "out_duration", 0.5))
        total_dur = max(in_dur + out_dur, getattr(self.template, "duration_default", 3.0))
        out_start = max(in_dur, total_dur - out_dur)
        t = max(0.0, min(total_dur, self.current_time))

        tracks_by_property = {}
        for track in layer.motion_tracks:
            if track.keyframes:
                tracks_by_property.setdefault(str(track.property).lower(), {})[str(track.phase).lower()] = track.keyframes

        for prop, phases in tracks_by_property.items():
            in_keys, hold_keys, out_keys = phases.get("in"), phases.get("hold"), phases.get("out")
            if t < in_dur and in_keys:
                value = self._sample_keyframes(in_keys, t, state.get(prop, 1.0))
            elif t >= out_start and out_keys:
                value = self._sample_keyframes(out_keys, min(out_dur, t - out_start), state.get(prop, 1.0))
            elif hold_keys:
                value = self._sample_keyframes(hold_keys, t - in_dur, state.get(prop, 1.0))
            elif in_keys:
                value = float(in_keys[-1].value)
            elif out_keys:
                value = float(out_keys[0].value)
            else:
                continue

            if prop in ("alpha", "opacity"):
                state["opacity"] = max(0.0, min(1.0, float(value)))
            elif prop == "size":
                state["scale"] = float(value)
            elif prop in state:
                state[prop] = float(value)

        return state

    @staticmethod
    def _apply_layer_transform(painter, state, center, width, height):
        """Apply a layer's own transform around its visual center."""
        dx = float(state.get("translate_x", 0.0))
        dy = float(state.get("translate_y", 0.0))
        dx = dx * width if abs(dx) <= 1.0 else dx
        dy = dy * height if abs(dy) <= 1.0 else dy
        sx = float(state.get("scale", 1.0)) * float(state.get("scale_x", 1.0))
        sy = float(state.get("scale", 1.0)) * float(state.get("scale_y", 1.0))
        painter.setOpacity(max(0.0, min(1.0, float(state.get("opacity", 1.0)))))
        painter.translate(center.x() + dx, center.y() - dy)
        painter.scale(sx, sy)
        painter.translate(-center.x(), -center.y())

    @staticmethod
    def _font_weight(layer, fallback=QFont.Weight.Medium):
        value = str(layer.props.get("weight", "") if layer else "").lower()
        if value in ("regular", "book", "roman", "normal"):
            return QFont.Weight.Normal
        if value in ("medium",):
            return QFont.Weight.Medium
        if value in ("demi", "demibold", "semibold"):
            return QFont.Weight.DemiBold
        if value in ("bold", "heavy", "extrabold", "black"):
            return QFont.Weight.Bold
        return fallback

    # ------------------------------------------------------------------
    # WYSIWYG rendering: the preview draws from the SAME scene resolver and
    # motion plan the Fusion compiler writes to DaVinci Resolve.
    # ------------------------------------------------------------------
    PREVIEW_FPS = 30.0

    def _preview_timing(self):
        from core.templates.motion_curves import plan_timing
        fps = self.PREVIEW_FPS
        total = max(0.5, float(getattr(self.template, "duration_default", 3.0) or 3.0))
        return plan_timing(self.template, int(round(total * fps)) - 1, fps, 1.0)

    @staticmethod
    def _qcolor(rgba, opacity=1.0):
        c = (list(rgba) + [1.0] * 4)[:4]
        return QColor(*(int(max(0.0, min(1.0, float(v))) * 255) for v in c[:3]),
                      int(max(0.0, min(1.0, float(c[3]) * opacity)) * 255))

    def paintEvent(self, event):
        QFrame.paintEvent(self, event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        w, h = float(self.width()), float(self.height())
        self.last_text_dy = 0.0

        if self.params.get("preview_guides", False):
            pen_guide = QPen(QColor(255, 255, 255, 38), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen_guide)
            painter.drawLine(int(w * 0.5), 0, int(w * 0.5), int(h))
            painter.drawLine(0, int(h * 0.5), int(w), int(h * 0.5))

        if not self.template:
            painter.setPen(QColor("#5d5677"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Select a template to preview")
            return

        from core.templates.scene import resolve_scene, resolve_params
        from core.templates.motion_curves import layer_channel_plan, evaluate_keys
        from core.font_catalog import resolve_available_font, infer_font_purpose

        def font_resolver(requested, purpose):
            p = purpose if purpose == "bengali" else infer_font_purpose(requested, purpose)
            return resolve_available_font(requested, p)

        params = resolve_params(self.template, self.params)
        scene, fit = resolve_scene(self.template, params, self.theme or {}, int(w), int(h), font_resolver)
        self._last_fit = fit
        timing = self._preview_timing()
        frame = max(0.0, min(timing["last_frame"], float(self.current_time) * self.PREVIEW_FPS))
        if not params.get("plate_enabled", True):
            scene = [l for l in scene if not l.is_plate]

        def ch(plan, name, rest):
            keys = plan.get(name)
            return evaluate_keys(keys, frame, rest) if keys else rest

        self.last_mask_rect = None
        ordered = sorted(scene, key=lambda l: (0 if l.is_plate else 1, l.index))
        for sl in ordered:
            if sl.kind == "shape" and sl.text_box:
                continue
            plan = layer_channel_plan(sl.spec, timing, 1.0)
            opacity = ch(plan, "opacity", 1.0)
            dx = fit.dx(ch(plan, "translate_x", 0.0)) * w
            dy = fit.dy(ch(plan, "translate_y", 0.0)) * h
            if sl.kind == "text":
                self.last_text_dy = max(self.last_text_dy, abs(dy), abs(dx))
            if sl.clip and self.last_mask_rect is None:
                band = (sl.line_h * 1.18 if sl.kind == "text" else sl.height * 1.02) * h
                self.last_mask_rect = QRectF(0.0, (1.0 - sl.cy) * h - band / 2.0, w, band)
            if opacity <= 0.001:
                continue
            scale = ch(plan, "scale", 1.0)
            painter.save()
            if sl.clip:
                band_h = (sl.line_h * 1.18 if sl.kind == "text" else sl.height * 1.02) * h
                clip_rect = QRectF(0.0, (1.0 - sl.cy) * h - band_h / 2.0, w, band_h)
                painter.setClipRect(clip_rect)
                if self.last_mask_rect is None:
                    self.last_mask_rect = clip_rect
            if sl.kind == "shape":
                self._paint_shape(painter, sl, plan, ch, opacity, dx, dy, scale, w, h)
            else:
                self._paint_text(painter, sl, plan, ch, opacity, dx, dy, scale, w, h)
            painter.restore()
        if self.last_mask_rect is None:
            self.last_mask_rect = QRectF(0.0, 0.0, w, h)
        painter.end()

    def _paint_shape(self, painter, sl, plan, ch, opacity, dx, dy, scale, w, h):
        sx = ch(plan, "scale_x", scale) if plan.get("scale_x") else scale
        sy = ch(plan, "scale_y", scale) if plan.get("scale_y") else scale
        bw, bh = sl.width * w, sl.height * h
        cw, chh = max(0.0, bw * sx), max(0.0, bh * sy)
        cx = sl.cx * w + dx
        cy = (1.0 - sl.cy) * h - dy
        if sl.origin == "left":
            cx -= (bw - cw) / 2.0
        elif sl.origin == "right":
            cx += (bw - cw) / 2.0
        elif sl.origin == "bottom":
            cy += (bh - chh) / 2.0
        elif sl.origin == "top":
            cy -= (bh - chh) / 2.0
        if cw < 0.5 or chh < 0.5:
            return
        rect = QRectF(cx - cw / 2.0, cy - chh / 2.0, cw, chh)
        radius = sl.corner * min(bw, bh) / 2.0
        radius = min(radius, cw / 2.0, chh / 2.0)
        painter.setOpacity(max(0.0, min(1.0, opacity)))
        if sl.border:
            px = max(1.0, float(sl.border.get("px", 1.0)) * w / 1920.0)
            painter.setPen(QPen(self._qcolor(sl.border["color"]), px))
        else:
            painter.setPen(Qt.PenStyle.NoPen)
        if sl.gradient:
            from PyQt6.QtGui import QLinearGradient
            grad = QLinearGradient(rect.left(), 0, rect.right(), 0)
            grad.setColorAt(0.0, self._qcolor(sl.gradient[0]))
            grad.setColorAt(1.0, self._qcolor(sl.gradient[1]))
            painter.setBrush(QBrush(grad))
        else:
            painter.setBrush(QBrush(self._qcolor(sl.color)))
        painter.drawRoundedRect(rect, radius, radius)

    def _paint_text(self, painter, sl, plan, ch, opacity, dx, dy, scale, w, h):
        if not sl.text:
            return
        if getattr(sl, "count", False):
            from core.templates.counter import parse_count, count_window, eased_progress
            spec = parse_count(sl.text)
            if spec is not None:
                timing = self._preview_timing()
                c0, c1 = count_window(plan, timing, sl.count_seconds)
                frame = float(self.current_time) * self.PREVIEW_FPS
                sl.text = spec.render(eased_progress(frame, c0, c1))
        blur = max(0.0, ch(plan, "blur", 0.0))
        tracking = ch(plan, "tracking", sl.tracking) if plan.get("tracking") else sl.tracking
        rotation = ch(plan, "rotation", 0.0)
        line_box_px = sl.size * w
        em_px = max(6, int(round(line_box_px / 1.2)))
        font = QFont(sl.font)
        font.setPixelSize(em_px)
        style = str(sl.style or "").lower()
        if "italic" in style or "oblique" in style:
            font.setItalic(True)
        weight_map = [("black", QFont.Weight.Black), ("heavy", QFont.Weight.Black), ("extrabold", QFont.Weight.ExtraBold),
                      ("bold", QFont.Weight.Bold), ("semi", QFont.Weight.DemiBold), ("demi", QFont.Weight.DemiBold),
                      ("medium", QFont.Weight.Medium), ("light", QFont.Weight.Light), ("thin", QFont.Weight.Thin)]
        weight = QFont.Weight.Normal
        for key, val in weight_map:
            if key in style.replace(" ", ""):
                weight = val
                break
        font.setWeight(weight)
        try:
            from core.font_catalog import resolve_font_style
            font.setStyleName(resolve_font_style(sl.style, sl.font))  # exact face, e.g. "Demi Bold"
        except Exception:
            pass
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, max(50.0, tracking * 100.0))
        painter.setFont(font)
        metrics = QFontMetricsF(font)
        lines = sl.text.split("\n")
        line_step = metrics.height() * max(0.6, sl.line_spacing)
        block_h = line_step * len(lines)
        text_w = max(metrics.horizontalAdvance(l) for l in lines) if lines else 0.0
        ax_px, ay_px = sl.cx * w, (1.0 - sl.cy) * h
        if sl.align < 0:
            left = ax_px
        elif sl.align > 0:
            left = ax_px - text_w
        else:
            left = ax_px - text_w / 2.0
        rect = QRectF(left, ay_px - block_h / 2.0, text_w, block_h)
        flag = {-1.0: Qt.AlignmentFlag.AlignLeft, 1.0: Qt.AlignmentFlag.AlignRight}.get(sl.align, Qt.AlignmentFlag.AlignHCenter)

        if sl.stagger and not getattr(sl, "count", False):
            self._paint_stagger(painter, sl, plan, font, metrics, lines, line_step, block_h, ax_px, ay_px, w, h)
            return

        painter.translate(ax_px + dx, ay_px - dy)
        painter.rotate(-rotation)
        painter.scale(scale, scale)
        painter.translate(-ax_px, -ay_px)
        # Approximate Fusion's blur-in: softer opacity while blurred.
        alpha = max(0.0, min(1.0, opacity / (1.0 + blur * 0.09)))
        painter.setOpacity(alpha)
        if sl.text_box and "color" in sl.text_box:
            pad_x = em_px * float(sl.text_box.get("pad_x", 0.35))
            pad_y = em_px * float(sl.text_box.get("pad_y", 0.12))
            box = rect.adjusted(-pad_x, -pad_y, pad_x, pad_y)
            r = min(box.height() / 2.0, em_px * float(sl.text_box.get("round", 0.35)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self._qcolor(sl.text_box["color"])))
            painter.drawRoundedRect(box, r, r)
        shadow = sl.shadow or {}
        if not shadow.get("off") and shadow.get("enabled", True):
            painter.setPen(QColor(0, 0, 0, int(255 * float(shadow.get("opacity", 0.38)) * 0.6)))
            painter.drawText(rect.translated(0, max(1.0, h * 0.003)), int(flag | Qt.AlignmentFlag.AlignVCenter), sl.text)
        if sl.stroke:
            sw = max(1.0, em_px * float(sl.stroke.get("width", 0.04)))
            painter.setPen(self._qcolor(sl.stroke["color"]))
            for ox, oy in ((sw, 0), (-sw, 0), (0, sw), (0, -sw)):
                painter.drawText(rect.translated(ox, oy), int(flag | Qt.AlignmentFlag.AlignVCenter), sl.text)
        painter.setPen(self._qcolor(sl.color))
        painter.drawText(rect, int(flag | Qt.AlignmentFlag.AlignVCenter), sl.text)

    def _paint_stagger(self, painter, sl, plan, font, metrics, lines, line_step, block_h, ax_px, ay_px, w, h):
        """Per-character cascade exactly like the Text+ Follower: character i
        plays the (exit-shifted) layer plan i*delay frames later."""
        from core.templates.motion_curves import stagger_delay, stagger_plan, evaluate_keys
        from core.templates.scene import resolve_scene  # noqa: F401 (fit lives on self)
        timing = self._preview_timing()
        delay = stagger_delay(sl.stagger, sl.text, timing)
        sp = stagger_plan(plan, sl.text, delay, timing)
        frame = float(self.current_time) * self.PREVIEW_FPS
        fit = getattr(self, "_last_fit", None)
        def val(name, f, rest):
            keys = sp.get(name)
            return evaluate_keys(keys, f, rest) if keys else rest
        idx = 0
        top = ay_px - block_h / 2.0
        for li, line in enumerate(lines):
            lw = metrics.horizontalAdvance(line)
            if sl.align < 0:
                x0 = ax_px
            elif sl.align > 0:
                x0 = ax_px - lw
            else:
                x0 = ax_px - lw / 2.0
            base_y = top + li * line_step + line_step / 2.0
            for ci, chr_ in enumerate(line):
                f = frame - idx * delay
                idx += 1
                op = max(0.0, min(1.0, val("opacity", f, 1.0)))
                blur = max(0.0, val("blur", f, 0.0))
                if op <= 0.001 or not chr_.strip():
                    continue
                cx = x0 + metrics.horizontalAdvance(line[:ci]) + metrics.horizontalAdvance(chr_) / 2.0
                tx = val("translate_x", f, 0.0)
                ty = val("translate_y", f, 0.0)
                if fit is not None:
                    tx, ty = fit.dx(tx) * w, fit.dy(ty) * h
                else:
                    tx, ty = tx * w, ty * h
                s = val("scale", f, 1.0)
                rot = val("rotation", f, 0.0)
                painter.save()
                painter.translate(cx + tx, base_y - ty)
                painter.rotate(-rot)
                painter.scale(s, s)
                painter.setOpacity(op / (1.0 + blur * 0.09))
                painter.setPen(self._qcolor(sl.color))
                r = QRectF(-metrics.horizontalAdvance(chr_), -line_step / 2.0, metrics.horizontalAdvance(chr_) * 2, line_step)
                painter.drawText(r, int(Qt.AlignmentFlag.AlignCenter), chr_)
                painter.restore()
