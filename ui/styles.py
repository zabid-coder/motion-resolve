"""
Motion Resolve - Visual Aesthetic Theme (EasyMotion Style)
Deep purple-black charcoal palette, neon orange accents, rounded pill controls,
mobile phone canvas preview, and glowing active states.
"""

# Palette definition
COLOR_BG_DARK = "#0d0b14"       # Deepest background
COLOR_PANEL_BG = "#151221"      # Card / panel background
COLOR_CANVAS_BG = "#000000"     # Pure black phone screen
COLOR_BORDER = "#252038"        # Subtle card border
COLOR_BORDER_LIGHT = "#362f52"  # Lighter border for interactive elements
COLOR_ACCENT = "#ff5500"        # Iconic EasyMotion neon orange
COLOR_ACCENT_HOVER = "#ff6a1a"
COLOR_ACCENT_MUTED = "#3d1b0d"  # Dark orange container background
COLOR_TEXT_WHITE = "#ffffff"
COLOR_TEXT_MUTED = "#857e9b"    # Lavender-tinted muted text
COLOR_GUIDELINE_PINK = "#ff2a85"# Vertical alignment guideline pink

EASYMOTION_QSS = f"""
QWidget {{
    background-color: {COLOR_BG_DARK};
    color: {COLOR_TEXT_WHITE};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 11px;
}}

/* Top Window & Containers */
QFrame#MainContainer {{
    background-color: {COLOR_BG_DARK};
}}

QFrame#PanelCard {{
    background-color: {COLOR_PANEL_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 12px;
}}

QFrame#PhoneCanvas {{
    background-color: {COLOR_CANVAS_BG};
    border: 1px solid {COLOR_BORDER};
    border-radius: 16px;
}}

/* Headings & Labels */
QLabel {{
    background: transparent;
    color: {COLOR_TEXT_MUTED};
    font-size: 11px;
}}

QLabel#AppTitleOrange {{
    color: {COLOR_ACCENT};
    font-size: 15px;
    font-weight: 800;
}}

QLabel#AppTitleWhite {{
    color: {COLOR_TEXT_WHITE};
    font-size: 15px;
    font-weight: 800;
}}

QLabel#SectionHeader {{
    color: {COLOR_TEXT_MUTED};
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QLabel#StatusMuted {{
    color: #6a647e;
    font-size: 9px;
    font-family: Menlo, Monaco, "Courier New", monospace;
}}

/* Push Buttons */
QPushButton {{
    background-color: #1e1930;
    color: {COLOR_TEXT_WHITE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 11px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: #2a2342;
    border-color: {COLOR_BORDER_LIGHT};
}}

QPushButton:pressed {{
    background-color: #151122;
}}

/* Active / Highlighted Orange Pill Buttons */
QPushButton#BtnOrangePill {{
    background-color: {COLOR_ACCENT};
    color: #ffffff;
    border: 1px solid {COLOR_ACCENT};
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: 700;
}}

QPushButton#BtnOrangePill:hover {{
    background-color: {COLOR_ACCENT_HOVER};
}}

QPushButton#BtnOrangeOutline {{
    background-color: transparent;
    color: {COLOR_ACCENT};
    border: 1.5px solid {COLOR_ACCENT};
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: 700;
}}

QPushButton#BtnOrangeOutline:hover {{
    background-color: {COLOR_ACCENT_MUTED};
}}

/* Big AUTO Button */
QPushButton#BtnBigAuto {{
    background-color: #1a1426;
    color: {COLOR_TEXT_WHITE};
    border: 1.5px solid {COLOR_ACCENT};
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 2px;
}}

QPushButton#BtnBigAuto:hover {{
    background-color: {COLOR_ACCENT};
    color: #ffffff;
}}

/* D-Pad Buttons */
QPushButton#BtnDPad {{
    background-color: #1b162b;
    color: {COLOR_TEXT_MUTED};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    min-width: 22px;
    max-width: 28px;
    min-height: 22px;
    max-height: 28px;
    font-size: 10px;
    padding: 0px;
}}

QPushButton#BtnDPad:hover {{
    background-color: #2e264a;
    color: #ffffff;
    border-color: {COLOR_ACCENT};
}}

QPushButton#BtnDPadActive {{
    background-color: {COLOR_ACCENT};
    color: #ffffff;
    border: 1px solid {COLOR_ACCENT};
    border-radius: 6px;
    font-size: 10px;
}}

/* Effect Center Grid Buttons */
QPushButton#BtnEffectItem {{
    background-color: #181427;
    color: {COLOR_TEXT_MUTED};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 6px 4px;
    font-size: 10px;
    font-weight: 600;
}}

QPushButton#BtnEffectItem:hover {{
    background-color: #251f3b;
    color: #ffffff;
    border-color: {COLOR_BORDER_LIGHT};
}}

QPushButton#BtnEffectItemActive {{
    background-color: {COLOR_ACCENT};
    color: #ffffff;
    border: 1px solid {COLOR_ACCENT};
    border-radius: 8px;
    padding: 6px 4px;
    font-size: 10px;
    font-weight: 700;
}}

/* Floating Canvas Toolbar Buttons */
QPushButton#BtnCanvasTool {{
    background-color: #19142b;
    color: {COLOR_TEXT_MUTED};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    min-width: 26px;
    max-width: 26px;
    min-height: 26px;
    max-height: 26px;
    padding: 0px;
    font-size: 11px;
}}

QPushButton#BtnCanvasTool:hover {{
    background-color: #2c234a;
    color: #ffffff;
    border-color: {COLOR_ACCENT};
}}

/* Tab Bar Segmented Control */
QTabBar {{
    background-color: #151124;
    border-radius: 12px;
    border: 1px solid {COLOR_BORDER};
}}

QTabBar::tab {{
    background-color: transparent;
    color: {COLOR_TEXT_MUTED};
    padding: 6px 20px;
    font-size: 11px;
    font-weight: 700;
    border-radius: 10px;
    margin: 2px;
}}

QTabBar::tab:selected {{
    background-color: #27213d;
    color: {COLOR_TEXT_WHITE};
    border: 1px solid {COLOR_BORDER_LIGHT};
}}

QTabBar::tab:hover {{
    color: {COLOR_TEXT_WHITE};
}}

/* Line Edit / Input */
QLineEdit, QTextEdit {{
    background-color: #100d1c;
    color: {COLOR_TEXT_WHITE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 5px 8px;
}}

QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {COLOR_ACCENT};
}}

/* ComboBox */
QComboBox {{
    background-color: #171326;
    color: {COLOR_TEXT_WHITE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 4px 8px;
}}

QComboBox:hover {{
    border-color: {COLOR_BORDER_LIGHT};
}}

/* Sliders */
QSlider::groove:horizontal {{
    height: 3px;
    background: #252038;
    border-radius: 1.5px;
}}

QSlider::sub-page:horizontal {{
    background: {COLOR_ACCENT};
    border-radius: 1.5px;
}}

QSlider::handle:horizontal {{
    background: #ffffff;
    border: 1.5px solid {COLOR_ACCENT};
    width: 12px;
    margin-top: -4.5px;
    margin-bottom: -4.5px;
    border-radius: 6px;
}}

/* CheckBoxes */
QCheckBox {{
    spacing: 6px;
    color: {COLOR_TEXT_MUTED};
    font-size: 11px;
}}

QCheckBox::indicator {{
    width: 13px;
    height: 13px;
    border-radius: 3px;
    border: 1px solid {COLOR_BORDER};
    background: #141021;
}}

QCheckBox::indicator:checked {{
    background: {COLOR_ACCENT};
    border-color: {COLOR_ACCENT};
}}

/* Floating Drawer Card */
QFrame#ConvertDrawer {{
    background-color: #1b162b;
    border: 1.5px solid {COLOR_ACCENT};
    border-radius: 12px;
    padding: 10px;
}}
"""
