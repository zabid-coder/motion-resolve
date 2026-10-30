"""
CaptionForge for Resolve - Auto Tab (PyQt6)
Batch Caption Automation Engine.
Extracts timeline subtitles or imports SRT files, chunks with words-per-slide slider,
allows word shifting between groups, and batch-generates animated Text+ titles.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QCheckBox, QTreeWidget, QTreeWidgetItem, QFrame,
    QProgressBar, QHeaderView, QComboBox, QFileDialog, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.subtitle_parser import SubtitleParser, SubtitleCue
from core.auto_generator import AutoGenerator
from ui_qt.theme import (
    COLOR_BG, COLOR_CARD, COLOR_BORDER, COLOR_BORDER_LIGHT,
    COLOR_ORANGE, COLOR_ORANGE_HOVER, COLOR_TEXT, COLOR_MUTED,
    STYLE_PILL_ACTIVE, STYLE_PILL_INACTIVE, STYLE_ORANGE_OUTLINE
)


class AutoTab(QWidget):
    """Batch Caption Automation Tab."""

    statusMessage = pyqtSignal(str)
    requestStyleChange = pyqtSignal()

    def __init__(self, bridge, builder, animator, parent=None):
        super().__init__(parent)
        self.bridge = bridge
        self.builder = builder
        self.animator = animator
        self.generator = AutoGenerator(bridge)

        self.active_style = self.builder.DEFAULT_STYLE
        self.raw_cues = []
        self.plan_cues = []
        self.is_sample_cues = False

        self._build_ui()
        self._wire_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(5)

        # 1. Active Style Card
        self.style_card = QFrame()
        self.style_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
        """)
        card_layout = QHBoxLayout(self.style_card)
        card_layout.setContentsMargins(8, 6, 8, 6)

        self.lbl_style_thumb = QLabel("🎨")
        self.lbl_style_thumb.setStyleSheet("font-size: 16px;")
        card_layout.addWidget(self.lbl_style_thumb)

        style_info = QVBoxLayout()
        style_info.setSpacing(1)
        self.lbl_style_name = QLabel("Hormozi Bold Yellow")
        self.lbl_style_name.setStyleSheet("font-weight: 800; font-size: 12px; color: #ffffff;")
        self.lbl_style_meta = QLabel("Impact · Yellow · Bounce Up")
        self.lbl_style_meta.setStyleSheet("font-size: 10px; color: #8a83a4;")
        style_info.addWidget(self.lbl_style_name)
        style_info.addWidget(self.lbl_style_meta)
        card_layout.addLayout(style_info)

        card_layout.addStretch()

        self.btn_change_style = QPushButton("Change ➔")
        self.btn_change_style.setStyleSheet("""
            QPushButton {
                background-color: #211b36;
                color: #ff5500;
                border: 1px solid #32294e;
                border-radius: 6px;
                font-size: 10px;
                font-weight: 700;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #2e264d;
                border-color: #ff5500;
            }
        """)
        card_layout.addWidget(self.btn_change_style)
        layout.addWidget(self.style_card)

        # 2. Automation Settings (Words Per Slide, Track, Punctuation, Layouts-only)
        settings_frame = QFrame()
        settings_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #110e1f;
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
        """)
        set_layout = QVBoxLayout(settings_frame)
        set_layout.setContentsMargins(8, 6, 8, 6)
        set_layout.setSpacing(4)

        # Track & Mode row
        track_row = QHBoxLayout()
        track_row.setSpacing(6)
        lbl_trk = QLabel("Source:")
        lbl_trk.setStyleSheet("color: #a49ebd; font-size: 10px; font-weight: 600;")
        track_row.addWidget(lbl_trk)

        self.combo_track = QComboBox()
        self.combo_track.setFixedHeight(24)
        self.combo_track.addItem("Subtitle Track 1")
        track_row.addWidget(self.combo_track, stretch=1)

        lbl_anim = QLabel("Motion:")
        lbl_anim.setStyleSheet("color: #a49ebd; font-size: 10px; font-weight: 600;")
        track_row.addWidget(lbl_anim)

        self.combo_anim_mode = QComboBox()
        self.combo_anim_mode.setFixedHeight(24)
        self.combo_anim_mode.addItems(["AUTO Alternating", "Bounce Up", "Pop In", "Slide Up", "From Style", "Off / Static"])
        track_row.addWidget(self.combo_anim_mode, stretch=1)

        set_layout.addLayout(track_row)

        # Words per slide slider
        slider_row = QHBoxLayout()
        lbl_wps = QLabel("Words per slide:")
        lbl_wps.setStyleSheet("color: #a49ebd; font-size: 10px; font-weight: 600;")
        self.lbl_wps_val = QLabel("2 words")
        self.lbl_wps_val.setStyleSheet(f"color: {COLOR_ORANGE}; font-size: 11px; font-weight: 800;")
        slider_row.addWidget(lbl_wps)
        slider_row.addStretch()
        slider_row.addWidget(self.lbl_wps_val)
        set_layout.addLayout(slider_row)

        self.slider_wps = QSlider(Qt.Orientation.Horizontal)
        self.slider_wps.setRange(1, 5)
        self.slider_wps.setValue(2)
        set_layout.addWidget(self.slider_wps)

        layout_row = QHBoxLayout()
        lbl_layout = QLabel("Caption layout:")
        lbl_layout.setStyleSheet("color: #a49ebd; font-size: 10px; font-weight: 600;")
        layout_row.addWidget(lbl_layout)
        self.combo_layout = QComboBox()
        self.combo_layout.setFixedHeight(25)
        self.combo_layout.addItem("Phrase hero stack", "hero")
        self.combo_layout.addItem("Balanced two-line", "two_line")
        self.combo_layout.addItem("Three-beat stack", "three_line")
        layout_row.addWidget(self.combo_layout, stretch=1)
        set_layout.addLayout(layout_row)

        # Checkboxes rows
        cb_row1 = QHBoxLayout()
        cb_row1.setSpacing(10)
        self.chk_punctuation = QCheckBox("Strip Punctuation")
        self.chk_punctuation.setChecked(True)
        self.chk_motion_blur = QCheckBox("Motion Blur")
        self.chk_motion_blur.setChecked(True)
        cb_row1.addWidget(self.chk_punctuation)
        cb_row1.addWidget(self.chk_motion_blur)

        lbl_case = QLabel("Case:")
        lbl_case.setStyleSheet("color: #a49ebd; font-size: 10px; font-weight: 600;")
        cb_row1.addWidget(lbl_case)
        self.combo_case = QComboBox()
        self.combo_case.setFixedHeight(24)
        self.combo_case.addItem("ALL CAPS", "upper")
        self.combo_case.addItem("Title Case", "title")
        self.combo_case.addItem("Sentence case", "sentence")
        self.combo_case.addItem("As-Is", "as_is")
        cb_row1.addWidget(self.combo_case)

        cb_row1.addStretch()
        set_layout.addLayout(cb_row1)

        cb_row2 = QHBoxLayout()
        self.chk_layouts_only = QCheckBox("Layouts only (Static text)")
        cb_row2.addWidget(self.chk_layouts_only)
        cb_row2.addStretch()
        set_layout.addLayout(cb_row2)

        # Shake & Flicker intensity sliders
        fx_row = QHBoxLayout()
        fx_row.setSpacing(8)

        # Shake
        shake_box = QVBoxLayout()
        shake_box.setSpacing(1)
        lbl_shake = QLabel("Shake IN: 0%")
        lbl_shake.setStyleSheet("color: #7e7796; font-size: 9px;")
        self.slider_shake = QSlider(Qt.Orientation.Horizontal)
        self.slider_shake.setRange(0, 100)
        self.slider_shake.setValue(0)
        self.slider_shake.valueChanged.connect(lambda v: lbl_shake.setText(f"Shake IN: {v}%"))
        shake_box.addWidget(lbl_shake)
        shake_box.addWidget(self.slider_shake)
        fx_row.addLayout(shake_box)

        # Flicker
        flicker_box = QVBoxLayout()
        flicker_box.setSpacing(1)
        lbl_flicker = QLabel("Flicker: 0%")
        lbl_flicker.setStyleSheet("color: #7e7796; font-size: 9px;")
        self.slider_flicker = QSlider(Qt.Orientation.Horizontal)
        self.slider_flicker.setRange(0, 100)
        self.slider_flicker.setValue(0)
        self.slider_flicker.valueChanged.connect(lambda v: lbl_flicker.setText(f"Flicker: {v}%"))
        flicker_box.addWidget(lbl_flicker)
        flicker_box.addWidget(self.slider_flicker)
        fx_row.addLayout(flicker_box)

        set_layout.addLayout(fx_row)
        layout.addWidget(settings_frame)

        self.lbl_layout_preview = QLabel("Choose a caption layout to preview it here.")
        self.lbl_layout_preview.setMinimumHeight(42)
        self.lbl_layout_preview.setWordWrap(True)
        self.lbl_layout_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_layout_preview.setStyleSheet(
            "background:#09070f; border:1px solid #28203f; border-radius:7px;"
            "padding:6px; color:#f7f2e8; font-size:13px; font-weight:800;"
        )
        layout.addWidget(self.lbl_layout_preview)

        # 3. Caption Plan Preview Table & Word Shifting Bar
        preview_header = QHBoxLayout()
        preview_header.setSpacing(4)
        self.lbl_plan_count = QLabel("Timeline Group Plan (0 captions)")
        self.lbl_plan_count.setStyleSheet("font-weight: 800; font-size: 10px; color: #a49ebd; letter-spacing: 0.5px;")
        preview_header.addWidget(self.lbl_plan_count)
        preview_header.addStretch()

        self.btn_import_srt = QPushButton("📄 Import SRT...")
        self.btn_import_srt.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #a49ebd;
                border: none;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        preview_header.addWidget(self.btn_import_srt)

        self.btn_refresh_subs = QPushButton("↻ Refresh Timeline")
        self.btn_refresh_subs.setStyleSheet("""
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
        preview_header.addWidget(self.btn_refresh_subs)
        layout.addLayout(preview_header)

        # Tree table
        self.tree_plan = QTreeWidget()
        self.tree_plan.setColumnCount(3)
        self.tree_plan.setHeaderLabels(["#", "Frames", "Caption Words (Double-click to edit)"])
        self.tree_plan.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tree_plan.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree_plan.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tree_plan, stretch=3)

        # Word Shifting Controls
        shift_bar = QHBoxLayout()
        shift_bar.setSpacing(4)
        lbl_shift = QLabel("Shift Word:")
        lbl_shift.setStyleSheet("color: #7b7493; font-size: 10px; font-weight: 600;")
        shift_bar.addWidget(lbl_shift)

        self.btn_shift_left = QPushButton("◄ Shift Left")
        self.btn_shift_right = QPushButton("Shift Right ►")
        shift_style = """
            QPushButton {
                background-color: #19142d;
                border: 1px solid #28203f;
                border-radius: 6px;
                color: #a49ebd;
                font-weight: 700;
                font-size: 10px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #272044;
                color: #ffffff;
                border-color: #ff5500;
            }
        """
        self.btn_shift_left.setStyleSheet(shift_style)
        self.btn_shift_right.setStyleSheet(shift_style)
        shift_bar.addWidget(self.btn_shift_left)
        shift_bar.addWidget(self.btn_shift_right)
        shift_bar.addStretch()

        self.btn_update_caption = QPushButton("Update Playhead Caption")
        self.btn_update_caption.setStyleSheet(STYLE_ORANGE_OUTLINE)
        shift_bar.addWidget(self.btn_update_caption)

        layout.addLayout(shift_bar)

        # 4. Progress Bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1a152d;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_ORANGE};
                border-radius: 4px;
            }}
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 5. Main Action Button: Create Captions
        self.btn_create_captions = QPushButton("★ CREATE CAPTIONS")
        self.btn_create_captions.setFixedHeight(38)
        self.btn_create_captions.setStyleSheet("""
            QPushButton {
                background-color: #ff5500;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-weight: 800;
                font-size: 12px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #ff6a1a;
            }
        """)
        layout.addWidget(self.btn_create_captions)

    def _wire_signals(self):
        self.btn_change_style.clicked.connect(self.requestStyleChange.emit)
        self.slider_wps.valueChanged.connect(self._on_wps_changed)
        self.combo_layout.currentIndexChanged.connect(self._rebuild_plan)
        self.combo_case.currentIndexChanged.connect(self._rebuild_plan)
        self.chk_punctuation.stateChanged.connect(self._rebuild_plan)
        self.combo_track.currentIndexChanged.connect(self._on_track_changed)
        self.btn_refresh_subs.clicked.connect(self.refresh_timeline_subtitles)
        self.btn_import_srt.clicked.connect(self._on_import_srt_clicked)

        self.btn_shift_left.clicked.connect(self._on_shift_left)
        self.btn_shift_right.clicked.connect(self._on_shift_right)

        self.btn_update_caption.clicked.connect(self._on_update_caption_clicked)
        self.btn_create_captions.clicked.connect(self._on_create_captions_clicked)
        self.tree_plan.itemChanged.connect(self._on_tree_item_changed)

    def set_active_style(self, style_dict):
        self.active_style = style_dict
        name = style_dict.get("name", "Custom Style")
        font = style_dict.get("font", "Arial")
        anim_in = style_dict.get("animation_in", "bounce_up")
        self.lbl_style_name.setText(name)
        self.lbl_style_meta.setText(f"{font} · {anim_in}")
        self._refresh_layout_preview()

    def _on_wps_changed(self, val):
        if val == 1:
            self.lbl_wps_val.setText("1 word (Rapid Punch)")
        else:
            self.lbl_wps_val.setText(f"{val} words")
        self._rebuild_plan()

    def _format_caption_text(self, text):
        layout_id = self.combo_layout.currentData() if hasattr(self, "combo_layout") else "hero"
        if layout_id == "two_line":
            return self.builder.apply_layout_template(text, template_num=2)
        if layout_id == "three_line":
            return self.builder.apply_layout_template(text, template_num=3)
        return self.builder.apply_layout_template(
            text, template_num=1, main_word=self.active_style.get("main_word")
        )

    def _refresh_layout_preview(self):
        if not hasattr(self, "lbl_layout_preview"):
            return
        cue_text = self.plan_cues[0].text if self.plan_cues else "YOUR CAPTION HERE"
        lines = self._format_caption_text(cue_text).splitlines() or [cue_text]
        base = self.active_style.get("color", [0.98, 0.96, 0.92, 1.0])
        accent = self.active_style.get("accent_color", [1.0, 0.78, 0.3, 1.0])
        color_css = "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(float(v) * 255))) for v in base[:3]))
        accent_css = "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(float(v) * 255))) for v in accent[:3]))
        hero = " ".join(str(self.active_style.get("main_word") or "").strip(".,!?").lower().split())
        hero_index = next((i for i, line in enumerate(lines)
                           if hero and " ".join(line.strip(".,!?").lower().split()) == hero), -1)
        if hero_index < 0 and len(lines) > 1:
            hero_index = len(lines) // 2
        from html import escape
        rendered = "<br>".join(
            f'<span style="color:{accent_css if i == hero_index else color_css}">{escape(line.upper())}</span>'
            for i, line in enumerate(lines)
        )
        family = escape(str(self.active_style.get("font", "Avenir Next Condensed")))
        self.lbl_layout_preview.setText(
            f'<div style="font-family:{family}; line-height:1.08">{rendered}</div>'
        )

    def refresh_timeline_subtitles(self):
        tl = self.bridge.get_current_timeline()
        if not tl:
            self.statusMessage.emit("No active timeline found.")
            return

        # Query all subtitle tracks
        self.combo_track.blockSignals(True)
        self.combo_track.clear()
        sub_cnt = tl.GetTrackCount("subtitle") if tl else 0
        if sub_cnt > 0:
            for i in range(1, sub_cnt + 1):
                name = tl.GetTrackName("subtitle", i) or f"Subtitle {i}"
                items = tl.GetItemListInTrack("subtitle", i) or []
                self.combo_track.addItem(f"{name} ({len(items)} cues)")
        else:
            self.combo_track.addItem("Subtitle 1 (0 cues)")
        self.combo_track.blockSignals(False)

        selected_track = self.combo_track.currentIndex() + 1
        self.raw_cues = SubtitleParser.extract_from_timeline(tl, track_index=selected_track)
        if not self.raw_cues:
            # Sample preview cues only (guarded from timeline insertion)
            self.is_sample_cues = True
            self.raw_cues = [
                SubtitleCue(0, 45, "[Sample Preview] Welcome to Motion Resolve"),
                SubtitleCue(46, 95, "[Sample Preview] The cleanest animated captions"),
                SubtitleCue(96, 145, "[Sample Preview] Fully editable Text plus titles"),
                SubtitleCue(146, 200, "[Sample Preview] Directly inside DaVinci Resolve Studio")
            ]
            self.statusMessage.emit("Previewing sample cues (no timeline subtitles found).")
        else:
            self.is_sample_cues = False
            self.statusMessage.emit(f"Extracted {len(self.raw_cues)} subtitle cues from timeline.")

        self._rebuild_plan()

    def _on_track_changed(self, index: int):
        if index < 0:
            return
        tl = self.bridge.get_current_timeline()
        if not tl:
            return
        selected_track = index + 1
        cues = SubtitleParser.extract_from_timeline(tl, track_index=selected_track)
        if cues:
            self.is_sample_cues = False
            self.raw_cues = cues
            self.statusMessage.emit(f"Switched to track {selected_track}: {len(cues)} cues loaded.")
        else:
            self.is_sample_cues = True
            self.raw_cues = [
                SubtitleCue(0, 45, "[Sample Preview] Welcome to Motion Resolve"),
                SubtitleCue(46, 95, "[Sample Preview] The cleanest animated captions"),
                SubtitleCue(96, 145, "[Sample Preview] Fully editable Text plus titles"),
                SubtitleCue(146, 200, "[Sample Preview] Directly inside DaVinci Resolve Studio")
            ]
            self.statusMessage.emit(f"Track {selected_track} has no cues; showing sample preview.")
        self._rebuild_plan()

    def _on_import_srt_clicked(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Subtitles", "", "Subtitle Files (*.srt *.json);;SRT Subtitles (*.srt);;Whisper Word JSON (*.json)"
        )
        if path:
            fps = self.bridge.get_timeline_fps() or 24.0
            if path.lower().endswith(".json"):
                cues = SubtitleParser.parse_whisper_json(path, fps=fps)
            else:
                cues = SubtitleParser.parse_srt_file(path, fps=fps)
            if cues:
                self.is_sample_cues = False
                self.raw_cues = cues
                fmt_name = "Whisper JSON" if path.lower().endswith(".json") else "SRT"
                self.statusMessage.emit(f"Imported {len(cues)} cues from {fmt_name} '{os.path.basename(path)}' (FPS: {fps})")
                self._rebuild_plan()
            else:
                QMessageBox.warning(self, "Import Error", "Could not parse valid cues from selected subtitle file.")

    def _rebuild_plan(self):
        if not self.raw_cues:
            self.tree_plan.clear()
            self.lbl_plan_count.setText("Timeline Group Plan (0 captions)")
            return

        wps = self.slider_wps.value()
        rem_punct = self.chk_punctuation.isChecked()
        case_mode = self.combo_case.currentData() if hasattr(self, "combo_case") else "as_is"
        self.plan_cues = SubtitleParser.chunk_cues(
            self.raw_cues, words_per_slide=wps, remove_punctuation=rem_punct, case_mode=case_mode
        )
        self._refresh_layout_preview()

        if self.is_sample_cues:
            self.lbl_plan_count.setText(f"Sample Preview Plan ({len(self.plan_cues)} captions — Preview Only)")
        else:
            self.lbl_plan_count.setText(f"Timeline Group Plan ({len(self.plan_cues)} captions)")

        self.tree_plan.blockSignals(True)
        self.tree_plan.clear()
        for idx, cue in enumerate(self.plan_cues):
            item = QTreeWidgetItem([
                str(idx + 1),
                f"{cue.start_frame}-{cue.end_frame}",
                cue.text
            ])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.tree_plan.addTopLevelItem(item)
        self.tree_plan.blockSignals(False)

    def _on_tree_item_changed(self, item, column):
        idx = self.tree_plan.indexOfTopLevelItem(item)
        if 0 <= idx < len(self.plan_cues):
            if column == 2:
                self.plan_cues[idx].text = item.text(2)
                self.plan_cues[idx].words = item.text(2).split()
            elif column in (0, 1):
                # Only caption text is editable; keep generated numbering/timing authoritative.
                cue = self.plan_cues[idx]
                self.tree_plan.blockSignals(True)
                item.setText(0, str(idx + 1))
                item.setText(1, f"{cue.start_frame}-{cue.end_frame}")
                self.tree_plan.blockSignals(False)

    def _on_shift_left(self):
        item = self.tree_plan.currentItem()
        if not item:
            return
        idx = self.tree_plan.indexOfTopLevelItem(item)
        if idx <= 0:
            return

        SubtitleParser.move_word(self.plan_cues, from_idx=idx, to_idx=idx - 1, word_idx=0)
        self._update_tree_from_plan()
        self.statusMessage.emit(f"Shifted word left to group #{idx}")

    def _on_shift_right(self):
        item = self.tree_plan.currentItem()
        if not item:
            return
        idx = self.tree_plan.indexOfTopLevelItem(item)
        if idx >= len(self.plan_cues) - 1:
            return

        from_cue = self.plan_cues[idx]
        if not from_cue.words:
            return
        last_word_idx = len(from_cue.words) - 1
        SubtitleParser.move_word(self.plan_cues, from_idx=idx, to_idx=idx + 1, word_idx=last_word_idx)
        self._update_tree_from_plan()
        self.statusMessage.emit(f"Shifted word right to group #{idx + 2}")

    def _update_tree_from_plan(self):
        self.tree_plan.blockSignals(True)
        for idx, cue in enumerate(self.plan_cues):
            item = self.tree_plan.topLevelItem(idx)
            if item:
                item.setText(2, cue.text)
        self.tree_plan.blockSignals(False)

    def _on_update_caption_clicked(self):
        item = self.tree_plan.currentItem()
        if not item:
            QMessageBox.information(self, "No Caption Selected", "Please select a caption row from the plan table to update the playhead caption.")
            return

        txt = self._format_caption_text(item.text(2))
        shake_val = self.slider_shake.value()
        flicker_val = self.slider_flicker.value()

        anim_opts = {
            "motion_blur": self.chk_motion_blur.isChecked(),
            "shake": (shake_val > 0),
            "shake_intensity": shake_val / 100.0,
            "shake_speed": 1.0,
            "flicker": (flicker_val > 0),
            "flicker_frequency": flicker_val / 100.0,
            "flicker_intensity": min(1.0, flicker_val / 50.0),
        }

        ok, msg = self.generator.update_active_caption(
            new_text=txt or "ACTIVE CAPTION",
            style_dict=self.active_style,
            anim_opts=anim_opts
        )
        self.statusMessage.emit(msg)

    def _on_create_captions_clicked(self):
        if not self.plan_cues or self.is_sample_cues:
            if self.is_sample_cues:
                QMessageBox.warning(
                    self,
                    "No Real Subtitles Found",
                    "The cues currently displayed in the table are sample previews.\n\n"
                    "To generate real captions on your timeline:\n"
                    "1. Click '📄 Import SRT...' to load a subtitle file, OR\n"
                    "2. Add subtitle cues to a Subtitle Track in DaVinci Resolve and click 'Refresh Timeline'."
                )
                return

            self.refresh_timeline_subtitles()
            if not self.plan_cues or self.is_sample_cues:
                QMessageBox.information(self, "No Captions", "Please import an SRT file or ensure a subtitle track with cues exists.")
                return

        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.btn_create_captions.setEnabled(False)

        layouts_only = self.chk_layouts_only.isChecked()

        # Motion mode selection
        mode_text = self.combo_anim_mode.currentText()
        if mode_text == "AUTO Alternating":
            in_effect = "auto"
        elif mode_text == "Bounce Up":
            in_effect = "bounce_up"
        elif mode_text == "Pop In":
            in_effect = "pop_in"
        elif mode_text == "Slide Up":
            in_effect = "slide_up"
        elif mode_text == "From Style":
            in_effect = self.active_style.get("animation_in", "bounce_up")
        else:
            in_effect = "off"

        shake_val = self.slider_shake.value()
        flicker_val = self.slider_flicker.value()

        anim_opts = {
            "in": in_effect,
            "out": "slide_down" if in_effect != "off" else "off",
            "motion_blur": self.chk_motion_blur.isChecked(),
            "shake": (shake_val > 0),
            "shake_intensity": shake_val / 100.0,
            "shake_speed": 1.0,
            "flicker": (flicker_val > 0),
            "flicker_frequency": flicker_val / 100.0,
            "flicker_intensity": min(1.0, flicker_val / 50.0),
        }

        def prog(curr, total, msg):
            self.progress_bar.setValue(int(curr / max(1, total) * 100))
            self.statusMessage.emit(msg)

        layout_cues = [
            SubtitleCue(cue.start_frame, cue.end_frame, self._format_caption_text(cue.text))
            for cue in self.plan_cues
        ]
        created = self.generator.generate_captions(
            layout_cues,
            self.active_style,
            animation_options=anim_opts,
            layouts_only=layouts_only or (in_effect == "off"),
            progress_callback=prog
        )

        self.progress_bar.hide()
        self.btn_create_captions.setEnabled(True)

        if created:
            if len(created) == len(layout_cues):
                self.statusMessage.emit(f"Done — all {len(created)} captions created on a new track.")
            else:
                self.statusMessage.emit(f"Partially completed — {len(created)} of {len(layout_cues)} captions created. Review the timeline and status details.")
        else:
            self.statusMessage.emit("Failed to create captions. Check timeline connection.")
