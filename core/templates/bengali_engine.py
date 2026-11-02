"""
Motion Resolve - Bengali Typographic & Conjunct Protection Engine
Enforces linguistic safety rules: protects matras/ref, disables character slicing,
calculates optical scaling, and handles Bengali numeral conversions.
"""

import re
from typing import List, Tuple

# Bengali Unicode Range: U+0980 to U+09FF
BENGALI_REGEX = re.compile(r'[\u0980-\u09FF]')

BENGALI_DIGITS = {
    '0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪',
    '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯'
}
WESTERN_DIGITS = {v: k for k, v in BENGALI_DIGITS.items()}


def contains_bengali(text: str) -> bool:
    """Returns True if the text contains any Bengali unicode characters."""
    if not text:
        return False
    return bool(BENGALI_REGEX.search(text))


def is_pure_bengali(text: str) -> bool:
    """Returns True if text is predominantly Bengali script."""
    if not text:
        return False
    bengali_chars = len(BENGALI_REGEX.findall(text))
    latin_chars = len(re.findall(r'[a-zA-Z]', text))
    return bengali_chars > 0 and latin_chars == 0


def get_optical_scale(text: str) -> float:
    """
    Returns optical size multiplier. In mixed lines (Bengali + Latin),
    Bengali glyphs are optically scaled ~1.08x to balance with Latin Cap Height.
    """
    if contains_bengali(text) and re.search(r'[a-zA-Z]', text):
        return 1.08
    return 1.0


def get_safe_line_height(text: str) -> float:
    """
    Returns standard line-height multiplier. Defaults to 1.0 (single line spacing).
    """
    return 1.0


def get_mask_padding_em(text: str) -> Tuple[float, float]:
    """
    Returns (horizontal_em, vertical_em) padding for mask reveals.
    Bengali gets +0.25em top/bottom expansion so ref (র্) and ukar (ূ) never clip.
    """
    if contains_bengali(text):
        return (0.10, 0.28)
    return (0.05, 0.12)


def to_bengali_numerals(text: str) -> str:
    """Translates Western digits '0-9' into Bengali digits '০-৯'."""
    if not text:
        return ""
    return "".join(BENGALI_DIGITS.get(ch, ch) for ch in text)


def to_western_numerals(text: str) -> str:
    """Translates Bengali digits '০-৯' into Western digits '0-9'."""
    if not text:
        return ""
    return "".join(WESTERN_DIGITS.get(ch, ch) for ch in text)


def chunk_text_safely(text: str) -> List[str]:
    """
    Splits text into words safely.
    Strictly forbids character-by-character splitting on Bengali runs.
    """
    if not text:
        return []
    # Preserve words with whitespace and punctuation
    return [w for w in text.strip().split() if w]


def resolve_font_for_script(text: str, latin_font: str, bengali_font: str = "Kohinoor Bangla") -> str:
    """Select an installed local family appropriate for the text script."""
    from core.font_catalog import resolve_available_font
    if contains_bengali(text):
        return resolve_available_font(bengali_font, "bengali")
    return resolve_available_font(latin_font, "display")
