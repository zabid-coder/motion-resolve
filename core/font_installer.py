"""
Bundled-font installer.

DaVinci Resolve's Text+ can only render fonts installed on the computer, so
the OFL fonts shipped in resources/fonts (licences in resources/fonts/licenses)
are copied into the CURRENT USER's font folder - no admin rights needed:

* macOS:   ~/Library/Fonts
* Windows: %LOCALAPPDATA%\\Microsoft\\Windows\\Fonts  (+ per-user registry entry)
* Linux:   ~/.local/share/fonts

Existing files are never overwritten. Resolve reads its font list at start-up,
so restart Resolve once after new fonts are installed.
"""

import glob
import os
import platform
import shutil
from typing import List

from core.paths import get_app_dir


def bundled_font_files() -> List[str]:
    folder = os.path.join(get_app_dir(), "resources", "fonts")
    return sorted(glob.glob(os.path.join(folder, "*.ttf")) + glob.glob(os.path.join(folder, "*.otf")))


def user_font_dir() -> str:
    system = platform.system()
    if system == "Darwin":
        return os.path.expanduser("~/Library/Fonts")
    if system == "Windows":
        local = os.environ.get("LOCALAPPDATA", os.path.expanduser(r"~\AppData\Local"))
        return os.path.join(local, "Microsoft", "Windows", "Fonts")
    return os.path.expanduser("~/.local/share/fonts")


def _register_windows_font(path: str) -> None:
    try:
        import winreg
        name = os.path.splitext(os.path.basename(path))[0] + " (TrueType)"
        key = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, name, 0, winreg.REG_SZ, path)
    except Exception as exc:
        print(f"[Motion Resolve] Could not register font {path}: {exc}")


def missing_fonts() -> List[str]:
    dest = user_font_dir()
    return [f for f in bundled_font_files() if not os.path.exists(os.path.join(dest, os.path.basename(f)))]


def install_bundled_fonts() -> List[str]:
    """Copy bundled fonts that are not yet in the user's font folder. Returns installed names."""
    dest = user_font_dir()
    installed = []
    todo = missing_fonts()
    if not todo:
        return installed
    os.makedirs(dest, exist_ok=True)
    for src in todo:
        target = os.path.join(dest, os.path.basename(src))
        try:
            shutil.copy2(src, target)
            if platform.system() == "Windows":
                _register_windows_font(target)
            installed.append(os.path.basename(src))
        except Exception as exc:
            print(f"[Motion Resolve] Could not install font {src}: {exc}")
    if installed and platform.system() == "Linux":
        os.system("fc-cache -f >/dev/null 2>&1")
    return installed


def register_app_fonts() -> int:
    """Make bundled fonts available to the Qt preview immediately (no restart)."""
    try:
        from PyQt6.QtGui import QFontDatabase
    except Exception:
        return 0
    count = 0
    for f in bundled_font_files():
        if QFontDatabase.addApplicationFont(f) >= 0:
            count += 1
    try:
        from core.font_catalog import refresh_installed_font_families
        refresh_installed_font_families()
    except Exception:
        pass
    return count
