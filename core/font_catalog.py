"""Installed-font catalog and predictable typographic fallbacks.

DaVinci Resolve's Text+ uses fonts installed on the host computer. Keep the
catalog sourced from Qt's local font database so presets and templates never
silently depend on a bundled or cloud-only font.
"""

from functools import lru_cache

from PyQt6.QtGui import QFontDatabase


FONT_FALLBACKS = {
    "display": ("Inter", "Montserrat", "Avenir Next", "Avenir Next Condensed", "Baskerville", "Helvetica Neue", "Arial"),
    "body": ("Inter", "Montserrat", "Avenir", "Avenir Next", "Helvetica Neue", "Arial"),
    "editorial": ("DM Serif Display", "Baskerville", "Didot", "Bodoni 72", "Georgia", "Arial"),
    "serif": ("DM Serif Display", "Instrument Serif", "Playfair Display", "Baskerville", "Didot", "Georgia"),
    "script": ("Pinyon Script", "Snell Roundhand", "Zapfino", "Brush Script MT", "Baskerville", "Georgia"),
    "sans": ("Inter", "Montserrat", "Manrope", "League Spartan", "Avenir Next", "Helvetica Neue", "Arial"),
    "mono": ("JetBrains Mono", "Menlo", "Monaco", "Consolas", "Andale Mono", "Courier New"),
    # Prefer Noto's Unicode-complete families: Resolve may show tofu with some
    # other locally installed Bengali fonts even though Qt lists them.
    "bengali": ("Noto Sans Bengali", "Noto Serif Bengali", "Nirmala UI", "Vrinda", "Shonar Bangla", "Hind Siliguri", "Kalpurush", "SolaimanLipi", "Kohinoor Bangla", "Bangla Sangam MN", "Bangla MN", "Arial Unicode MS"),
}


def is_script_font(font_name: str) -> bool:
    """Return True if the font name denotes a script, handwritten, or cursive typeface."""
    if not font_name:
        return False
    name_lower = str(font_name).lower()
    script_keywords = ("script", "hand", "brush", "cursive", "roundhand", "zapfino", "calligraphy")
    return any(kw in name_lower for kw in script_keywords)


def infer_font_purpose(font_name: str, default="body") -> str:
    """Choose a fallback family with the same typographic character as requested."""
    name = str(font_name or "").strip().lower()
    if is_script_font(name):
        return "script"
    if any(token in name for token in ("mono", "menlo", "monaco", "courier", "console")):
        return "mono"
    if any(token in name for token in (
        "serif", "baskerville", "didot", "bodoni", "garamond", "georgia",
        "charter", "book antiqu", "bell mt", "calisto", "times new roman",
    )):
        return "editorial"
    if any(token in name for token in (
        "avenir", "helvetica", "arial", "inter", "montserrat", "poppins",
        "roboto", "segoe", "gill sans", "league spartan", "manrope",
        "futura", "verdana", "century gothic", "open sans", "source sans",
    )):
        return "body"
    return default


def _discover_system_fonts():
    """Fallback font family discovery when Qt offscreen QPA returns no fonts."""
    found = set()
    try:
        import platform
        if platform.system() == "Windows":
            import winreg
            for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts") as key:
                        for i in range(winreg.QueryInfoKey(key)[1]):
                            name = winreg.EnumValue(key, i)[0]
                            clean = name.split("(")[0].strip()
                            if clean:
                                for part in clean.split("&"):
                                    p = part.strip()
                                    if p:
                                        found.add(p)
                except Exception:
                    pass
    except Exception:
        pass
    if not found:
        found.update(["Arial", "Helvetica", "Times New Roman", "Georgia", "Courier New", "Verdana", "Segoe UI", "Calibri"])
    return found


@lru_cache(maxsize=1)
def installed_font_families():
    """Return canonical family names visible to this computer's Qt runtime."""
    raw = []
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QGuiApplication
        if QApplication.instance() or QGuiApplication.instance():
            raw = [str(name).strip() for name in QFontDatabase.families() if str(name).strip()]
    except Exception:
        raw = []

    if not raw:
        raw = list(_discover_system_fonts())
    return tuple(sorted({name for name in raw if name}, key=str.casefold))


def refresh_installed_font_families():
    """Refresh the catalog after the user installs or removes system fonts."""
    installed_font_families.cache_clear()
    return installed_font_families()


def resolve_available_font(requested, purpose="body"):
    """Use the requested installed font, or a premium local fallback by role."""
    families = installed_font_families()
    by_casefold = {name.casefold(): name for name in families}
    name = str(requested or "").strip()
    if name.casefold() in by_casefold:
        return by_casefold[name.casefold()]

    fallback_order = FONT_FALLBACKS.get(purpose, FONT_FALLBACKS["body"])
    for candidate in fallback_order:
        if candidate.casefold() in by_casefold:
            return by_casefold[candidate.casefold()]
    return families[0] if families else "Arial"


def installed_font_options(include_bengali=True):
    """Return installed font names in a practical order for font pickers."""
    families = installed_font_families()
    preferred = list(FONT_FALLBACKS["display"] + FONT_FALLBACKS["body"] + FONT_FALLBACKS["editorial"] + FONT_FALLBACKS["mono"])
    if include_bengali:
        preferred.extend(FONT_FALLBACKS["bengali"])
    by_casefold = {name.casefold(): name for name in families}
    ordered = []
    for name in preferred:
        actual = by_casefold.get(name.casefold())
        if actual and actual not in ordered:
            ordered.append(actual)
    ordered.extend(name for name in families if name not in ordered)
    return ordered


