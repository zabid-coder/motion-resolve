#!/usr/bin/env python
"""
=============================================================================
 MOTION RESOLVE - Viral Captions & Titles Toolkit for DaVinci Resolve Studio
 Runs natively under: Workspace > Scripts > Motion Resolve
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
    main_mod = sys.modules.get("__main__")
    if main_mod:
        if hasattr(main_mod, "resolve") or hasattr(main_mod, "fu") or hasattr(main_mod, "fusion"):
            return True
    if "resolve" in globals() or "fu" in globals() or "fusion" in globals():
        return True
    if "fusionscript" in sys.modules or "DaVinciResolveScript" in sys.modules or "bmd" in sys.modules:
        return True
    return False


def launch_detached_companion():
    """Launch Motion Resolve as an independent desktop process that keeps Resolve unblocked."""
    python_bin = find_system_python()
    main_script = os.path.join(APP_DIR, "main.py")

    env = os.environ.copy()
    env["PYTHONPATH"] = APP_DIR + os.pathsep + env.get("PYTHONPATH", "")

    progdata = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
    if "RESOLVE_SCRIPT_API" not in env:
        env["RESOLVE_SCRIPT_API"] = os.path.join(progdata, "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting")
    if "RESOLVE_SCRIPT_LIB" not in env and sys.platform == "win32":
        env["RESOLVE_SCRIPT_LIB"] = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"

    try:
        if sys.platform == "win32":
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            CREATE_BREAKAWAY_FROM_JOB = 0x01000000
            flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
            try:
                subprocess.Popen(
                    [python_bin, main_script],
                    creationflags=flags | CREATE_BREAKAWAY_FROM_JOB,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                    env=env
                )
            except Exception:
                subprocess.Popen(
                    [python_bin, main_script],
                    creationflags=flags,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                    env=env
                )
        else:
            subprocess.Popen(
                [python_bin, main_script],
                start_new_session=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                env=env
            )
        print("[Motion Resolve] Companion panel launched successfully beside DaVinci Resolve!")
        return True
    except Exception as e:
        print(f"[Motion Resolve] Error launching companion process: {e}")
        return False


def main():
    if is_running_inside_resolve():
        launch_detached_companion()
    else:
        from ui_qt.main_window import launch
        app, win = launch()
        sys.exit(app.exec())


if __name__ == "__main__":
    main()
