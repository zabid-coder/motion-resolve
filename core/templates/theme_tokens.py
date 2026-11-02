"""
Motion Resolve - Typography Template Engine: Global Theme Tokens
Centralized color palettes, typography tokens, radius, and stroke scale.
"""

from typing import Dict, Any, List, Optional


GLOBAL_THEMES: Dict[str, Dict[str, Any]] = {
    "mono": {
        "id": "mono",
        "name": "Porcelain Noir",
        "bg_plate": [0.055, 0.052, 0.05, 0.88],
        "text_primary": [0.97, 0.95, 0.90, 1.0],
        "text_secondary": [0.70, 0.67, 0.61, 1.0],
        "accent": [0.78, 0.56, 0.34, 1.0],
        "border": [0.36, 0.30, 0.23, 0.68],
        "font_heading": "Avenir Next",
        "font_heading_bn": "Kohinoor Bangla",
        "font_body": "Avenir",
        "font_body_bn": "Kohinoor Bangla",
        "corner_radius": 8,
        "stroke_width": 1,
        "default_motion_speed": 0.92
    },
    "warm": {
        "id": "warm",
        "name": "Warm Editorial",
        "bg_plate": [0.10, 0.09, 0.08, 0.95],      # #1A1614
        "text_primary": [0.98, 0.96, 0.94, 1.0],   # #FAF6F0
        "text_secondary": [0.75, 0.70, 0.65, 1.0],
        "accent": [0.85, 0.47, 0.21, 1.0],         # #D97736 Terracotta
        "border": [0.25, 0.22, 0.19, 0.8],
        "font_heading": "Baskerville",
        "font_heading_bn": "Kohinoor Bangla",
        "font_body": "Charter",
        "font_body_bn": "Kohinoor Bangla",
        "corner_radius": 4,
        "stroke_width": 2,
        "default_motion_speed": 0.95
    },
    "ocean": {
        "id": "ocean",
        "name": "Ocean Glow",
        "bg_plate": [0.03, 0.07, 0.12, 0.95],      # #08131E
        "text_primary": [0.92, 0.96, 0.98, 1.0],   # #EBF4FA
        "text_secondary": [0.55, 0.68, 0.78, 1.0],
        "accent": [0.0, 0.82, 1.0, 1.0],           # #00D2FF Cyan Glow
        "border": [0.12, 0.25, 0.38, 0.8],
        "font_heading": "Avenir Next",
        "font_heading_bn": "Kohinoor Bangla",
        "font_body": "Helvetica Neue",
        "font_body_bn": "Kohinoor Bangla",
        "corner_radius": 8,
        "stroke_width": 2,
        "default_motion_speed": 1.05
    },
    "neon_tech": {
        "id": "neon_tech",
        "name": "Neon Tech / SaaS",
        "bg_plate": [0.03, 0.02, 0.06, 0.96],      # #08060F
        "text_primary": [1.0, 1.0, 1.0, 1.0],      # #FFFFFF
        "text_secondary": [0.60, 0.58, 0.70, 1.0],
        "accent": [0.0, 1.0, 0.62, 1.0],           # #00FF9D Electric Mint
        "border": [0.18, 0.15, 0.28, 0.9],
        "font_heading": "Avenir Next Condensed",
        "font_heading_bn": "Kohinoor Bangla",
        "font_body": "Helvetica Neue",
        "font_body_bn": "Kohinoor Bangla",
        "font_mono": "JetBrains Mono",
        "corner_radius": 6,
        "stroke_width": 2,
        "default_motion_speed": 1.10
    },
    "earth": {
        "id": "earth",
        "name": "Earth Organic",
        "bg_plate": [0.07, 0.08, 0.07, 0.95],      # #121411
        "text_primary": [0.95, 0.96, 0.94, 1.0],   # #F2F4F0
        "text_secondary": [0.68, 0.72, 0.65, 1.0],
        "accent": [0.53, 0.69, 0.29, 1.0],         # #88B04B Sage Green
        "border": [0.20, 0.24, 0.19, 0.8],
        "font_heading": "Georgia",
        "font_heading_bn": "Kohinoor Bangla",
        "font_body": "Avenir",
        "font_body_bn": "Kohinoor Bangla",
        "corner_radius": 5,
        "stroke_width": 2,
        "default_motion_speed": 0.90
    },
    "frosted_slate": {
        "id": "frosted_slate",
        "name": "Frosted Slate",
        "bg_plate": [0.10, 0.13, 0.16, 0.82],
        "text_primary": [0.94, 0.96, 0.94, 1.0],
        "text_secondary": [0.68, 0.76, 0.78, 1.0],
        "accent": [0.50, 0.72, 0.72, 1.0],
        "border": [0.45, 0.58, 0.60, 0.58],
        "font_heading": "Helvetica Neue",
        "font_heading_bn": "Kohinoor Bangla",
        "font_body": "Avenir",
        "font_body_bn": "Kohinoor Bangla",
        "font_mono": "Menlo",
        "corner_radius": 12,
        "stroke_width": 1,
        "default_motion_speed": 0.88
    },
    "porcelain": {
        "id": "porcelain",
        "name": "Warm Porcelain",
        "bg_plate": [0.13, 0.11, 0.095, 0.94],
        "text_primary": [0.99, 0.96, 0.88, 1.0],
        "text_secondary": [0.78, 0.71, 0.57, 1.0],
        "accent": [0.73, 0.43, 0.25, 1.0],
        "border": [0.43, 0.31, 0.21, 0.76],
        "font_heading": "Georgia",
        "font_heading_bn": "Kohinoor Bangla",
        "font_body": "Avenir",
        "font_body_bn": "Kohinoor Bangla",
        "font_mono": "Menlo",
        "corner_radius": 5,
        "stroke_width": 1,
        "default_motion_speed": 0.9
    },
    "rosewood": {
        "id": "rosewood",
        "name": "Rosewood Editorial",
        "bg_plate": [0.12, 0.065, 0.075, 0.94],
        "text_primary": [0.98, 0.91, 0.88, 1.0],
        "text_secondary": [0.83, 0.61, 0.63, 1.0],
        "accent": [0.76, 0.37, 0.42, 1.0],
        "border": [0.48, 0.23, 0.29, 0.78],
        "font_heading": "Charter",
        "font_heading_bn": "Kohinoor Bangla",
        "font_body": "Helvetica Neue",
        "font_body_bn": "Kohinoor Bangla",
        "font_mono": "Menlo",
        "corner_radius": 6,
        "stroke_width": 1,
        "default_motion_speed": 0.94
    }
}


