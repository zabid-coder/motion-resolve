"""
CaptionForge for Resolve - Master Application Window (Redirect to PyQt6)
Ensures any legacy calls route directly to the polished, non-buggy PyQt6 interface.
"""

from ui_qt.main_window import MainWindow, launch

__all__ = ["MainWindow", "launch"]
