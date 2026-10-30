"""
CaptionForge for Resolve - Workspace Tab (PyQt6)
Unites the Sub-toolbar, Convert Drawer, Interactive Phone Canvas, and Motion Effects Controller.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QColorDialog, QFontDialog, QInputDialog
)
from PyQt6.QtCore import pyqtSignal

from core.style_manager import StyleManager
from ui_qt.widgets.phone_canvas_view import PhoneCanvasView
from ui_qt.widgets.motion_panel import MotionEffectsControllerWidget
from ui_qt.widgets.convert_drawer import ConvertCaptionsDrawer
from ui_qt.styles import STYLE_PILL_ACTIVE, STYLE_PILL_INACTIVE, STYLE_ORANGE_OUTLINE

class WorkspaceTab(QWidget):
    """Main Workspace tab with phone preview canvas and bottom motion panel."""

    statusMessage = pyqtSignal(str)

    def __init__(self, bridge, builder, animator, parent=None):
        super().__init__(parent)
        self.bridge = bridge
        self.builder = builder
        self.animator = animator
        self.style_mgr = StyleManager()
        self.target_mode = "playhead"
        self.main_word = None

        self._build_ui()
        self._wire_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        # 1. Sub-Toolbar
        sub_bar = QHBoxLayout()
        sub_bar.setContentsMargins(4, 2, 4, 2)
        sub_bar.setSpacing(4)

        self.btn_mode_playhead = QPushButton("Playhead")
        self.btn_mode_inout = QPushButton("In/Out")
        self.btn_mode_playhead.setStyleSheet(STYLE_PILL_ACTIVE)
        self.btn_mode_inout.setStyleSheet(STYLE_PILL_INACTIVE)

        self.btn_snap_to_cut = QPushButton("🧲 Snap to Cut")
        self.btn_snap_to_cut.setCheckable(True)
        self.btn_snap_to_cut.setChecked(False)
        self.btn_snap_to_cut.setToolTip("Magnetically snap title duration to underlying video cut bounds")
        self.btn_snap_to_cut.setStyleSheet(STYLE_PILL_INACTIVE)

        sub_bar.addWidget(self.btn_mode_playhead)
        sub_bar.addWidget(self.btn_mode_inout)
        sub_bar.addWidget(self.btn_snap_to_cut)
        sub_bar.addSpacing(2)

        tpl_style = """
            QPushButton {
                background-color: #171328;
                border: 1px solid #28213e;
                border-radius: 6px;
                color: #a49ebd;
                font-weight: bold;
                font-size: 11px;
                padding: 4px 6px;
            }
            QPushButton:hover {
                background-color: #261f3e;
                color: #ffffff;
                border-color: #ff5500;
            }
        """

        self.btn_tpl_1 = QPushButton("—")
        self.btn_tpl_1.setToolTip("Single Line / Hero Word Layout")
        self.btn_tpl_2 = QPushButton("═")
        self.btn_tpl_2.setToolTip("Two Lines Stacked Layout")
        self.btn_tpl_3 = QPushButton("≡")
        self.btn_tpl_3.setToolTip("Three Lines Stacked Layout")
        for b in [self.btn_tpl_1, self.btn_tpl_2, self.btn_tpl_3]:
            b.setStyleSheet(tpl_style)
            sub_bar.addWidget(b)

        sub_bar.addSpacing(2)

        self.btn_add_text = QPushButton("+ Text")
        self.btn_add_text.setStyleSheet(STYLE_ORANGE_OUTLINE)
        sub_bar.addWidget(self.btn_add_text)

        sub_bar.addSpacing(2)

        self.btn_undo = QPushButton("↶")
        self.btn_undo.setToolTip("Undo the last title insertion or style edit")
        self.btn_undo.setStyleSheet(tpl_style + " QPushButton:disabled { color: #3a3250; background-color: #120e21; border-color: #211a36; }")
        sub_bar.addWidget(self.btn_undo)

        self.btn_redo = QPushButton("↷")
        self.btn_redo.setToolTip("Redo last undone style modification")
        self.btn_redo.setEnabled(False)
        self.btn_redo.setStyleSheet(tpl_style + " QPushButton:disabled { color: #3a3250; background-color: #120e21; border-color: #211a36; }")
        sub_bar.addWidget(self.btn_redo)

        sub_bar.addStretch()
        layout.addLayout(sub_bar)

        # 2. Convert Captions Drawer (collapsible)
        self.drawer_convert = ConvertCaptionsDrawer(self)
        self.drawer_convert.hide()
        layout.addWidget(self.drawer_convert)

        # 3. Smartphone Canvas Area
        self.canvas_view = PhoneCanvasView(self)
        layout.addWidget(self.canvas_view, stretch=3)

        # 4. Motion Effects Controller Panel
        self.motion_panel = MotionEffectsControllerWidget(self)
        layout.addWidget(self.motion_panel, stretch=2)

    def _wire_signals(self):
        self.btn_mode_playhead.clicked.connect(lambda: self._set_target_mode("playhead"))
        self.btn_mode_inout.clicked.connect(lambda: self._set_target_mode("inout"))
        self.btn_snap_to_cut.clicked.connect(self._toggle_snap_to_cut)

        self.btn_tpl_1.clicked.connect(lambda: self._apply_template(1))
        self.btn_tpl_2.clicked.connect(lambda: self._apply_template(2))
        self.btn_tpl_3.clicked.connect(lambda: self._apply_template(3))

        self.btn_add_text.clicked.connect(self._on_add_text_clicked)
        self.btn_undo.clicked.connect(self._on_undo_clicked)
        self.btn_redo.clicked.connect(self._on_redo_clicked)

        # Drawer
        self.drawer_convert.closed.connect(self.drawer_convert.hide)
        self.drawer_convert.convertRequested.connect(self._on_convert_requested)

        # Canvas actions
        self.canvas_view.textUpdated.connect(self._on_canvas_text_updated)
        self.canvas_view.positionUpdated.connect(self._on_canvas_pos_updated)
        self.canvas_view.actionTriggered.connect(self._on_canvas_action)

        # Motion Panel
        self.motion_panel.motionChanged.connect(self._on_motion_changed)
        self.motion_panel.autoTriggered.connect(self._on_auto_motion_clicked)

        self._update_undo_redo_state()

    def toggle_convert_drawer(self):
        if self.drawer_convert.isVisible():
            self.drawer_convert.hide()
        else:
            self._refresh_drawer_tracks()
            self.drawer_convert.show()

    def _refresh_drawer_tracks(self):
        tl = self.bridge.get_current_timeline()
        self.drawer_convert.combo_track.clear()
        cnt = tl.GetTrackCount("subtitle") if tl else 0
        if cnt > 0:
            for i in range(1, cnt + 1):
                name = tl.GetTrackName("subtitle", i) or f"Subtitle {i}"
                self.drawer_convert.combo_track.addItem(f"{name} (Track {i})")
        else:
            self.drawer_convert.combo_track.addItem("Subtitle 1")

        styles = self.style_mgr.get_presets()
        style_names = [s.get("name", "Untitled") for s in styles]
        self.drawer_convert.populate_styles(style_names)

    def _set_target_mode(self, mode):
        self.target_mode = mode
        self.btn_mode_playhead.setStyleSheet(STYLE_PILL_ACTIVE if mode == "playhead" else STYLE_PILL_INACTIVE)
        self.btn_mode_inout.setStyleSheet(STYLE_PILL_ACTIVE if mode == "inout" else STYLE_PILL_INACTIVE)
        msg = "Targeting title directly under Playhead" if mode == "playhead" else "Targeting ALL titles in In/Out Range"
        self.statusMessage.emit(msg)

    def _toggle_snap_to_cut(self):
        is_active = self.btn_snap_to_cut.isChecked()
        self.btn_snap_to_cut.setStyleSheet(STYLE_PILL_ACTIVE if is_active else STYLE_PILL_INACTIVE)
        if is_active:
            self.statusMessage.emit("🧲 Magnetic Snapping enabled: Titles will snap to cut bounds.")
        else:
            self.statusMessage.emit("Magnetic Snapping disabled.")

    def sync_from_timeline(self):
        """Live two-way sync: Pulls active title properties from timeline into canvas."""
        if self.canvas_view.canvas_area.editor.isVisible() or self.canvas_view.canvas_area.is_dragging:
            return

        area = self.canvas_view.canvas_area

        # Auto-detect timeline aspect ratio
        try:
            rw, rh = self.bridge.get_timeline_resolution()
            if rw >= rh * 1.3:
                if area.aspect_ratio != "16:9":
                    self.canvas_view._set_aspect("16:9")
            elif rh >= rw * 1.3:
                if area.aspect_ratio != "9:16":
                    self.canvas_view._set_aspect("9:16")
            else:
                if area.aspect_ratio != "1:1":
                    self.canvas_view._set_aspect("1:1")
        except Exception:
            pass

        meta = self.bridge.get_active_caption_metadata()
        if not meta:
            return

        active_text = meta.get("text", "")
        hero_line_index = meta.get("hero_line_index")
        hero_color = meta.get("hero_color")
        from core.font_catalog import resolve_available_font
        font_family = resolve_available_font(meta.get("font", "Helvetica Neue"), "display")
        pt_size = max(16, min(44, int(meta.get("size", 0.08) * 260.0)))
        pos_x = float(meta.get("center_x", 0.5))
        pos_y = 1.0 - float(meta.get("center_y", 0.5))
        alignment = meta.get("alignment", "center")
        box_enabled = meta.get("box_enabled", False)
        box_color = meta.get("box_color")

        has_changed = (
            (active_text and area.caption_text != active_text) or
            area.hero_line_index != hero_line_index or
            area.hero_color != hero_color or
            area.font_family != font_family or
            abs(area.font_size - pt_size) > 2 or
            abs(area.pos_x - pos_x) > 0.02 or
            abs(area.pos_y - pos_y) > 0.02 or
            area.alignment != alignment or
            area.box_enabled != box_enabled
        )

        if has_changed:
            if active_text:
                area.caption_text = active_text
            area.hero_line_index = hero_line_index
            area.hero_color = hero_color
            area.font_family = font_family
            area.font_size = pt_size
            c = meta.get("color", [1.0, 1.0, 1.0, 1.0])
            area.set_color(c[0], c[1], c[2])
            area.pos_x = pos_x
            area.pos_y = pos_y
            area.alignment = alignment
            area.set_box(box_enabled, box_color)
            area.update()
            clean_name = active_text.replace('\n', ' ')
            if len(clean_name) > 30:
                clean_name = clean_name[:27] + "..."
            self.statusMessage.emit(f"Synced with timeline title: '{clean_name}'")

    def _update_undo_redo_state(self):
        can_u = getattr(self.bridge, "can_undo", lambda: bool(getattr(self.bridge, "_undo_history", [])))()
        can_r = getattr(self.bridge, "can_redo", lambda: bool(getattr(self.bridge, "_redo_history", [])))()
        self.btn_undo.setEnabled(can_u)
        self.btn_redo.setEnabled(can_r)
        self.btn_redo.setToolTip("Redo last undone modification" if can_r else "No modifications in redo history")

    def _apply_template(self, t_num):
        txt = self.canvas_view.canvas_area.caption_text
        formatted = self.builder.apply_layout_template(txt, template_num=t_num, main_word=self.main_word)
        self.canvas_view.canvas_area.set_text(formatted)

        targets = self.bridge.get_target_clips(self.target_mode)
        records = []
        for item in targets:
            prev_style = self.builder.extract_style_from_clip(item) or {}
            new_style = dict(prev_style)
            new_style["text"] = formatted
            records.append({"item": item, "prev_style": prev_style, "new_style": new_style})
            self.builder.update_text(item, formatted)
        if records:
            self.bridge.push_modify_snapshot(records, f"Layout Template {t_num}")
        self._update_undo_redo_state()
        if targets:
            self.statusMessage.emit(f"Applied Template {t_num} to {len(targets)} timeline titles.")
        else:
            self.statusMessage.emit(f"Applied Template {t_num} to Canvas preview (no timeline title targeted).")

    def _on_add_text_clicked(self):
        snap_enabled = self.btn_snap_to_cut.isChecked()
        start_frame, end_frame = None, None
        if snap_enabled:
            tl = self.bridge.get_current_timeline()
            playhead = self.bridge.get_playhead_frame()
            if tl and playhead is not None:
                from core.timeline_intelligence import TimelineIntelligence
                snapped = TimelineIntelligence.detect_magnetic_snap_bounds(tl, playhead)
                if snapped:
                    start_frame, end_frame = snapped

        item = self.bridge.insert_text_plus_title(
            start_frame=start_frame,
            end_frame=end_frame,
            snap_to_footage=snap_enabled
        )
        if item:
            txt = self.canvas_view.canvas_area.caption_text
            self.builder.apply_style(item, self.builder.DEFAULT_STYLE, text_override=txt)
            self.bridge.push_undo_snapshot([item], "Insert Text+ Title")
            self._update_undo_redo_state()
            if snap_enabled and start_frame is not None:
                self.statusMessage.emit(f"Created new +Text title snapped to cut ({start_frame} - {end_frame})!")
            else:
                self.statusMessage.emit("Created new +Text title at playhead!")
        else:
            self.statusMessage.emit("Ensure an active timeline is open.")

    def _on_undo_clicked(self):
        ok, msg = self.bridge.undo_last_batch()
        self._update_undo_redo_state()
        self.statusMessage.emit(msg)

    def _on_redo_clicked(self):
        ok, msg = self.bridge.redo_last_batch()
        self._update_undo_redo_state()
        self.statusMessage.emit(msg)

    def _on_canvas_text_updated(self, new_text):
        targets = self.bridge.get_target_clips(self.target_mode)
        if targets:
            for item in targets:
                self.builder.update_text(item, new_text)
            self.statusMessage.emit(f"Updated text on {len(targets)} timeline titles.")
        else:
            self.statusMessage.emit("Updated Canvas preview (no timeline title targeted).")

    def _on_canvas_pos_updated(self, norm_x, norm_y):
        # Update center in Resolve Text+
        targets = self.bridge.get_target_clips(self.target_mode)
        if targets:
            for item in targets:
                for tool in self.builder.get_text_layers(item):
                    tool.SetInput("Center", [norm_x, 1.0 - norm_y]) # Invert Y for Fusion coords
            self.statusMessage.emit(f"Updated position on {len(targets)} timeline titles.")
        else:
            self.statusMessage.emit("Updated Canvas position (no timeline title targeted).")

    def _on_canvas_action(self, action_name):
        targets = self.bridge.get_target_clips(self.target_mode)

        if action_name == "align_left":
            if targets:
                records = []
                for item in targets:
                    prev_style = self.builder.extract_style_from_clip(item) or {}
                    new_style = dict(prev_style)
                    new_style["alignment"] = "left"
                    records.append({"item": item, "prev_style": prev_style, "new_style": new_style})
                    for tool in self.builder.get_text_layers(item):
                        tool.SetInput("HorizontalLeftCenterRight", -1.0)
                        tool.SetInput("HorizontalJustificationNew", 0.0)
                if records:
                    self.bridge.push_modify_snapshot(records, "Align Left")
                    self._update_undo_redo_state()
                self.statusMessage.emit(f"Aligned {len(targets)} timeline titles Left.")
            else:
                self.statusMessage.emit("Aligned Canvas preview Left (no timeline title targeted).")
        elif action_name == "align_center":
            if targets:
                records = []
                for item in targets:
                    prev_style = self.builder.extract_style_from_clip(item) or {}
                    new_style = dict(prev_style)
                    new_style["center_x"] = 0.5
                    new_style["center_y"] = 0.5
                    new_style["alignment"] = "center"
                    records.append({"item": item, "prev_style": prev_style, "new_style": new_style})
                    for tool in self.builder.get_text_layers(item):
                        tool.SetInput("Center", [0.5, 0.5])
                        tool.SetInput("HorizontalLeftCenterRight", 0.0)
                        tool.SetInput("HorizontalJustificationNew", 1.0)
                        tool.SetInput("VerticalTopCenterBottom", 0.0)
                        tool.SetInput("VerticalJustificationNew", 1.0)
                if records:
                    self.bridge.push_modify_snapshot(records, "Align Center")
                    self._update_undo_redo_state()
                self.statusMessage.emit(f"Centered {len(targets)} timeline titles in EXACT Middle [0.5, 0.5].")
            else:
                self.statusMessage.emit("Centered Canvas preview in EXACT Middle [0.5, 0.5] (no timeline title targeted).")
            self.canvas_view.canvas_area.pos_x = 0.5
            self.canvas_view.canvas_area.pos_y = 0.5
            self.canvas_view.canvas_area.is_snapped_x = True
            self.canvas_view.canvas_area.is_snapped_y = True
            self.canvas_view.canvas_area.set_alignment("center")
            self.canvas_view.canvas_area.update()
        elif action_name == "align_lower_third":
            if targets:
                records = []
                for item in targets:
                    prev_style = self.builder.extract_style_from_clip(item) or {}
                    new_style = dict(prev_style)
                    new_style["center_x"] = 0.5
                    new_style["center_y"] = 0.28
                    new_style["alignment"] = "center"
                    records.append({"item": item, "prev_style": prev_style, "new_style": new_style})
                    for tool in self.builder.get_text_layers(item):
                        tool.SetInput("Center", [0.5, 0.28])
                        tool.SetInput("HorizontalLeftCenterRight", 0.0)
                        tool.SetInput("HorizontalJustificationNew", 1.0)
                if records:
                    self.bridge.push_modify_snapshot(records, "Align Lower Third")
                    self._update_undo_redo_state()
                self.statusMessage.emit(f"Positioned {len(targets)} timeline titles in Lower Third baseline [0.5, 0.28].")
            else:
                self.statusMessage.emit("Positioned Canvas preview in Lower Third baseline [0.5, 0.28] (no timeline title targeted).")
            self.canvas_view.canvas_area.pos_x = 0.5
            self.canvas_view.canvas_area.pos_y = 0.72
            self.canvas_view.canvas_area.is_snapped_x = True
            self.canvas_view.canvas_area.is_snapped_y = False
            self.canvas_view.canvas_area.update()
        elif action_name == "align_right":
            if targets:
                records = []
                for item in targets:
                    prev_style = self.builder.extract_style_from_clip(item) or {}
                    new_style = dict(prev_style)
                    new_style["alignment"] = "right"
                    records.append({"item": item, "prev_style": prev_style, "new_style": new_style})
                    for tool in self.builder.get_text_layers(item):
                        tool.SetInput("HorizontalLeftCenterRight", 1.0)
                        tool.SetInput("HorizontalJustificationNew", 2.0)
                if records:
                    self.bridge.push_modify_snapshot(records, "Align Right")
                    self._update_undo_redo_state()
                self.statusMessage.emit(f"Aligned {len(targets)} timeline titles Right.")
            else:
                self.statusMessage.emit("Aligned Canvas preview Right (no timeline title targeted).")
        elif action_name == "fit":
            self.canvas_view._adjust_zoom(100 - self.canvas_view.current_zoom)
            self.statusMessage.emit("Preview zoom reset to 100%.")
        elif action_name == "duplicate":
            if targets:
                item = targets[0]
                new_item = self.bridge.insert_text_plus_title(start_frame=item.GetEnd(), end_frame=item.GetEnd() + item.GetDuration())
                if new_item:
                    style = self.builder.extract_style_from_clip(item) or {}
                    self.builder.apply_style(new_item, style)
                    self.bridge.push_undo_snapshot([new_item], "Duplicate Title")
                    self._update_undo_redo_state()
                    self.statusMessage.emit("Duplicated title to next frame position!")
            else:
                self.statusMessage.emit("No target title to duplicate. Select or place playhead over a title.")
        elif action_name == "copy":
            if targets:
                self.builder.copy_clip_attributes(targets[0])
                self.statusMessage.emit("Copied attributes to clipboard.")
            else:
                self.statusMessage.emit("No target title to copy attributes from.")
        elif action_name == "paste":
            if targets:
                records = []
                for item in targets:
                    prev_style = self.builder.extract_style_from_clip(item) or {}
                    new_style = dict(prev_style)
                    new_style.update(self.builder._clipboard or {})
                    records.append({"item": item, "prev_style": prev_style, "new_style": new_style})
                pasted_cnt = self.builder.paste_clip_attributes(targets)
                if records and pasted_cnt > 0:
                    self.bridge.push_modify_snapshot(records, "Paste Attributes")
                    self._update_undo_redo_state()
                self.statusMessage.emit(f"Pasted attributes to {pasted_cnt} timeline titles.")
            else:
                self.statusMessage.emit("No target clips found to paste attributes.")
        elif action_name == "crosshair":
            self.canvas_view.canvas_area.is_snapped_x = True
            self.canvas_view.canvas_area.is_snapped_y = True
            self.canvas_view.canvas_area.update()
            self.statusMessage.emit("Snapped preview guide to center [0.5, 0.5].")
        elif action_name == "palette":
            col = QColorDialog.getColor()
            if col.isValid():
                r, g, b = col.redF(), col.greenF(), col.blueF()
                self.canvas_view.canvas_area.set_color(r, g, b)
                self.canvas_view.canvas_area.hero_color = None
                if targets:
                    records = []
                    for item in targets:
                        prev_style = self.builder.extract_style_from_clip(item) or {}
                        new_style = dict(prev_style)
                        new_style["color"] = [r, g, b, 1.0]
                        records.append({"item": item, "prev_style": prev_style, "new_style": new_style})
                        for tool in self.builder.get_text_layers(item):
                            tool.SetInput("Red1", float(r))
                            tool.SetInput("Green1", float(g))
                            tool.SetInput("Blue1", float(b))
                    if records:
                        self.bridge.push_modify_snapshot(records, "Change Title Color")
                    self._update_undo_redo_state()
                    self.statusMessage.emit(f"Applied color ({int(r*255)}, {int(g*255)}, {int(b*255)}) to {len(targets)} titles.")
                else:
                    self.statusMessage.emit("Applied color to Canvas preview (no timeline title targeted).")
        elif action_name == "font":
            ok, font = QFontDialog.getFont()
            if ok:
                family = font.family()
                pt = font.pointSize()
                self.canvas_view.canvas_area.set_font(family, pt)
                norm_size = max(0.04, min(0.18, pt / 300.0))
                records = []
                for item in targets:
                    prev_style = self.builder.extract_style_from_clip(item) or {}
                    new_style = dict(prev_style)
                    new_style["font"] = family
                    new_style["size"] = norm_size
                    records.append({"item": item, "prev_style": prev_style, "new_style": new_style})
                    for tool in self.builder.get_text_layers(item):
                        tool.SetInput("Font", str(family))
                        tool.SetInput("Size", float(norm_size))
                if records:
                    self.bridge.push_modify_snapshot(records, "Change Title Font")
                    self._update_undo_redo_state()
                self.statusMessage.emit(f"Applied font '{family}' ({pt}pt) to titles.")
        elif action_name == "scale":
            area = self.canvas_view.canvas_area
            area.set_font(area.font_family, round(area.font_size * 1.15))
            records = []
            for item in targets:
                prev_style = self.builder.extract_style_from_clip(item) or {}
                new_style = dict(prev_style)
                for tool in self.builder.get_text_layers(item):
                    try:
                        current_size = float(tool.GetInput("Size") or 0.08)
                        new_size = min(0.5, current_size * 1.15)
                        new_style["size"] = new_size
                        tool.SetInput("Size", new_size)
                    except Exception:
                        continue
                records.append({"item": item, "prev_style": prev_style, "new_style": new_style})
            if records:
                self.bridge.push_modify_snapshot(records, "Scale Title Size")
                self._update_undo_redo_state()
            self.statusMessage.emit(f"Increased title text size by 15% on {len(targets)} title(s).")

    def _on_motion_changed(self, motion_data):
        targets = self.bridge.get_target_clips(self.target_mode)
        count = 0
        fusion_records = []
        for item in targets:
            if item.GetFusionCompCount() > 0:
                before = self.bridge.capture_fusion_comp_snapshot(item)
                if self.animator.apply_motion_preset(
                    item,
                    effect_in=motion_data.get("in"),
                    effect_out=motion_data.get("out"),
                    options=motion_data
                ):
                    after = self.bridge.capture_fusion_comp_snapshot(item) if before else None
                    if before and after:
                        fusion_records.append({"item": item, "before": before, "after": after})
                    elif before:
                        self.bridge.discard_fusion_comp_snapshot(before)
                    count += 1
                elif before:
                    self.bridge.discard_fusion_comp_snapshot(before)
        if fusion_records:
            self.bridge.push_fusion_snapshot(
                fusion_records,
                f"Apply Motion ({motion_data.get('in')} / {motion_data.get('out')})"
            )
            self._update_undo_redo_state()
        self.statusMessage.emit(f"Applied motion ({motion_data.get('in')} / {motion_data.get('out')}) to {count} clips.")

    def _on_auto_motion_clicked(self):
        targets = self.bridge.get_target_clips(self.target_mode)
        if not targets:
            self.statusMessage.emit(f"No title found for '{self.target_mode.upper()}'. Move playhead over a title or select clips.")
            return

        active_motion = self.motion_panel.get_motion_data()
        mode_in = getattr(self.motion_panel, "mode_in", "slide")
        mode_out = getattr(self.motion_panel, "mode_out", "slide")

        count = 0
        fusion_records = []
        for item in targets:
            direction = self.animator.get_auto_next_direction(continuity=True)
            eff_in = f"{mode_in}_{direction}"
            eff_out = active_motion.get("out") if active_motion.get("out") != "none" else f"{mode_out}_down"
            before = self.bridge.capture_fusion_comp_snapshot(item) if item.GetFusionCompCount() > 0 else None
            if self.animator.apply_motion_preset(item, effect_in=eff_in, effect_out=eff_out, options=active_motion):
                after = self.bridge.capture_fusion_comp_snapshot(item) if before else None
                if before and after:
                    fusion_records.append({"item": item, "before": before, "after": after})
                elif before:
                    self.bridge.discard_fusion_comp_snapshot(before)
                count += 1
            elif before:
                self.bridge.discard_fusion_comp_snapshot(before)

        if fusion_records:
            self.bridge.push_fusion_snapshot(fusion_records, f"Apply AUTO continuity ({mode_in})")
            self._update_undo_redo_state()

        active_fx = []
        if active_motion.get("shake"):
            active_fx.append("Shake")
        if active_motion.get("jitter"):
            active_fx.append("Jitter")
        if active_motion.get("scribble"):
            active_fx.append("Scribble")
        if active_motion.get("motion_blur"):
            active_fx.append("Blur")
        if active_motion.get("flicker"):
            active_fx.append("Flicker")
        fx_str = f" + [{', '.join(active_fx)}]" if active_fx else ""

        self.statusMessage.emit(f"Applied AUTO continuity ({mode_in} ↺){fx_str} with active tuning to {count} clip(s).")

    def _on_convert_requested(self, data):
        from core.auto_generator import AutoGenerator
        gen = AutoGenerator(self.bridge)
        track_idx = data.get("track_idx", 1)
        rem_punct = data.get("remove_punctuation", True)
        style_name = data.get("style_name")
        use_inout = data.get("use_inout", False)

        if use_inout:
            in_out = self.bridge.get_in_out_range()
            if not in_out or in_out[1] <= in_out[0]:
                self.statusMessage.emit("No In/Out marks set. Mark In [I] and Out [O] in timeline, or uncheck 'Only In/Out Range'.")
                return

        target_style = self.builder.DEFAULT_STYLE
        if style_name and "Look from style" not in style_name:
            for s in self.style_mgr.get_presets():
                if s.get("name") == style_name:
                    target_style = s
                    break

        def prog(curr, total, msg):
            self.statusMessage.emit(msg)

        created = gen.convert_timeline_subtitles(
            target_style,
            track_index=track_idx,
            words_per_slide=2,
            remove_punctuation=rem_punct,
            progress_callback=prog,
            filter_in_out=use_inout
        )
        if created:
            self.statusMessage.emit(f"Converted {len(created)} captions into animated titles!")
            self.drawer_convert.hide()
        else:
            self.statusMessage.emit("No subtitles found to convert on selected track / range.")
