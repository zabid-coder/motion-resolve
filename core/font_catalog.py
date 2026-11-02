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
    "mono": ("Menlo", "Monaco", "Andale Mono", "Courier New"),
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

