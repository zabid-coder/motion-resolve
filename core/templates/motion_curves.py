"""
Motion Resolve - Shared motion curves and keyframe planning.

One source of truth for both the DaVinci Resolve compiler and the in-app
preview: every easing token is a cubic Bezier (exactly what a Fusion
BezierSpline can store), and every template track is converted into a frame
plan before it is written to Resolve or drawn in the preview. If the preview
shows it, the timeline gets it.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple

# Cubic Bezier control points (x1, y1, x2, y2) for each easing token.
# The easing of a key describes the segment LEAVING that key.
BEZIER_TOKENS: Dict[str, Tuple[float, float, float, float]] = {
    "linear": (0.0, 0.0, 1.0, 1.0),
    "expoOut": (0.16, 1.0, 0.30, 1.0),
    "quintOut": (0.22, 1.0, 0.36, 1.0),
    "expoIn": (0.70, 0.0, 0.84, 0.0),
    "expoInOut": (0.87, 0.0, 0.13, 1.0),
    "quartInOut": (0.76, 0.0, 0.24, 1.0),
    "cubicIn": (0.32, 0.0, 0.67, 0.0),
    "softSpring": (0.34, 1.56, 0.64, 1.0),
    "backIn": (0.36, 0.0, 0.66, -0.56),
    "hold": (0.0, 0.0, 1.0, 1.0),
}

# "spring" is a real damped spring: it is expanded into extra keys
# (overshoot, undershoot, settle) so Fusion reproduces genuine oscillation.
SPRING_SHAPE: Sequence[Tuple[float, float, str]] = (
    (0.42, 1.085, "quartInOut"),
    (0.68, 0.975, "quartInOut"),
    (0.86, 1.008, "quartInOut"),
)

ALL_TOKENS = tuple(BEZIER_TOKENS.keys()) + ("spring",)


def token_name(easing: Any) -> str:
    name = easing.value if hasattr(easing, "value") else str(easing or "expoOut")
    return name if name in ALL_TOKENS else "expoOut"


def _bezier_axis(t: float, p1: float, p2: float) -> float:
    u = 1.0 - t
    return 3.0 * u * u * t * p1 + 3.0 * u * t * t * p2 + t * t * t


def cubic_bezier(token: str, x: float) -> float:
    """Evaluate a cubic-bezier easing at progress x (0..1), like CSS / Fusion."""
    x = max(0.0, min(1.0, float(x)))
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    name = token_name(token)
    if name == "hold":
        return 0.0
    x1, y1, x2, y2 = BEZIER_TOKENS.get(name, BEZIER_TOKENS["expoOut"])
    # Solve bezier_x(t) == x with bisection (monotonic since x1,x2 in [0,1]).
    lo, hi = 0.0, 1.0
    t = x
    for _ in range(40):
        bx = _bezier_axis(t, x1, x2)
        if abs(bx - x) < 1e-6:
            break
        if bx < x:
            lo = t
        else:
            hi = t
        t = (lo + hi) * 0.5
    return _bezier_axis(t, y1, y2)


# ---------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------

Key = Tuple[float, float, str]  # (time-or-frame, value, easing leaving this key)


def expand_springs(keys: List[Key]) -> List[Key]:
    """Replace any segment leaving a 'spring' key with a multi-key damped spring."""
    out: List[Key] = []
    for i, (t, v, e) in enumerate(keys):
        if e != "spring" or i == len(keys) - 1:
            out.append((t, v, "expoOut" if e == "spring" else e))
            continue
        t1, v1, _ = keys[i + 1]
        out.append((t, v, "expoOut"))
        span, dv = t1 - t, v1 - v
        if abs(dv) < 1e-9 or span <= 0:
            continue
        for frac, mult, ease in SPRING_SHAPE:
            out.append((t + span * frac, v + dv * mult, ease))
    # de-duplicate equal times (keep the later definition)
    dedup: Dict[float, Key] = {}
    for k in out:
        dedup[round(k[0], 4)] = k
    return [dedup[t] for t in sorted(dedup)]


def evaluate_keys(keys: List[Key], t: float, default: float = 0.0) -> float:
    """Evaluate expanded keys at time/frame t with cubic-bezier segments."""
    if not keys:
        return default
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    for (t0, v0, e0), (t1, v1, _) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            span = t1 - t0
            if span <= 0:
                return v1
            return v0 + (v1 - v0) * cubic_bezier(e0, (t - t0) / span)
    return keys[-1][1]


def fusion_keyframes(keys: List[Key]) -> Dict[float, Dict[Any, Any]]:
    """Convert keys (frame, value, easing) into a Fusion BezierSpline key table.

    Fusion stores handles RELATIVE to their key: RH of the left key and LH of
    the right key are derived from the segment's cubic-bezier control points.
    Verified against DaVinci Resolve 21 (SetKeyFrames / GetKeyFrames).
    """
    table: Dict[float, Dict[Any, Any]] = {}
    for f, v, _ in keys:
        table[float(f)] = {1: float(v)}
    for (f0, v0, e0), (f1, v1, _) in zip(keys, keys[1:]):
        df, dv = float(f1 - f0), float(v1 - v0)
        if df <= 0:
            continue
        name = token_name(e0)
        if name == "hold":
            x1, y1, x2, y2 = (0.33, 0.0, 0.67, 0.0)
        else:
            x1, y1, x2, y2 = BEZIER_TOKENS.get(name, BEZIER_TOKENS["expoOut"])
        table[float(f0)]["RH"] = {1: x1 * df, 2: y1 * dv}
        table[float(f1)]["LH"] = {1: (x2 - 1.0) * df, 2: (y2 - 1.0) * dv}
    return table


# ---------------------------------------------------------------------------
# Template -> frame plan
# ---------------------------------------------------------------------------

REST_VALUES = {
    "opacity": 1.0, "translate_x": 0.0, "translate_y": 0.0, "scale": 1.0,
    "scale_x": 1.0, "scale_y": 1.0, "rotation": 0.0, "blur": 0.0,
    "tracking": None, "write_on": 1.0,
}
ALIASES = {"alpha": "opacity", "size": "scale", "angle": "rotation"}


def _attr(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _norm_prop(p: str) -> str:
    p = str(p or "").lower()
    return ALIASES.get(p, p)


def _track_keys(track) -> List[Tuple[float, Any, str]]:
    raw = _attr(track, "keyframes", []) or []
    keys = []
    for k in raw:
        keys.append((float(_attr(k, "time", 0.0)), _attr(k, "value", 0.0), token_name(_attr(k, "easing", "expoOut"))))
    keys.sort(key=lambda k: k[0])
    return keys


def phase_extents(template) -> Tuple[float, float]:
    """Natural (unscaled) in / out choreography lengths in seconds across all layers."""
    n_in, n_out = 0.0, 0.0
    for layer in _attr(template, "layers", []) or []:
        for tr in _attr(layer, "motion_tracks", []) or []:
            keys = _track_keys(tr)
            if not keys:
                continue
            phase = str(_attr(tr, "phase", "in"))
            if phase == "in":
                n_in = max(n_in, keys[-1][0])
            elif phase == "out":
                n_out = max(n_out, keys[-1][0])
    n_in = n_in or float(_attr(template, "in_duration", 0.5) or 0.5)
    n_out = n_out or float(_attr(template, "out_duration", 0.35) or 0.35)
    return n_in, n_out


def plan_timing(template, last_frame: int, fps: float, speed: float = 1.0) -> Dict[str, float]:
    """Fit the template choreography inside a clip of last_frame+1 frames.

    Entrance and exit keep their authored rhythm when there is room and are
    compressed proportionally on short clips, so the exit always completes
    exactly on the clip's last frame.
    """
    fps = max(1.0, float(fps))
    speed = max(0.1, float(speed))
    last_frame = max(4, int(last_frame))
    n_in, n_out = phase_extents(template)
    nat_in = n_in * fps / speed
    nat_out = n_out * fps / speed
    k_in = min(1.0, (last_frame * 0.45) / max(1e-6, nat_in))
    k_out = min(1.0, (last_frame * 0.35) / max(1e-6, nat_out))
    out_len = nat_out * k_out
    return {
        "fps": fps, "speed": speed, "last_frame": float(last_frame),
        "in_scale": (fps / speed) * k_in, "out_scale": (fps / speed) * k_out,
        "in_end": nat_in * k_in, "out_start": float(last_frame) - out_len,
    }


def layer_channel_plan(layer, timing: Dict[str, float], intensity: float = 1.0,
                       ensure_fades: bool = True) -> Dict[str, List[Key]]:
    """Return {channel: [(frame, value, easing), ...]} for one layer, springs expanded."""
    by_prop: Dict[str, Dict[str, List]] = {}
    for tr in _attr(layer, "motion_tracks", []) or []:
        keys = _track_keys(tr)
        if not keys:
            continue
        prop = _norm_prop(_attr(tr, "property", ""))
        phase = str(_attr(tr, "phase", "in"))
        by_prop.setdefault(prop, {}).setdefault(phase, keys)

    last = timing["last_frame"]
    plan: Dict[str, List[Key]] = {}
    for prop, phases in by_prop.items():
        frames: List[Key] = []
        for t, v, e in phases.get("in", []):
            frames.append((round(t * timing["in_scale"], 3), v, e))
        for t, v, e in phases.get("out", []):
            f = timing["out_start"] + t * timing["out_scale"]
            frames.append((round(min(last, f), 3), v, e))
        if not frames:
            continue
        frames.sort(key=lambda k: k[0])
        cleaned: List[Key] = []
        for f, v, e in frames:
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if prop in ("translate_x", "translate_y", "rotation", "blur"):
                fv *= float(intensity)
            cleaned.append((f, fv, e))
        if cleaned:
            plan[prop] = expand_springs(cleaned)

    if ensure_fades:
        # A title must never be visible on the first or last frame of its clip
        # (otherwise it "pops" on cuts). Authored fades are kept; missing ones
        # get a short, clean fade.
        fade = max(1.0, min(3.0, last * 0.08))
        op = list(plan.get("opacity") or [])
        if not op:
            op = [(0.0, 0.0, "quartInOut"), (fade, 1.0, "linear"),
                  (last - fade, 1.0, "quartInOut"), (last, 0.0, "linear")]
        else:
            if op[0][1] > 0.001:
                if op[0][0] < fade:
                    op[0] = (fade, op[0][1], op[0][2])
                op.insert(0, (0.0, 0.0, "quartInOut"))
            if op[-1][1] > 0.001:
                if op[-1][0] > last - fade:
                    op[-1] = (last - fade, op[-1][1], "quartInOut")
                else:
                    op[-1] = (op[-1][0], op[-1][1], "quartInOut")
                op.append((last, 0.0, "linear"))
        plan["opacity"] = sorted({round(k[0], 4): k for k in op}.values(), key=lambda k: k[0])
    return plan


def sample_layer(layer, timing: Dict[str, float], frame: float, intensity: float = 1.0) -> Dict[str, float]:
    """Evaluate every channel of a layer at a frame (used by the preview)."""
    state = {k: v for k, v in REST_VALUES.items() if v is not None}
    for prop, keys in layer_channel_plan(layer, timing, intensity).items():
        state[prop] = evaluate_keys(keys, frame, state.get(prop, 0.0))
    return state


# ---------------------------------------------------------------------------
# Per-character stagger (Text+ Follower)
# ---------------------------------------------------------------------------

def stagger_delay(stagger: Dict[str, Any], text: str, timing: Dict[str, float]) -> float:
    """Frames between characters, scaled with the template's speed and capped so
    the whole cascade never takes more than ~18% of the clip (long titles would
    otherwise start leaving letter by letter in the middle of their hold)."""
    if not stagger:
        return 0.0
    base = float(stagger.get("delay", 1.2))           # authored at 24 fps
    d = base * float(timing.get("in_scale", 24.0)) / 24.0
    n = max(1, len(str(text).replace("\n", "")))
    cap = (float(timing.get("last_frame", 72.0)) * 0.18) / max(1, n - 1)
    return max(0.25, min(d, cap))


def stagger_plan(plan: Dict[str, List[Key]], text: str, delay: float, timing: Dict[str, float]) -> Dict[str, List[Key]]:
    """Follower plays each character's keys `i*delay` later; shift the exit keys
    earlier by the whole cascade so the LAST character still finishes on the
    clip's last frame."""
    n = max(1, len(str(text).replace("\n", "")))
    shift = (n - 1) * delay
    out_start = float(timing.get("out_start", 1e9))
    shifted: Dict[str, List[Key]] = {}
    for prop, keys in plan.items():
        new = []
        for f, v, e in keys:
            if f >= out_start - 1e-6:
                f = max(0.0, f - shift)
            new.append((f, v, e))
        new.sort(key=lambda k: k[0])
        shifted[prop] = new
    return shifted
