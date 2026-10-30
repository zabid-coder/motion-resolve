"""
Motion Resolve for DaVinci Resolve Studio - Interactive Adaptive Canvas Preview
Draws responsive 16:9 Landscape, 9:16 Vertical Reel, or 1:1 Square frames with
dead-center crosshairs (snapping at 0.5, 0.5), TV/TikTok safe zones, interactive
drag-and-drop bounding box, live in-place text editor, and floating tool strip.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, QRect, QPoint, QSize, pyqtSignal, QTimer, QByteArray
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QFontMetrics, QIcon, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from ui_qt.theme import COLOR_ORANGE, COLOR_PINK


_TOOL_ICON_PATHS = {
    "play": '<polygon points="7 4 19 12 7 20 7 4"/>',
    "pause": '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>',
    "duplicate": '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/>',
    "copy": '<path d="M8 4h8l4 4v12H8z"/><path d="M16 4v4h4M11 13h6M11 17h6"/>',
    "paste": '<rect x="5" y="6" width="14" height="16" rx="2"/><path d="M9 6V4h6v2M9 12h6M9 16h6"/>',
    "center": '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2"/><path d="M12 1v4m0 14v4M1 12h4m14 0h4"/>',
    "scale": '<path d="M12 3v18M8 7l4-4 4 4M8 17l4 4 4-4"/>',
    "palette": '<path d="M12 3a9 9 0 1 0 0 18h1.2a2 2 0 0 0 1.6-3.2 1.8 1.8 0 0 1 1.5-2.8H18a3 3 0 0 0 3-3c0-5-4-9-9-9Z"/><circle cx="7.5" cy="11" r="1"/><circle cx="10" cy="7.5" r="1"/><circle cx="15" cy="8" r="1"/>',
}


def _tool_icon(name, color="#c9c0d9"):
    path = _TOOL_ICON_PATHS[name]
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{path}</g></svg>'
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


class CanvasInteractiveArea(QWidget):
    """Custom painted responsive canvas area with guideline crosshairs, safe-zones, and bounding box."""

    textChanged = pyqtSignal(str)
    positionChanged = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.caption_text = "Clean Minimal Caption"
        self.hero_word = None
        self.hero_line_index = None
        self.hero_color = None
        self.font_family = "Helvetica Neue"
        self.font_size = 20
        self.text_color = QColor(255, 255, 255)
        self.stroke_enabled = True
        self.box_enabled = False
        self.box_color = QColor(255, 224, 0, 240) # Vox yellow default
        self.pos_x = 0.5  # Normalized 0.0 - 1.0 (0.5 = horizontal center)
        self.pos_y = 0.5  # Normalized 0.0 - 1.0 (0.5 = vertical center)
        self.alignment = "center" # "left", "center", "right"
        self.aspect_ratio = "16:9" # "16:9", "9:16", "1:1"
        self.is_dragging = False
        self.is_snapped_x = True
        self.is_snapped_y = True
        self.show_safe_zone = True
        self.safe_zone_platform = "TikTok"  # "TikTok", "Instagram Reels", "YouTube Shorts", "Broadcast (SMPTE)"
        self.zoom_factor = 1.0
        self.drag_start = QPoint()

        # Motion preview loop timer (30 fps)
        self.is_playing = False
        self.anim_progress = 1.0
        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(33)
        self.anim_timer.timeout.connect(self._on_anim_tick)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # In-place line edit
        self.editor = QLineEdit(self)
        self.editor.setStyleSheet("""
            QLineEdit {
                background: rgba(20, 15, 30, 0.94);
                border: 2px solid #ff5500;
                border-radius: 6px;
                color: #ffffff;
                font-family: "Helvetica Neue", Arial;
                font-weight: bold;
                padding: 4px 8px;
            }
        """)
        self.editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.editor.textChanged.connect(self._on_editor_changed)
        self.editor.returnPressed.connect(self._on_editor_finished)
        self.editor.hide()

    def set_text(self, text):
        if text and self.caption_text != text:
            self.caption_text = text
            self.update()

    def set_font(self, family, size_pt):
        self.font_family = family
        self.font_size = max(16, min(72, int(size_pt)))
        self.update()

    def set_color(self, r, g, b):
        self.text_color = QColor(int(r * 255), int(g * 255), int(b * 255))
        self.update()

    def set_alignment(self, align_str):
        self.alignment = align_str.lower()
        if self.alignment == "left":
            self.editor.setAlignment(Qt.AlignmentFlag.AlignLeft)
        elif self.alignment == "right":
            self.editor.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            self.editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.update()

    def set_aspect_ratio(self, ratio_str):
        if ratio_str in ["16:9", "9:16", "1:1"]:
            self.aspect_ratio = ratio_str
            self.update()

    def set_safe_zone_platform(self, platform_name):
        self.safe_zone_platform = platform_name
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.toggle_play_preview()
            event.accept()
            return
        super().keyPressEvent(event)

    def _on_anim_tick(self):
        self.anim_progress += 0.025
        if self.anim_progress > 1.25:
            self.anim_progress = 0.0
        self.update()

    def toggle_play_preview(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.anim_progress = 0.0
            self.anim_timer.start()
        else:
            self.anim_timer.stop()
            self.anim_progress = 1.0
            self.update()
        return self.is_playing

    def set_box(self, enabled, color=None):
        self.box_enabled = bool(enabled)
        if color:
            if isinstance(color, (list, tuple)) and len(color) >= 3:
                a = int(color[3] * 255) if len(color) > 3 else 240
                self.box_color = QColor(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), a)
            elif isinstance(color, QColor):
                self.box_color = color
        self.update()

    def _on_editor_changed(self, txt):
        self.caption_text = txt
        self.textChanged.emit(txt)
        self.update()

    def _on_editor_finished(self):
        self.editor.hide()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            box = self.get_text_bounding_box()
            if box.contains(event.pos()):
                self.is_dragging = True
                self.drag_start = event.pos() - QPoint(int(self.pos_x * self.width()), int(self.pos_y * self.height()))
            else:
                self.editor.hide()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            new_pos = event.pos() - self.drag_start
            raw_x = max(0.08, min(0.92, new_pos.x() / max(1, self.width())))
            raw_y = max(0.08, min(0.92, new_pos.y() / max(1, self.height())))

            # Magnetic snapping to horizontal center (0.5)
            if abs(raw_x - 0.5) < 0.035:
                self.pos_x = 0.5
                self.is_snapped_x = True
            else:
                self.pos_x = raw_x
                self.is_snapped_x = False

            # Magnetic snapping to exact vertical center (0.5) or lower third (0.72)
            if abs(raw_y - 0.5) < 0.035:
                self.pos_y = 0.5
                self.is_snapped_y = True
            elif abs(raw_y - 0.72) < 0.03:
                self.pos_y = 0.72
                self.is_snapped_y = False
            else:
                self.pos_y = raw_y
                self.is_snapped_y = False

            self.positionChanged.emit(self.pos_x, self.pos_y)
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        box = self.get_text_bounding_box()
        self.editor.setGeometry(box.adjusted(-10, -5, 10, 5))
        self.editor.setFont(QFont(self.font_family, int(self.font_size * 0.7), QFont.Weight.Bold))
        self.editor.setText(self.caption_text)
        self.editor.show()
        self.editor.setFocus()
        self.editor.selectAll()
        super().mouseDoubleClickEvent(event)

    def get_text_bounding_box(self):
        w = max(1, self.width())
        h = max(1, self.height())
        cx = int(self.pos_x * w)
        cy = int(self.pos_y * h)

        font = QFont(self.font_family, int(self.font_size), QFont.Weight.Bold)
        fm = QFontMetrics(font)

        max_text_w = max(120, w - 48)
        align_flag = Qt.AlignmentFlag.AlignCenter
        if self.alignment == "left":
            align_flag = Qt.AlignmentFlag.AlignLeft
        elif self.alignment == "right":
            align_flag = Qt.AlignmentFlag.AlignRight

        text_rect = fm.boundingRect(
            QRect(0, 0, max_text_w, 1000),
            align_flag | Qt.TextFlag.TextWordWrap,
            self.caption_text
        )

        box_w = max(90, min(w - 24, text_rect.width() + 28))
        box_h = max(34, text_rect.height() + 16)

        # Keep within bounds horizontally
        half_w = box_w // 2
        clamped_cx = max(half_w + 10, min(w - half_w - 10, cx))
        return QRect(clamped_cx - half_w, cy - box_h // 2, box_w, box_h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        center_x = w // 2
        center_y = h // 2

        # 1. Background Fill
        painter.fillRect(0, 0, w, h, QColor("#0d0b14"))

        painter.save()
        if self.zoom_factor != 1.0:
            painter.translate(center_x, center_y)
            painter.scale(self.zoom_factor, self.zoom_factor)
            painter.translate(-center_x, -center_y)

        # 2. Viewport Frame Rendering (16:9, 9:16, 1:1)
        if self.aspect_ratio == "16:9":
            # 16:9 Landscape Frame
            frame_pen = QPen(QColor("#26203a"), 1)
            painter.setPen(frame_pen)
            painter.setBrush(QBrush(QColor("#000000")))
            painter.drawRoundedRect(12, 12, w - 24, h - 24, 16, 16)

            # TV / Broadcast Title Safe Zone (90% Action, 80% Title)
            if self.show_safe_zone:
                # 90% Action Safe
                act_pen = QPen(QColor(255, 255, 255, 25), 1, Qt.PenStyle.DashLine)
                painter.setPen(act_pen)
                ax = int(w * 0.08)
                ay = int(h * 0.08)
                painter.drawRect(ax, ay, w - ax * 2, h - ay * 2)

                # 80% Title Safe
                title_pen = QPen(QColor(0, 210, 255, 45), 1, Qt.PenStyle.DashLine)
                painter.setPen(title_pen)
                tx = int(w * 0.12)
                ty = int(h * 0.12)
                painter.drawRect(tx, ty, w - tx * 2, h - ty * 2)

                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                painter.setPen(QColor(0, 210, 255, 80))
                painter.drawText(tx + 6, ty + 14, "16:9 BROADCAST TITLE SAFE (80%)")

        elif self.aspect_ratio == "9:16":
            # 9:16 Smartphone Bezel
            frame_pen = QPen(QColor("#26203a"), 1)
            painter.setPen(frame_pen)
            painter.setBrush(QBrush(QColor("#000000")))
            painter.drawRoundedRect(16, 8, w - 32, h - 16, 16, 16)

            # Dynamic Island Notch
            notch_w, notch_h = 60, 11
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(24, 22, 32)))
            painter.drawRoundedRect(center_x - notch_w // 2, 14, notch_w, notch_h, 5, 5)

            # Platform-Specific Safe Zone Overlays (TikTok, Instagram Reels, YouTube Shorts)
            if self.show_safe_zone:
                plat = self.safe_zone_platform.lower()

                if "reels" in plat:
                    top_y = int(h * 0.11)
                    bot_y = int(h * 0.75)
                    rail_w = 42
                    plat_label = "INSTAGRAM REELS"
                elif "shorts" in plat:
                    top_y = int(h * 0.10)
                    bot_y = int(h * 0.76)
                    rail_w = 42
                    plat_label = "YOUTUBE SHORTS"
                elif "broadcast" in plat:
                    top_y = int(h * 0.10)
                    bot_y = int(h * 0.90)
                    rail_w = 20
                    plat_label = "SMPTE SAFE"
                else:  # Default TikTok
                    top_y = int(h * 0.14)
                    bot_y = int(h * 0.78)
                    rail_w = 48
                    plat_label = "TIKTOK"

                # Danger zone shading: Top header
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(255, 60, 80, 22)))
                painter.drawRect(18, 10, w - 36, top_y - 10)

                # Danger zone shading: Bottom caption / audio bar
                painter.drawRect(18, bot_y, w - 36, h - bot_y - 10)

                # Danger zone shading: Right action buttons rail
                right_rail_x = w - 18 - rail_w
                painter.drawRect(right_rail_x, int(h * 0.40), rail_w, int(bot_y - h * 0.40))

                # Optimal Center Safe Rectangle (Emerald highlight)
                safe_rect = QRect(22, top_y, right_rail_x - 26, bot_y - top_y)
                safe_pen = QPen(QColor(0, 255, 170, 75), 1.2, Qt.PenStyle.DashLine)
                painter.setPen(safe_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(safe_rect, 6, 6)

                # Boundary labels
                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                painter.setPen(QColor(0, 255, 170, 140))
                painter.drawText(26, top_y + 13, f"✔ {plat_label} SAFE ZONE")

                painter.setPen(QColor(255, 80, 90, 130))
                painter.drawText(26, bot_y + 14, "⚠ DANGER: NATIVE UI / CAPTIONS")

                # Right interaction rail dots (Like, comment, share indicators)
                icon_cx = w - 18 - (rail_w // 2)
                icon_ys = [int(h * 0.44), int(h * 0.52), int(h * 0.60), int(h * 0.68), int(h * 0.75)]
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(255, 255, 255, 38)))
                for iy in icon_ys:
                    painter.drawEllipse(icon_cx - 5, iy - 5, 10, 10)

        else: # 1:1 Square
            side = min(w - 24, h - 24)
            sx = (w - side) // 2
            sy = (h - side) // 2
            frame_pen = QPen(QColor("#26203a"), 1)
            painter.setPen(frame_pen)
            painter.setBrush(QBrush(QColor("#000000")))
            painter.drawRoundedRect(sx, sy, side, side, 16, 16)

            if self.show_safe_zone:
                safe_pen = QPen(QColor(255, 255, 255, 35), 1, Qt.PenStyle.DashLine)
                painter.setPen(safe_pen)
                margin = int(side * 0.1)
                painter.drawRect(sx + margin, sy + margin, side - margin * 2, side - margin * 2)

        # 3. Dead-Center Alignment Crosshairs
        guide_color = QColor(COLOR_PINK)
        guide_pen_x = QPen(guide_color, 2 if self.is_snapped_x else 1)
        if not self.is_snapped_x:
            guide_pen_x.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(guide_pen_x)
        painter.drawLine(center_x, 0, center_x, h)

        guide_pen_y = QPen(guide_color, 2 if self.is_snapped_y else 1)
        if not self.is_snapped_y:
            guide_pen_y.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(guide_pen_y)
        painter.drawLine(0, center_y, w, center_y)

        # Center Crosshair Reticle (Exact 0.5, 0.5 indicator)
        if self.is_snapped_x and self.is_snapped_y:
            painter.setPen(QPen(QColor(COLOR_ORANGE), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center_x - 10, center_y - 10, 20, 20)
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.setPen(QColor(COLOR_ORANGE))
            painter.drawText(center_x + 14, center_y - 12, "CENTER [0.5, 0.5]")

        # 4. Text Bounding Box & Handles
        box = self.get_text_bounding_box()

        painter.save()
        if self.is_playing:
            p = self.anim_progress
            if p <= 0.35:  # Entrance phase
                norm = p / 0.35
                ease = 1.0 - (1.0 - norm) ** 3
                anim_dy = (1.0 - ease) * 45.0
                anim_sc = 0.88 + 0.12 * ease
                anim_op = min(1.0, norm * 1.8)
            elif p <= 0.75:  # Hold phase
                anim_dy = 0.0
                anim_sc = 1.0
                anim_op = 1.0
            elif p <= 1.0:  # Exit phase
                norm = (p - 0.75) / 0.25
                ease = norm ** 2
                anim_dy = ease * 40.0
                anim_sc = 1.0 - 0.08 * ease
                anim_op = max(0.0, 1.0 - norm)
            else:
                anim_dy = 0.0
                anim_sc = 1.0
                anim_op = 0.0

            bc = box.center()
            painter.translate(bc.x(), bc.y() + anim_dy)
            painter.scale(anim_sc, anim_sc)
            painter.translate(-bc.x(), -bc.y())
            painter.setOpacity(anim_op)

        # Render Background Box (Vox / Ali Abdaal highlight styles)
        if self.box_enabled:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self.box_color))
            painter.drawRoundedRect(box.adjusted(-4, -2, 4, 2), 6, 6)

        # Orange outline
        orange_pen = QPen(QColor(COLOR_ORANGE), 2)
        painter.setPen(orange_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(box, 6, 6)

        # 6 Anchor Handles (Corners + Midpoints)
        handle_size = 7
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.setBrush(QBrush(QColor(COLOR_ORANGE)))

        handles = [
            box.topLeft(),
            box.topRight(),
            box.bottomLeft(),
            box.bottomRight(),
            QPoint(box.center().x(), box.top()),
            QPoint(box.center().x(), box.bottom())
        ]
        for pt in handles:
            painter.drawRect(pt.x() - handle_size // 2, pt.y() - handle_size // 2, handle_size, handle_size)

        # 5. Render Caption Text
        if not self.editor.isVisible():
            font = QFont(self.font_family, int(self.font_size), QFont.Weight.Bold)
            painter.setFont(font)

            draw_rect = box.adjusted(6, 2, -6, -2)
            align_flag = Qt.AlignmentFlag.AlignCenter
            if self.alignment == "left":
                align_flag = Qt.AlignmentFlag.AlignLeft
            elif self.alignment == "right":
                align_flag = Qt.AlignmentFlag.AlignRight

            if self.hero_line_index is None or not self.hero_color:
                # Drop shadow
                if self.stroke_enabled and not self.box_enabled:
                    painter.setPen(QPen(QColor(0, 0, 0, 200), 3))
                    painter.drawText(draw_rect.adjusted(-1, -1, -1, -1), align_flag | Qt.TextFlag.TextWordWrap, self.caption_text)
                    painter.drawText(draw_rect.adjusted(1, 1, 1, 1), align_flag | Qt.TextFlag.TextWordWrap, self.caption_text)

                painter.setPen(QPen(self.text_color))
                painter.drawText(draw_rect, align_flag | Qt.TextFlag.TextWordWrap, self.caption_text)
            else:
                # Draw the same line split used by the two-layer Fusion title.
                lines = self.caption_text.split("\n")
                metrics = QFontMetrics(font)
                line_height = metrics.height()
                block_height = line_height * len(lines)
                first_y = draw_rect.center().y() - block_height // 2
                for index, line in enumerate(lines):
                    line_rect = QRect(draw_rect.x(), first_y + index * line_height, draw_rect.width(), line_height)
                    if self.stroke_enabled and not self.box_enabled:
                        painter.setPen(QPen(QColor(0, 0, 0, 200), 3))
                        painter.drawText(line_rect.adjusted(-1, -1, -1, -1), align_flag | Qt.AlignmentFlag.AlignVCenter, line)
                        painter.drawText(line_rect.adjusted(1, 1, 1, 1), align_flag | Qt.AlignmentFlag.AlignVCenter, line)
                    color = self.text_color
                    if index == self.hero_line_index:
                        color = QColor.fromRgbF(*self.hero_color[:3])
                    painter.setPen(QPen(color))
                    painter.drawText(line_rect, align_flag | Qt.AlignmentFlag.AlignVCenter, line)

        painter.restore()  # Restore motion transform
        painter.restore()  # Restore viewport zoom

        if self.is_playing:
            # Draw pulsing playhead banner
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.setPen(QPen(QColor(COLOR_ORANGE)))
            painter.setBrush(QBrush(QColor(255, 85, 0, 45)))
            badge_rect = QRect(w - 175, 14, 155, 20)
            painter.drawRoundedRect(badge_rect, 5, 5)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, "▶ MOTION PREVIEWING")


class PhoneCanvasView(QWidget):
    """Container widget matching Motion Resolve's responsive canvas."""

    textUpdated = pyqtSignal(str)
    positionUpdated = pyqtSignal(float, float)
    actionTriggered = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_zoom = 100

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Top Alignment & Position Controls Bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(8, 6, 8, 4)
        top_bar.setSpacing(6)

        self.lbl_title = QLabel("Composition / Typography Preview")
        self.lbl_title.setStyleSheet("color: #8b80a8; font-size: 11px; font-weight: 700; letter-spacing: 0.3px; padding-right: 4px;")
        top_bar.addWidget(self.lbl_title)

        btn_style = """
            QPushButton {
                background-color: #171328;
                border: 1px solid #28213e;
                border-radius: 6px;
                color: #c5bcdb;
                font-size: 11px;
                font-weight: 700;
                padding: 6px 7px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #272042;
                color: #ffffff;
                border-color: #ff5500;
            }
        """

        self.btn_left = QPushButton("⇤ Left")
        self.btn_left.setToolTip("Align Text to Left Boundary")

        self.btn_center = QPushButton("⤱ Center")
        self.btn_center.setToolTip("Snap to EXACT Dead Center [0.5, 0.5] in Both Viewport and Resolve Timeline")

        self.btn_right = QPushButton("Right ⇥")
        self.btn_right.setToolTip("Align Text to Right Boundary")

        self.btn_lower = QPushButton("⤓ Lower 3rd")
        self.btn_lower.setToolTip("Snap to Lower Third Position [0.5, 0.28]")

        for b in [self.btn_left, self.btn_center, self.btn_right, self.btn_lower]:
            b.setStyleSheet(btn_style)
            top_bar.addWidget(b)

        top_bar.addStretch()

        self.btn_fit = QPushButton("⤢ 100%")
        self.btn_fit.setToolTip("Reset canvas zoom to 100%")
        self.btn_fit.setStyleSheet(btn_style)
        top_bar.addWidget(self.btn_fit)

        layout.addLayout(top_bar)

        # 2. Center Body: Floating Tools + Painted Canvas
        center_row = QHBoxLayout()
        center_row.setContentsMargins(6, 0, 6, 4)
        center_row.setSpacing(6)

        # Floating Left Tool Strip with larger, clear icons
        tool_col = QVBoxLayout()
        tool_col.setSpacing(6)

        tool_btn_style = """
            QPushButton {
                background-color: #19142b;
                border: 1.5px solid #2f254e;
                border-radius: 8px;
                color: #d4cced;
                font-size: 16px;
                font-weight: bold;
                min-width: 38px;
                max-width: 38px;
                min-height: 38px;
                max-height: 38px;
            }
            QPushButton:hover {
                background-color: #2d234e;
                color: #ffffff;
                border-color: #ff5500;
            }
        """

        self.btn_play = QPushButton()
        self.btn_play.setIcon(_tool_icon("play"))
        self.btn_play.setToolTip("Preview Title Motion Entrance & Exit (Spacebar)")
        self.btn_dup = QPushButton()
        self.btn_dup.setIcon(_tool_icon("duplicate"))
        self.btn_dup.setToolTip("Duplicate Active Title Clip (Alt+D)")
        self.btn_copy = QPushButton()
        self.btn_copy.setIcon(_tool_icon("copy"))
        self.btn_copy.setToolTip("Copy title font, fill, stroke, shadow, and box styling")
        self.btn_paste = QPushButton()
        self.btn_paste.setIcon(_tool_icon("paste"))
        self.btn_paste.setToolTip("Paste copied text styling to selected titles; motion is not included")
        self.btn_cross = QPushButton()
        self.btn_cross.setIcon(_tool_icon("center"))
        self.btn_cross.setToolTip("Snap Text Box to Exact Screen Center [0.5, 0.5]")
        self.btn_scale = QPushButton()
        self.btn_scale.setIcon(_tool_icon("scale"))
        self.btn_scale.setToolTip("Increase title text size by 15%")
        self.btn_palette = QPushButton()
        self.btn_palette.setIcon(_tool_icon("palette"))
        self.btn_palette.setToolTip("Pick Text & Accent Fill Color")
        self.btn_font = QPushButton("Aa")
        self.btn_font.setToolTip("Select Font Family & Size")

        for b in [self.btn_play, self.btn_dup, self.btn_copy, self.btn_paste, self.btn_cross, self.btn_scale, self.btn_palette, self.btn_font]:
            b.setStyleSheet(tool_btn_style)
            b.setIconSize(QSize(20, 20))
            if b is not self.btn_font:
                b.setText("")
            tool_col.addWidget(b)

        tool_col.addStretch()
        center_row.addLayout(tool_col)

        # Interactive Canvas Area
        self.canvas_area = CanvasInteractiveArea(self)
        self.canvas_area.setStyleSheet("background-color: #000000; border: 1px solid #26203a; border-radius: 16px;")
        self.canvas_area.textChanged.connect(self.textUpdated.emit)
        self.canvas_area.positionChanged.connect(self.positionUpdated.emit)
        center_row.addWidget(self.canvas_area, stretch=1)

        layout.addLayout(center_row, stretch=1)

        # 3. Bottom Aspect Ratio, Safe Zone, & Zoom Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(8, 2, 8, 6)
        bottom_bar.setSpacing(6)

        # Aspect Ratio Selector Pills
        ar_container = QWidget()
        ar_container.setStyleSheet("""
            QWidget {
                background-color: #171325;
                border: 1px solid #282140;
                border-radius: 12px;
            }
        """)
        ar_layout = QHBoxLayout(ar_container)
        ar_layout.setContentsMargins(4, 2, 4, 2)
        ar_layout.setSpacing(2)

        ar_btn_style = """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 9px;
                color: #9d93b8;
                font-size: 10px;
                font-weight: 700;
                padding: 3px 8px;
            }
            QPushButton:checked {
                background-color: #ff5500;
                color: #ffffff;
            }
        """
        self.btn_ar_16_9 = QPushButton("16:9")
        self.btn_ar_16_9.setCheckable(True)
        self.btn_ar_16_9.setChecked(True)
        self.btn_ar_16_9.setStyleSheet(ar_btn_style)

        self.btn_ar_9_16 = QPushButton("9:16")
        self.btn_ar_9_16.setCheckable(True)
        self.btn_ar_9_16.setStyleSheet(ar_btn_style)

        self.btn_ar_1_1 = QPushButton("1:1")
        self.btn_ar_1_1.setCheckable(True)
        self.btn_ar_1_1.setStyleSheet(ar_btn_style)

        ar_layout.addWidget(self.btn_ar_16_9)
        ar_layout.addWidget(self.btn_ar_9_16)
        ar_layout.addWidget(self.btn_ar_1_1)
        bottom_bar.addWidget(ar_container)

        self.btn_ar_16_9.clicked.connect(lambda: self._set_aspect("16:9"))
        self.btn_ar_9_16.clicked.connect(lambda: self._set_aspect("9:16"))
        self.btn_ar_1_1.clicked.connect(lambda: self._set_aspect("1:1"))

        # Safe Zone Pill Button
        self.btn_safe_zone = QPushButton("🛡 Safe Zone")
        self.btn_safe_zone.setToolTip("Toggle Action & Title Safe Zone Overlays")
        self.btn_safe_zone.setCheckable(True)
        self.btn_safe_zone.setChecked(True)
        self.btn_safe_zone.setStyleSheet("""
            QPushButton {
                background-color: #171325;
                border: 1px solid #282140;
                border-radius: 10px;
                color: #9d93b8;
                font-size: 10px;
                font-weight: 700;
                padding: 4px 10px;
            }
            QPushButton:checked {
                background-color: #311508;
                border-color: #ff5500;
                color: #ff5500;
            }
            QPushButton:hover {
                border-color: #ff6a1a;
            }
        """)
        self.btn_safe_zone.clicked.connect(self._toggle_safe_zone)
        bottom_bar.addWidget(self.btn_safe_zone)

        self.combo_safe_platform = QComboBox()
        self.combo_safe_platform.addItems(["TikTok", "Instagram Reels", "YouTube Shorts", "Broadcast (SMPTE)"])
        self.combo_safe_platform.setToolTip("Target platform for mobile/broadcast safe zone overlay guides")
        self.combo_safe_platform.setStyleSheet("""
            QComboBox {
                background-color: #171328;
                border: 1px solid #28213e;
                border-radius: 9px;
                color: #c5bcdb;
                font-size: 10px;
                font-weight: 700;
                padding: 3px 6px;
                min-width: 90px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #171328;
                color: #ffffff;
                selection-background-color: #ff5500;
            }
        """)
        self.combo_safe_platform.currentTextChanged.connect(self.canvas_area.set_safe_zone_platform)
        bottom_bar.addWidget(self.combo_safe_platform)

        bottom_bar.addStretch()

        # Floating zoom pill [- 100% +] at bottom center
        zoom_container = QWidget()
        zoom_container.setStyleSheet("""
            QWidget {
                background-color: #171325;
                border: 1px solid #282140;
                border-radius: 12px;
            }
        """)
        zoom_layout = QHBoxLayout(zoom_container)
        zoom_layout.setContentsMargins(8, 2, 8, 2)
        zoom_layout.setSpacing(6)

        zoom_btn_style = "border: none; background: transparent; color: #f3f1fa; font-weight: bold; font-size: 14px;"
        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setStyleSheet(zoom_btn_style)
        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setStyleSheet("border: none; color: #f3f1fa; font-size: 10px; font-weight: bold;")
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setStyleSheet(zoom_btn_style)

        zoom_layout.addWidget(self.btn_zoom_out)
        zoom_layout.addWidget(self.lbl_zoom)
        zoom_layout.addWidget(self.btn_zoom_in)

        bottom_bar.addWidget(zoom_container)
        layout.addLayout(bottom_bar)

        # Wire canvas controls
        self.btn_left.clicked.connect(lambda: self._on_align_btn("align_left"))
        self.btn_center.clicked.connect(lambda: self._on_align_btn("align_center"))
        self.btn_right.clicked.connect(lambda: self._on_align_btn("align_right"))
        self.btn_lower.clicked.connect(lambda: self._on_align_btn("align_lower_third"))
        self.btn_fit.clicked.connect(lambda: self.actionTriggered.emit("fit"))

        self.btn_play.clicked.connect(self._toggle_motion_play)
        self.btn_dup.clicked.connect(lambda: self.actionTriggered.emit("duplicate"))
        self.btn_copy.clicked.connect(lambda: self.actionTriggered.emit("copy"))
        self.btn_paste.clicked.connect(lambda: self.actionTriggered.emit("paste"))
        self.btn_cross.clicked.connect(lambda: self._on_align_btn("align_center"))
        self.btn_scale.clicked.connect(lambda: self.actionTriggered.emit("scale"))
        self.btn_palette.clicked.connect(lambda: self.actionTriggered.emit("palette"))
        self.btn_font.clicked.connect(lambda: self.actionTriggered.emit("font"))

        self.btn_zoom_in.clicked.connect(lambda: self._adjust_zoom(10))
        self.btn_zoom_out.clicked.connect(lambda: self._adjust_zoom(-10))

    def _set_aspect(self, aspect):
        self.btn_ar_16_9.setChecked(aspect == "16:9")
        self.btn_ar_9_16.setChecked(aspect == "9:16")
        self.btn_ar_1_1.setChecked(aspect == "1:1")
        self.canvas_area.set_aspect_ratio(aspect)
        if aspect == "16:9":
            self.combo_safe_platform.setCurrentText("Broadcast (SMPTE)")
        elif aspect == "9:16" and self.combo_safe_platform.currentText() == "Broadcast (SMPTE)":
            self.combo_safe_platform.setCurrentText("TikTok")

    def _toggle_motion_play(self):
        playing = self.canvas_area.toggle_play_preview()
        if playing:
            self.btn_play.setIcon(_tool_icon("pause", COLOR_ORANGE))
            self.btn_play.setToolTip("Pause Motion Preview (Spacebar)")
        else:
            self.btn_play.setIcon(_tool_icon("play"))
            self.btn_play.setToolTip("Preview Title Motion Entrance & Exit (Spacebar)")

    def _on_align_btn(self, action):
        if action == "align_left":
            self.canvas_area.set_alignment("left")
        elif action == "align_right":
            self.canvas_area.set_alignment("right")
        elif action == "align_center":
            self.canvas_area.set_alignment("center")
            self.canvas_area.pos_x = 0.5
            self.canvas_area.pos_y = 0.5
            self.canvas_area.is_snapped_x = True
            self.canvas_area.is_snapped_y = True
            self.canvas_area.update()
        elif action == "align_lower_third":
            self.canvas_area.set_alignment("center")
            self.canvas_area.pos_x = 0.5
            self.canvas_area.pos_y = 0.72
            self.canvas_area.is_snapped_x = True
            self.canvas_area.is_snapped_y = False
            self.canvas_area.update()
        self.actionTriggered.emit(action)

    def _toggle_safe_zone(self):
        self.canvas_area.show_safe_zone = self.btn_safe_zone.isChecked()
        self.canvas_area.update()

    def _adjust_zoom(self, delta):
        self.current_zoom = max(50, min(200, self.current_zoom + delta))
        self.lbl_zoom.setText(f"{self.current_zoom}%")
        self.canvas_area.zoom_factor = self.current_zoom / 100.0
        self.canvas_area.update()
