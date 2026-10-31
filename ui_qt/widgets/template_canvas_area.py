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
        from core.font_catalog import resolve_available_font
        requested = self._resolve_val(layer.props.get("font", fallback)) if layer else fallback
        return resolve_available_font(requested, purpose)

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

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = self.width()
        h = self.height()

        # Guides are useful while adjusting a layout, but should never contaminate
        # the artwork preview or its screenshots.
        if self.params.get("preview_guides", False):
            pen_guide = QPen(QColor(255, 255, 255, 38), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen_guide)
            painter.drawLine(int(w * 0.5), 0, int(w * 0.5), h)
            painter.drawLine(0, int(h * 0.5), w, int(h * 0.5))

        if not self.template:
            painter.setPen(QColor("#5d5677"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Select a template to preview")
            return

        in_dur = max(0.1, getattr(self.template, "in_duration", 0.5))
        out_dur = max(0.1, getattr(self.template, "out_duration", 0.5))
        total_dur = max(in_dur + out_dur, getattr(self.template, "duration_default", 3.0))

        pos_y_norm = float(self.params.get("pos_y", 0.28))
        pos_x_norm = float(self.params.get("pos_x", 0.5))
        center_x = w * pos_x_norm
        base_center_y = h * (1.0 - pos_y_norm)
        text_layers = [l for l in self.template.layers if l.type == LayerType.TEXT]
        line_layers = [l for l in self.template.layers if l.type == LayerType.SHAPE_LINE]
        box_layers = [l for l in self.template.layers if l.type in (LayerType.SHAPE_RECT, LayerType.SHAPE_PILL)]
        plate_layers = [l for l in box_layers if l.props.get("role") == "plate"]

        # Reveal mask calculation
        mask_top, mask_bottom = pos_y_norm - 0.08, pos_y_norm + 0.08
        for layer in text_layers:
            try:
                layer_y = float(self._resolve_val(layer.props.get("center_y", pos_y_norm)))
            except (TypeError, ValueError):
                layer_y = pos_y_norm
            try:
                layer_y += float(self._resolve_val(layer.props.get("offset_y", 0.0)))
            except (TypeError, ValueError):
                pass
            try:
                size = float(self._resolve_val(layer.props.get("size", 0.075)))
            except (TypeError, ValueError):
                size = 0.075
            mask_top = min(mask_top, layer_y - size * 0.75)
            mask_bottom = max(mask_bottom, layer_y + size * 0.75)
        for layer in box_layers:
            try:
                layer_y = float(self._resolve_val(layer.props.get("center_y", pos_y_norm)))
            except (TypeError, ValueError):
                layer_y = pos_y_norm
            try:
                layer_y += float(self._resolve_val(layer.props.get("offset_y", 0.0)))
            except (TypeError, ValueError):
                pass
            try:
                height = float(self._resolve_val(layer.props.get("height", 0.1)))
            except (TypeError, ValueError):
                height = 0.1
            mask_top = min(mask_top, layer_y - height * 0.55)
            mask_bottom = max(mask_bottom, layer_y + height * 0.55)
        mask_height = max(0.22, min(0.85, mask_bottom - mask_top + 0.04))
        mask_center_y = (mask_top + mask_bottom) * 0.5
        if abs(mask_center_y - pos_y_norm) < 0.025:
            mask_center_y = pos_y_norm
        mask_rect = QRectF(center_x - w * 0.475, h * (1.0 - mask_center_y - mask_height * 0.5), w * 0.95, h * mask_height)
        if h < 200:
            mask_rect = QRectF(0, 0, w, h)
        self.last_mask_rect = mask_rect

        # Authored motion tracks
        motion_tracks = [track for layer in self.template.layers for track in layer.motion_tracks]
        def first_track(prop, phase_name):
            return next((track.keyframes for track in motion_tracks
                         if track.property == prop and track.phase == phase_name and track.keyframes), [])
        in_x, out_x = first_track("translate_x", "in"), first_track("translate_x", "out")
        in_y, out_y = first_track("translate_y", "in"), first_track("translate_y", "out")
        in_scale = first_track("scale", "in") or first_track("scale_x", "in") or first_track("scale_y", "in")
        out_scale = first_track("scale", "out") or first_track("scale_x", "out") or first_track("scale_y", "out")
        in_op = first_track("opacity", "in") or first_track("alpha", "in")
        out_op = first_track("opacity", "out") or first_track("alpha", "out")
        has_pop = bool(in_scale or out_scale)

        phase = self.playback_phase
        global_alpha = 1.0
        global_scale = 1.0
        global_dx = 0.0
        global_dy = 0.0
        ease_in = 1.0

        # Three-phase animation lifecycle
        if phase < 0.35:
            # 1. Entrance phase (0.0 -> 0.35): translation from offscreen / scale up / fade in
            progress = max(0.0, min(1.0, phase / 0.35))
            ease_in = evaluate_easing("expoOut", progress)
            phase_t = progress * in_dur
            authored_alpha = self._sample_keyframes(in_op, phase_t, 1.0) if in_op else 1.0
            global_alpha = max(0.0, min(1.0, authored_alpha * ease_in))
            scale_start = 0.90 if has_pop else 0.88
            global_scale = self._sample_keyframes(in_scale, phase_t, scale_start) if in_scale else scale_start + (1.0 - scale_start) * ease_in
            global_dy = self._sample_keyframes(in_y, phase_t, 0.0) if in_y else -0.045 * (1.0 - ease_in)
            global_dx = self._sample_keyframes(in_x, phase_t, 0.0) if in_x else 0.0
        elif phase > 0.75:
            # 3. Exit phase (0.75 -> 1.0): translation offscreen / fade out
            progress = max(0.0, min(1.0, (phase - 0.75) / 0.25))
            ease_out = evaluate_easing("cubicIn", progress)
            ease_in = max(0.0, 1.0 - ease_out)
            phase_t = progress * out_dur
            authored_alpha = self._sample_keyframes(out_op, phase_t, 0.0) if out_op else 1.0
            global_alpha = max(0.0, min(1.0, authored_alpha * (1.0 - ease_out)))
            global_scale = self._sample_keyframes(out_scale, phase_t, 1.0) if out_scale else (1.0 - 0.10 * ease_out if has_pop else 1.0)
            global_dy = self._sample_keyframes(out_y, phase_t, 0.0) if out_y else -0.045 * ease_out
            global_dx = self._sample_keyframes(out_x, phase_t, 0.0) if out_x else 0.0
        else:
            # 2. Hold phase (0.35 -> 0.75): resting state at 100% opacity and [0,0] offset
            global_alpha = 1.0
            global_scale = 1.0
            global_dx = 0.0
            global_dy = 0.0
            ease_in = 1.0

        global_dx = global_dx / 1920.0 if abs(global_dx) > 1.0 else global_dx
        global_dy = global_dy / 1080.0 if abs(global_dy) > 1.0 else global_dy
        self.last_text_dy = -global_dy * h

        painter.save()
        painter.setOpacity(max(0.0, min(1.0, global_alpha)))
        painter.translate(w * (0.5 + global_dx), h * (0.5 - global_dy))
        painter.scale(global_scale, global_scale)
        painter.translate(-w * 0.5, -h * 0.5)

        # Draw authored geometry in layer order using normalized template dimensions.
        if self.params.get("plate_enabled", True):
            for shape in box_layers:
                try:
                    shape_w = w * max(0.0, float(self._resolve_val(shape.props.get("width", 0.15))))
                    shape_h = h * max(0.0, float(self._resolve_val(shape.props.get("height", 0.04))))
                    shape_x, shape_y = self._layer_center_px(shape, w, h, center_x, base_center_y)
                    corner = max(0.0, float(self._resolve_val(shape.props.get("corner_radius", 4))))
                except (TypeError, ValueError):
                    continue
                fallback = "bg_plate" if shape in plate_layers or shape.props.get("role") == "plate" else "accent"
                border_value = self._resolve_val(shape.props.get("border_color"))
                try:
                    border_width = max(0.0, float(self._resolve_val(shape.props.get("border_width", 0.0))))
                except (TypeError, ValueError):
                    border_width = 0.0
                if isinstance(border_value, (list, tuple)) and len(border_value) >= 3 and border_width > 0:
                    rgba = list(border_value[:4])
                    while len(rgba) < 4:
                        rgba.append(1.0)
                    border_color = QColor(*(int(max(0.0, min(1.0, float(c))) * 255) for c in rgba[:3]), int(max(0.0, min(1.0, float(rgba[3]))) * 255))
                    painter.setPen(QPen(border_color, border_width))
                else:
                    painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(self._layer_color(shape, fallback)))
                rect = QRectF(shape_x - shape_w / 2, shape_y - shape_h / 2, shape_w, shape_h)
                if shape.type == LayerType.SHAPE_PILL or corner > 0:
                    painter.drawRoundedRect(rect, min(corner, shape_w / 2), min(corner, shape_h / 2))
                else:
                    painter.drawRect(rect)

        # Accents stay behind the text.
        for line in line_layers:
            try:
                line_w = w * max(0.0, float(self._resolve_val(line.props.get("width", 0.22)))) * ease_in
                line_h = max(1.0, h * float(self._resolve_val(line.props.get("height", 0.003))))
                primary_size = float(self._resolve_val(text_layers[0].props.get("size", 0.075))) if text_layers else 0.075
                default_line_y = base_center_y + h * primary_size * 0.62
                line_x, line_y = self._layer_center_px(line, w, h, center_x, default_line_y)
                if text_layers and line_w >= line_h * 2:
                    primary_x, primary_y = self._layer_center_px(text_layers[0], w, h, center_x, base_center_y)
                    if abs(line_y - primary_y) < h * primary_size * 0.42:
                        line_y = primary_y + h * primary_size * 0.72
            except (TypeError, ValueError):
                continue
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self._layer_color(line, "accent")))
            painter.drawRect(QRectF(line_x - line_w / 2, line_y - line_h / 2, line_w, line_h))

        # Draw every authored text layer. Normalized font sizes scale with canvas
        # height, keeping titles legible in both landscape and portrait previews.
        painter.save()
        painter.setClipRect(self.rect())
        string_params = [p.id for p in self.template.parameters if p.type == ParameterType.STRING]
        implicit_stack_px = 0.0
        previous_line_height = 0.0
        painted_text_bounds = []
        for index, layer in enumerate(text_layers):
            raw_text = str(self._resolve_val(layer.props.get("text", "")))
            if not raw_text and index < len(string_params):
                raw_text = str(self.params.get(string_params[index], ""))
            if not raw_text:
                continue
            if self.params.get("bengali_digits", False):
                raw_text = to_bengali_numerals(raw_text)
            is_bn = contains_bengali(raw_text)
            role = str(layer.props.get("role", "")).lower()
            purpose = "bengali" if is_bn else ("mono" if "tag" in role or "eyebrow" in role else ("display" if index == 0 else "body"))
            font_token = ("font_heading_bn" if index == 0 else "font_body_bn") if is_bn else ("font_heading" if index == 0 else "font_body")
            fallback_font = self.theme.get(font_token, "Arial")
            font_name = self._layer_font_name(layer, fallback_font, purpose)
            try:
                normalized_size = float(self._resolve_val(layer.props.get("size", 0.045)))
                tracking = float(self._resolve_val(layer.props.get("character_spacing", 1.0)))
            except (TypeError, ValueError):
                normalized_size, tracking = 0.045, 1.0
            optical = get_optical_scale(raw_text) if is_bn else 1.0
            point_size = max(8, round(normalized_size * h * optical))
            font = QFont(font_name, point_size, self._font_weight(layer, QFont.Weight.Bold if index == 0 else QFont.Weight.Medium))
            font.setPixelSize(point_size)
            font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, max(80.0, tracking * 100.0))
            default_y = base_center_y + implicit_stack_px
            rect, alignment_name = self._layer_text_rect(layer, w, h, center_x, default_y, max(point_size * 2.0, h * 0.055))
            margin = max(4.0, w * 0.025)
            rect.setLeft(max(margin, rect.left()))
            rect.setRight(min(w - margin, rect.right()))
            flags = {"left": Qt.AlignmentFlag.AlignLeft, "right": Qt.AlignmentFlag.AlignRight}.get(alignment_name, Qt.AlignmentFlag.AlignHCenter)
            flags |= Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap
            metrics = QFontMetricsF(font)
            while point_size > 8 and metrics.horizontalAdvance(raw_text.splitlines()[0]) > rect.width() * 0.96:
                point_size -= 1
                font.setPixelSize(point_size)
                metrics = QFontMetricsF(font)
            content_bounds = metrics.boundingRect(rect, int(flags), raw_text)
            for prior_text, prior_bounds in painted_text_bounds:
                if raw_text != prior_text and content_bounds.intersects(prior_bounds):
                    dy = prior_bounds.bottom() - content_bounds.top() + max(3.0, h * 0.008)
                    rect.translate(0.0, dy)
                    content_bounds.translate(0.0, dy)
            painter.setFont(font)
            painter.setPen(self._layer_color(layer, "text_primary" if index == 0 else "text_secondary"))
            painter.drawText(rect, flags, raw_text)
            painted_text_bounds.append((raw_text, content_bounds))
            if "center_y" not in layer.props and "offset_y" not in layer.props:
                implicit_stack_px += (previous_line_height + metrics.height()) * 0.72 + h * 0.01
            previous_line_height = metrics.height()
        painter.restore()

        painter.restore()
