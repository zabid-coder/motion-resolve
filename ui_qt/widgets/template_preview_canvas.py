"""
Motion Resolve - Template Interactive 60fps Preview Canvas Widget (PyQt6)
Renders declarative typography template layers with scrubbable timeline,
60fps play/pause loop, frame-rate independent easing evaluation, and Bengali script support.
"""

from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush

from core.templates.schema import TemplateSpec, LayerType, ParameterType
from core.templates.motion_tokens import evaluate_easing
from core.templates.theme_tokens import get_theme
from core.templates.bengali_engine import (
    contains_bengali, get_optical_scale, to_bengali_numerals
)
from ui_qt.widgets.template_canvas_area import TemplateCanvasArea


class TemplatePreviewCanvasWidget(QWidget):
    """Complete 60fps Scrubbable Template Preview Player."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.template: Optional[TemplateSpec] = None
        self.params: Dict[str, Any] = {}
        self.theme: Dict[str, Any] = get_theme("mono")

        self.is_playing = False
        self.playback_time = 0.8

        self._build_ui()
        self._setup_timer()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 1. Canvas Area
        self.canvas = TemplateCanvasArea(self)
        layout.addWidget(self.canvas)

        # 2. Controls & Scrubber Bar
        ctrl_bar = QHBoxLayout()
        ctrl_bar.setContentsMargins(4, 0, 4, 0)
        ctrl_bar.setSpacing(6)

        self.btn_play = QPushButton("▶ Play")
        self.btn_play.setStyleSheet("""
            QPushButton {
                background-color: #211a36;
                color: #ff5500;
                border: 1px solid #362952;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 800;
                padding: 4px 10px;
                min-width: 55px;
            }
            QPushButton:hover {
                background-color: #2e234c;
                border-color: #ff5500;
            }
        """)
        self.btn_play.clicked.connect(self._toggle_playback)
        ctrl_bar.addWidget(self.btn_play)

        self.btn_reset = QPushButton("↺")
        self.btn_reset.setToolTip("Reset to start (0.0s)")
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #171328;
                color: #928ba8;
                border: 1px solid #282140;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: #ffffff;
                border-color: #ff5500;
            }
        """)
        self.btn_reset.clicked.connect(self._reset_time)
        ctrl_bar.addWidget(self.btn_reset)

        # Time Scrubber Slider
        self.slider_time = QSlider(Qt.Orientation.Horizontal)
        self.slider_time.setRange(0, 4500)
        self.slider_time.setValue(800)
        self.slider_time.setStyleSheet("""
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
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
        """)
        self.slider_time.valueChanged.connect(self._on_slider_scrubbed)
        ctrl_bar.addWidget(self.slider_time, stretch=1)

        self.lbl_time = QLabel("00:00.80 / 00:04.50")
        self.lbl_time.setStyleSheet("color: #a49ebd; font-size: 10px; font-weight: 700; min-width: 105px;")
        ctrl_bar.addWidget(self.lbl_time)

        layout.addLayout(ctrl_bar)

    def _setup_timer(self):
        self.timer = QTimer(self)
        self.timer.setInterval(16)  # ~60fps
        self.timer.timeout.connect(self._on_tick)

    def set_template(self, template: TemplateSpec, params: Dict[str, Any], theme: Dict[str, Any]):
        self.template = template
        self.params = params
        self.theme = theme

        dur_ms = int(template.duration_default * 1000)
        self.slider_time.setRange(0, dur_ms)
        self._update_display(self.playback_time)

    def update_params(self, params: Dict[str, Any]):
        self.params = params
        self.canvas.set_state(self.template, self.params, self.theme, self.playback_time)

    def _toggle_playback(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play.setText("⏸ Pause")
            self.timer.start()
        else:
            self.btn_play.setText("▶ Play")
            self.timer.stop()

    def _reset_time(self):
        self.playback_time = 0.0
        self.slider_time.setValue(0)
        self._update_display(0.0)

    def _on_slider_scrubbed(self, val_ms):
        if not self.is_playing:
            self.playback_time = val_ms / 1000.0
            self._update_display(self.playback_time)

    def _on_tick(self):
        if not self.template:
            return
        total_dur = self.template.duration_default
        self.playback_time += 0.016
        if self.playback_time >= total_dur:
            self.playback_time = 0.0  # Seamless loop

        val_ms = int(self.playback_time * 1000)
        self.slider_time.blockSignals(True)
        self.slider_time.setValue(val_ms)
        self.slider_time.blockSignals(False)
        self._update_display(self.playback_time)

    def _update_display(self, t_sec: float):
        total_dur = self.template.duration_default if self.template else 4.5
        m_curr, s_curr = divmod(t_sec, 60)
        m_tot, s_tot = divmod(total_dur, 60)
        self.lbl_time.setText(f"{int(m_curr):02d}:{s_curr:05.2f} / {int(m_tot):02d}:{s_tot:05.2f}")
        self.canvas.set_state(self.template, self.params, self.theme, t_sec)
