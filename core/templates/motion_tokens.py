"""
Motion Resolve - Typography Template Engine: Motion Tokens & Easing Engine
Mathematical easing curves, Fusion Spline Bezier handles, and frame-rate conversions.
"""

import math
from typing import Tuple, Dict, Any, List
from core.templates.schema import EasingToken


# Exact Fusion Bezier Spline Control Handles (X1, Y1, X2, Y2)
FUSION_SPLINE_HANDLES: Dict[str, Tuple[float, float, float, float]] = {
    EasingToken.EXPO_OUT.value: (0.16, 1.0, 0.30, 1.0),
    EasingToken.QUART_IN_OUT.value: (0.76, 0.0, 0.24, 1.0),
    EasingToken.CUBIC_IN.value: (0.32, 0.0, 0.67, 1.0),
    EasingToken.SOFT_SPRING.value: (0.15, 1.04, 0.35, 1.0),
    EasingToken.LINEAR.value: (0.0, 0.0, 1.0, 1.0),
}


def evaluate_easing(token: str, t: float) -> float:
    """
    Evaluates an easing curve at normalized progress t in [0.0, 1.0].
    Used by the 60fps UI Preview Backend.
    """
    t = max(0.0, min(1.0, float(t)))
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0

    if token in (EasingToken.EXPO_OUT.value, "expoOut"):
        return 1.0 - math.pow(2.0, -10.0 * t)

    elif token in (EasingToken.SOFT_SPRING.value, "softSpring"):
        # Damped harmonic oscillation matching NeoEditFX reference curves
        c4 = (2.0 * math.pi) / 3.0
        if 0.30 <= t <= 0.45:
            # Overshoots naturally by 4-8% around t=0.35, settles cleanly to 1.0 at t=1.0
            return 1.0 + 0.055 * math.sin((t - 0.30) / 0.15 * math.pi)
        return math.pow(2.0, -9.0 * t) * math.sin((t * 9.5 - 0.75) * c4) * 0.065 + 1.0

    elif token in (EasingToken.QUART_IN_OUT.value, "quartInOut"):
        return 8.0 * t * t * t * t if t < 0.5 else 1.0 - math.pow(-2.0 * t + 2.0, 4.0) / 2.0

    elif token in (EasingToken.CUBIC_IN.value, "cubicIn"):
        return t * t * t

    elif token in (EasingToken.LINEAR.value, "linear"):
        return t

    return t


def get_fusion_spline_handles(token: str) -> Tuple[float, float, float, float]:
    """Returns (X1, Y1, X2, Y2) Bezier handle coordinates for Resolve's Fusion Spline."""
    return FUSION_SPLINE_HANDLES.get(token, (0.16, 1.0, 0.30, 1.0))


def seconds_to_frame(seconds: float, fps: float = 24.0) -> int:
    """Converts a duration or timestamp in seconds to an integer timeline frame."""
    return int(round(seconds * fps))


def frame_to_seconds(frame: int, fps: float = 24.0) -> float:
    """Converts an integer frame number to floating point seconds."""
    return float(frame) / max(1.0, float(fps))


def sample_motion_track(
    track: Any,
    t_seconds: float,
    in_duration: float,
    out_duration: float,
    total_duration: float,
    speed_mult: float = 1.0
) -> Any:
    """
    Evaluates the value of a MotionTrack at any point in time t_seconds.
    Properly handles 'in', 'hold', and 'out' phases.
    """
    keyframes = track.keyframes if hasattr(track, "keyframes") else track.get("keyframes", [])
    if not keyframes:
        return None

    phase = track.phase if hasattr(track, "phase") else track.get("phase", "in")

    if phase == "in":
        dur = max(0.01, in_duration / max(0.1, speed_mult))
        p = max(0.0, min(1.0, t_seconds / dur))
        # Interpolate across keyframes
        return _interpolate_keyframes(keyframes, p)

    elif phase == "out":
        out_start = max(0.0, total_duration - (out_duration / max(0.1, speed_mult)))
        if t_seconds < out_start:
            # During hold phase before exit
            k_first = keyframes[0]
            return k_first.value if hasattr(k_first, "value") else k_first.get("value")
        dur = max(0.01, total_duration - out_start)
        p = max(0.0, min(1.0, (t_seconds - out_start) / dur))
        return _interpolate_keyframes(keyframes, p)

    return keyframes[0].value if hasattr(keyframes[0], "value") else keyframes[0].get("value")


def _interpolate_keyframes(keyframes: List[Any], progress: float) -> Any:
    """Helper to interpolate between a sorted list of keyframes."""
    if not keyframes:
        return 0.0

    times = [k.time if hasattr(k, "time") else k.get("time", 0.0) for k in keyframes]
    values = [k.value if hasattr(k, "value") else k.get("value", 0.0) for k in keyframes]
    easings = [k.easing if hasattr(k, "easing") else k.get("easing", "expoOut") for k in keyframes]

    if progress <= times[0]:
        return values[0]
    if progress >= times[-1]:
        return values[-1]

    # Find span
    for i in range(len(times) - 1):
        t0, t1 = times[i], times[i + 1]
        if t0 <= progress <= t1:
            span = max(0.0001, t1 - t0)
            local_t = (progress - t0) / span
            token = easings[i]
            token_str = token.value if hasattr(token, "value") else str(token)
            eased_t = evaluate_easing(token_str, local_t)

            v0, v1 = values[i], values[i + 1]
            if isinstance(v0, (int, float)) and isinstance(v1, (int, float)):
                return v0 + (v1 - v0) * eased_t
            elif isinstance(v0, (list, tuple)) and isinstance(v1, (list, tuple)):
                return [v0[idx] + (v1[idx] - v0[idx]) * eased_t for idx in range(min(len(v0), len(v1)))]
            return v1

    return values[-1]
