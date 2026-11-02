"""
CaptionForge for Resolve / Motion Resolve - Main Window (PyQt6)
The master desktop companion panel for DaVinci Resolve Studio.
Integrates Workspace, Titles, Auto tabs, floating Convert drawer,
and collapsible mini-playback bar.
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabBar, QStackedWidget, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QAction, QFont, QIcon

from core.resolve_api import ResolveBridge
from core.text_plus_builder import TextPlusBuilder
from core.animation_engine import AnimationEngine
from ui_qt.theme import (
    GLOBAL_QSS, COLOR_BG, COLOR_CARD, COLOR_BORDER, COLOR_BORDER_LIGHT,
    COLOR_ORANGE, COLOR_ORANGE_HOVER, COLOR_TEXT, COLOR_MUTED,
    STYLE_PILL_ACTIVE, STYLE_PILL_INACTIVE, STYLE_ORANGE_OUTLINE
)
from ui_qt.tabs.workspace_tab import WorkspaceTab
from ui_qt.tabs.templates_tab import TemplatesTab
from ui_qt.tabs.titles_tab import TitlesTab
from ui_qt.tabs.auto_tab import AutoTab


class MainWindow(QMainWindow):
    """Master Application Window for CaptionForge / Motion Resolve."""

    def __init__(self, bridge=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Motion Resolve for DaVinci Resolve Studio")
        self.resize(460, 900)
        self.setMinimumSize(400, 520)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        # Initialize Core Engines
        self.bridge = bridge or ResolveBridge()
        self.builder = TextPlusBuilder(self.bridge)
        self.animator = AnimationEngine()

        self.is_minimized_bar = False
        self.normal_height = 900

        # Apply Global Dark Purple/Neon Orange Theme
        self.setStyleSheet(GLOBAL_QSS)

        self._build_ui()
        self._wire_signals()
        self._check_resolve_connection()

        # Live Real-Time Timeline Sync Timer (every 400ms)
        from PyQt6.QtCore import QTimer
        self.sync_timer = QTimer(self)
        self.sync_timer.setInterval(400)
        self.sync_timer.timeout.connect(self._on_sync_timer_tick)
        self.sync_timer.start()

        # Immediate Initial Sync
        self.tab_workspace.sync_from_timeline()

    def _build_ui(self):
        self.central_container = QWidget(self)
        self.setCentralWidget(self.central_container)

        self.root_layout = QVBoxLayout(self.central_container)
        self.root_layout.setContentsMargins(6, 6, 6, 6)
        self.root_layout.setSpacing(4)

        # 1. Custom Header Bar
        self.header_bar = QWidget()
        self.header_bar.setFixedHeight(38)
        self.header_bar.setStyleSheet(f"""
            QWidget {{
                background-color: #110e1e;
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
        """)
        h_layout = QHBoxLayout(self.header_bar)
        h_layout.setContentsMargins(10, 2, 8, 2)
        h_layout.setSpacing(6)

        # App Brand Logo & Live Status Dot
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(6)
        self.lbl_logo = QLabel("<b>motion<span style='color:#ff5500;'>resolve</span></b>")
        self.lbl_logo.setStyleSheet("font-size: 13px; color: #ffffff; letter-spacing: 0.5px;")
        logo_layout.addWidget(self.lbl_logo)

        self.lbl_live_badge = QLabel("● LIVE")
        self.lbl_live_badge.setStyleSheet("""
            background-color: #0d2818;
            color: #00e676;
            border: 1px solid #1b4d2e;
            border-radius: 4px;
            font-size: 9px;
            font-weight: 800;
            padding: 2px 5px;
        """)
        logo_layout.addWidget(self.lbl_live_badge)
        h_layout.addLayout(logo_layout)

        h_layout.addStretch()

        # Convert Captions Header Pill Button
        self.btn_convert_hdr = QPushButton("CC Convert Captions")
        self.btn_convert_hdr.setStyleSheet(STYLE_ORANGE_OUTLINE)
        h_layout.addWidget(self.btn_convert_hdr)

        # Collapse / Minimize for Playback Button
        self.btn_minimize = QPushButton("−")
        self.btn_minimize.setFixedSize(26, 26)
        self.btn_minimize.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a152d;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #272044;
                border-color: {COLOR_ORANGE};
            }}
        """)
        h_layout.addWidget(self.btn_minimize)

        # Utility Menu Button (···)
        self.btn_more = QPushButton("···")
        self.btn_more.setFixedSize(26, 26)
        self.btn_more.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a152d;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #272044;
                border-color: {COLOR_ORANGE};
            }}
        """)
        h_layout.addWidget(self.btn_more)

        self.root_layout.addWidget(self.header_bar)

        # 2. Main Tab Bar (Workspace | Templates | Presets | Auto)
        self.tab_bar = QTabBar()
        self.tab_bar.addTab("Workspace")
        self.tab_bar.addTab("Templates")
        self.tab_bar.addTab("Presets")
        self.tab_bar.addTab("Auto")
        self.tab_bar.setExpanding(True)
        self.root_layout.addWidget(self.tab_bar)

        # 3. Stacked View Area
        self.stack = QStackedWidget()

        self.tab_workspace = WorkspaceTab(self.bridge, self.builder, self.animator, self)
        self.tab_templates = TemplatesTab(self.bridge, self.builder, self.animator, self)
        self.tab_titles = TitlesTab(self.bridge, self.builder, self.animator, self)
        self.tab_auto = AutoTab(self.bridge, self.builder, self.animator, self)

        self.stack.addWidget(self.tab_workspace) # Index 0
        self.stack.addWidget(self.tab_templates) # Index 1
        self.stack.addWidget(self.tab_titles)    # Index 2
        self.stack.addWidget(self.tab_auto)      # Index 3

        self.root_layout.addWidget(self.stack, stretch=1)

        # 4. Bottom Status Bar
        self.status_bar_frame = QWidget()
        self.status_bar_frame.setFixedHeight(24)
        self.status_bar_frame.setStyleSheet(f"""
            QWidget {{
                background-color: #0c0916;
                border: 1px solid #1a142c;
                border-radius: 6px;
            }}
        """)
        s_layout = QHBoxLayout(self.status_bar_frame)
        s_layout.setContentsMargins(8, 2, 8, 2)

        self.lbl_status = QLabel("SAMPLE · 1080×1920 · 0 captions at playhead")
        self.lbl_status.setStyleSheet("color: #726b8b; font-size: 10px; font-weight: 500;")
        s_layout.addWidget(self.lbl_status)
        s_layout.addStretch()

        lbl_undo = QLabel("⌘Z · undo title batch")
        lbl_undo.setStyleSheet("color: #4a4460; font-size: 9px;")
        s_layout.addWidget(lbl_undo)

        self.root_layout.addWidget(self.status_bar_frame)

    def _wire_signals(self):
        # Header Actions
        self.btn_convert_hdr.clicked.connect(self._on_convert_captions_clicked)
        self.btn_minimize.clicked.connect(self._toggle_minimize_playback)
        self.btn_more.clicked.connect(self._show_utility_menu)

        # Navigation
        self.tab_bar.currentChanged.connect(self.stack.setCurrentIndex)

        # Inter-tab signaling
        self.tab_titles.switchToAutoTab.connect(self._on_switch_to_auto)
        self.tab_titles.styleSelected.connect(self._on_style_selected)
        self.tab_titles.presetApplied.connect(self._on_preset_applied_globally)
        self.tab_auto.requestStyleChange.connect(lambda: self.tab_bar.setCurrentIndex(2))
        self.tab_templates.statusMessage.connect(self.set_status)

        # Status Bar Updates
        self.tab_workspace.statusMessage.connect(self.set_status)
        self.tab_titles.statusMessage.connect(self.set_status)
        self.tab_auto.statusMessage.connect(self.set_status)

    def _on_sync_timer_tick(self):
        """Periodic sync callback: Syncs timeline title with canvas if Resolve is connected."""
        if not self.bridge.is_connected():
            return
        try:
            # Poll canvas sync if Workspace tab is visible
            if self.tab_bar.currentIndex() == 0 and not self.is_minimized_bar:
                self.tab_workspace.sync_from_timeline()

            # Refresh playhead status in status bar
            tl = self.bridge.get_current_timeline()
            if tl:
                tc = tl.GetCurrentTimecode()
                meta = self.bridge.get_active_caption_metadata()
                if meta:
                    title_preview = meta.get("text", "").replace("\n", " ")
                    if len(title_preview) > 28:
                        title_preview = title_preview[:25] + "..."
                    self.lbl_status.setText(f"{tc} · \"{title_preview}\" (Track {meta.get('track', 1)})")
                else:
                    self.lbl_status.setText(f"{tc} · (No title under playhead)")
        except Exception:
            pass

    def _on_preset_applied_globally(self, style_dict):
        """When a preset is applied from Titles tab, update Canvas view instantly."""
        try:
            area = self.tab_workspace.canvas_view.canvas_area
            if "font" in style_dict:
                area.font_family = style_dict["font"]
            if "size" in style_dict:
                area.font_size = max(18, min(64, int(style_dict["size"] * 320.0)))
            if "color" in style_dict:
                c = style_dict["color"]
                area.set_color(c[0], c[1], c[2])
            if "box_enabled" in style_dict:
                area.set_box(style_dict["box_enabled"], style_dict.get("box_color"))
            area.update()
        except Exception:
            pass

    def _check_resolve_connection(self):
        if self.bridge.is_connected():
            tl = self.bridge.get_current_timeline()
            tl_name = tl.GetName() if tl else "None"
            self.lbl_live_badge.setText("● LIVE")
            self.lbl_live_badge.setStyleSheet("""
                background-color: #0d2818;
                color: #00e676;
                border: 1px solid #1b4d2e;
                border-radius: 4px;
                font-size: 9px;
                font-weight: 800;
                padding: 2px 5px;
            """)
            self.set_status(f"Connected to DaVinci Resolve Studio · Active: '{tl_name}'")
        else:
            self.lbl_live_badge.setText("○ PREVIEW")
            self.lbl_live_badge.setStyleSheet("""
                background-color: #2b1f0d;
                color: #ffaa00;
                border: 1px solid #4d381b;
                border-radius: 4px;
                font-size: 9px;
                font-weight: 800;
                padding: 2px 5px;
            """)
            self.set_status("DaVinci Resolve not detected. Running in preview mode.")

    def keyPressEvent(self, event):
        from PyQt6.QtGui import QKeySequence
        if event.matches(QKeySequence.StandardKey.Undo):
            self._undo_batch()
            event.accept()
        else:
            super().keyPressEvent(event)

    def set_status(self, message):
        self.lbl_status.setText(message)

    def _on_convert_captions_clicked(self):
        # Switch to workspace tab if not active, and toggle drawer
        self.tab_bar.setCurrentIndex(0)
        self.tab_workspace.toggle_convert_drawer()

    def _on_switch_to_auto(self, style_dict):
        self.tab_auto.set_active_style(style_dict)
        self.tab_bar.setCurrentIndex(3) # Switch to Auto tab

    def _on_style_selected(self, style_dict):
        self.tab_auto.set_active_style(style_dict)

    def _toggle_minimize_playback(self):
        """Collapse into a sleek floating mini-bar for unobstructed timeline playback."""
        if not self.is_minimized_bar:
            self.normal_height = self.height()
            self.tab_bar.hide()
            self.stack.hide()
            self.status_bar_frame.hide()
            self.btn_minimize.setText("+")
            self.setFixedHeight(50)
            self.is_minimized_bar = True
            self.set_status("Mini Playback Mode Active")
        else:
            self.setFixedHeight(self.normal_height)
            self.setMinimumSize(380, 500)
            self.setMaximumSize(16777215, 16777215)
            self.tab_bar.show()
            self.stack.show()
            self.status_bar_frame.show()
            self.btn_minimize.setText("−")
            self.is_minimized_bar = False

    def _show_utility_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: #17132a;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                color: #ffffff;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 14px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {COLOR_ORANGE};
            }}
        """)

        act_reconnect = QAction("↻ Reconnect to DaVinci Resolve", self)
        act_reconnect.triggered.connect(self._reconnect_resolve)
        menu.addAction(act_reconnect)

        act_render_cache = QAction("⚡ Resolve Render Cache Guidance", self)
        act_render_cache.triggered.connect(self._show_render_cache_info)
        menu.addAction(act_render_cache)

        act_undo = QAction("↶ Undo Last Caption Batch", self)
        act_undo.triggered.connect(self._undo_batch)
        menu.addAction(act_undo)

        menu.addSeparator()

        act_about = QAction("ℹ About Motion Resolve", self)
        act_about.triggered.connect(self._show_about)
        menu.addAction(act_about)

        menu.exec(self.btn_more.mapToGlobal(QPoint(0, self.btn_more.height())))

    def _reconnect_resolve(self):
        old_undo = getattr(self.bridge, "_undo_history", []) if hasattr(self, "bridge") and self.bridge else []
        self.bridge = ResolveBridge()
        if old_undo:
            self.bridge._undo_history = old_undo
        self.builder = TextPlusBuilder(self.bridge)
        self.animator = AnimationEngine()

        # Synchronize all tabs and sub-engines with the fresh bridge
        if hasattr(self, "tab_workspace"):
            self.tab_workspace.bridge = self.bridge
            self.tab_workspace.builder = self.builder
            self.tab_workspace.animator = self.animator
            if hasattr(self.tab_workspace, "sync_from_timeline"):
                try:
                    self.tab_workspace.sync_from_timeline()
                except Exception:
                    pass

        if hasattr(self, "tab_templates"):
            from core.templates.fusion_compiler import FusionCompiler
            self.tab_templates.bridge = self.bridge
            self.tab_templates.builder = self.builder
            self.tab_templates.animator = self.animator
            self.tab_templates.compiler = FusionCompiler(self.bridge, animator=self.animator)

        if hasattr(self, "tab_titles"):
            self.tab_titles.bridge = self.bridge
            self.tab_titles.builder = self.builder
            self.tab_titles.animator = self.animator

        if hasattr(self, "tab_auto"):
            from core.auto_generator import AutoGenerator
            self.tab_auto.bridge = self.bridge
            self.tab_auto.builder = self.builder
            self.tab_auto.animator = self.animator
            self.tab_auto.generator = AutoGenerator(self.bridge)
            if hasattr(self.tab_auto, "refresh_timeline_subtitles"):
                try:
                    self.tab_auto.refresh_timeline_subtitles()
                except Exception:
                    pass

        self._check_resolve_connection()

    def _show_render_cache_info(self):
        QMessageBox.information(
            self,
            "Render Cache Guidance",
            "Performance Tip for Heavy Motion Graphics:\n\n"
            "If your timeline contains multiple animated Text+ captions with motion blur or shake, "
            "set DaVinci Resolve's Playback menu:\n"
            "• Playback > Render Cache > Smart\n"
            "• Playback > Timeline Proxy Resolution > Half\n\n"
            "This ensures smooth real-time 60fps playback!"
        )

    def _undo_batch(self):
        ok, msg = self.bridge.undo_last_batch()
        self.set_status(msg)

    def _show_about(self):
        QMessageBox.about(
            self,
            "About Motion Resolve",
            "<b>Motion Resolve for DaVinci Resolve Studio</b><br>"
            "Version 2.0.0 (Clean-room Reconstruction)<br><br>"
            "A high-performance desktop companion app for DaVinci Resolve Studio.<br>"
            "Automate animated viral subtitles, customize typography, and apply procedural motion physics."
        )


def launch():
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    window = MainWindow()

    # Position on right side of primary screen near Resolve viewer
    screen = app.primaryScreen()
    if screen:
        geom = screen.availableGeometry()
        x = geom.x() + geom.width() - 480
        y = geom.y() + 60
        window.move(max(0, x), max(0, y))

    window.show()
    window.raise_()
    window.activateWindow()
    return app, window


if __name__ == "__main__":
    app, win = launch()
    sys.exit(app.exec())
