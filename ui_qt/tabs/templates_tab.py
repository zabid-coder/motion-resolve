"""
Motion Resolve - Typography Template Engine Tab (PyQt6)
Enterprise template review gallery with category filter pills,
60fps scrub canvas, instant search, and one-click Fusion compiler.
"""

import os
import json
import re
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QScrollArea, QFrame, QSlider, QCheckBox,
    QColorDialog, QMessageBox, QGridLayout, QFileDialog, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QEvent
from PyQt6.QtGui import QColor

from core.templates.registry import TemplateRegistry
from core.templates.fusion_compiler import FusionCompiler
from core.templates.theme_tokens import get_theme, get_available_themes
from core.templates.schema import ParameterType, TemplateSpec
from ui_qt.widgets.template_canvas_area import TemplateCanvasArea
from ui_qt.styles import (
    COLOR_BG_BASE, COLOR_SURFACE_CARD, COLOR_BORDER_SUBTLE,
    COLOR_ACCENT_ORANGE, COLOR_ACCENT_HOVER, COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    STYLE_PILL_ACTIVE, STYLE_PILL_INACTIVE
)

# Semantic aliases
COLOR_BG = COLOR_BG_BASE
COLOR_CARD = COLOR_SURFACE_CARD
COLOR_BORDER = COLOR_BORDER_SUBTLE
COLOR_ORANGE = COLOR_ACCENT_ORANGE
COLOR_TEXT = COLOR_TEXT_PRIMARY
COLOR_MUTED = COLOR_TEXT_SECONDARY


def get_template_pill_category_key(category: str) -> str:
    """Map any category name to one of the 8 canonical pill categories."""
    c = str(category or "").lower()
    if "agency" in c or "viral" in c:
        return "viral_agency"
    if "saas" in c or "tech" in c:
        return "saas_tech"
    if "cinematic" in c or "documentary" in c or "ngo" in c:
        return "cinematic_doc"
    if "minimal" in c or "luxury" in c:
        return "minimal_luxury"
    if "editorial" in c or "magazine" in c or "broadcast" in c or "news" in c:
        return "broadcast_news"
    if "kinetic" in c or "bold" in c:
        return "bold_kinetic"
    if "podcast" in c or "reels" in c or "social" in c or "creator" in c:
        return "modern_creator"
    return "other"


CATEGORY_PILLS = [
    ("all", "All"),
    ("viral_agency", "Viral Agency"),
    ("saas_tech", "SaaS & Tech"),
    ("cinematic_doc", "Cinematic Documentary"),
    ("minimal_luxury", "Minimal Luxury"),
    ("modern_creator", "Modern Creator"),
    ("broadcast_news", "Broadcast & News"),
    ("bold_kinetic", "Bold Kinetic"),
]


def _recommended_theme_id(category: str) -> str:
    """Map a template family to a restrained starting palette."""
    value = str(category or "").casefold()
    if "editorial" in value or "magazine" in value or "broadcast" in value:
        return "porcelain"
    if "cinematic" in value:
        return "warm"
    if "podcast" in value or "saas" in value:
        return "frosted_slate"
    if "documentary" in value or "corporate" in value:
        return "rosewood"
    if "kinetic" in value:
        return "ocean"
    if "social" in value or "reel" in value or "agency" in value:
        return "warm"
    return "mono"


