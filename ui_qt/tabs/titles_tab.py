"""
CaptionForge for Resolve - Titles Tab (PyQt6)
Visual Style Gallery & Title Composer.
Displays style presets, captures styles from timeline Text+ clips,
and provides a word-staging composer with hero word accentuation.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QScrollArea, QFrame,
    QFileDialog, QInputDialog, QMessageBox, QTextEdit, QSizePolicy, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import (
    QColor, QFont, QCursor, QPainter, QPainterPath, QPen, QBrush, QFontMetricsF,
    QLinearGradient
)

from core.style_manager import StyleManager
from ui_qt.theme import (
    COLOR_BG, COLOR_CARD, COLOR_BORDER, COLOR_BORDER_LIGHT,
    COLOR_ORANGE, COLOR_ORANGE_HOVER, COLOR_TEXT, COLOR_MUTED,
    STYLE_PILL_ACTIVE, STYLE_PILL_INACTIVE, STYLE_ORANGE_OUTLINE
)


class PresetPreviewCanvas(QWidget):
    """High-fidelity Text+ typography preview canvas rendering real character strokes, drop shadows, and boxes."""

    def __init__(self, preset_data, parent=None):
        super().__init__(parent)
        self.preset_data = preset_data
        self.setFixedHeight(84)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_preset_data(self, preset_data):
        self.preset_data = preset_data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = float(self.width())
        h = float(self.height())

        # Restrained, style-tinted preview plate instead of the same flat tile
        # for every preset.
        accent_data = self.preset_data.get("accent_color") or self.preset_data.get("color", [0.78, 0.56, 0.39, 1.0])
        accent = QColor(*(int(max(0, min(1, float(v))) * 255) for v in accent_data[:3]))
        bg_rect = QRectF(0, 0, w, h)
        gradient = QLinearGradient(0, 0, w, h)
        base = QColor("#111116")
        # QWidget's default backing surface is light on some Qt styles. Paint an
        # opaque dark base first so the translucent accent never composites to
        # white in the gallery preview.
        painter.fillRect(bg_rect, base)
        tint = QColor(
            int(base.red() * 0.74 + accent.red() * 0.26),
            int(base.green() * 0.74 + accent.green() * 0.26),
            int(base.blue() * 0.74 + accent.blue() * 0.26),
        )
        gradient.setColorAt(0.0, tint)
        gradient.setColorAt(1.0, base)
        painter.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 85), 1))
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(bg_rect, 6, 6)

        text = self.preset_data.get("text", "PREVIEW")
        hero_line_text = str(self.preset_data.get("main_word") or "").strip().upper()
        if self.preset_data.get("use_2color", False) and "\n" not in str(text):
            words = str(text).split()
            requested = [word.strip(".,!?").lower() for word in str(self.preset_data.get("main_word") or "").split()]
            match_start = next((i for i in range(len(words) - len(requested) + 1)
                                if requested and [word.strip(".,!?").lower() for word in words[i:i + len(requested)]] == requested), None)
            if match_start is None and words:
                match_start = max(range(len(words)), key=lambda i: len(words[i]))
                requested = [words[match_start].strip(".,!?").lower()]
            before = words[:match_start] if match_start is not None else words
            hero_words = words[match_start:match_start + len(requested)] if match_start is not None else []
            after = words[match_start + len(requested):] if match_start is not None else []
            hero_line_text = " ".join(hero_words).upper()
            hero = hero_line_text
            text = "\n".join(part for part in (" ".join(before), hero.upper(), " ".join(after)) if part)
        font_family = self.preset_data.get("font", "Avenir Next")
        try:
            from core.font_catalog import resolve_available_font, is_script_font
            from core.templates.bengali_engine import contains_bengali, resolve_font_for_script
            if contains_bengali(text):
                bn_font = self.preset_data.get("font_bn") or "Kohinoor Bangla"
                font_family = resolve_font_for_script(text, font_family, bn_font)
            else:
                requested = str(font_family).lower()
                serif_names = ("serif", "baskerville", "didot", "bodoni", "georgia", "times", "playfair", "charter")
                purpose = "script" if is_script_font(font_family) else ("editorial" if any(name in requested for name in serif_names) else "display")
                font_family = resolve_available_font(font_family, purpose)
        except Exception:
            pass
        tracking = float(self.preset_data.get("character_spacing", 1.0))

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            lines = [text]

        style_name = str(self.preset_data.get("style", "Demi")).strip().lower()
        weight = QFont.Weight.Normal
        if any(token in style_name for token in ("bold", "heavy", "black")):
            weight = QFont.Weight.Bold
        elif any(token in style_name for token in ("demi", "semi")):
            weight = QFont.Weight.DemiBold
        elif "medium" in style_name:
            weight = QFont.Weight.Medium
        size_token = float(self.preset_data.get("size", 0.075))
        fit_size = max(12, int((h - 24.0) / max(1.25, len(lines) * 1.32)))
        font_size = max(12, min(27, fit_size, round(size_token * 250)))
        font = QFont(font_family, font_size, weight)
        font.setStyleName(str(self.preset_data.get("style", "")))
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, max(80.0, tracking * 100.0))
        painter.setFont(font)

        hero_index = next((i for i, line in enumerate(lines) if hero_line_text and line.upper() == hero_line_text), -1)
        hero_multiplier = max(1.0, min(1.5, float(self.preset_data.get("hero_size_multiplier", 1.0))))
        hero_font_name = self.preset_data.get("hero_font")
        def line_fonts(base_font):
            result = []
            for idx in range(len(lines)):
                if idx == hero_index and hero_font_name:
                    from core.font_catalog import resolve_available_font, is_script_font
                    hero_name_lower = str(hero_font_name).lower()
                    serif_terms = ("serif", "baskerville", "didot", "bodoni", "georgia", "times", "playfair")
                    purpose = "script" if is_script_font(hero_font_name) else ("editorial" if any(term in hero_name_lower for term in serif_terms) else "display")
                    fam = resolve_available_font(hero_font_name, purpose)
                    sz = max(1, round(base_font.pointSize() * (hero_multiplier if hero_multiplier > 1.0 else (1.15 if is_script_font(hero_font_name) else 1.0))))
                    weight = QFont.Weight.Normal if is_script_font(hero_font_name) else QFont.Weight.Bold
                    line_font = QFont(fam, sz, weight)
                    if is_script_font(hero_font_name):
                        line_font.setItalic(True)
                    if self.preset_data.get("hero_style"):
                        try:
                            line_font.setStyleName(str(self.preset_data["hero_style"]))
                        except Exception:
                            pass
                else:
                    line_font = QFont(base_font)
                    if idx == hero_index and hero_multiplier > 1.0:
                        line_font.setPointSize(max(1, round(base_font.pointSize() * hero_multiplier)))
                        if self.preset_data.get("hero_style"):
                            line_font.setStyleName(str(self.preset_data["hero_style"]))
                result.append(line_font)
            return result
        fonts = line_fonts(font)
        metrics = [QFontMetricsF(line_font) for line_font in fonts]
        max_line_w = max(metrics[i].horizontalAdvance(line) for i, line in enumerate(lines))
        width_limit = max(40.0, w - 34.0)
        if max_line_w > width_limit:
            font_size = max(10, int(font_size * width_limit / max_line_w))
            font.setPointSize(font_size)
            painter.setFont(font)
            fonts = line_fonts(font)
            metrics = [QFontMetricsF(line_font) for line_font in fonts]
            max_line_w = max(metrics[i].horizontalAdvance(line) for i, line in enumerate(lines))

        line_heights = [metric.height() for metric in metrics]
        raw_spacing = float(self.preset_data.get("line_spacing", 1.0))
        # TextPlus 0.0 offset = 1.00 normal spacing
        line_spacing = 1.0 if abs(raw_spacing) < 0.05 else (raw_spacing if raw_spacing > 0.3 else 1.0 + raw_spacing)
        line_gaps = [max(1.0, max(line_heights[i], line_heights[i + 1]) * (0.16 + (line_spacing - 1.0) * 0.5)) for i in range(max(0, len(lines) - 1))]
        total_block_h = sum(line_heights) + sum(line_gaps)
        # Point-sized fonts can occupy more vertical space than the card's
        # logical height (especially for Bengali combining marks). Refit the
        # full stack until every line has a calm margin inside the preview.
        while total_block_h > h - 20.0 and font_size > 10:
            font_size -= 1
            font.setPointSize(font_size)
            fonts = line_fonts(font)
            metrics = [QFontMetricsF(line_font) for line_font in fonts]
            line_heights = [metric.height() for metric in metrics]
            line_gaps = [max(1.0, max(line_heights[i], line_heights[i + 1]) * (0.16 + (line_spacing - 1.0) * 0.5)) for i in range(max(0, len(lines) - 1))]
            total_block_h = sum(line_heights) + sum(line_gaps)
        align = str(self.preset_data.get("alignment", "center")).lower()
        center_x = w * max(0.12, min(0.88, float(self.preset_data.get("center_x", 0.5))))
        raw_center_y = float(self.preset_data.get("center_y", 0.28))
        # Compress the full-frame Text+ coordinate into a safe, readable card
        # preview while preserving each preset's relative vertical placement.
        center_y = h * (0.5 + (0.28 - max(0.1, min(0.7, raw_center_y))) * 0.75)
        center_y = max(5.0 + total_block_h / 2, min(h - 5.0 - total_block_h / 2, center_y))

        def line_x(text_line, metric):
            line_w = metric.horizontalAdvance(text_line)
            if align == "left":
                return max(16.0, min(w - line_w - 8.0, center_x))
            if align == "right":
                return max(8.0, min(w - line_w - 16.0, center_x - line_w))
            return center_x - line_w / 2.0

        def text_path():
            result = QPainterPath()
            cursor_y = center_y - total_block_h / 2.0
            for i, line_str in enumerate(lines):
                metric = metrics[i]
                baseline = cursor_y + line_heights[i] - metric.descent()
                result.addText(QPointF(line_x(line_str, metric), baseline), fonts[i], line_str)
                cursor_y += line_heights[i] + (line_gaps[i] if i < len(line_gaps) else 0.0)
            return result

        path = text_path()
        bounds = path.boundingRect()
        text_shift_y = 0.0
        if bounds.top() < 7.0:
            text_shift_y = 7.0 - bounds.top()
        elif bounds.bottom() > h - 7.0:
            text_shift_y = h - 7.0 - bounds.bottom()
        path.translate(0.0, text_shift_y)
        pad_x = max(8.0, float(self.preset_data.get("box_extend_x", 0.04)) * 320.0)
        pad_y = max(4.0, float(self.preset_data.get("box_extend_y", 0.025)) * 220.0)
        box_rect = QRectF(center_x - max_line_w / 2 - pad_x, center_y - total_block_h / 2 - pad_y,
                          max_line_w + 2 * pad_x, total_block_h + 2 * pad_y)

        # Element 4: Background Box
        if self.preset_data.get("box_enabled", False):
            bc = self.preset_data.get("box_color", [1.0, 0.88, 0.0, 0.95])
            box_qcolor = QColor(
                int(bc[0] * 255),
                int(bc[1] * 255),
                int(bc[2] * 255),
                int((bc[3] if len(bc) > 3 else 0.95) * 255)
            )
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(box_qcolor))
            roundness = float(self.preset_data.get("box_round", 0.25))
            painter.drawRoundedRect(box_rect, max(3.0, min(11.0, roundness * 22.0)), max(3.0, min(11.0, roundness * 22.0)))

        # Element 3: Drop Shadow
        if self.preset_data.get("shadow_enabled", False):
            shc = self.preset_data.get("shadow_color", [0.0, 0.0, 0.0, 0.50])
            shadow_qcolor = QColor(
                int(shc[0] * 255),
                int(shc[1] * 255),
                int(shc[2] * 255),
                int((shc[3] if len(shc) > 3 else 0.50) * 255)
            )
            off = self.preset_data.get("shadow_offset", [0.0, 0.0])
            off_x = float(off[0]) * 320.0
            off_y = -float(off[1]) * 320.0
            if abs(off_x) < 0.1 and abs(off_y) < 0.1:
                # Ambient 360-degree diffusion shadow: render soft feathered atmospheric glow
                soft = float(self.preset_data.get("shadow_softness", 0.045))
                steps = 3
                base_alpha = shadow_qcolor.alpha()
                for step in range(steps, 0, -1):
                    radius = (step / steps) * max(1.5, soft * 50.0)
                    step_alpha = int(base_alpha * (0.35 / step))
                    pen_glow = QPen(QColor(shadow_qcolor.red(), shadow_qcolor.green(), shadow_qcolor.blue(), step_alpha), radius * 2)
                    pen_glow.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                    painter.strokePath(path, pen_glow)
            else:
                shadow_path = QPainterPath(path)
                shadow_path.translate(off_x, off_y)
                painter.fillPath(shadow_path, QBrush(shadow_qcolor))

        # Element 2: Stroke
        if self.preset_data.get("stroke_enabled", False):
            sc = self.preset_data.get("stroke_color", [0.0, 0.0, 0.0, 1.0])
            stroke_qcolor = QColor(
                int(sc[0] * 255),
                int(sc[1] * 255),
                int(sc[2] * 255),
                int((sc[3] if len(sc) > 3 else 1.0) * 255)
            )
            thickness = float(self.preset_data.get("stroke_thickness", 0.03))
            stroke_px = max(0.8, thickness * 28.0)
            pen = QPen(stroke_qcolor, stroke_px)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.strokePath(path, pen)

        # Element 1: Main Text Fill with 2-Color Hero Accent support
        c = self.preset_data.get("color", [1.0, 1.0, 1.0, 1.0])
        fill_qcolor = QColor(
            int(c[0] * 255),
            int(c[1] * 255),
            int(c[2] * 255),
            int((c[3] if len(c) > 3 else 1.0) * 255)
        )

        use_2color = bool(self.preset_data.get("use_2color", False))
        if use_2color and len(lines) > 1:
            ac = self.preset_data.get("accent_color", [1.0, 0.85, 0.0, 1.0])
            accent_qcolor = QColor(
                int(ac[0] * 255),
                int(ac[1] * 255),
                int(ac[2] * 255),
                int((ac[3] if len(ac) > 3 else 1.0) * 255)
            )
            # Render each line with its distinct tone
            cursor_y = center_y - total_block_h / 2.0
            for i, line_str in enumerate(lines):
                line_path = QPainterPath()
                metric = metrics[i]
                lx = line_x(line_str, metric)
                ly = cursor_y + line_heights[i] - metric.descent() + text_shift_y
                line_path.addText(QPointF(lx, ly), fonts[i], line_str)
                # Middle or second line gets hero accent
                if hero_line_text and line_str.strip().upper() == hero_line_text:
                    painter.fillPath(line_path, QBrush(accent_qcolor))
                else:
                    painter.fillPath(line_path, QBrush(fill_qcolor))
                cursor_y += line_heights[i] + (line_gaps[i] if i < len(line_gaps) else 0.0)
        else:
            painter.fillPath(path, QBrush(fill_qcolor))


class PresetCardWidget(QFrame):
    """Visual preset card showing typography preview, category, and action buttons."""

    clicked = pyqtSignal(dict)
    applied = pyqtSignal(dict)
    deleted = pyqtSignal(str)

    def __init__(self, preset_data, is_selected=False, parent=None):
        super().__init__(parent)
        self.setObjectName("PresetCard")
        self.preset_data = preset_data
        self.is_selected = is_selected
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._build_ui()
        self.update_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Header: Name and Category badge
        top_row = QHBoxLayout()
        self.lbl_name = QLabel(self.preset_data.get("name", "Untitled Style"))
        self.lbl_name.setStyleSheet("font-weight: 700; font-size: 12px; color: #ffffff;")
        top_row.addWidget(self.lbl_name)
        top_row.addStretch()

        cat = self.preset_data.get("category", "General")
        self.lbl_cat = QLabel(cat)
        accent = self._accent_hex()
        self.lbl_cat.setStyleSheet(f"""
            background-color: {accent}26;
            color: {accent};
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 9px;
            font-weight: 700;
        """)
        top_row.addWidget(self.lbl_cat)
        layout.addLayout(top_row)

        # Typography Preview Canvas (High-Fidelity Text+ rendering)
        self.preview_canvas = PresetPreviewCanvas(self.preset_data)
        layout.addWidget(self.preview_canvas)

        # Bottom info row: Motion badge & Apply button
        bot_row = QHBoxLayout()
        anim_in = self.preset_data.get("animation_in", "fade").replace("_", " ").upper()
        font_label = self.preset_data.get("font", "AVENIR").upper()
        style_label = self.preset_data.get("style", "DEMI").upper()
        self.lbl_motion = QLabel(f"{font_label} · {style_label}   /   IN · {anim_in}")
        self.lbl_motion.setStyleSheet(f"font-size: 8px; color: {accent}; font-weight: 700; letter-spacing:0.25px;")
        bot_row.addWidget(self.lbl_motion)
        bot_row.addStretch()

        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setToolTip(
            "Apply this look to the Text+ title under the playhead; "
            "if there is no title there, insert a new editable Text+ title."
        )
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #b77a56;
                color: #191411;
                border: none;
                border-radius: 5px;
                padding: 4px 12px;
                font-weight: 700;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #c78a64;
            }
        """)
        self.btn_apply.clicked.connect(lambda: self.applied.emit(self.preset_data))
        bot_row.addWidget(self.btn_apply)

        # Delete button if custom preset
        preset_id = self.preset_data.get("id", "")
        default_ids = [
            "hormozi_yellow", "mrbeast_bold", "clean_minimal", "neon_glow",
            "cinematic_sub", "bounce_pop", "alex_cooper", "alex_cooper_pink", "ali_abdaal", "ali_abdaal_clean",
            "fintech_green", "fintech_emerald", "cyber_glitch", "glitch_cyber", "gadzhi_luxury", "iman_gadzhi_luxury",
            "high_retention_pop", "vox_documentary", "ssa_classic_sub", "podcast_bold",
            "em_bold", "em_bold_yellow", "nowy", "bouncy", "style_21", "corporate_un", "retro_vhs"
        ]
        if preset_id not in default_ids:
            self.btn_del = QPushButton("×")
            self.btn_del.setFixedSize(16, 16)
            self.btn_del.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #726c88;
                    border: none;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    color: #ff4444;
                }
            """)
            self.btn_del.clicked.connect(lambda: self.deleted.emit(preset_id))
            bot_row.addWidget(self.btn_del)

        layout.addLayout(bot_row)

    def mousePressEvent(self, event):
        self.clicked.emit(self.preset_data)
        super().mousePressEvent(event)

    def set_selected(self, selected):
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        accent = self._accent_hex()
        if self.is_selected:
            self.setStyleSheet(f"""
                QFrame#PresetCard {{
                    background-color: #1c1918;
                    border: 1.5px solid {accent};
                    border-radius: 10px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#PresetCard {{
                    background-color: #151416;
                    border: 1px solid #302d30;
                    border-radius: 10px;
                }}
                QFrame#PresetCard:hover {{
                    border: 1px solid {accent};
                    background-color: #1b1919;
                }}
            """)

    def _accent_hex(self):
        values = self.preset_data.get("accent_color") or self.preset_data.get("color", [0.72, 0.54, 0.38, 1.0])
        try:
            return QColor(*(int(max(0, min(1, float(v))) * 255) for v in values[:3])).name()
        except (TypeError, ValueError):
            return "#b77a56"


class TitlesTab(QWidget):
    """Full Titles / Presets Gallery Tab with Title Composer."""

    statusMessage = pyqtSignal(str)
    styleSelected = pyqtSignal(dict)
    presetApplied = pyqtSignal(dict)
    switchToAutoTab = pyqtSignal(dict)

    def __init__(self, bridge, builder, animator, parent=None):
        super().__init__(parent)
        self.bridge = bridge
        self.builder = builder
        self.animator = animator
        self.style_mgr = StyleManager()

        self.target_mode = "playhead"
        self.active_style = None
        self.preset_cards = []

        self._build_ui()
        self._load_presets()
        self._wire_signals()
        self._refresh_word_chips()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        # 1. Top Sub-Bar: Playhead / In/Out and Add from Timeline
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(4, 2, 4, 2)
        top_bar.setSpacing(4)

        self.btn_mode_playhead = QPushButton("Playhead")
        self.btn_mode_inout = QPushButton("In/Out")
        self.btn_mode_playhead.setStyleSheet(STYLE_PILL_ACTIVE)
        self.btn_mode_inout.setStyleSheet(STYLE_PILL_INACTIVE)
        top_bar.addWidget(self.btn_mode_playhead)
        top_bar.addWidget(self.btn_mode_inout)

        top_bar.addSpacing(4)

        self.btn_add_from_timeline = QPushButton("+ Add From Timeline")
        self.btn_add_from_timeline.setStyleSheet(STYLE_ORANGE_OUTLINE)
        top_bar.addWidget(self.btn_add_from_timeline)

        self.btn_import = QPushButton("Import...")
        self.btn_import.setStyleSheet("""
            QPushButton {
                background-color: #171328;
                border: 1px solid #28213e;
                border-radius: 6px;
                color: #a49ebd;
                font-weight: 600;
                font-size: 11px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #261f3e;
                color: #ffffff;
                border-color: #ff5500;
            }
        """)
        top_bar.addWidget(self.btn_import)

        self.btn_export = QPushButton("Export...")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #171329;
                border: 1px solid #28203f;
                border-radius: 6px;
                color: #a49ebd;
                font-weight: 600;
                font-size: 11px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #261f3e;
                color: #ffffff;
                border-color: #ff5500;
            }
        """)
        top_bar.addWidget(self.btn_export)
        top_bar.addStretch()

        layout.addLayout(top_bar)

        # 2. Search & Category Filter Row
        filter_bar = QHBoxLayout()
        filter_bar.setContentsMargins(4, 2, 4, 2)
        filter_bar.setSpacing(4)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Search styles...")
        self.txt_search.setFixedHeight(26)
        filter_bar.addWidget(self.txt_search, stretch=2)

        self.combo_category = QComboBox()
        self.combo_category.setFixedHeight(26)
        self.combo_category.addItems([
            "All Categories",
            "Clean Subtitles",
            "Bold Social",
            "Documentary",
            "Brand / Corporate",
            "Cinematic",
            "Kinetic / Tech",
            "Bengali / Multilingual",
            "Tutorial Inspired"
        ])
        filter_bar.addWidget(self.combo_category, stretch=1)

        layout.addLayout(filter_bar)

        # 3. Presets Scrollable Gallery Grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"background-color: {COLOR_BG}; border: none;")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet(f"background-color: {COLOR_BG};")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 2, 8, 2)
        self.grid_layout.setSpacing(6)
        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 1)

        self.scroll_area.setWidget(self.grid_container)
        layout.addWidget(self.scroll_area, stretch=3)

        # 4. Creator / Composer Drawer (Word Staging & Template Inserting)
        self.composer_frame = QFrame()
        self.composer_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #120f21;
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
        """)
        comp_layout = QVBoxLayout(self.composer_frame)
        comp_layout.setContentsMargins(8, 6, 8, 6)
        comp_layout.setSpacing(4)

        # Composer Header
        comp_top = QHBoxLayout()
        lbl_comp = QLabel("TITLE COMPOSER")
        lbl_comp.setStyleSheet(f"font-weight: 800; font-size: 10px; color: {COLOR_ORANGE}; letter-spacing: 1px;")
        comp_top.addWidget(lbl_comp)

        self.lbl_active_style_badge = QLabel("Active: None")
        self.lbl_active_style_badge.setStyleSheet("color: #8c85a6; font-size: 10px;")
        comp_top.addWidget(self.lbl_active_style_badge)
        comp_top.addStretch()

        self.btn_edit_in_auto = QPushButton("Edit in Auto ➔")
        self.btn_edit_in_auto.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ff5500;
                border: none;
                font-size: 10px;
                font-weight: 700;
            }
            QPushButton:hover {
                color: #ff7722;
                text-decoration: underline;
            }
        """)
        comp_top.addWidget(self.btn_edit_in_auto)
        comp_layout.addLayout(comp_top)

        # Composer Input
        self.txt_composer = QLineEdit("MIGHT BE THE EASIEST")
        self.txt_composer.setPlaceholderText("Enter caption phrase...")
        self.txt_composer.setFixedHeight(28)
        comp_layout.addWidget(self.txt_composer)

        # Word Chips Staging Area
        self.chips_container = QWidget()
        self.chips_row = QHBoxLayout(self.chips_container)
        self.chips_row.setContentsMargins(0, 2, 0, 2)
        self.chips_row.setSpacing(4)
        self.chips_row.addStretch()
        comp_layout.addWidget(self.chips_container)
        self.main_word = "EASIEST"

        spacing_row = QHBoxLayout()
        spacing_label = QLabel("Line spacing  ·  1.00 = normal")
        spacing_label.setStyleSheet("color: #8c85a6; font-size: 9px; font-weight: 600;")
        spacing_row.addWidget(spacing_label)
        self.spin_line_spacing = QDoubleSpinBox()
        self.spin_line_spacing.setRange(0.4, 2.5)
        self.spin_line_spacing.setSingleStep(0.05)
        self.spin_line_spacing.setDecimals(2)
        self.spin_line_spacing.setValue(1.0)
        self.spin_line_spacing.setFixedWidth(82)
        self.spin_line_spacing.setFixedHeight(24)
        self.spin_line_spacing.setToolTip("Text+ line spacing. 1.00 is the normal line spacing.")
        self.spin_line_spacing.setStyleSheet("QDoubleSpinBox { background:#100d19; color:#eee6dc; border:1px solid #30283b; border-radius:5px; padding:2px 5px; }")
        spacing_row.addWidget(self.spin_line_spacing)
        spacing_row.addSpacing(10)

        pair_label = QLabel("Dual-Font (80/20)")
        pair_label.setStyleSheet("color: #8c85a6; font-size: 9px; font-weight: 600;")
        spacing_row.addWidget(pair_label)
        self.combo_font_pairing = QComboBox()
        self.combo_font_pairing.setFixedHeight(24)
        self.combo_font_pairing.setStyleSheet("QComboBox { background:#100d19; color:#eee6dc; border:1px solid #30283b; border-radius:5px; padding:2px 8px; font-size:10px; }")
        self.combo_font_pairing.addItems([
            "Auto (Preset Default)",
            "Montserrat + Pinyon Script (Viral Creator)",
            "Inter + DM Serif Display (Editorial)",
            "Inter + Syne (Tech / SaaS)",
            "Didot + Playfair Display (Luxury)",
            "Kohinoor Bangla (Bengali Script)"
        ])
        spacing_row.addWidget(self.combo_font_pairing, stretch=1)
        comp_layout.addLayout(spacing_row)

        # Composer Actions: Templates & Hero Word Accent
        action_bar = QHBoxLayout()
        action_bar.setSpacing(4)

        self.btn_c_tpl1 = QPushButton("Template 1★")
        self.btn_c_tpl2 = QPushButton("Template 2")
        self.btn_c_tpl3 = QPushButton("Template 3")

        tpl_style = """
            QPushButton {
                background-color: #19142d;
                border: 1px solid #28203f;
                border-radius: 6px;
                color: #a49ebd;
                font-weight: 700;
                font-size: 10px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #272044;
                color: #ffffff;
                border-color: #ff5500;
            }
        """
        for b in [self.btn_c_tpl1, self.btn_c_tpl2, self.btn_c_tpl3]:
            b.setStyleSheet(tpl_style)
            action_bar.addWidget(b)

        action_bar.addSpacing(4)

        self.btn_hero_accent = QPushButton("2-Color 🎨")
        self.btn_hero_accent.setCheckable(True)
        self.btn_hero_accent.setStyleSheet("""
            QPushButton {
                background-color: #19142d;
                border: 1px solid #28203f;
                border-radius: 6px;
                color: #a49ebd;
                font-weight: 700;
                font-size: 10px;
                padding: 4px 8px;
            }
            QPushButton:checked {
                background-color: #3b170c;
                border-color: #ff5500;
                color: #ff5500;
            }
        """)
        action_bar.addWidget(self.btn_hero_accent)
        action_bar.addStretch()

        self.btn_insert_title = QPushButton("★ Insert Title")
        self.btn_insert_title.setStyleSheet("""
            QPushButton {
                background-color: #ff5500;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: 800;
                font-size: 11px;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background-color: #ff6a1a;
            }
        """)
        action_bar.addWidget(self.btn_insert_title)
        comp_layout.addLayout(action_bar)

        layout.addWidget(self.composer_frame, stretch=1)

    def _wire_signals(self):
        self.btn_mode_playhead.clicked.connect(lambda: self._set_target_mode("playhead"))
        self.btn_mode_inout.clicked.connect(lambda: self._set_target_mode("inout"))

        self.btn_add_from_timeline.clicked.connect(self._on_add_from_timeline)
        self.btn_import.clicked.connect(self._on_import_preset)
        self.btn_export.clicked.connect(self._on_export_preset)

        self.txt_search.textChanged.connect(self._filter_presets)
        self.combo_category.currentTextChanged.connect(self._filter_presets)

        self.btn_c_tpl1.clicked.connect(lambda: self._apply_composer_template(1))
        self.btn_c_tpl2.clicked.connect(lambda: self._apply_composer_template(2))
        self.btn_c_tpl3.clicked.connect(lambda: self._apply_composer_template(3))
        self.btn_hero_accent.toggled.connect(self._on_hero_accent_toggled)

        self.btn_insert_title.clicked.connect(self._on_insert_title_clicked)
        self.btn_edit_in_auto.clicked.connect(self._on_edit_in_auto_clicked)
        self.txt_composer.textChanged.connect(self._refresh_word_chips)
        self.combo_font_pairing.currentIndexChanged.connect(self._on_font_pairing_changed)

    def _on_font_pairing_changed(self, idx):
        if not self.active_style:
            return
        pairings = {
            1: ("Montserrat", "Pinyon Script", "Regular", 1.18),
            2: ("Inter", "DM Serif Display", "Italic", 1.12),
            3: ("Inter", "Syne", "Bold", 1.10),
            4: ("Didot", "Playfair Display", "Italic", 1.14),
            5: ("Kohinoor Bangla", "Kohinoor Bangla", "Bold", 1.15),
        }
        if idx in pairings:
            font, hero_font, hero_style, hero_mult = pairings[idx]
            self.active_style["font"] = font
            self.active_style["hero_font"] = hero_font
            self.active_style["hero_style"] = hero_style
            self.active_style["hero_size_multiplier"] = hero_mult
            self.statusMessage.emit(f"Applied dual-font pairing: {font} + {hero_font}")

    def _refresh_word_chips(self):
        while self.chips_row.count():
            item = self.chips_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        txt = self.txt_composer.text().strip()
        words = txt.split()
        if not words:
            self.chips_row.addStretch()
            return

        for w in words:
            btn = QPushButton(w)
            is_hero = (w.upper() == str(self.main_word).upper())
            if is_hero:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3b170c;
                        border: 1.5px solid #ff5500;
                        border-radius: 5px;
                        color: #ff5500;
                        font-weight: 800;
                        font-size: 10px;
                        padding: 3px 8px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #171329;
                        border: 1px solid #28203f;
                        border-radius: 5px;
                        color: #a49ebd;
                        font-weight: 600;
                        font-size: 10px;
                        padding: 3px 8px;
                    }
                    QPushButton:hover {
                        border-color: #ff5500;
                        color: #ffffff;
                    }
                """)
            btn.clicked.connect(lambda ch, word=w: self._set_hero_word(word))
            self.chips_row.addWidget(btn)

        self.chips_row.addStretch()

    def _set_hero_word(self, word):
        self.main_word = word
        self._refresh_word_chips()
        self.statusMessage.emit(f"Set Hero Word to '{word}' (emphasized on line 2)")

    def _set_target_mode(self, mode):
        self.target_mode = mode
        self.btn_mode_playhead.setStyleSheet(STYLE_PILL_ACTIVE if mode == "playhead" else STYLE_PILL_INACTIVE)
        self.btn_mode_inout.setStyleSheet(STYLE_PILL_ACTIVE if mode == "inout" else STYLE_PILL_INACTIVE)
        msg = f"Target mode: {mode.upper()} titles"
        self.statusMessage.emit(msg)

    def _load_presets(self):
        # Clear existing grid
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        self.preset_cards.clear()

        presets = self.style_mgr.get_presets()
        if not presets:
            lbl_empty = QLabel("No presets found.")
            lbl_empty.setStyleSheet("color: #777; font-size: 11px;")
            self.grid_layout.addWidget(lbl_empty, 0, 0)
            return

        row, col = 0, 0
        for p in presets:
            card = PresetCardWidget(p)
            card.clicked.connect(self._on_preset_clicked)
            card.applied.connect(self._on_preset_applied)
            card.deleted.connect(self._on_preset_deleted)
            self.grid_layout.addWidget(card, row, col)
            self.preset_cards.append((p, card))
            col += 1
            if col > 1:
                col = 0
                row += 1

        if not self.active_style and presets:
            self.select_preset(presets[0])

    def _filter_presets(self):
        query = self.txt_search.text().strip().lower()
        cat = self.combo_category.currentText().strip()

        for preset, card in self.preset_cards:
            name_match = query in preset.get("name", "").lower() or query in preset.get("text", "").lower()
            p_cat = preset.get("category", "").strip().lower()
            s_cat = cat.lower()

            if cat == "All Categories":
                cat_match = True
            elif s_cat == p_cat:
                cat_match = True
            elif "clean" in s_cat and ("clean" in p_cat or "ssa" in p_cat):
                cat_match = True
            elif "social" in s_cat and ("social" in p_cat or "retention" in p_cat or "easymotion" in p_cat):
                cat_match = True
            elif "documentary" in s_cat and ("documentary" in p_cat or "podcast" in p_cat or "vox" in p_cat):
                cat_match = True
            elif "corporate" in s_cat and ("corporate" in p_cat or "brand" in p_cat):
                cat_match = True
            elif "cinematic" in s_cat and ("cinematic" in p_cat or "film" in p_cat):
                cat_match = True
            elif "tech" in s_cat and ("tech" in p_cat or "gaming" in p_cat or "glitch" in p_cat or "kinetic" in p_cat):
                cat_match = True
            elif "bengali" in s_cat and ("bengali" in p_cat or "multilingual" in p_cat):
                cat_match = True
            else:
                cat_match = False

            card.setVisible(name_match and cat_match)

    def select_preset(self, preset_data):
        self.active_style = preset_data
        raw_ls = float(preset_data.get("line_spacing", 1.0))
        ui_ls = 1.0 if abs(raw_ls) < 0.05 else (raw_ls if raw_ls > 0.3 else 1.0 + raw_ls)
        self.spin_line_spacing.setValue(ui_ls)
        for p, card in self.preset_cards:
            card.set_selected(p.get("id") == preset_data.get("id"))
        self.lbl_active_style_badge.setText(f"Active: {preset_data.get('name', 'Style')}")
        self.styleSelected.emit(preset_data)

    def _on_preset_clicked(self, preset_data):
        self.select_preset(preset_data)
        self.statusMessage.emit(f"Selected style '{preset_data.get('name')}'")

    def _on_preset_applied(self, preset_data):
        self.select_preset(preset_data)
        self.presetApplied.emit(preset_data)
        targets = self.bridge.get_target_clips(self.target_mode)
        inserted_item = None
        if not targets:
            # Match the template workflow: a preset click always has a useful
            # timeline result. Reuse a target title when present; otherwise
            # create a native Text+ clip carrying the preset's sample copy.
            inserted_item = self.bridge.insert_text_plus_title()
            if inserted_item:
                targets = [inserted_item]
            else:
                self.statusMessage.emit("Could not insert title. Ensure an active timeline is open.")
                return

        records = []
        if not inserted_item:
            for item in targets:
                prev_style = self.builder.extract_style_from_clip(item) or {}
                records.append({
                    "item": item,
                    "prev_style": prev_style,
                    "new_style": dict(preset_data)
                })

        applied_count = 0
        failed_count = 0
        fusion_records = []
        for item in targets:
            before = None
            if not inserted_item:
                before = self.bridge.capture_fusion_comp_snapshot(item)
                if not before:
                    failed_count += 1
                    continue
            if item is inserted_item:
                current_text = preset_data.get("text", "SAMPLE TITLE")
            else:
                matching = next((r["prev_style"] for r in records if r["item"] is item), None)
                current_style = matching if matching is not None else (self.builder.extract_style_from_clip(item) or {})
                current_text = current_style.get("text") or preset_data.get("text", "SAMPLE TITLE")
            style_ok = self.builder.apply_style(item, preset_data, text_override=current_text)
            anim_in = preset_data.get("animation_in")
            anim_out = preset_data.get("animation_out")
            # Preserve the preset's authored animation entrance. Only resolve continuity
            # if the preset specifically requested "auto" or didn't define an entrance.
            if not anim_in and self.animator.has_motion_continuity():
                anim_in = "auto"
            motion_ok = True
            if style_ok and (anim_in or anim_out):
                motion_ok = self.animator.apply_motion_preset(item, effect_in=anim_in, effect_out=anim_out)

            if not style_ok or not motion_ok:
                failed_count += 1
                if inserted_item:
                    timeline = self.bridge.get_current_timeline()
                    if timeline:
                        timeline.DeleteClips([item])
                elif not self.bridge.restore_fusion_comp_snapshot(item, before):
                    self.statusMessage.emit("Preset apply failed and its previous Fusion comp could not be restored. Inspect the affected title before continuing.")
                else:
                    self.bridge.discard_fusion_comp_snapshot(before)
                continue

            if inserted_item:
                applied_count += 1
            else:
                after = self.bridge.capture_fusion_comp_snapshot(item)
                if after:
                    fusion_records.append({"item": item, "before": before, "after": after})
                    applied_count += 1
                else:
                    failed_count += 1
                    if not self.bridge.restore_fusion_comp_snapshot(item, before):
                        self.statusMessage.emit("Preset apply succeeded but the undo backup failed, and the previous Fusion comp could not be restored. Inspect the affected title.")
                    else:
                        self.bridge.discard_fusion_comp_snapshot(before)

        if inserted_item and applied_count:
            self.bridge.push_undo_snapshot([inserted_item], f"Insert {preset_data.get('name', 'Preset')} Title")
            self.statusMessage.emit(f"Inserted editable Text+ title with preset '{preset_data.get('name')}'.")
        elif inserted_item:
            self.statusMessage.emit(f"Preset '{preset_data.get('name')}' could not be applied; no title was created.")
        else:
            if fusion_records:
                self.bridge.push_fusion_snapshot(fusion_records, f"Apply {preset_data.get('name', 'Preset')}")
            if applied_count:
                self.statusMessage.emit(f"Applied preset '{preset_data.get('name')}' to {applied_count} title(s); full Fusion undo/redo is available.")
            else:
                self.statusMessage.emit(f"Preset '{preset_data.get('name')}' was not applied. Check the selected title and Resolve connection.")
        if failed_count and applied_count:
            self.statusMessage.emit(f"Preset applied to {applied_count} of {len(targets)} title(s); {failed_count} failed.")

    def _on_preset_deleted(self, preset_id):
        res = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete preset '{preset_id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            if self.style_mgr.delete_preset(preset_id):
                self._load_presets()
                self.statusMessage.emit(f"Deleted preset '{preset_id}'")

    def _on_add_from_timeline(self):
        targets = self.bridge.get_target_clips("playhead")
        if not targets:
            QMessageBox.warning(self, "No Title", "Please position the playhead over a Text+ title on the timeline.")
            return

        clip = targets[0]
        extracted = self.builder.extract_style_from_clip(clip)
        if not extracted:
            QMessageBox.warning(self, "Extraction Failed", "Could not extract Text+ styling from the selected clip.")
            return

        name, ok = QInputDialog.getText(self, "Save Preset", "Enter name for new Style Preset:", text="My Timeline Style")
        if ok and name.strip():
            preset_id = name.strip().lower().replace(" ", "_")
            extracted["id"] = preset_id
            extracted["name"] = name.strip()
            extracted["category"] = "Custom"
            if self.style_mgr.save_preset(preset_id, extracted):
                self._load_presets()
                self.statusMessage.emit(f"Saved timeline style as '{name.strip()}'!")

    def _on_import_preset(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Style Preset", "", "JSON Files (*.json)")
        if path and os.path.exists(path):
            try:
                import json
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("Preset JSON must contain an object.")
                raw_id = data.get("id") or os.path.splitext(os.path.basename(path))[0]
                preset_id = "".join(c for c in str(raw_id) if c.isalnum() or c in ("_", "-")).lower() or "preset_custom"
                if self.style_mgr.get_preset_by_id(preset_id):
                    answer = QMessageBox.question(
                        self,
                        "Replace Existing Preset?",
                        f"A preset with ID '{preset_id}' already exists. Replace it?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if answer != QMessageBox.StandardButton.Yes:
                        return
                if self.style_mgr.import_preset(path):
                    self._load_presets()
                    self.statusMessage.emit("Successfully imported preset!")
                else:
                    QMessageBox.warning(self, "Import Failed", "Invalid preset file format.")
            except Exception as e:
                QMessageBox.warning(self, "Import Failed", f"Could not read preset: {e}")

    def _on_export_preset(self):
        if not self.active_style:
            QMessageBox.information(self, "No Style Selected", "Please select a style preset to export.")
            return

        suggested = f"{self.active_style.get('id', 'style_preset')}.json"
        path, _ = QFileDialog.getSaveFileName(self, "Export Style Preset", suggested, "JSON Files (*.json)")
        if path:
            try:
                import json
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.active_style, f, indent=2, ensure_ascii=False)
                self.statusMessage.emit(f"Exported style '{self.active_style.get('name')}' to {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.warning(self, "Export Failed", f"Could not export style preset: {e}")

    def _apply_composer_template(self, t_num):
        txt = self.txt_composer.text().strip()
        if not txt:
            return
        style = self.active_style or {}
        formatted = self.builder.apply_layout_template(
            txt, template_num=t_num, main_word=self.main_word, hero_font=style.get("hero_font")
        )
        self.txt_composer.setText(formatted.replace("\n", " "))
        self.statusMessage.emit(f"Formatted composer text with Template {t_num}")

    def _on_hero_accent_toggled(self, checked):
        if checked:
            hw = self.main_word or "Accent"
            self.statusMessage.emit(f"2-Color mode enabled: Accent color applied to hero word ('{hw}').")
        else:
            self.statusMessage.emit("2-Color mode disabled: Standard palette restored.")

    def _on_insert_title_clicked(self):
        txt = self.txt_composer.text().strip()
        if not txt:
            self.statusMessage.emit("Please enter text into the composer.")
            return

        style = dict(self.active_style or self.builder.DEFAULT_STYLE)
        ui_val = self.spin_line_spacing.value()
        # In DaVinci Resolve TextPlus LineSpacingClone: 0.0 is normal single spacing
        style["line_spacing"] = 0.0 if abs(ui_val - 1.0) < 0.01 else (ui_val - 1.0)
        item = self.bridge.insert_text_plus_title()
        if not item:
            self.statusMessage.emit("Could not insert title. Ensure an active timeline is open.")
            return

        # 2-Color Accent styling
        if self.btn_hero_accent.isChecked():
            style["use_2color"] = True
            style["main_word"] = self.main_word
            style["accent_color"] = style.get("accent_color") or [1.0, 0.85, 0.0, 1.0] # High-retention Gold/Yellow
            if not style.get("stroke_enabled") and not style.get("box_enabled"):
                style["stroke_enabled"] = True
                style["stroke_color"] = [0.0, 0.0, 0.0, 1.0]
                style["stroke_thickness"] = 0.028

        # Format layout using hero word or templates
        words = txt.split()
        if self.main_word and len(words) > 1:
            formatted = self.builder.apply_layout_template(txt, template_num=1, main_word=self.main_word)
        elif len(words) > 2:
            formatted = self.builder.apply_layout_template(txt, template_num=2)
        else:
            formatted = txt

        self.builder.apply_style(item, style, text_override=formatted)

        # Apply AUTO continuity motion
        next_dir = self.animator.get_auto_next_direction()
        self.animator.apply_motion_preset(item, effect_in=f"bounce_{next_dir}", effect_out="slide_down", options={"motion_blur": True})
        self.bridge.push_undo_snapshot([item], "Insert Composed Title")

        self.statusMessage.emit(f"Inserted title '{txt}' with AUTO continuity motion!")

    def _on_edit_in_auto_clicked(self):
        if self.active_style:
            self.switchToAutoTab.emit(self.active_style)
        else:
            self.statusMessage.emit("Select a style first.")
