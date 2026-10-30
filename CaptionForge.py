#!/usr/bin/env python
"""
=============================================================================
 CAPTIONFORGE FOR RESOLVE / MOTION RESOLVE
 High-Performance Animated Captions & Titles Companion for DaVinci Resolve
 Runs natively under: Workspace > Scripts > CaptionForge
=============================================================================
"""

import os
import sys
import subprocess

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from core.paths import ensure_sys_path, find_system_python
ensure_sys_path()


def is_running_inside_resolve():
    """Detect if running inside DaVinci Resolve's embedded script runner."""
    exe = sys.executable.lower()
    if "resolvepython" in exe or "davinci resolve" in exe:
        return True
    if "resolve" in globals() or "fu" in globals():
        return True
    return False


def launch_detached_companion():
    """Launch CaptionForge as an independent desktop process that keeps Resolve unblocked."""
    python_bin = find_system_python()
    main_script = os.path.join(APP_DIR, "main.py")

    env = os.environ.copy()
    env["PYTHONPATH"] = APP_DIR + os.pathsep + env.get("PYTHONPATH", "")

    try:
        if sys.platform == "win32":
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            subprocess.Popen(
                [python_bin, main_script],
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
                env=env
            )
        else:
            subprocess.Popen(
                [python_bin, main_script],
                start_new_session=True,
                close_fds=True,
                env=env
            )
        print("[CaptionForge] Companion panel launched successfully beside DaVinci Resolve!")
        return True
    except Exception as e:
        print(f"[CaptionForge] Error launching companion process: {e}")
        return False


def main():
    if is_running_inside_resolve():
        # When triggered from Workspace > Scripts > CaptionForge, launch as detached companion
        # This keeps DaVinci Resolve 100% interactive and prevents Cocoa thread contention.
        launch_detached_companion()
    else:
        # Running directly via python3 CaptionForge.py
        from ui_qt.main_window import launch
        app, win = launch()
        sys.exit(app.exec())


if __name__ == "__main__":
    main()