class TemplateCardWidget(QFrame):
    """Pro template card displaying aspect ratio badges, font pairing info, and quick apply."""

    clicked = pyqtSignal(object)
    quick_apply = pyqtSignal(object)

    def __init__(self, template_spec: TemplateSpec, is_selected: bool = False, parent=None):
        super().__init__(parent)
        self.template_spec = template_spec
        self.is_selected = is_selected
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui()
        self.update_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)

        # 1. Top row: Name, Category badge, Aspect ratio badges
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        self.lbl_name = QLabel(self.template_spec.name)
        self.lbl_name.setStyleSheet("font-weight: 700; font-size: 12px; color: #ffffff;")
        top_row.addWidget(self.lbl_name)
        top_row.addStretch()

        # Aspect ratio badges
        self.ratio_badges = []
        for ar in getattr(self.template_spec, "aspect_ratios", ["16:9"]):
            lbl_ar = QLabel(str(ar))
            lbl_ar.setStyleSheet("""
                background-color: #1a162b;
                color: #ff9944;
                border: 1px solid #362952;
                border-radius: 3px;
                padding: 1px 4px;
                font-size: 9px;
                font-weight: 700;
            """)
            top_row.addWidget(lbl_ar)
            self.ratio_badges.append(lbl_ar)

        # Category badge
        self.lbl_cat = QLabel(self.template_spec.category)
        self.lbl_cat.setStyleSheet("""
            background-color: #211a36;
            color: #b3a8d4;
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 9px;
            font-weight: 700;
        """)
        top_row.addWidget(self.lbl_cat)
        self.lbl_cat.setToolTip(
            f"{self.template_spec.category} · Ratios: "
            f"{', '.join(str(ar) for ar in getattr(self.template_spec, 'aspect_ratios', ['16:9']))}"
        )
        layout.addLayout(top_row)

        # 2. Preview canvas thumbnail
        self.preview = TemplateCanvasArea()
        self.preview.setMinimumHeight(135)
        self.preview.setMaximumHeight(145)
        self.preview.setStyleSheet("""
            QFrame {
                background-color: #0b0a10;
                border: 1px solid #282432;
                border-radius: 6px;
            }
        """)
        sample_params = {param.id: param.default for param in self.template_spec.parameters}
        sample_theme = get_theme(_recommended_theme_id(self.template_spec.category))
        preview_time = min(
            max(self.template_spec.in_duration + 0.08, 0.85),
            max(0.85, self.template_spec.duration_default - self.template_spec.out_duration - 0.08),
        )
        self.preview.set_state(self.template_spec, sample_params, sample_theme, preview_time)
        layout.addWidget(self.preview)

        # 3. Description
        desc = self.template_spec.description
        if len(desc) > 85:
            desc = desc[:82] + "..."
        self.lbl_desc = QLabel(desc)
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("color: #8c85a6; font-size: 10px;")
        layout.addWidget(self.lbl_desc)

        # 4. Font pairing & duration row
        bot_row = QHBoxLayout()
        bot_row.setSpacing(6)

        font_pairing = self._get_font_pairing()
        self.lbl_font = QLabel(f"Aa {font_pairing}")
        self.lbl_font.setStyleSheet("color: #9d93b8; font-size: 9px; font-weight: 600;")
        bot_row.addWidget(self.lbl_font)

        self.lbl_dur = QLabel(f"⏱ {self.template_spec.duration_default}s ({self.template_spec.in_duration}s in)")
        self.lbl_dur.setStyleSheet("color: #ff7722; font-size: 9px; font-weight: 600;")
        bot_row.addWidget(self.lbl_dur)

        bot_row.addStretch()

        # Quick Apply Button
        self.btn_quick_apply = QPushButton("⚡ Apply")
        self.btn_quick_apply.setFixedHeight(22)
        self.btn_quick_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_quick_apply.setStyleSheet("""
            QPushButton {
                background-color: #ff5500;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 700;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #ff6a1a;
            }
        """)
        self.btn_quick_apply.clicked.connect(self._on_quick_apply_clicked)
        bot_row.addWidget(self.btn_quick_apply)

        layout.addLayout(bot_row)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        compact = self.width() < 560
        for badge in self.ratio_badges:
            badge.setVisible(not compact)

    def _get_font_pairing(self) -> str:
        fonts = []
        for layer in getattr(self.template_spec, "layers", []):
            f = layer.props.get("font")
            if f and isinstance(f, str) and f not in fonts:
                if not f.startswith("param:") and not f.startswith("$") and not f.startswith("token:"):
                    fonts.append(f)
        if not fonts and hasattr(self.template_spec, "parameters"):
            for p in self.template_spec.parameters:
                if p.type == ParameterType.FONT and p.default:
                    fonts.append(str(p.default))
        if len(fonts) >= 2:
            return f"{fonts[0]} + {fonts[1]}"
        elif len(fonts) == 1:
            return f"{fonts[0]} + Inter"
        return "Syne + Inter"

    def _on_quick_apply_clicked(self):
        self.quick_apply.emit(self.template_spec)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        if self.is_selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #1c1530;
                    border: 1.5px solid {COLOR_ORANGE};
                    border-radius: 8px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #120e21;
                    border: 1px solid #261f3e;
                    border-radius: 8px;
                }}
                QFrame:hover {{
                    background-color: #19142e;
                    border-color: #4a3d75;
                }}
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.template_spec)
        super().mousePressEvent(event)


class PreviewPlayerAdapter:
    """Backward-compatible adapter for tests and legacy callers accessing preview_player."""

    def __init__(self, tab: "TemplatesTab"):
        self._tab = tab
        self._playback_time = 0.8

    @property
    def canvas(self):
        return self._tab.canvas_area

    @property
    def is_playing(self) -> bool:
        return self._tab.is_playing

    @is_playing.setter
    def is_playing(self, val: bool):
        self._tab.is_playing = bool(val)

    @property
    def playback_time(self) -> float:
        return self._playback_time

    @playback_time.setter
    def playback_time(self, val: float):
        self._playback_time = float(val)

    def _toggle_playback(self):
        self._tab._toggle_playback()

    def _on_slider_scrubbed(self, val_ms: int):
        self._playback_time = float(val_ms) / 1000.0
        total_dur = self._tab.active_template.duration_default if self._tab.active_template else 4.5
        phase = max(0.0, min(1.0, self._playback_time / max(0.1, total_dur)))
        self._tab.slider_scrub.setValue(int(round(phase * 100.0)))

    def set_template(self, template: TemplateSpec, params: Dict[str, Any], theme: Dict[str, Any]):
        self._tab.canvas_area.set_state(template, params, theme, self._tab.canvas_area.current_time)

    def update_params(self, params: Dict[str, Any]):
        self._tab.canvas_area.params = params
        self._tab.canvas_area.update()


