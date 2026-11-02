"""
CaptionForge for Resolve - Floating Convert Captions Drawer (PyQt6)
Matches EasyMotion Toolkit screenshot 3:
- Glowing orange border
- Track dropdown with cue count
- Style dropdown
- Remove punctuation checkbox
- 'Convert · In/Out' button
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QCheckBox
)
from PyQt6.QtCore import pyqtSignal
from ui_qt.styles import STYLE_DRAWER_CONTAINER

class ConvertCaptionsDrawer(QWidget):
    """Floating conversion panel with glowing orange border."""

    convertRequested = pyqtSignal(dict)
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Header
        head_row = QHBoxLayout()
        title_lbl = QLabel("Convert Captions · style sample word, then Convert")
        title_lbl.setStyleSheet("color: #e2ddf2; font-size: 11px; font-weight: bold;")
        head_row.addWidget(title_lbl)

        head_row.addStretch()

        self.btn_close = QPushButton("✕")
        self.btn_close.setStyleSheet("background: transparent; border: none; color: #ff5500; font-size: 12px; font-weight: bold;")
        self.btn_close.clicked.connect(self.closed.emit)
        head_row.addWidget(self.btn_close)

        layout.addLayout(head_row)

        # Dropdowns Row
        drop_row = QHBoxLayout()
        drop_row.setSpacing(6)

        self.combo_track = QComboBox()
        self.combo_track.addItem("Subtitle 1 · Cues")

        self.lbl_type = QLabel("Toolkit Title")
        self.lbl_type.setToolTip("Toolkit Title is the currently supported conversion output.")
        self.lbl_type.setStyleSheet("color: #b0a9c6; background: #0c0916; border: 1px solid #282140; border-radius: 5px; padding: 5px 8px; font-size: 11px;")

        self.combo_style = QComboBox()
        self.combo_style.addItem("Look from style...")

        drop_row.addWidget(self.combo_track, stretch=2)
        drop_row.addWidget(self.lbl_type, stretch=2)
        drop_row.addWidget(self.combo_style, stretch=2)

        layout.addLayout(drop_row)

        # Action Row
        act_row = QHBoxLayout()
        act_row.setSpacing(12)

        self.chk_punct = QCheckBox("Remove punctuation")
        self.chk_punct.setChecked(True)
        self.chk_punct.setStyleSheet("color: #b0a9c6; font-size: 11px; font-weight: 500;")
        act_row.addWidget(self.chk_punct)

        self.chk_inout = QCheckBox("Only In/Out Range")
        self.chk_inout.setChecked(True)
        self.chk_inout.setToolTip("When checked, converts only cues within In/Out marks. When unchecked, converts the entire track.")
        self.chk_inout.setStyleSheet("color: #b0a9c6; font-size: 11px; font-weight: 500;")
        self.chk_inout.toggled.connect(lambda chk: self.btn_convert.setText("Convert Marked In/Out" if chk else "Convert Entire Track"))
        act_row.addWidget(self.chk_inout)

        act_row.addStretch()

        self.btn_convert = QPushButton("Convert Marked In/Out")
        self.btn_convert.setStyleSheet("""
            QPushButton {
                background-color: #ff5500;
                color: #ffffff;
                border: 1px solid #ff7722;
                border-radius: 9px;
                font-weight: 800;
                font-size: 11px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #ff6a1a;
            }
        """)
        self.btn_convert.clicked.connect(self._on_convert_clicked)
        act_row.addWidget(self.btn_convert)

        layout.addLayout(act_row)

        self.setStyleSheet(STYLE_DRAWER_CONTAINER)

    def populate_styles(self, style_names):
        """Populates the style dropdown with loaded preset looks."""
        self.combo_style.clear()
        self.combo_style.addItem("Look from style... (Default Look)")
        if not style_names:
            return
        for name in style_names:
            if name != "Look from style... (Default Look)":
                self.combo_style.addItem(name)

    def get_selected_style_name(self):
        style = self.combo_style.currentText()
        if not style or "Look from style" in style:
            return None
        return style

    def _on_convert_clicked(self):
        style_selected = self.get_selected_style_name()
        self.convertRequested.emit({
            "track_idx": max(1, self.combo_track.currentIndex() + 1),
            "style_name": style_selected,
            "remove_punctuation": self.chk_punct.isChecked(),
            "use_inout": self.chk_inout.isChecked()
        })
