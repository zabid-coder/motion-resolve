#!/usr/bin/env python
"""
Motion Resolve / CaptionForge - Standalone / CLI Launcher
"""

import sys
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from core.paths import ensure_sys_path
ensure_sys_path()

from ui_qt.main_window import launch

if __name__ == "__main__":
    app, win = launch()
    sys.exit(app.exec())