class TemplatesTab(QWidget):
    """Main tab for Declarative Typography Template Engine."""

    statusMessage = pyqtSignal(str)

    def __init__(self, bridge=None, builder=None, animator=None, parent=None):
        super().__init__(parent)
        self.bridge = bridge
        self.builder = builder
        self.animator = animator
        self.registry = TemplateRegistry()
        self.compiler = FusionCompiler(self.bridge, animator=self.animator) if self.bridge else None

        self.active_template: Optional[TemplateSpec] = None
        self.active_theme = "mono"
        self._manual_theme_choice = False
        self.active_params: Dict[str, Any] = {}
        self.cards: List[tuple] = []
        self.is_playing = False
        self.active_category_key = "all"
        self.pill_buttons: Dict[str, QPushButton] = {}
        self._gallery_columns = 0

        self._build_ui()
        self._load_templates()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # 1. Search Bar & Theme Control Bar
        hdr_bar = QHBoxLayout()
        hdr_bar.setSpacing(6)

        # Instant search input with clear button
        self.search_input = QLineEdit()
        self.search_input.setFixedHeight(26)
        self.search_input.setPlaceholderText("Search templates (name, description, tags)... 🔍")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #171325;
                color: #f3f1fa;
                border: 1px solid #282140;
                border-radius: 6px;
                padding: 3px 8px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 1px solid #ff5500;
            }
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_bar = self.search_input  # convenient alias
        hdr_bar.addWidget(self.search_input, stretch=2)

        lbl_theme = QLabel("Theme:")
        lbl_theme.setStyleSheet("color: #928ba8; font-size: 11px; font-weight: 600;")
        hdr_bar.addWidget(lbl_theme)

        self.combo_theme = QComboBox()
        self.combo_theme.setFixedHeight(26)
        for t in get_available_themes():
            self.combo_theme.addItem(t["name"], t["id"])
        self.combo_theme.currentIndexChanged.connect(self._on_theme_changed)
        hdr_bar.addWidget(self.combo_theme, stretch=1)

        # Legacy combobox compatibility (hidden or synced)
        self.combo_cat = QComboBox()
        self.combo_cat.setVisible(False)
        self.combo_cat.addItem("All Categories", "all")
        for cat in self.registry.get_categories():
            self.combo_cat.addItem(cat, cat)
        hdr_bar.addWidget(self.combo_cat)

        btn_style = """
            QPushButton {
                background-color: #171329;
                border: 1px solid #28203f;
                border-radius: 5px;
                color: #a49ebd;
                font-weight: 600;
                font-size: 10px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                border-color: #ff5500;
                color: #ffffff;
            }
        """
        self.btn_import_template = QPushButton("⇩ Import...")
        self.btn_import_template.setFixedHeight(26)
        self.btn_import_template.setStyleSheet(btn_style)
        self.btn_import_template.clicked.connect(self._on_import_template_clicked)
        hdr_bar.addWidget(self.btn_import_template)

        self.btn_export_template = QPushButton("⇪ Export...")
        self.btn_export_template.setFixedHeight(26)
        self.btn_export_template.setStyleSheet(btn_style)
        self.btn_export_template.clicked.connect(self._on_export_template_clicked)
        hdr_bar.addWidget(self.btn_export_template)

        layout.addLayout(hdr_bar)

        # 2. Category Filter Pills Row (wrapped in QButtonGroup)
        self.pill_scroll = QScrollArea()
        self.pill_scroll.setWidgetResizable(True)
        self.pill_scroll.setFixedHeight(42)
        self.pill_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.pill_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.pill_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.pill_scroll.setStyleSheet("background: transparent; border: none;")

        self.pill_container = QWidget()
        self.pill_container.setStyleSheet("background: transparent;")
        self.pill_layout = QHBoxLayout(self.pill_container)
        self.pill_layout.setContentsMargins(0, 2, 0, 2)
        self.pill_layout.setSpacing(6)

        self.category_button_group = QButtonGroup(self)
        self.category_button_group.setExclusive(True)

        self._populate_category_pills()
        self.pill_scroll.setWidget(self.pill_container)
        layout.addWidget(self.pill_scroll)

        # 3. Templates Scrollable Grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"background-color: {COLOR_BG}; border: none;")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet(f"background-color: {COLOR_BG};")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(2, 2, 2, 2)
        self.grid_layout.setSpacing(6)

        self.scroll_area.setWidget(self.grid_container)
        self.scroll_area.viewport().installEventFilter(self)
        layout.addWidget(self.scroll_area, stretch=3)

        # 4. Dynamic Parameter Inspector
        self.inspector_frame = QFrame()
        self.inspector_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #120e21;
                border: 1px solid #282142;
                border-radius: 8px;
            }}
        """)
        self.inspector_layout = QVBoxLayout(self.inspector_frame)
        self.inspector_layout.setContentsMargins(8, 6, 8, 6)
        self.inspector_layout.setSpacing(5)

        insp_header = QHBoxLayout()
        self.lbl_insp_title = QLabel("TEMPLATE INSPECTOR")
        self.lbl_insp_title.setStyleSheet(f"font-weight: 800; font-size: 10px; color: {COLOR_ORANGE}; letter-spacing: 1px;")
        insp_header.addWidget(self.lbl_insp_title)
        insp_header.addStretch()

        self.lbl_active_name = QLabel("Select a template")
        self.lbl_active_name.setStyleSheet("color: #b5adc9; font-size: 10px; font-weight: 600;")
        insp_header.addWidget(self.lbl_active_name)
        self.inspector_layout.addLayout(insp_header)

        # 4b. Scrub Canvas Area
        self.canvas_area = TemplateCanvasArea(self)
        self.inspector_layout.addWidget(self.canvas_area)

        # 4c. Interactive Scrubbing & Playback Bar
        ctrl_bar = QHBoxLayout()
        ctrl_bar.setContentsMargins(2, 2, 2, 2)
        ctrl_bar.setSpacing(8)

        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedWidth(38)
        self.btn_play.setFixedHeight(26)
        self.btn_play.setStyleSheet(STYLE_PILL_INACTIVE)
        self.btn_play.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play.setToolTip("Play / Pause Animation")
        self.btn_play.clicked.connect(self._toggle_playback)
        ctrl_bar.addWidget(self.btn_play)

        self.slider_scrub = QSlider(Qt.Orientation.Horizontal)
        self.slider_scrub.setRange(0, 100)
        self.slider_scrub.setValue(0)
        self.slider_scrub.setFixedHeight(24)
        self.slider_scrub.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #231b38;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #ff5500;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 2px solid #ff5500;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)
        self.slider_scrub.valueChanged.connect(self._on_scrub_changed)
        ctrl_bar.addWidget(self.slider_scrub, stretch=1)

        self.lbl_timecode = QLabel("00:00 / 03:00")
        self.lbl_timecode.setStyleSheet("color: #a49ebd; font-size: 11px; font-weight: 700; min-width: 90px;")
        self.lbl_timecode.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        ctrl_bar.addWidget(self.lbl_timecode)

        self.inspector_layout.addLayout(ctrl_bar)

        # Setup 60fps / 40fps playback timer (~25ms interval)
        self.playback_timer = QTimer(self)
        self.playback_timer.setInterval(25)
        self.playback_timer.timeout.connect(self._on_playback_tick)
        self.timer = self.playback_timer  # alias

        # Backward compatibility adapter for test_ui.py
        self.preview_player = PreviewPlayerAdapter(self)

        # Dynamic fields container
        self.fields_container = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.setContentsMargins(0, 0, 0, 0)
        self.fields_layout.setSpacing(4)
        self.inspector_layout.addWidget(self.fields_container)

        # 5. Action Bar (Apply to Timeline)
        self.btn_apply = QPushButton("★ Apply Template to Timeline")
        self.btn_apply.setToolTip(
            "Apply this editable Fusion/Text+ design to the title under the playhead; "
            "if none is there, insert a new title clip."
        )
        self.btn_apply.setFixedHeight(34)
        self.btn_apply.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ORANGE};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background-color: #ff6a1a;
            }}
        """)
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        self.inspector_layout.addWidget(self.btn_apply)

        layout.addWidget(self.inspector_frame, stretch=2)

    def _populate_category_pills(self):
        for btn in self.category_button_group.buttons():
            self.category_button_group.removeButton(btn)
            btn.deleteLater()
        self.pill_buttons.clear()

        all_templates = self.registry.get_all()
        counts = {"all": len(all_templates)}
        for t in all_templates:
            k = get_template_pill_category_key(t.category)
            counts[k] = counts.get(k, 0) + 1

        for idx, (cat_key, cat_name) in enumerate(CATEGORY_PILLS):
            cnt = counts.get(cat_key, 0)
            btn = QPushButton(f"{cat_name} ({cnt})")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            is_active = (cat_key == self.active_category_key)
            btn.setChecked(is_active)
            btn.setStyleSheet(STYLE_PILL_ACTIVE if is_active else STYLE_PILL_INACTIVE)
            self.category_button_group.addButton(btn, idx)
            self.pill_buttons[cat_key] = btn
            btn.clicked.connect(lambda checked, key=cat_key: self._on_category_pill_clicked(key))
            self.pill_layout.addWidget(btn)

        self.pill_layout.addStretch()

    def _on_category_pill_clicked(self, key: str):
        self.active_category_key = key
        for cat_k, btn in self.pill_buttons.items():
            if cat_k == key:
                btn.setChecked(True)
                btn.setStyleSheet(STYLE_PILL_ACTIVE)
            else:
                btn.setChecked(False)
                btn.setStyleSheet(STYLE_PILL_INACTIVE)
        self._filter_cards()

    def _on_search_changed(self, text: str):
        self._filter_cards()

    def _filter_cards(self):
        query = self.search_input.text().strip().lower()
        visible_cards = []

        for tpl, card in self.cards:
            tpl_key = get_template_pill_category_key(tpl.category)
            cat_match = (self.active_category_key == "all" or tpl_key == self.active_category_key)

            if not query:
                search_match = True
            else:
                tags = " ".join(getattr(tpl, "tags", []) or []).lower()
                search_match = (
                    query in tpl.name.lower() or
                    query in tpl.description.lower() or
                    query in tpl.category.lower() or
                    query in tags or
                    query in tpl.id.lower()
                )

            is_vis = bool(cat_match and search_match)
            card.setVisible(is_vis)
            if is_vis:
                visible_cards.append((tpl, card))

        self._reflow_template_cards()

        # If current template is not in visible list, select first visible
        if visible_cards and self.active_template:
            if not any(t.id == self.active_template.id for t, _ in visible_cards):
                self._on_template_selected(visible_cards[0][0])

    def _toggle_playback(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play.setText("❚❚")
            self.playback_timer.start(25)
        else:
            self.btn_play.setText("▶")
            self.playback_timer.stop()

    def _on_playback_tick(self):
        if not self.is_playing:
            return
        val = self.slider_scrub.value()
        next_val = (val + 1) if val < 100 else 0
        self.slider_scrub.setValue(next_val)

    def _on_scrub_changed(self, val: int):
        phase = max(0.0, min(1.0, float(val) / 100.0))
        self.canvas_area.set_playback_phase(phase)
        self._update_timecode(phase)

    def _update_timecode(self, phase: float):
        dur = float(self.active_template.duration_default) if self.active_template else 3.0
        curr_sec = phase * dur

        m_curr, s_curr = divmod(int(curr_sec), 60)
        f_curr = int((curr_sec - int(curr_sec)) * 30.0)
        m_tot, s_tot = divmod(int(dur), 60)
        f_tot = int((dur - int(dur)) * 30.0)

        if dur >= 60.0:
            self.lbl_timecode.setText(f"{m_curr:02d}:{s_curr:02d} / {m_tot:02d}:{s_tot:02d}")
        else:
            self.lbl_timecode.setText(f"{s_curr:02d}:{f_curr:02d} / {s_tot:02d}:{f_tot:02d}")

    def _load_templates(self):
        for _, card in self.cards:
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()

        templates = self.registry.get_all()

        for idx, t in enumerate(templates):
            card = TemplateCardWidget(t, is_selected=(idx == 0))
            card.clicked.connect(self._on_template_selected)
            card.quick_apply.connect(self._on_quick_apply_clicked)
            self.cards.append((t, card))

        self._reflow_template_cards()

        self._populate_category_pills()
        self._filter_cards()

        if templates:
            self._on_template_selected(templates[0])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self._reflow_template_cards)

    def eventFilter(self, obj, event):
        if (hasattr(self, "scroll_area") and obj is self.scroll_area.viewport()
                and event.type() == QEvent.Type.Resize):
            QTimer.singleShot(0, self._reflow_template_cards)
        return super().eventFilter(obj, event)

    def _reflow_template_cards(self):
        """Keep cards compact on wide windows and unclipped in the narrow dock."""
        if not hasattr(self, "scroll_area") or not hasattr(self, "grid_layout"):
            return
        width = self.scroll_area.viewport().width()
        columns = 1 if width < 760 else (2 if width < 1540 else 3)
        if columns == self._gallery_columns:
            return

        self._gallery_columns = columns
        while self.grid_layout.count():
            self.grid_layout.takeAt(0)
        for index, (_, card) in enumerate(self.cards):
            row, col = divmod(index, columns)
            self.grid_layout.addWidget(card, row, col)
        for col in range(3):
            self.grid_layout.setColumnStretch(col, 1 if col < columns else 0)

    def _on_theme_changed(self):
        self._manual_theme_choice = True
        self.active_theme = self.combo_theme.currentData() or "mono"
        if self.active_template:
            self.canvas_area.set_state(
                self.active_template,
                self.active_params,
                get_theme(self.active_theme),
                self.canvas_area.current_time
            )
        self.statusMessage.emit(f"Switched global theme to '{self.combo_theme.currentText()}'")

    def select_template(self, tpl: TemplateSpec):
        """Public method to select a template and rebuild inspector & preview."""
        self._on_template_selected(tpl)

    def _on_template_selected(self, tpl: TemplateSpec):
        self.active_template = tpl
        if not self._manual_theme_choice:
            recommended = _recommended_theme_id(tpl.category)
            theme_index = self.combo_theme.findData(recommended)
            if theme_index >= 0 and theme_index != self.combo_theme.currentIndex():
                self.combo_theme.blockSignals(True)
                self.combo_theme.setCurrentIndex(theme_index)
                self.combo_theme.blockSignals(False)
                self.active_theme = recommended

        for t, card in self.cards:
            card.set_selected(t.id == tpl.id)

        self.lbl_active_name.setText(tpl.name)
        self._rebuild_inspector(tpl)

        self.canvas_area.set_state(
            tpl,
            self.active_params,
            get_theme(self.active_theme),
            tpl.in_duration + 0.1
        )
        self.slider_scrub.blockSignals(True)
        self.slider_scrub.setValue(int(round(self.canvas_area.playback_phase * 100.0)))
        self.slider_scrub.blockSignals(False)
        self._update_timecode(self.canvas_area.playback_phase)
        self.statusMessage.emit(f"Loaded template: {tpl.name}")

    def _on_quick_apply_clicked(self, tpl: TemplateSpec):
        self._on_template_selected(tpl)
        self._on_apply_clicked()

    def _rebuild_inspector(self, tpl: TemplateSpec):
        while self.fields_layout.count():
            item = self.fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        self.active_params = {}

        for p in tpl.parameters:
            self.active_params[p.id] = p.default
            row = QHBoxLayout()
            row.setSpacing(6)

            lbl = QLabel(p.name)
            lbl.setFixedWidth(110)
            lbl.setStyleSheet("color: #928ba8; font-size: 10px; font-weight: 600;")
            row.addWidget(lbl)

            if p.type == ParameterType.STRING:
                txt = QLineEdit(str(p.default))
                txt.setFixedHeight(24)
                txt.setStyleSheet("""
                    QLineEdit {
                        background-color: #0c0916;
                        border: 1px solid #282140;
                        border-radius: 4px;
                        color: #ffffff;
                        padding: 2px 6px;
                        font-size: 11px;
                    }
                """)
                txt.textChanged.connect(lambda val, pid=p.id: self._set_param(pid, val))
                row.addWidget(txt, stretch=1)

            elif p.type == ParameterType.NUMBER:
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setFixedHeight(20)
                min_v = int((p.min_val or 0.0) * 100)
                max_v = int((p.max_val or 1.0) * 100)
                slider.setRange(min_v, max_v)
                slider.setValue(int(float(p.default) * 100))
                lbl_val = QLabel(f"{float(p.default):.2f}")
                lbl_val.setFixedWidth(36)
                lbl_val.setStyleSheet("color: #ff7722; font-size: 10px; font-weight: bold;")

                def on_slide(val, pid=p.id, label=lbl_val):
                    fval = val / 100.0
                    label.setText(f"{fval:.2f}")
                    self._set_param(pid, fval)

                slider.valueChanged.connect(on_slide)
                row.addWidget(slider, stretch=1)
                row.addWidget(lbl_val)

            elif p.type == ParameterType.BOOLEAN:
                chk = QCheckBox("Enable")
                chk.setChecked(bool(p.default))
                chk.setStyleSheet("color: #ffffff; font-size: 10px;")
                chk.toggled.connect(lambda val, pid=p.id: self._set_param(pid, val))
                row.addWidget(chk)
                row.addStretch()

            elif p.type == ParameterType.COLOR:
                cur_color = str(p.default) if p.default else "#ff5500"
                btn_color = QPushButton(f"  {cur_color}")
                btn_color.setFixedHeight(24)
                btn_color.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {cur_color};
                        color: {"#000000" if cur_color.lower() in ["#ffffff", "#ffe500", "#00ffcc", "#00ffff"] else "#ffffff"};
                        border: 1px solid #3d345c;
                        border-radius: 4px;
                        font-size: 10px;
                        font-weight: bold;
                        text-align: left;
                        padding-left: 8px;
                    }}
                    QPushButton:hover {{
                        border-color: #ff5500;
                    }}
                """)

                def on_pick_color(btn=btn_color, pid=p.id, init_color=cur_color):
                    initial = QColor(self.active_params.get(pid, init_color))
                    c = QColorDialog.getColor(initial, self, f"Select {p.name}")
                    if c.isValid():
                        hex_code = c.name()
                        btn.setText(f"  {hex_code}")
                        btn.setStyleSheet(f"""
                            QPushButton {{
                                background-color: {hex_code};
                                color: {"#000000" if c.lightness() > 150 else "#ffffff"};
                                border: 1px solid #3d345c;
                                border-radius: 4px;
                                font-size: 10px;
                                font-weight: bold;
                                text-align: left;
                                padding-left: 8px;
                            }}
                        """)
                        self._set_param(pid, hex_code)

                btn_color.clicked.connect(on_pick_color)
                row.addWidget(btn_color, stretch=1)

            elif p.type == ParameterType.FONT:
                from core.font_catalog import installed_font_options, resolve_available_font
                combo_font = QComboBox()
                combo_font.setFixedHeight(24)
                combo_font.setStyleSheet("""
                    QComboBox {
                        background-color: #0c0916;
                        border: 1px solid #282140;
                        border-radius: 4px;
                        color: #ffffff;
                        padding: 2px 6px;
                        font-size: 11px;
                    }
                    QComboBox QAbstractItemView {
                        background-color: #17122b;
                        color: #ffffff;
                        selection-background-color: #ff5500;
                    }
                """)
                standard_fonts = installed_font_options()
                requested_font = str(p.default) if p.default else "Avenir Next"
                cur_font = resolve_available_font(requested_font, "display")
                combo_font.addItems(standard_fonts)
                combo_font.setCurrentText(cur_font)
                combo_font.setToolTip("Choose a font installed on this computer")
                combo_font.currentTextChanged.connect(lambda val, pid=p.id: self._set_param(pid, val))
                row.addWidget(combo_font, stretch=1)

            elif p.type == ParameterType.SELECT:
                combo_select = QComboBox()
                combo_select.setFixedHeight(24)
                combo_select.setStyleSheet("""
                    QComboBox {
                        background-color: #0c0916;
                        border: 1px solid #282140;
                        border-radius: 4px;
                        color: #ffffff;
                        padding: 2px 6px;
                        font-size: 11px;
                    }
                    QComboBox QAbstractItemView {
                        background-color: #17122b;
                        color: #ffffff;
                        selection-background-color: #ff5500;
                    }
                """)
                opts = p.options or ["Default"]
                combo_select.addItems(opts)
                cur_opt = str(p.default) if p.default else (opts[0] if opts else "")
                combo_select.setCurrentText(cur_opt)
                combo_select.currentTextChanged.connect(lambda val, pid=p.id: self._set_param(pid, val))
                row.addWidget(combo_select, stretch=1)

            self.fields_layout.addLayout(row)

    def _set_param(self, pid: str, val: Any):
        self.active_params[pid] = val
        self.canvas_area.params = self.active_params
        self.canvas_area.update()

    def _on_export_template_clicked(self):
        if not self.active_template:
            QMessageBox.information(self, "No Template", "Please select a template to export.")
            return

        suggested_name = f"{self.active_template.id}.json"
        path, _ = QFileDialog.getSaveFileName(self, "Export Template JSON", suggested_name, "JSON Files (*.json)")
        if path:
            try:
                src_path = self.registry.get_template_path(self.active_template.id)
                if src_path and os.path.exists(src_path):
                    with open(src_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    data = {
                        "id": self.active_template.id,
                        "name": self.active_template.name,
                        "category": self.active_template.category,
                        "description": self.active_template.description,
                        "duration_default": self.active_template.duration_default,
                        "parameters": [
                            {"id": p.id, "name": p.name, "type": p.type.value, "default": self.active_params.get(p.id, p.default)}
                            for p in self.active_template.parameters
                        ]
                    }
                for parameter in data.get("parameters", []):
                    parameter_id = parameter.get("id")
                    if parameter_id in self.active_params:
                        parameter["default"] = self.active_params[parameter_id]
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.statusMessage.emit(f"Exported '{self.active_template.name}' with current settings to {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.warning(self, "Export Failed", f"Could not export template: {e}")

    def _on_import_template_clicked(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Template JSON", "", "JSON Files (*.json)")
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                parsed = self.registry._parse_template(data)
                if parsed:
                    category = re.sub(r"[^a-z0-9_-]+", "_", (parsed.category or "custom").lower()).strip("_") or "custom"
                    template_id = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(parsed.id)).strip("_")
                    if not template_id:
                        QMessageBox.warning(self, "Import Failed", "Template ID must contain letters or numbers.")
                        return
                    data["id"] = template_id
                    parsed.id = template_id
                    target_dir = os.path.join(self.registry.templates_dir, category)
                    os.makedirs(target_dir, exist_ok=True)
                    target_file = os.path.join(target_dir, f"{template_id}.json")

                    existing_path = self.registry.get_template_path(template_id)
                    if existing_path and os.path.realpath(existing_path) != os.path.realpath(target_file):
                        QMessageBox.warning(
                            self,
                            "Duplicate Template ID",
                            f"Template ID '{parsed.id}' is already used by another template. Choose a unique ID before importing."
                        )
                        return

                    if os.path.exists(target_file):
                        ret = QMessageBox.question(
                            self,
                            "Overwrite Existing Template?",
                            f"A template with ID '{parsed.id}' already exists in '{category}'.\nDo you want to overwrite it?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No
                        )
                        if ret != QMessageBox.StandardButton.Yes:
                            self.statusMessage.emit("Import cancelled by user.")
                            return

                    with open(target_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                    self.registry.reload()
                    self._load_templates()
                    self.select_template(parsed)
                    self.statusMessage.emit(f"Successfully imported template '{parsed.name}' into '{category}'!")
                else:
                    QMessageBox.warning(self, "Import Failed", "Invalid template schema format.")
            except Exception as e:
                QMessageBox.warning(self, "Import Failed", f"Could not parse template: {e}")

    def _on_apply_clicked(self):
        if not self.active_template:
            self.statusMessage.emit("Please select a template first.")
            return

        if not self.bridge:
            self.statusMessage.emit("DaVinci Resolve bridge is not connected.")
            return

        targets = self.bridge.get_target_clips("playhead")
        inserted_item = None
        if not targets:
            new_item = self.bridge.insert_text_plus_title()
            if new_item:
                targets = [new_item]
                inserted_item = new_item

        if not targets:
            self.statusMessage.emit("Ensure an active DaVinci Resolve timeline is open.")
            return

        applied_count = 0
        failed_count = 0
        fusion_records = []
        restore_failures = 0
        snapshot_failures = 0

        for item in targets:
            before = None
            if not inserted_item:
                before = self.bridge.capture_fusion_comp_snapshot(item)
                if not before:
                    snapshot_failures += 1
                    failed_count += 1
                    continue

            try:
                ok = self.compiler.compile_and_apply(
                    item,
                    self.active_template,
                    self.active_params,
                    theme_id=self.active_theme
                )
            except Exception as exc:
                print(f"[TemplatesTab] Could not compile '{self.active_template.name}': {exc}")
                ok = False

            if ok:
                if inserted_item:
                    applied_count += 1
                else:
                    after = self.bridge.capture_fusion_comp_snapshot(item)
                    if after:
                        fusion_records.append({"item": item, "before": before, "after": after})
                        applied_count += 1
                    else:
                        if not self.bridge.restore_fusion_comp_snapshot(item, before):
                            restore_failures += 1
                        else:
                            self.bridge.discard_fusion_comp_snapshot(before)
                        failed_count += 1
            else:
                failed_count += 1
                if before and not self.bridge.restore_fusion_comp_snapshot(item, before):
                    restore_failures += 1
                elif before:
                    self.bridge.discard_fusion_comp_snapshot(before)

        if inserted_item and applied_count == 0:
            try:
                timeline = self.bridge.get_current_timeline()
                removed = bool(timeline and timeline.DeleteClips([inserted_item]))
            except Exception:
                removed = False
            detail = " The empty Text+ clip was removed." if removed else " The inserted Text+ clip may still be on the timeline."
            self.statusMessage.emit(f"Template '{self.active_template.name}' failed to compile.{detail}")
            return

        if applied_count == 0:
            if restore_failures:
                self.statusMessage.emit(f"Template apply failed, and {restore_failures} prior Fusion comp(s) could not be restored. Stop editing those title(s) and inspect the Resolve timeline.")
            elif snapshot_failures:
                self.statusMessage.emit(f"Template '{self.active_template.name}' was not applied: Resolve could not create an undo backup, so the selected title was left unchanged.")
            else:
                self.statusMessage.emit(f"Template '{self.active_template.name}' was not applied. Check the selected title and Resolve connection.")
            return

        if inserted_item:
            self.bridge.push_undo_snapshot([inserted_item], f"Insert {self.active_template.name} Template Title")
            self.statusMessage.emit(f"Inserted editable Text+ title with template '{self.active_template.name}'.")
        else:
            if fusion_records:
                self.bridge.push_fusion_snapshot(fusion_records, f"Apply Template {self.active_template.name}")
            self.statusMessage.emit(f"Applied template '{self.active_template.name}' to {applied_count} title clip(s). Fusion composition snapshots are available through Undo/Redo.")

        if failed_count:
            details = []
            if snapshot_failures:
                details.append(f"{snapshot_failures} title(s) were skipped because an undo backup could not be saved")
            if restore_failures:
                details.append(f"{restore_failures} title(s) could not be restored after a failed apply; inspect these clips")
            suffix = "; " + "; ".join(details) if details else ""
            self.statusMessage.emit(f"Applied to {applied_count} of {len(targets)} title(s); {failed_count} failed{suffix}.")
