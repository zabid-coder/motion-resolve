"""
Motion Resolve - EasyMotion Obsidian & Neon Orange Theme Tokens and Styles
Unified PyQt6 styling matching EasyMotion Toolkit 1-to-1.
"""

# 1. Exact EasyMotion Color Tokens
COLOR_BG_BASE = "#0d0b14"
COLOR_SURFACE_CARD = "#13101d"
COLOR_SURFACE_ELEVATED = "#181426"
COLOR_BORDER_SUBTLE = "#26203a"
COLOR_BORDER_CARD = "#1e1930"
COLOR_ACCENT_ORANGE = "#ff5500"
COLOR_ACCENT_HOVER = "#ff6a1a"
COLOR_ACCENT_ACTIVE = "#e04a00"
COLOR_TEXT_PRIMARY = "#f3f1fa"
COLOR_TEXT_SECONDARY = "#9d93b8"
COLOR_TEXT_MUTED = "#635b7b"
COLOR_PINK = "#ff2a85"

# Legacy & Semantic Aliases
COLOR_BG = COLOR_BG_BASE
COLOR_CARD = COLOR_SURFACE_CARD
COLOR_CANVAS = "#000000"
COLOR_BORDER = COLOR_BORDER_SUBTLE
COLOR_BORDER_LIGHT = "#3b325c"
COLOR_ORANGE = COLOR_ACCENT_ORANGE
COLOR_ORANGE_HOVER = COLOR_ACCENT_HOVER
COLOR_ORANGE_MUTED = "#331508"
COLOR_TEXT = COLOR_TEXT_PRIMARY
COLOR_MUTED = COLOR_TEXT_SECONDARY

# 2. Pill Stylesheets
STYLE_PILL_ACTIVE = """
    QPushButton {
        background-color: #ff5500;
        color: #ffffff;
        border: 1px solid #ff7722;
        border-radius: 7px;
        font-weight: 700;
        font-size: 11px;
        padding: 5px 12px;
    }
    QPushButton:hover {
        background-color: #ff6a1a;
    }
"""

STYLE_PILL_INACTIVE = """
    QPushButton {
        background-color: #171325;
        color: #9d93b8;
        border: 1px solid #282140;
        border-radius: 7px;
        font-weight: 600;
        font-size: 11px;
        padding: 5px 12px;
    }
    QPushButton:hover {
        background-color: #211c33;
        color: #f3f1fa;
        border-color: #3b325c;
    }
"""

# 3. Drawer & Canvas Containers
STYLE_DRAWER_CONTAINER = """
    ConvertCaptionsDrawer {
        background-color: #171225;
        border: 1.5px solid #ff5500;
        border-radius: 12px;
    }
"""

STYLE_CANVAS_VIEWPORT = """
    background-color: #000000;
    border: 1px solid #26203a;
    border-radius: 16px;
"""

# 4. Outlined & Action Buttons
STYLE_ORANGE_OUTLINE = """
    QPushButton {
        background-color: transparent;
        color: #ffffff;
        border: 1.5px solid #ff5500;
        border-radius: 7px;
        font-weight: 700;
        font-size: 11px;
        padding: 5px 12px;
    }
    QPushButton:hover {
        background-color: #331508;
        border-color: #ff6a1a;
    }
"""

STYLE_DPAD_NORMAL = """
    QPushButton {
        background-color: #171325;
        color: #9d93b8;
        border: 1px solid #282140;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 700;
        min-width: 32px;
        max-width: 36px;
        min-height: 30px;
        max-height: 34px;
    }
    QPushButton:hover {
        background-color: #211c33;
        color: #f3f1fa;
        border-color: #3b325c;
    }
"""

STYLE_DPAD_ACTIVE = """
    QPushButton {
        background-color: #ff5500;
        color: #ffffff;
        border: 1px solid #ff7722;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 800;
        min-width: 32px;
        max-width: 36px;
        min-height: 30px;
        max-height: 34px;
    }
"""

STYLE_EFFECT_NORMAL = """
    QPushButton {
        background-color: #171325;
        color: #9d93b8;
        border: 1px solid #282140;
        border-radius: 9px;
        font-size: 11px;
        font-weight: 600;
        padding: 8px 6px;
    }
    QPushButton:hover {
        background-color: #211c33;
        color: #f3f1fa;
        border-color: #3b325c;
    }
"""

STYLE_EFFECT_ACTIVE = """
    QPushButton {
        background-color: #ff5500;
        color: #ffffff;
        border: 1px solid #ff7722;
        border-radius: 9px;
        font-size: 11px;
        font-weight: 800;
        padding: 8px 6px;
    }
    QPushButton:hover {
        background-color: #ff6a1a;
    }
"""