def get_theme(theme_id: str) -> Dict[str, Any]:
    """Retrieve theme tokens, resolving every family to an installed local font."""
    from core.font_catalog import resolve_available_font
    theme = dict(GLOBAL_THEMES.get(theme_id, GLOBAL_THEMES["mono"]))
    for key, purpose in (
        ("font_heading", "display"), ("font_body", "body"), ("font_mono", "mono"),
        ("font_heading_bn", "bengali"), ("font_body_bn", "bengali"),
    ):
        if theme.get(key):
            theme[key] = resolve_available_font(theme[key], purpose)
    return theme


def get_available_themes() -> List[Dict[str, str]]:
    """Returns list of theme IDs and display names for UI selectors."""
    return [{"id": t["id"], "name": t["name"]} for t in GLOBAL_THEMES.values()]


def normalize_color(val: Any, default: Optional[List[float]] = None) -> List[float]:
    """
    Parses any color representation (Hex string '#rrggbb', '#rrggbbaa', 
    RGBA float list [r, g, b, a], or int list 0-255) into [r, g, b, a] float values (0.0 - 1.0).
    """
    d = default or [1.0, 1.0, 1.0, 1.0]
    if val is None:
        return d
    if isinstance(val, (list, tuple)):
        floats = [float(x) for x in val]
        if any(x > 1.0 for x in floats[:3]):
            floats = [x / 255.0 for x in floats]
        while len(floats) < 4:
            floats.append(1.0)
        return floats[:4]
    if isinstance(val, str):
        s = val.strip().lstrip("#")
        if len(s) == 6:
            try:
                r = int(s[0:2], 16) / 255.0
                g = int(s[2:4], 16) / 255.0
                b = int(s[4:6], 16) / 255.0
                return [r, g, b, 1.0]
            except Exception:
                return d
        elif len(s) == 8:
            try:
                r = int(s[0:2], 16) / 255.0
                g = int(s[2:4], 16) / 255.0
                b = int(s[4:6], 16) / 255.0
                a = int(s[6:8], 16) / 255.0
                return [r, g, b, a]
            except Exception:
                return d
        elif len(s) == 3:
            try:
                r = int(s[0]*2, 16) / 255.0
                g = int(s[1]*2, 16) / 255.0
                b = int(s[2]*2, 16) / 255.0
                return [r, g, b, 1.0]
            except Exception:
                return d
    return d


def color_to_hex(val: Any) -> str:
    """Converts any color representation into '#rrggbb' hex format."""
    c = normalize_color(val)
    return f"#{int(c[0]*255):02x}{int(c[1]*255):02x}{int(c[2]*255):02x}"
