"""
CaptionForge for Resolve - Cross-Platform Paths & Environment Resolver
Handles OS-specific paths for macOS and Windows DaVinci Resolve Studio,
and discovers system Python installations with PyQt6.
"""

import os
import sys
import shutil
import subprocess
import platform
import glob

IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"


def get_home_dir():
    return os.path.expanduser("~")


def get_resolve_support_dir():
    """Return the base DaVinci Resolve application support directory."""
    if IS_MAC:
        return os.path.join(get_home_dir(), "Library", "Application Support", "Blackmagic Design", "DaVinci Resolve")
    elif IS_WINDOWS:
        appdata = os.environ.get("APPDATA", os.path.join(get_home_dir(), "AppData", "Roaming"))
        return os.path.join(appdata, "Blackmagic Design", "DaVinci Resolve", "Support")
    else:
        return os.path.join(get_home_dir(), ".local", "share", "DaVinciResolve")


def get_resolve_developer_dir():
    """Return the DaVinci Resolve Developer / Scripting API directory."""
    if IS_MAC:
        return "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
    elif IS_WINDOWS:
        progdata = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        return os.path.join(progdata, "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting")
    else:
        return "/opt/resolve/Developer/Scripting"


def get_scripts_comp_dir():
    """Return the directory where Fusion comp scripts reside."""
    return os.path.join(get_resolve_support_dir(), "Fusion", "Scripts", "Comp")


def get_scripts_edit_dir():
    """Return the directory where Edit page scripts reside."""
    return os.path.join(get_resolve_support_dir(), "Fusion", "Scripts", "Edit")


def get_app_dir():
    """Return the root directory of the Motion Resolve app."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return base


def get_user_presets_dir():
    """Return the user presets storage directory, ensuring write permission."""
    primary_dir = os.path.join(get_app_dir(), "data", "styles")
    try:
        if os.path.exists(primary_dir):
            if os.access(primary_dir, os.W_OK):
                return primary_dir
        else:
            os.makedirs(primary_dir, exist_ok=True)
            if os.access(primary_dir, os.W_OK):
                return primary_dir
    except Exception:
        pass

    fallback_dir = os.path.join(get_home_dir(), ".motion_resolve", "styles")
    try:
        os.makedirs(fallback_dir, exist_ok=True)
    except Exception:
        pass
    return fallback_dir


def find_system_python():
    """Locate the system Python executable capable of running PyQt6."""
    candidates = [
        "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3",
        "/opt/homebrew/bin/python3",
        "/usr/local/bin/python3",
        shutil.which("python3"),
        sys.executable
    ]

    if IS_MAC:
        for v in ["3.14", "3.13", "3.12", "3.11", "3.10"]:
            p = f"/Library/Frameworks/Python.framework/Versions/{v}/bin/python3"
            if os.path.exists(p) and p not in candidates:
                candidates.append(p)
    elif IS_WINDOWS:
        localappdata = os.environ.get("LOCALAPPDATA", "")
        for v in ["314", "313", "312", "311", "310"]:
            p = os.path.join(localappdata, "Programs", "Python", f"Python{v}", "python.exe")
            if os.path.exists(p):
                candidates.append(p)
            candidates.append(f"C:\\Python{v}\\python.exe")
        candidates.extend([shutil.which("python"), shutil.which("py")])

    # Validate that candidate executable exists and can import PyQt6
    for c in candidates:
        if c and os.path.exists(c) and os.path.isfile(c) and "ResolvePython" not in c:
            try:
                res = subprocess.run([c, "-c", "import PyQt6"], capture_output=True, timeout=2)
                if res.returncode == 0:
                    return c
            except Exception:
                pass

    # Fallback to sys.executable
    return sys.executable


def get_system_site_packages():
    """Find all potential system python site-packages containing PyQt6."""
    paths = []
    if IS_MAC:
        paths.extend(glob.glob("/Library/Frameworks/Python.framework/Versions/*/lib/python*/site-packages"))
        paths.extend(glob.glob("/opt/homebrew/lib/python*/site-packages"))
        paths.extend(glob.glob("/usr/local/lib/python*/site-packages"))
        paths.append(os.path.expanduser("~/.local/lib/python3.14/site-packages"))
        paths.append(os.path.expanduser("~/.local/lib/python3.13/site-packages"))
        paths.append(os.path.expanduser("~/.local/lib/python3.12/site-packages"))
    elif IS_WINDOWS:
        appdata = os.environ.get("APPDATA", "")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        paths.extend(glob.glob(os.path.join(appdata, "Python", "Python*", "site-packages")))
        paths.extend(glob.glob(os.path.join(localappdata, "Programs", "Python", "Python*", "Lib", "site-packages")))
        paths.extend(glob.glob(r"C:\Python*\Lib\site-packages"))

    return [p for p in paths if os.path.exists(p)]


def ensure_sys_path():
    """Ensure Resolve scripting modules, system site-packages, and app modules are present in sys.path."""
    # 0. Set default environment variables for Resolve Scripting on Windows
    if IS_WINDOWS:
        progdata = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        if "RESOLVE_SCRIPT_API" not in os.environ:
            os.environ["RESOLVE_SCRIPT_API"] = os.path.join(progdata, "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting")
        if "RESOLVE_SCRIPT_LIB" not in os.environ:
            dll_path = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
            if os.path.exists(dll_path):
                os.environ["RESOLVE_SCRIPT_LIB"] = dll_path
        resolve_dir = r"C:\Program Files\Blackmagic Design\DaVinci Resolve"
        if os.path.exists(resolve_dir) and hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(resolve_dir)
            except Exception:
                pass

    # 1. Add system site-packages so ResolvePython can import PyQt6 if running in-process
    for sp in get_system_site_packages():
        if sp not in sys.path:
            sys.path.append(sp)

    # 2. Add DaVinciResolveScript path
    dev_dir = get_resolve_developer_dir()
    modules_dir = os.path.join(dev_dir, "Modules")
    if os.path.exists(modules_dir) and modules_dir not in sys.path:
        sys.path.append(modules_dir)

    # 3. Add app directory
    app_dir = get_app_dir()
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