STYLE_BTN_AUTO = """
    QPushButton {
        background-color: #13101d;
        color: #f3f1fa;
        border: 1.5px solid #ff5500;
        border-radius: 9px;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 2px;
        padding: 8px 16px;
    }
    QPushButton:hover {
        background-color: #ff5500;
        color: #ffffff;
        border-color: #ff6a1a;
    }
"""

# 5. Master Obsidian & Neon Orange Application Stylesheet
STYLE_OBSIDIAN_SHEET = f"""
QWidget {{
    background-color: {COLOR_BG_BASE};
    color: {COLOR_TEXT_PRIMARY};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 11px;
    selection-background-color: {COLOR_ACCENT_ORANGE};
}}

/* Top Window */
QMainWindow {{
    background-color: {COLOR_BG_BASE};
}}

QFrame#MainContainer {{
    background-color: {COLOR_BG_BASE};
}}

QFrame#PanelCard, QWidget#PanelCard {{
    background-color: {COLOR_SURFACE_CARD};
    border: 1px solid {COLOR_BORDER_SUBTLE};
    border-radius: 12px;
}}

QFrame#PhoneCanvas, QWidget#PhoneCanvas {{
    background-color: #000000;
    border: 1px solid {COLOR_BORDER_SUBTLE};
    border-radius: 16px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: #110e1c;
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: #2b2342;
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLOR_ACCENT_ORANGE};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Tab Bar */
QTabBar {{
    background-color: #141022;
    border: 1px solid {COLOR_BORDER_SUBTLE};
    border-radius: 12px;
}}
QTabBar::tab {{
    background: transparent;
    color: {COLOR_TEXT_SECONDARY};
    padding: 7px 22px;
    font-size: 12px;
    font-weight: 700;
    border-radius: 10px;
    margin: 2px;
}}
QTabBar::tab:selected {{
    background-color: #26203d;
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER_SUBTLE};
}}
QTabBar::tab:hover {{
    color: {COLOR_TEXT_PRIMARY};
}}

/* Inputs & Combos */
QLineEdit, QTextEdit {{
    background-color: #100d1c;
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER_SUBTLE};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 11px;
}}
QLineEdit:focus, QTextEdit:focus {{
    border: 1.5px solid {COLOR_ACCENT_ORANGE};
}}

QComboBox {{
    background-color: #171328;
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER_SUBTLE};
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 11px;
}}
QComboBox:hover {{
    border-color: {COLOR_BORDER_LIGHT};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: #1a152d;
    border: 1px solid {COLOR_BORDER_SUBTLE};
    selection-background-color: {COLOR_ACCENT_ORANGE};
    color: {COLOR_TEXT_PRIMARY};
    border-radius: 6px;
    padding: 4px;
}}

/* Sliders */
QSlider::groove:horizontal {{
    height: 4px;
    background: {COLOR_BORDER_SUBTLE};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {COLOR_ACCENT_ORANGE};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: #ffffff;
    border: 1.5px solid {COLOR_ACCENT_ORANGE};
    width: 14px;
    height: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{
    background: {COLOR_ACCENT_HOVER};
}}

/* CheckBoxes */
QCheckBox {{
    spacing: 7px;
    color: {COLOR_TEXT_SECONDARY};
    font-size: 11px;
    font-weight: 500;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 4px;
    border: 1px solid {COLOR_BORDER_SUBTLE};
    background: #141024;
}}
QCheckBox::indicator:checked {{
    background: {COLOR_ACCENT_ORANGE};
    border-color: {COLOR_ACCENT_ORANGE};
}}

/* Tree / Lists */
QTreeWidget {{
    background-color: #120e20;
    border: 1px solid {COLOR_BORDER_SUBTLE};
    border-radius: 10px;
    color: {COLOR_TEXT_PRIMARY};
    padding: 4px;
}}
QTreeWidget::item {{
    padding: 6px 8px;
    border-radius: 6px;
}}
QTreeWidget::item:selected {{
    background-color: #272042;
    color: #ffffff;
    border: 1px solid {COLOR_ACCENT_ORANGE};
}}
QTreeWidget::item:hover {{
    background-color: #1d1733;
}}
QHeaderView::section {{
    background-color: #171328;
    color: {COLOR_TEXT_MUTED};
    font-size: 10px;
    font-weight: 700;
    border: none;
    padding: 4px 8px;
    border-radius: 4px;
}}
"""

MAIN_STYLE = STYLE_OBSIDIAN_SHEET
GLOBAL_QSS = STYLE_OBSIDIAN_SHEET
