"""
CaptionForge for Resolve - Motion Effects Controller Widget (PyQt6)
Dual D-Pads with live neon-orange active states, Center 2x2 grid,
accent sub-toggles, and prominent AUTO button.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QSlider, QLabel, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtCore import QByteArray, QSize
from PyQt6.QtSvg import QSvgRenderer
from ui_qt.styles import (
    STYLE_PILL_ACTIVE, STYLE_PILL_INACTIVE,
    STYLE_DPAD_NORMAL, STYLE_DPAD_ACTIVE,
    STYLE_EFFECT_NORMAL, STYLE_EFFECT_ACTIVE,
    STYLE_BTN_AUTO, COLOR_ACCENT_ORANGE
)


ICON_PATHS = {
    "up": '<path d="m5 14 7-7 7 7"/>',
    "down": '<path d="m5 10 7 7 7-7"/>',
    "left": '<path d="m14 5-7 7 7 7"/>',
    "right": '<path d="m10 5 7 7-7 7"/>',
    "center": '<circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="1.5"/>',
    "pop": '<circle cx="12" cy="12" r="2"/><path d="M12 3v3m0 12v3M3 12h3m12 0h3"/>',
    "shake": '<path d="M2 9c2.4-7 4.5 7 7 0s4.5 7 7 0 3-3 6 0"/>',
    "jitter": '<path d="M4 4h5v5H4zM15 4h5v5h-5zM4 15h5v5H4zM15 15h5v5h-5z"/><path d="m9 9 3 3m3-3-3 3m-3 3 3-3m3 3-3-3"/>',
    "scribble": '<path d="M3 16c3-8 4 5 7-2s4 5 6-2 3 1 5-3"/>',
    "blur": '<path d="M3 6h12M6 10h15M3 14h12M7 18h14"/>',
    "flicker": '<path d="m12 2 1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8L12 2Z"/><path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z"/>',
    "tune": '<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="9" cy="6" r="2"/><circle cx="15" cy="12" r="2"/><circle cx="11" cy="18" r="2"/>',
    "auto": '<path d="m12 2 2.2 6.2L21 10.5l-6.8 2.2L12 20l-2.2-7.3L3 10.5l6.8-2.3L12 2Z"/>',
}


def _line_icon(name, color="#b7a99b"):
    """Small consistent vector icons; avoids platform-dependent emoji glyphs."""
    path = ICON_PATHS.get(name, "")
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{path}</g></svg>'
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def _section_label(text):
    label = QLabel(text)
    label.setStyleSheet("color:#8f8991; font-size:8px; font-weight:800; letter-spacing:1px; background:transparent; border:none;")
    return label

class MotionEffectsControllerWidget(QWidget):
    """Tactile motion animation pad matching EasyMotion Toolkit layout."""

    motionChanged = pyqtSignal(dict)
    autoTriggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mode_in = "slide"
        self.mode_out = "slide"
        self.dir_in = "up"
        self.dir_out = "down"
        self.shake_enabled = False
        self.jitter_enabled = False
        self.scribble_enabled = False
        self.mblur_enabled = True
        self.flicker_enabled = False
        self.blur_enabled = False

        # Tunable parameters
        self.shake_intensity = 100  # 10% to 200%
        self.shake_speed = 100      # 50% to 250%
        self.motion_dist = 100      # 20% to 200%
        self.motion_dur = 10        # 4 to 24 frames
        self.jitter_intensity = 100
        self.jitter_speed = 100
        self.scribble_intensity = 100
        self.scribble_speed = 100
        self.motion_blur_intensity = 100
        self.motion_blur_angle = 90
        self.tune_visible = False

        self._build_ui()
        self._update_visuals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(9)

        # 1. Top Mode Toggles
        top_row = QHBoxLayout()
        top_row.setContentsMargins(4, 2, 4, 2)
        top_row.setSpacing(6)

        in_group = QVBoxLayout()
        in_group.setSpacing(4)
        in_group.addWidget(_section_label("ENTER"), alignment=Qt.AlignmentFlag.AlignLeft)
        self.btn_in_slide = QPushButton("Slide")
        self.btn_in_bounce = QPushButton("Bounce")
        self.btn_in_slide.clicked.connect(lambda: self._set_in_mode("slide"))
        self.btn_in_bounce.clicked.connect(lambda: self._set_in_mode("bounce"))
        self.btn_in_slide.setToolTip("Enter the title with a directional slide")
        self.btn_in_bounce.setToolTip("Enter the title with a damped bounce")

        in_box = QHBoxLayout()
        in_box.setSpacing(5)
        in_box.addWidget(self.btn_in_slide)
        in_box.addWidget(self.btn_in_bounce)
        in_group.addLayout(in_box)
        top_row.addLayout(in_group)

        top_row.addStretch()

        out_group = QVBoxLayout()
        out_group.setSpacing(4)
        out_group.addWidget(_section_label("EXIT"), alignment=Qt.AlignmentFlag.AlignRight)
        self.btn_out_slide = QPushButton("Slide")
        self.btn_out_bounce = QPushButton("Bounce")
        self.btn_out_slide.clicked.connect(lambda: self._set_out_mode("slide"))
        self.btn_out_bounce.clicked.connect(lambda: self._set_out_mode("bounce"))
        self.btn_out_slide.setToolTip("Exit the title with a directional slide")
        self.btn_out_bounce.setToolTip("Exit the title with a damped bounce")

        out_box = QHBoxLayout()
        out_box.setSpacing(5)
        out_box.addWidget(self.btn_out_slide)
        out_box.addWidget(self.btn_out_bounce)
        out_group.addLayout(out_box)
        top_row.addLayout(out_group)

        layout.addLayout(top_row)

        # 2. Main Middle Row: Left D-Pad + Center Effects + Right D-Pad
        middle_row = QHBoxLayout()
        middle_row.setSpacing(6)

        # Left D-Pad (IN Direction)
        left_pad_group = QVBoxLayout()
        left_pad_group.setSpacing(5)
        left_pad_group.addWidget(_section_label("ENTRY VECTOR"), alignment=Qt.AlignmentFlag.AlignCenter)
        left_dpad_col = QGridLayout()
        left_dpad_col.setContentsMargins(0, 0, 0, 0)
        left_dpad_col.setHorizontalSpacing(3)
        left_dpad_col.setVerticalSpacing(3)

        self.btn_in_up = QPushButton()
        self.btn_in_left = QPushButton()
        self.btn_in_center = QPushButton()
        self.btn_in_right = QPushButton()
        self.btn_in_down = QPushButton()

        self.btn_in_up.clicked.connect(lambda: self._set_in_dir("up"))
        self.btn_in_left.clicked.connect(lambda: self._set_in_dir("left"))
        self.btn_in_center.clicked.connect(lambda: self._set_in_dir("pop"))
        self.btn_in_right.clicked.connect(lambda: self._set_in_dir("right"))
        self.btn_in_down.clicked.connect(lambda: self._set_in_dir("down"))
        for button, tip in zip(
            (self.btn_in_up, self.btn_in_left, self.btn_in_center, self.btn_in_right, self.btn_in_down),
            ("Enter from above", "Enter from left", "Pop in at center", "Enter from right", "Enter from below")
        ):
            button.setToolTip(tip)

        left_dpad_col.addWidget(self.btn_in_up, 0, 1)
        left_dpad_col.addWidget(self.btn_in_left, 1, 0)
        left_dpad_col.addWidget(self.btn_in_center, 1, 1)
        left_dpad_col.addWidget(self.btn_in_right, 1, 2)
        left_dpad_col.addWidget(self.btn_in_down, 2, 1)
        for col in range(3):
            left_dpad_col.setColumnMinimumWidth(col, 36)
        for row in range(3):
            left_dpad_col.setRowMinimumHeight(row, 34)

        left_pad_group.addLayout(left_dpad_col)
        middle_row.addLayout(left_pad_group, stretch=1)

        # Center Effects Grid (Shake, Jitter, Scribble, M. Blur)
        center_col = QVBoxLayout()
        center_col.setSpacing(6)
        center_col.addWidget(_section_label("TEXT MOTION"), alignment=Qt.AlignmentFlag.AlignCenter)

        row1 = QHBoxLayout()
        row1.setSpacing(4)
        self.btn_shake = QPushButton("Shake")
        self.btn_shake.setIconSize(QSize(16, 16))
        self.btn_jitter = QPushButton("Jitter")
        self.btn_jitter.setIconSize(QSize(16, 16))
        self.btn_shake.clicked.connect(lambda: self._toggle_effect("shake"))
        self.btn_jitter.clicked.connect(lambda: self._toggle_effect("jitter"))
        row1.addWidget(self.btn_shake)
        row1.addWidget(self.btn_jitter)
        center_col.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(4)
        self.btn_scribble = QPushButton("Scribble")
        self.btn_scribble.setIconSize(QSize(16, 16))
        self.btn_mblur = QPushButton("Motion Blur")
        self.btn_mblur.setToolTip("Apply a directional motion blur during movement")
        self.btn_mblur.setIconSize(QSize(16, 16))
        self.btn_scribble.clicked.connect(lambda: self._toggle_effect("scribble"))
        self.btn_mblur.clicked.connect(lambda: self._toggle_effect("mblur"))
        row2.addWidget(self.btn_scribble)
        row2.addWidget(self.btn_mblur)
        center_col.addLayout(row2)

        middle_row.addLayout(center_col, stretch=2)

        # Right D-Pad (OUT Direction)
        right_pad_group = QVBoxLayout()
        right_pad_group.setSpacing(5)
        right_pad_group.addWidget(_section_label("EXIT VECTOR"), alignment=Qt.AlignmentFlag.AlignCenter)
        right_dpad_col = QGridLayout()
        right_dpad_col.setContentsMargins(0, 0, 0, 0)
        right_dpad_col.setHorizontalSpacing(3)
        right_dpad_col.setVerticalSpacing(3)

        self.btn_out_up = QPushButton()
        self.btn_out_left = QPushButton()
        self.btn_out_center = QPushButton()
        self.btn_out_right = QPushButton()
        self.btn_out_down = QPushButton()

        self.btn_out_up.clicked.connect(lambda: self._set_out_dir("up"))
        self.btn_out_left.clicked.connect(lambda: self._set_out_dir("left"))
        self.btn_out_center.setToolTip("Keep the title centered; no exit movement")
        self.btn_out_center.clicked.connect(lambda: self._set_out_dir("center"))
        self.btn_out_right.clicked.connect(lambda: self._set_out_dir("right"))
        self.btn_out_down.clicked.connect(lambda: self._set_out_dir("down"))
        for button, tip in zip(
            (self.btn_out_up, self.btn_out_left, self.btn_out_center, self.btn_out_right, self.btn_out_down),
            ("Exit upward", "Exit to the left", "Stay centered on exit", "Exit to the right", "Exit downward")
        ):
            button.setToolTip(tip)

        right_dpad_col.addWidget(self.btn_out_up, 0, 1)
        right_dpad_col.addWidget(self.btn_out_left, 1, 0)
        right_dpad_col.addWidget(self.btn_out_center, 1, 1)
        right_dpad_col.addWidget(self.btn_out_right, 1, 2)
        right_dpad_col.addWidget(self.btn_out_down, 2, 1)
        for col in range(3):
            right_dpad_col.setColumnMinimumWidth(col, 36)
        for row in range(3):
            right_dpad_col.setRowMinimumHeight(row, 34)

        # Keep both pads physically identical, including active-state size.
        for button in (
            self.btn_in_up, self.btn_in_left, self.btn_in_center, self.btn_in_right, self.btn_in_down,
            self.btn_out_up, self.btn_out_left, self.btn_out_center, self.btn_out_right, self.btn_out_down,
        ):
            button.setFixedSize(36, 34)
            button.setIconSize(QSize(16, 16))

        right_pad_group.addLayout(right_dpad_col)
        middle_row.addLayout(right_pad_group, stretch=1)

        layout.addLayout(middle_row)
        layout.addStretch(1)

        # 3. Optional finishing accents; a single control per shared option.
        sub_row = QHBoxLayout()
        sub_row.setSpacing(7)

        sub_btn_style = """
            QPushButton {
                background: #18171a;
                border: 1px solid #343138;
                border-radius: 8px;
                color: #a29ca7;
                font-size: 9px;
                font-weight: 700;
                padding: 5px 9px;
            }
            QPushButton:hover {
                color: #f4e9dd;
                border-color: #76543f;
            }
        """

        self.btn_sub_flicker = QPushButton("Flicker")
        self.btn_sub_flicker.setIconSize(QSize(14, 14))
        self.btn_sub_blur = QPushButton("Blur In")
        self.btn_sub_blur.setIconSize(QSize(14, 14))
        self.btn_sub_blur.setToolTip("Add a short directional blur to the title entrance")
        for b in [self.btn_sub_flicker, self.btn_sub_blur]:
            b.setStyleSheet(sub_btn_style)

        self.btn_sub_flicker.clicked.connect(lambda: self._toggle_sub("flicker"))
        self.btn_sub_blur.clicked.connect(lambda: self._toggle_sub("blur"))

        sub_row.addWidget(_section_label("FINISH"))
        sub_row.addWidget(self.btn_sub_flicker)
        sub_row.addWidget(self.btn_sub_blur)
        sub_row.addStretch()

        layout.addLayout(sub_row)

        # 3b. Motion Tuning Toggle & Drawer
        self.btn_tune_toggle = QPushButton("Fine-tune motion")
        self.btn_tune_toggle.setIconSize(QSize(15, 15))
        self.btn_tune_toggle.setStyleSheet("""
            QPushButton {
                background: #19181b;
                color: #d2c0ad;
                border: 1px solid #403a3b;
                border-radius: 8px;
                font-size: 11px;
                font-weight: 700;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: #f0d4bb;
                border-color: #a77658;
            }
        """)
        self.btn_tune_toggle.clicked.connect(self._toggle_tune_panel)
        layout.addWidget(self.btn_tune_toggle)

        self.tune_container = QFrame()
        self.tune_container.setObjectName("motionTuneContainer")
        self.tune_container.setStyleSheet("""
            QFrame#motionTuneContainer {
                background: #171619;
                border: 1px solid #343034;
                border-radius: 9px;
                padding: 4px;
            }
            QLabel {
                color: #aaa1a5;
                font-size: 10px;
                font-weight: 600;
                background: transparent;
                border: none;
                padding: 0;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #343034;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #b77a56;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #f2e7dc;
                border: 2px solid #b77a56;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
        """)
        tune_layout = QVBoxLayout(self.tune_container)
        tune_layout.setContentsMargins(6, 6, 6, 6)
        tune_layout.setSpacing(4)

        def add_tune_heading(title):
            heading = QLabel(title.upper())
            heading.setStyleSheet("color:#c5a78f; font-size:9px; font-weight:800; letter-spacing:1px; padding-top:5px; border:none; background:transparent;")
            tune_layout.addWidget(heading)

        # Keep each effect's manual controls grouped and independently adjustable.
        add_tune_heading("Shake")
        # Shake Intensity
        row_si = QHBoxLayout()
        lbl_si = QLabel("Shake Amount:")
        self.lbl_si_val = QLabel("100%")
        self.lbl_si_val.setStyleSheet("color: #ff5500; font-weight: bold; min-width: 36px;")
        self.slider_shake_int = QSlider(Qt.Orientation.Horizontal)
        self.slider_shake_int.setRange(10, 200)
        self.slider_shake_int.setValue(100)
        self.slider_shake_int.valueChanged.connect(self._on_tune_slider_changed)
        row_si.addWidget(lbl_si)
        row_si.addWidget(self.slider_shake_int)
        row_si.addWidget(self.lbl_si_val)
        tune_layout.addLayout(row_si)

        # Shake Speed / Frequency
        row_ss = QHBoxLayout()
        lbl_ss = QLabel("Shake Speed:")
        self.lbl_ss_val = QLabel("1.0x")
        self.lbl_ss_val.setStyleSheet("color: #ff5500; font-weight: bold; min-width: 36px;")
        self.slider_shake_spd = QSlider(Qt.Orientation.Horizontal)
        self.slider_shake_spd.setRange(50, 250)
        self.slider_shake_spd.setValue(100)
        self.slider_shake_spd.valueChanged.connect(self._on_tune_slider_changed)
        row_ss.addWidget(lbl_ss)
        row_ss.addWidget(self.slider_shake_spd)
        row_ss.addWidget(self.lbl_ss_val)
        tune_layout.addLayout(row_ss)

        def add_tune_row(name, minimum, maximum, value, unit="%"):
            row = QHBoxLayout()
            label = QLabel(name)
            initial_text = f"{value / 100.0:.1f}x" if unit == "x" else f"{value}{unit}"
            value_label = QLabel(initial_text)
            value_label.setStyleSheet("color: #d7c9a7; font-weight: bold; min-width: 42px;")
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(minimum, maximum)
            slider.setValue(value)
            slider.setToolTip(f"Manually tune {name.lower()} for this motion pass")
            slider.valueChanged.connect(self._on_tune_slider_changed)
            row.addWidget(label)
            row.addWidget(slider)
            row.addWidget(value_label)
            tune_layout.addLayout(row)
            return slider, value_label

        add_tune_heading("Jitter")
        self.slider_jitter_int, self.lbl_jitter_int = add_tune_row("Jitter Amount:", 0, 200, 100)
        self.slider_jitter_spd, self.lbl_jitter_spd = add_tune_row("Jitter Rate:", 25, 300, 100, "x")
        add_tune_heading("Scribble")
        self.slider_scribble_int, self.lbl_scribble_int = add_tune_row("Scribble Amount:", 0, 200, 100)
        self.slider_scribble_spd, self.lbl_scribble_spd = add_tune_row("Scribble Steps:", 25, 300, 100, "x")
        add_tune_heading("Directional Blur")
        self.slider_mblur_int, self.lbl_mblur_int = add_tune_row("Blur Amount:", 0, 200, 100)
        self.slider_mblur_angle, self.lbl_mblur_angle = add_tune_row("Blur Angle:", 0, 180, 90, "°")

        add_tune_heading("Travel")
        # Motion Distance
        row_dist = QHBoxLayout()
        lbl_dist = QLabel("Slide Distance:")
        self.lbl_dist_val = QLabel("1.0x")
        self.lbl_dist_val.setStyleSheet("color: #ffffff; font-weight: bold; min-width: 36px;")
        self.slider_dist = QSlider(Qt.Orientation.Horizontal)
        self.slider_dist.setRange(20, 200)
        self.slider_dist.setValue(100)
        self.slider_dist.valueChanged.connect(self._on_tune_slider_changed)
        row_dist.addWidget(lbl_dist)
        row_dist.addWidget(self.slider_dist)
        row_dist.addWidget(self.lbl_dist_val)
        tune_layout.addLayout(row_dist)

        # Motion Duration
        row_dur = QHBoxLayout()
        lbl_dur = QLabel("Duration (Frames):")
        self.lbl_dur_val = QLabel("10f")
        self.lbl_dur_val.setStyleSheet("color: #ffffff; font-weight: bold; min-width: 36px;")
        self.slider_dur = QSlider(Qt.Orientation.Horizontal)
        self.slider_dur.setRange(4, 24)
        self.slider_dur.setValue(10)
        self.slider_dur.valueChanged.connect(self._on_tune_slider_changed)
        row_dur.addWidget(lbl_dur)
        row_dur.addWidget(self.slider_dur)
        row_dur.addWidget(self.lbl_dur_val)
        tune_layout.addLayout(row_dur)

        self.tune_scroll = QScrollArea()
        self.tune_scroll.setWidgetResizable(True)
        self.tune_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.tune_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tune_scroll.setMaximumHeight(250)
        self.tune_scroll.setWidget(self.tune_container)
        self.tune_scroll.setVisible(False)
        layout.addWidget(self.tune_scroll)
        layout.addStretch(1)

        # 4. Large Bold AUTO Button
        self.btn_auto = QPushButton("AUTO APPLY")
        self.btn_auto.setIcon(_line_icon("auto", COLOR_ACCENT_ORANGE))
        self.btn_auto.setIconSize(QSize(16, 16))
        self.btn_auto.setStyleSheet(STYLE_BTN_AUTO)
        self.btn_auto.clicked.connect(self.autoTriggered.emit)
        layout.addWidget(self.btn_auto)

        self.setStyleSheet("""
            MotionEffectsControllerWidget {
                background-color: #13101d;
                border: 1px solid #26203a;
                border-radius: 12px;
            }
        """)

    def _set_in_mode(self, mode):
        self.mode_in = mode
        self._update_visuals()
        self._emit_changes()

    def _set_out_mode(self, mode):
        self.mode_out = mode
        self._update_visuals()
        self._emit_changes()

    def _set_in_dir(self, direction):
        self.dir_in = direction
        self._update_visuals()
        self._emit_changes()

    def _set_out_dir(self, direction):
        self.dir_out = direction
        self._update_visuals()
        self._emit_changes()

    def _toggle_tune_panel(self):
        self.tune_visible = not self.tune_visible
        self.tune_scroll.setVisible(self.tune_visible)
        self.btn_tune_toggle.setText("Fine-tune motion" if not self.tune_visible else "Hide motion controls")

    def _on_tune_slider_changed(self):
        self.shake_intensity = self.slider_shake_int.value()
        self.shake_speed = self.slider_shake_spd.value()
        self.motion_dist = self.slider_dist.value()
        self.motion_dur = self.slider_dur.value()
        self.jitter_intensity = self.slider_jitter_int.value()
        self.jitter_speed = self.slider_jitter_spd.value()
        self.scribble_intensity = self.slider_scribble_int.value()
        self.scribble_speed = self.slider_scribble_spd.value()
        self.motion_blur_intensity = self.slider_mblur_int.value()
        self.motion_blur_angle = self.slider_mblur_angle.value()

        self.lbl_si_val.setText(f"{self.shake_intensity}%")
        self.lbl_ss_val.setText(f"{self.shake_speed / 100.0:.1f}x")
        self.lbl_dist_val.setText(f"{self.motion_dist / 100.0:.1f}x")
        self.lbl_dur_val.setText(f"{self.motion_dur}f")
        self.lbl_jitter_int.setText(f"{self.jitter_intensity}%")
        self.lbl_jitter_spd.setText(f"{self.jitter_speed / 100.0:.1f}x")
        self.lbl_scribble_int.setText(f"{self.scribble_intensity}%")
        self.lbl_scribble_spd.setText(f"{self.scribble_speed / 100.0:.1f}x")
        self.lbl_mblur_int.setText(f"{self.motion_blur_intensity}%")
        self.lbl_mblur_angle.setText(f"{self.motion_blur_angle}°")

        self._emit_changes()

    def _toggle_effect(self, eff_name):
        if eff_name == "shake":
            self.shake_enabled = not self.shake_enabled
            if self.shake_enabled and not self.tune_visible:
                self._toggle_tune_panel()
        elif eff_name == "jitter":
            self.jitter_enabled = not self.jitter_enabled
            if self.jitter_enabled and not self.tune_visible:
                self._toggle_tune_panel()
        elif eff_name == "scribble":
            self.scribble_enabled = not self.scribble_enabled
            if self.scribble_enabled and not self.tune_visible:
                self._toggle_tune_panel()
        elif eff_name == "mblur":
            self.mblur_enabled = not self.mblur_enabled
        self._update_visuals()
        self._emit_changes()

    def _toggle_sub(self, sub_name):
        if sub_name == "flicker":
            self.flicker_enabled = not self.flicker_enabled
        elif sub_name == "shake":
            self.shake_enabled = not self.shake_enabled
            if self.shake_enabled and not self.tune_visible:
                self._toggle_tune_panel()
        elif sub_name == "blur":
            self.blur_enabled = not self.blur_enabled
        self._update_visuals()
        self._emit_changes()

    def _update_visuals(self):
        # Mode Pills
        self.btn_in_slide.setStyleSheet(STYLE_PILL_ACTIVE if self.mode_in == "slide" else STYLE_PILL_INACTIVE)
        self.btn_in_bounce.setStyleSheet(STYLE_PILL_ACTIVE if self.mode_in == "bounce" else STYLE_PILL_INACTIVE)
        self.btn_out_slide.setStyleSheet(STYLE_PILL_ACTIVE if self.mode_out == "slide" else STYLE_PILL_INACTIVE)
        self.btn_out_bounce.setStyleSheet(STYLE_PILL_ACTIVE if self.mode_out == "bounce" else STYLE_PILL_INACTIVE)

        # Left D-Pad
        dpad_in = {
            "up": self.btn_in_up,
            "down": self.btn_in_down,
            "left": self.btn_in_left,
            "right": self.btn_in_right,
            "pop": self.btn_in_center
        }
        for d, btn in dpad_in.items():
            btn.setStyleSheet(STYLE_DPAD_ACTIVE if self.dir_in == d else STYLE_DPAD_NORMAL)
            btn.setIcon(_line_icon("pop" if d == "pop" else d, "#f7eee7" if self.dir_in == d else "#aaa2ad"))

        # Right D-Pad
        dpad_out = {
            "up": self.btn_out_up,
            "down": self.btn_out_down,
            "left": self.btn_out_left,
            "right": self.btn_out_right,
            "center": self.btn_out_center
        }
        for d, btn in dpad_out.items():
            btn.setStyleSheet(STYLE_DPAD_ACTIVE if self.dir_out == d else STYLE_DPAD_NORMAL)
            btn.setIcon(_line_icon("center" if d == "center" else d, "#f7eee7" if self.dir_out == d else "#aaa2ad"))

        # Center Effects
        self.btn_shake.setStyleSheet(STYLE_EFFECT_ACTIVE if self.shake_enabled else STYLE_EFFECT_NORMAL)
        self.btn_jitter.setStyleSheet(STYLE_EFFECT_ACTIVE if self.jitter_enabled else STYLE_EFFECT_NORMAL)
        self.btn_scribble.setStyleSheet(STYLE_EFFECT_ACTIVE if self.scribble_enabled else STYLE_EFFECT_NORMAL)
        self.btn_mblur.setStyleSheet(STYLE_EFFECT_ACTIVE if self.mblur_enabled else STYLE_EFFECT_NORMAL)
        for button, name, active in (
            (self.btn_shake, "shake", self.shake_enabled),
            (self.btn_jitter, "jitter", self.jitter_enabled),
            (self.btn_scribble, "scribble", self.scribble_enabled),
            (self.btn_mblur, "blur", self.mblur_enabled),
            (self.btn_sub_flicker, "flicker", self.flicker_enabled),
            (self.btn_sub_blur, "blur", self.blur_enabled),
        ):
            button.setIcon(_line_icon(name, "#ffffff" if active else "#9d93b8"))
        self.btn_tune_toggle.setIcon(_line_icon("tune", "#9d93b8"))

        active_sub_style = "QPushButton{background:#ff5500;border:1px solid #ff7722;border-radius:8px;color:#ffffff;font-size:9px;font-weight:700;padding:5px 9px;}"
        normal_sub_style = "QPushButton{background:#171325;border:1px solid #282140;border-radius:8px;color:#9d93b8;font-size:9px;font-weight:700;padding:5px 9px;} QPushButton:hover{color:#f3f1fa;border-color:#3b325c;}"
        self.btn_sub_flicker.setStyleSheet(active_sub_style if self.flicker_enabled else normal_sub_style)
        self.btn_sub_blur.setStyleSheet(active_sub_style if self.blur_enabled else normal_sub_style)

    def get_motion_data(self):
        eff_in = "pop_in" if self.dir_in == "pop" else f"{self.mode_in}_{self.dir_in}"
        eff_out = "none" if self.dir_out == "center" else f"{self.mode_out}_{self.dir_out}"
        return {
            "in": eff_in,
            "out": eff_out,
            "shake": self.shake_enabled,
            "jitter": self.jitter_enabled,
            "scribble": self.scribble_enabled,
            "motion_blur": self.mblur_enabled,
            "flicker": self.flicker_enabled,
            "blur_in": self.blur_enabled,
            "intensity": self.shake_intensity / 100.0,
            "shake_intensity": self.shake_intensity / 100.0,
            "shake_speed": self.shake_speed / 100.0,
            "jitter_intensity": self.jitter_intensity / 100.0,
            "jitter_speed": self.jitter_speed / 100.0,
            "scribble_intensity": self.scribble_intensity / 100.0,
            "scribble_speed": self.scribble_speed / 100.0,
            "motion_blur_intensity": self.motion_blur_intensity / 100.0,
            "motion_blur_angle": self.motion_blur_angle,
            "distance": self.motion_dist / 100.0,
            "duration": self.motion_dur
        }

    def _emit_changes(self):
        self.motionChanged.emit(self.get_motion_data())
