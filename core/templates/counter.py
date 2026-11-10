"""
Motion Resolve - Count-up numbers.

Finds the number inside a title ("87%", "+$2,000.00", "94.8%", "1,000,000
SUBSCRIBERS", "10X FASTER", "১৪ জুলাই") and renders it at any progress
0..1 with the SAME formatting: prefix / suffix kept, thousands separators,
decimal places and Bengali digits preserved, never wider than the final value.
"""

import re
from dataclasses import dataclass
from typing import Optional

BN_DIGITS = "০১২৩৪৫৬৭৮৯"
_TO_LATIN = {ord(b): str(i) for i, b in enumerate(BN_DIGITS)}
_TO_BN = {ord(str(i)): b for i, b in enumerate(BN_DIGITS)}

# a number with optional thousands separators and decimals, Latin or Bengali digits
_NUM = re.compile(r"(?<![\w.])([0-9০-৯]{1,3}(?:,[0-9০-৯]{3})+|[0-9০-৯]+)(\.[0-9০-৯]+)?")


@dataclass
class CountSpec:
    prefix: str
    suffix: str
    value: float
    decimals: int
    grouped: bool
    bengali: bool

    def render(self, progress: float, start: float = 0.0) -> str:
        p = max(0.0, min(1.0, float(progress)))
        v = start + (self.value - start) * p
        if p >= 1.0:
            v = self.value
        if self.decimals:
            body = f"{v:,.{self.decimals}f}" if self.grouped else f"{v:.{self.decimals}f}"
        else:
            body = f"{int(v):,d}" if self.grouped else f"{int(v):d}"
        if self.bengali:
            body = body.translate(_TO_BN)
        return f"{self.prefix}{body}{self.suffix}"


def parse_count(text: str) -> Optional[CountSpec]:
    """Return a CountSpec for the FIRST number in text, or None if there is none."""
    if not text:
        return None
    m = _NUM.search(str(text))
    if not m:
        return None
    whole, frac = m.group(1), m.group(2) or ""
    bengali = any(ch in BN_DIGITS for ch in whole + frac)
    latin = (whole + frac).translate(_TO_LATIN).replace(",", "")
    try:
        value = float(latin)
    except ValueError:
        return None
    return CountSpec(prefix=text[:m.start()], suffix=text[m.end():], value=value,
                     decimals=max(0, len(frac) - 1), grouped="," in whole, bengali=bengali)


def lua_count_expression(spec: CountSpec, start_frame, end_frame, start: float = 0.0) -> str:
    """Fusion SimpleExpression for a Text+ StyledText input that counts up with an
    expo-out ease between start_frame and end_frame (comp time)."""
    def lua_str(s):
        s = s.replace("\\", "\\\\").replace('"', '\\"')
        s = s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        return '"' + s + '"'
    if isinstance(start_frame, str):
        # relative form, e.g. start_frame="comp.RenderStart + 2", end_frame=span in frames
        span = max(1.0, float(end_frame))
        p = f"math.max(0, math.min(1, (time - ({start_frame})) / {span:.3f}))"
    else:
        span = max(1.0, float(end_frame) - float(start_frame))
        p = f"math.max(0, math.min(1, (time - {start_frame:.3f}) / {span:.3f}))"
    ease = f"(1 - math.pow(1 - {p}, 3))"   # cubic-out: a readable, steady climb
    val = f"({start} + ({spec.value} - {start}) * ({ease}))"
    val = f"math.min({spec.value}, {val})"
    if spec.decimals:
        num = f'string.format("%.{spec.decimals}f", {val})'
    else:
        num = f'string.format("%d", math.floor({val}))'
    if spec.grouped:
        # insert thousands separators in Lua
        num = (f'(function(s) local i, j, minus, int, frac = s:find("([-]?)(%d+)([.]?%d*)") '
               f'int = int:reverse():gsub("(%d%d%d)", "%1,"):reverse():gsub("^,", "") '
               f'return minus .. int .. frac end)({num})')
    if spec.bengali:
        num = (f'(({num}):gsub("%d", function(d) return ({{"০","১","২","৩","৪","৫","৬","৭","৮","৯"}})[tonumber(d)+1] end))')
    return f"Text({lua_str(spec.prefix)} .. {num} .. {lua_str(spec.suffix)})"


def count_window(plan, timing, seconds: float = 1.4):
    """(start_frame, end_frame) relative to comp start for a layer's count-up:
    starts when the layer starts fading in and ends well before its exit."""
    op = (plan or {}).get("opacity") or []
    start = 0.0
    for f, v, _ in op:
        if v <= 0.001:
            start = f
        else:
            break
    fps_scale = float(timing.get("in_scale", 24.0)) or 24.0
    end = start + max(6.0, seconds * fps_scale)
    end = min(end, float(timing.get("out_start", end + 1)) - 2.0)
    return start, max(start + 3.0, end)


def eased_progress(frame: float, start: float, end: float) -> float:
    """Same cubic-out curve as the Fusion expression."""
    import math
    p = max(0.0, min(1.0, (frame - start) / max(1.0, end - start)))
    return 1 - math.pow(1 - p, 3)
