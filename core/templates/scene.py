"""
Motion Resolve - Scene resolver (single layout engine for Resolve + preview).

Templates are authored on a 1920x1080 reference frame using Fusion's own
coordinate conventions, which were measured in DaVinci Resolve 21:

* positions are normalized, origin bottom-left, Y grows upward;
* Text+ ``Size`` is a fraction of the frame WIDTH and equals one line box;
* RectangleMask ``Width`` is a fraction of frame width, ``Height`` of height.

For any other timeline format (9:16, 1:1, 4:5, 2.39:1...) the whole design is
scaled uniformly in pixel space around its anchor (``pos_x``/``pos_y``), so a
lower third keeps its exact proportions instead of being stretched.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.templates.schema import LayerType, ParameterType
from core.templates.theme_tokens import normalize_color
from core.templates.bengali_engine import contains_bengali, get_optical_scale, to_bengali_numerals

AUTHOR_W, AUTHOR_H = 1920.0, 1080.0
LEGACY_MASK_TEMPLATES = {"kin_masked_line", "min_underline_reveal", "kin_split_reveal", "pod_lower_third_slate"}
CHAR_ADVANCE = 0.48  # average glyph advance as a fraction of the Text+ line box


def resolve_value(val: Any, params: Dict[str, Any], theme: Dict[str, Any]) -> Any:
    if isinstance(val, str):
        if val.startswith("param:"):
            return params.get(val[6:], val)
        if val.startswith("$"):
            return params.get(val[1:], val)
        if val.startswith("token:"):
            return theme.get(val[6:], [1.0, 1.0, 1.0, 1.0])
    return val


def resolve_params(template, overrides: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    overrides = overrides or {}
    res = {p.id: overrides.get(p.id, p.default) for p in template.parameters}
    for k, v in overrides.items():
        res.setdefault(k, v)
    return res


def _f(val: Any, default: float) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return float(default)


@dataclass
class FrameFit:
    width: int
    height: int
    scale: float          # uniform design scale (1.0 on 1920x1080)
    anchor: Tuple[float, float]

    @property
    def aspect(self) -> float:
        return self.width / float(max(1, self.height))

    @property
    def is_vertical(self) -> bool:
        return self.aspect < 0.85

    @property
    def is_square(self) -> bool:
        return 0.85 <= self.aspect < 1.4

    # authored-normalized deltas -> target-normalized deltas
    def dx(self, d: float) -> float:
        return d * self.scale

    def dy(self, d: float) -> float:
        return d * self.scale * (AUTHOR_H / AUTHOR_W) * self.aspect

    def point(self, x: float, y: float) -> Tuple[float, float]:
        ax, ay = self.anchor
        return ax + self.dx(x - ax), ay + self.dy(y - ay)


@dataclass
class SceneLayer:
    spec: Any
    kind: str                      # "text" | "shape"
    index: int
    cx: float = 0.5
    cy: float = 0.5
    # text
    text: str = ""
    font: str = ""
    style: str = "Regular"
    size: float = 0.05             # Text+ size (fraction of frame width)
    tracking: float = 1.0
    line_spacing: float = 0.0
    align: float = 0.0             # -1 left, 0 center, 1 right
    lines: int = 1
    est_width: float = 0.0         # estimated text width (fraction of frame width)
    line_h: float = 0.05           # line box height (fraction of frame height)
    shadow: Optional[Dict[str, Any]] = None
    stroke: Optional[Dict[str, Any]] = None
    text_box: Optional[Dict[str, Any]] = None
    # shape
    width: float = 0.2
    height: float = 0.05
    corner: float = 0.0            # Fusion CornerRadius 0..1
    border: Optional[Dict[str, Any]] = None
    gradient: Optional[List[float]] = None
    origin: str = "center"
    fit_id: Optional[str] = None
    stagger: Optional[Dict[str, Any]] = None   # per-character cascade (Text+ Follower)
    count: bool = False            # count the number in this text up from 0
    count_seconds: float = 1.4
    # shared
    color: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0, 1.0])
    clip: bool = False
    is_plate: bool = False

    @property
    def id(self) -> str:
        return getattr(self.spec, "id", f"layer{self.index}")


def _estimate_width(text: str, size: float, tracking: float) -> float:
    longest = max((len(l) for l in str(text).split("\n")), default=1)
    return longest * size * CHAR_ADVANCE * max(0.6, tracking)


_MEASURE_CACHE: Dict[Tuple, float] = {}


def _measure_width(text: str, family: str, weight: str, size: float, tracking: float) -> Optional[float]:
    """Real width (fraction of a 1920-wide frame) of the widest line, measured with
    the actual installed font. Text+ draws an em of about size*W/1.2 (measured in
    Resolve 21). Returns None when no Qt font database is available."""
    key = (text, family, weight, round(size, 5), round(tracking, 3))
    if key in _MEASURE_CACHE:
        return _MEASURE_CACHE[key]
    try:
        from PyQt6.QtGui import QGuiApplication, QFont, QFontMetricsF
        if QGuiApplication.instance() is None:
            return None
        from core.font_catalog import resolve_font_style
        font = QFont(family)
        font.setPixelSize(max(4, int(round(size * AUTHOR_W / 1.2))))
        font.setStyleName(resolve_font_style(weight, family))
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, max(50.0, tracking * 100.0))
        fm = QFontMetricsF(font)
        w = max(fm.horizontalAdvance(line) for line in str(text).split("\n")) / AUTHOR_W
    except Exception:
        return None
    _MEASURE_CACHE[key] = w
    return w


def _pass1_font(props, text, is_first, params, theme, font_resolver):
    purpose = "bengali" if contains_bengali(text) else ("display" if is_first else "body")
    raw = props.get("font_bn") if purpose == "bengali" and props.get("font_bn") else props.get("font")
    if not raw:
        raw = "token:" + ({"bengali": "font_heading_bn", "display": "font_heading"}.get(purpose, "font_body"))
    requested = resolve_value(raw, params, theme)
    if not isinstance(requested, str):
        requested = "Helvetica Neue"
    return font_resolver(requested, purpose) if font_resolver else requested


def _wrap(text: str, size: float, tracking: float, max_w: float) -> str:
    """Insert line breaks so no line exceeds max_w (fraction of frame width)."""
    out_lines = []
    per_char = max(1e-4, size * CHAR_ADVANCE * max(0.6, tracking))
    max_chars = max(6, int(max_w / per_char))
    for para in str(text).split("\n"):
        words, cur = para.split(" "), ""
        for w in words:
            cand = (cur + " " + w).strip()
            if len(cand) > max_chars and cur:
                out_lines.append(cur)
                cur = w
            else:
                cur = cand
        out_lines.append(cur)
    return "\n".join(out_lines)


def resolve_scene(template, params: Dict[str, Any], theme: Dict[str, Any],
                  frame_w: int = 1920, frame_h: int = 1080,
                  font_resolver=None) -> Tuple[List[SceneLayer], FrameFit]:
    """Resolve every template layer to absolute, target-frame geometry."""
    frame_w = int(frame_w or 1920)
    frame_h = int(frame_h or 1080)
    aspect = frame_w / float(max(1, frame_h))

    ax = _f(params.get("pos_x", 0.5), 0.5)
    ay = _f(params.get("pos_y", 0.5), 0.5)
    has_pos_y = "pos_y" in params
    if aspect < 0.85 and has_pos_y:
        # keep lower thirds above TikTok / Reels / Shorts caption UI
        ay = min(0.80, max(0.30, ay if ay >= 0.28 else ay + 0.08))
    elif 0.85 <= aspect < 1.4 and has_pos_y and ay < 0.24:
        ay = max(0.26, ay + 0.04)

    string_params = [p.id for p in template.parameters if p.type == ParameterType.STRING]
    layers: List[SceneLayer] = []
    text_specs = [l for l in template.layers if l.type == LayerType.TEXT]

    # ---------- pass 1: text content + authored (16:9) geometry ----------
    auth: Dict[str, Dict[str, float]] = {}
    prev_text = None
    for idx, spec in enumerate(template.layers):
        props = spec.props or {}
        if spec.type == LayerType.TEXT:
            t_index = text_specs.index(spec)
            text = resolve_value(props.get("text", ""), params, theme)
            if (not text or str(text).startswith("param:")) and t_index < len(string_params):
                text = params.get(string_params[t_index], "")
            text = str(text or "")
            if params.get("bengali_digits", False):
                text = to_bengali_numerals(text)
            if props.get("uppercase") or props.get("text_transform") == "uppercase":
                text = text.upper()
            size = _f(resolve_value(props.get("size", 0.05), params, theme), 0.05)
            if contains_bengali(text):
                size *= get_optical_scale(text)
            tracking = _f(props.get("character_spacing", 1.0), 1.0)
            wrap_w = _f(props.get("text_width", 0.0), 0.0)
            # Wrapping is opt-in: legacy templates carry text_width but were
            # authored (and always rendered) as single lines.
            if props.get("wrap") and wrap_w > 0.05:
                text = _wrap(text, size, tracking, wrap_w)
            lines = max(1, text.count("\n") + 1)
            line_h_auth = size * AUTHOR_W / AUTHOR_H  # normalized-y of one line box
            ls = _f(props.get("line_spacing", 1.0), 1.0)
            block_h = line_h_auth * (1 + (lines - 1) * (ls if ls > 0.3 else 1.0) * 0.92)

            explicit = "center_y" in props or "offset_y" in props
            cx = _f(resolve_value(props.get("center_x", ax), params, theme), ax) + _f(props.get("offset_x", 0.0), 0.0)
            if explicit:
                cy = _f(resolve_value(props.get("center_y", ay), params, theme), ay) + _f(props.get("offset_y", 0.0), 0.0)
            elif prev_text is None:
                cy = ay
            else:
                gap = _f(props.get("gap", 0.012), 0.012)
                cy = prev_text["cy"] - prev_text["h"] * 0.5 - gap - block_h * 0.5
            fam = _pass1_font(props, text, t_index == 0, params, theme, font_resolver)
            weight = str(props.get("weight", "Bold" if t_index == 0 else "Medium"))
            measured = _measure_width(text, fam, weight, size, tracking)
            auth[spec.id] = {"cx": cx, "cy": cy, "h": block_h, "size": size,
                             "w": measured if measured is not None else _estimate_width(text, size, tracking)}
            prev_text = auth[spec.id]
            align = {"left": -1.0, "center": 0.0, "right": 1.0}.get(str(props.get("alignment", "center")).lower(), 0.0)
            layers.append(SceneLayer(spec=spec, kind="text", index=idx, text=text, size=size,
                                     tracking=tracking, align=align, lines=lines))
        else:
            layers.append(SceneLayer(spec=spec, kind="shape", index=idx))

    # text stack bounds (authored space)
    if auth:
        top = max(a["cy"] + a["h"] * 0.5 for a in auth.values())
        bottom = min(a["cy"] - a["h"] * 0.5 for a in auth.values())
        lefts, rights = [], []
        for sl in layers:
            if sl.kind != "text":
                continue
            a = auth[sl.id]
            if sl.align < 0:
                lefts.append(a["cx"]); rights.append(a["cx"] + a["w"])
            elif sl.align > 0:
                lefts.append(a["cx"] - a["w"]); rights.append(a["cx"])
            else:
                lefts.append(a["cx"] - a["w"] / 2); rights.append(a["cx"] + a["w"] / 2)
        stack = {"top": top, "bottom": bottom, "left": min(lefts), "right": max(rights)}
    else:
        stack = {"top": ay + 0.03, "bottom": ay - 0.03, "left": ax - 0.1, "right": ax + 0.1}

    first_text = next((sl for sl in layers if sl.kind == "text"), None)

    # ---------- pass 2: shapes (authored space) ----------
    for sl in layers:
        if sl.kind != "shape":
            continue
        props = sl.spec.props or {}
        w = _f(resolve_value(props.get("width", 0.2), params, theme), 0.2)
        h = _f(resolve_value(props.get("height", 0.04), params, theme), 0.04)
        sl.is_plate = props.get("role") == "plate"
        has_cx = "center_x" in props or "offset_x" in props
        has_cy = "center_y" in props or "offset_y" in props
        cx = _f(resolve_value(props.get("center_x", ax), params, theme), ax) + _f(props.get("offset_x", 0.0), 0.0)
        cy = _f(resolve_value(props.get("center_y", ay), params, theme), ay) + _f(props.get("offset_y", 0.0), 0.0)
        fit = props.get("fit_to")
        if (not fit and not sl.is_plate and not has_cx and not has_cy
                and sl.spec.type != LayerType.SHAPE_LINE and first_text is not None):
            fit = first_text.id  # legacy: box hugs the headline (Text+ element 4)
        sl.fit_id = fit if fit in auth else None
        if sl.is_plate:
            pad_y = _f(props.get("pad_y", 0.035), 0.035)
            if not has_cy:
                cy = (stack["top"] + stack["bottom"]) * 0.5
            h = max(h, (stack["top"] - stack["bottom"]) + pad_y * 2)
            if not has_cx:
                cx = (stack["left"] + stack["right"]) * 0.5
        elif sl.fit_id:
            sl.text_box = {"target": fit}
        elif sl.spec.type == LayerType.SHAPE_LINE and not has_cy and first_text is not None:
            a = auth[first_text.id]
            if h > w:  # vertical rule beside the stack
                cy = (stack["top"] + stack["bottom"]) * 0.5
                h = max(h, stack["top"] - stack["bottom"])
                cx = (stack["left"] - 0.012) if not has_cx else cx
            else:      # hairline under the headline
                cy = a["cy"] - a["h"] * 0.5 - 0.006
                if not has_cx:
                    cx = {-1.0: a["cx"] + w / 2, 1.0: a["cx"] - w / 2}.get(first_text.align, a["cx"])
        auth[sl.id] = {"cx": cx, "cy": cy, "w": w, "h": h}

    # ---------- uniform fit for the target frame ----------
    xs = []
    for sl in layers:
        a = auth[sl.id]
        if sl.kind == "text":
            if sl.align < 0:
                xs += [a["cx"], a["cx"] + a["w"]]
            elif sl.align > 0:
                xs += [a["cx"] - a["w"], a["cx"]]
            else:
                xs += [a["cx"] - a["w"] / 2, a["cx"] + a["w"] / 2]
        elif not sl.text_box:
            xs += [a["cx"] - a["w"] / 2, a["cx"] + a["w"] / 2]
    left_ext = max([ax - x for x in xs] + [0.0])
    right_ext = max([x - ax for x in xs] + [0.0])
    margin = 0.05 if aspect < 1.4 else 0.04
    limits = []
    if left_ext > 1e-3:
        limits.append(max(0.05, ax - margin) / left_ext)
    if right_ext > 1e-3:
        limits.append(max(0.05, 1.0 - margin - ax) / right_ext)
    room = min(limits) if limits else 1.0
    # Phones need far larger type than a 16:9 frame: let designs grow until
    # they meet the side margins (2.4x max on 9:16, 1.5x on square).
    cap = 2.4 if aspect < 0.85 else (1.5 if aspect < 1.4 else 1.0)
    scale = min(cap, room)
    fit_ = FrameFit(width=frame_w, height=frame_h, scale=max(0.35, scale), anchor=(ax, ay))

    # Templates authored for the old global reveal mask keep a masked reveal,
    # now as a per-layer clip that cannot cut neighbouring layers.
    legacy_mask = bool(getattr(template, "use_mask", False)) or bool(params.get("use_mask", False)) or \
        template.id in LEGACY_MASK_TEMPLATES

    # ---------- pass 3: map to target + styling ----------
    for sl in layers:
        props = sl.spec.props or {}
        a = auth[sl.id]
        sl.cx, sl.cy = fit_.point(a["cx"], a["cy"])
        sl.clip = bool(props.get("clip", legacy_mask and sl.kind == "text"))
        if sl.kind == "text":
            st = props.get("stagger")
            sl.stagger = st if isinstance(st, dict) else ({"delay": 1.2} if st else None)
            if sl.stagger and contains_bengali(sl.text):
                sl.stagger = None  # per-letter split would break Bengali conjuncts
            want_count = props.get("count") and str(params.get("count_up", True)).lower() not in ("false", "0", "no")
            if want_count:
                from core.templates.counter import parse_count
                sl.count = parse_count(sl.text) is not None
                sl.count_seconds = _f(params.get("count_duration", props.get("count_duration", 1.4)), 1.4)
            sl.size = a["size"] * fit_.scale
            sl.est_width = a["w"] * fit_.scale
            sl.line_h = fit_.dy(a["h"])
            sl.line_spacing = _line_spacing(props.get("line_spacing", 1.0))
            sl.color = normalize_color(resolve_value(props.get("color", "token:text_primary" if sl.index == 0 else "token:text_secondary"), params, theme))
            weight = str(props.get("weight", "Bold" if sl is first_text else "Medium"))
            sl.style = weight
            purpose = "bengali" if contains_bengali(sl.text) else ("display" if sl is first_text else "body")
            raw_font = props.get("font_bn") if purpose == "bengali" and props.get("font_bn") else props.get("font")
            if not raw_font:
                raw_font = "token:" + ({"bengali": "font_heading_bn", "display": "font_heading"}.get(purpose, "font_body"))
            requested = resolve_value(raw_font, params, theme)
            if not isinstance(requested, str):
                requested = "Helvetica Neue"
            sl.font = font_resolver(requested, purpose) if font_resolver else requested
            sh = props.get("shadow")
            sl.shadow = sh if isinstance(sh, dict) else None
            stroke_c = props.get("stroke_color") or props.get("outline_color")
            if stroke_c:
                sl.stroke = {"color": normalize_color(resolve_value(stroke_c, params, theme)),
                             "width": _f(props.get("stroke_width", 0.04), 0.04)}
        else:
            sl.width = min(0.98, a["w"] * fit_.scale)
            sl.height = fit_.dy(a["h"])
            sl.color = normalize_color(resolve_value(props.get("color", "token:bg_plate" if sl.is_plate else "token:accent"), params, theme))
            r_px = _f(resolve_value(props.get("corner_radius", 0), params, theme), 0.0) * fit_.scale * (frame_w / AUTHOR_W)
            min_px = max(1.0, min(sl.width * frame_w, sl.height * frame_h))
            sl.corner = 1.0 if sl.spec.type == LayerType.SHAPE_PILL else max(0.0, min(1.0, r_px / (min_px / 2.0)))
            bc, bw = props.get("border_color"), _f(props.get("border_width", 0.0), 0.0)
            if bc and bw > 0:
                sl.border = {"color": normalize_color(resolve_value(bc, params, theme)), "px": bw * fit_.scale}
            grad = props.get("gradient")
            if isinstance(grad, (list, tuple)) and len(grad) == 2:
                sl.gradient = [normalize_color(resolve_value(grad[0], params, theme)),
                               normalize_color(resolve_value(grad[1], params, theme))]
            sl.origin = str(props.get("origin", "center")).lower()
            if sl.text_box:
                target = next((t for t in layers if t.id == sl.fit_id), None)
                if target is not None:
                    target.text_box = {
                        "color": sl.color,
                        "pad_x": _f(props.get("pad_x", 0.35), 0.35),
                        "pad_y": _f(props.get("pad_y", 0.12), 0.12),
                        "round": _f(props.get("round", 0.35), 0.35),
                        "layer": sl.id,
                    }
    return layers, fit_


def _line_spacing(raw: Any) -> float:
    """Template line spacing -> Text+ LineSpacing.

    Text+ LineSpacing is a MULTIPLIER whose default is 1.0 (measured in
    Resolve 21). Legacy data stored 0.0 to mean "normal"; values <= 0.3 are
    treated as that legacy offset form.
    """
    f = _f(raw, 1.0)
    if f <= 0.3:
        f = 1.0 + f
    return max(0.5, min(2.5, f))