def normalize_font_style(weight: str, font_family: str = "") -> str:
    """Maps CSS-like font weights (e.g. Medium, Semibold) to universally valid DaVinci Resolve styles."""
    w = str(weight or "").strip().lower()
    if w in ("bold", "heavy", "black", "extrabold", "bolder"):
        return "Bold"
    elif w in ("italic", "oblique"):
        return "Italic"
    elif w in ("bold italic", "bolditalic"):
        return "Bold Italic"
    elif w in ("medium", "semibold", "semi-bold", "demibold"):
        fam = str(font_family or "").lower()
        if "arial" in fam or "helvetica" in fam or "segoe" in fam or "menlo" in fam:
            return "Bold" if "semi" in w else "Regular"
        return "Regular"
    return "Regular"



_WEIGHT_PREFERENCES = {
    "thin": ["Thin", "Hairline", "Ultra Light", "UltraLight", "Extra Light", "ExtraLight", "Light"],
    "ultralight": ["Ultra Light", "UltraLight", "Extra Light", "ExtraLight", "Thin", "Light"],
    "light": ["Light", "Book", "Ultra Light", "UltraLight", "Regular"],
    "regular": ["Regular", "Roman", "Book", "Normal", "Medium"],
    "medium": ["Medium", "Demi Bold", "DemiBold", "Semibold", "SemiBold", "Regular"],
    "semibold": ["Semibold", "SemiBold", "Demi Bold", "DemiBold", "Demi", "Medium", "Bold"],
    "bold": ["Bold", "Demi Bold", "DemiBold", "Semibold", "Heavy"],
    "heavy": ["Heavy", "Black", "Extra Bold", "ExtraBold", "Ultra Bold", "Bold"],
    "black": ["Black", "Heavy", "Ultra Black", "Extra Bold", "ExtraBold", "Bold"],
}
_WEIGHT_ALIASES = {
    "hairline": "thin", "extralight": "ultralight", "ultra light": "ultralight", "ultra-light": "ultralight",
    "book": "regular", "roman": "regular", "normal": "regular", "": "regular",
    "demibold": "semibold", "demi bold": "semibold", "semi bold": "semibold", "semi-bold": "semibold", "demi": "semibold",
    "extrabold": "heavy", "extra bold": "heavy", "ultrabold": "heavy", "ultra bold": "heavy",
}


def resolve_font_style(weight: str, font_family: str = "") -> str:
    """Pick the closest REAL style name the installed family offers (e.g. 'Demi Bold').

    Text+ needs the exact style string of the font. Falls back to the
    conservative Regular/Bold mapping when the font database is unavailable.
    """
    raw = str(weight or "").strip()
    italic = "italic" in raw.lower() or "oblique" in raw.lower()
    key = raw.lower().replace("italic", "").replace("oblique", "").strip()
    key = _WEIGHT_ALIASES.get(key, key)
    # Resolve's own font list wins: it can differ from macOS (e.g. Qt lists
    # "Futura Heavy" but Resolve does not), and Text+ renders NOTHING for a
    # style it does not know.
    styles = resolve_font_styles(str(font_family))
    if not styles:
        try:
            from PyQt6.QtGui import QGuiApplication
            if QGuiApplication.instance() is None:
                raise RuntimeError("no Qt app")
            styles = list(QFontDatabase.styles(str(font_family)))
        except Exception:
            styles = []
    if not styles:
        return normalize_font_style(weight, font_family)
    by_cf = {s.casefold(): s for s in styles}
    if raw.casefold() in by_cf:
        return by_cf[raw.casefold()]
    for cand in _WEIGHT_PREFERENCES.get(key, [raw.title()]):
        names = [cand + " Italic", cand + " Oblique"] if italic else [cand]
        if italic and cand == "Regular":
            names = ["Italic", "Oblique"] + names
        for n in names:
            if n.casefold() in by_cf:
                return by_cf[n.casefold()]
    if italic:
        for s in styles:
            if "italic" in s.casefold():
                return s
    for fallback in ("Regular", "Roman", "Book", "Medium"):
        if fallback.casefold() in by_cf:
            return by_cf[fallback.casefold()]
    return styles[0]


_RESOLVE_FONTS = None


def resolve_font_styles(family: str):
    """Style names Resolve's Fusion FontManager knows for a family ([] if unknown/offline)."""
    global _RESOLVE_FONTS
    if _RESOLVE_FONTS is None:
        _RESOLVE_FONTS = {}
        try:
            # Only reuse a connection the app already made: opening one here can
            # block (tests, offline use, or a busy Resolve).
            import core.resolve_api as _ra
            if _ra._RESOLVE_INSTANCE is None:
                _RESOLVE_FONTS = None
                return []
            fu = _ra.get_fusion()
            fl = fu.FontManager.GetFontList() if fu else None
            if isinstance(fl, dict):
                _RESOLVE_FONTS = {str(k): list(v.keys()) if isinstance(v, dict) else [] for k, v in fl.items()}
        except Exception:
            _RESOLVE_FONTS = {}
    return list(_RESOLVE_FONTS.get(family, []))


def refresh_resolve_fonts():
    global _RESOLVE_FONTS
    _RESOLVE_FONTS = None
