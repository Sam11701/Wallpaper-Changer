"""Wallpaper Engine CLI integration."""
import os
import subprocess
import psutil

DEFAULT_WE_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\wallpaper_engine"
EXECUTABLES = ["wallpaper64.exe", "wallpaper32.exe"]


def is_running() -> bool:
    """Check if Wallpaper Engine process is currently running."""
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] in ("wallpaper64.exe", "wallpaper32.exe"):
            return True
    return False


def find_executable(custom_path: str = None) -> str | None:
    """Find wallpaper_engine executable. Checks custom path first, then default Steam location."""
    search_paths = []
    if custom_path:
        search_paths.append(custom_path)
    search_paths.append(DEFAULT_WE_PATH)

    for folder in search_paths:
        for exe in EXECUTABLES:
            full_path = os.path.join(folder, exe)
            if os.path.isfile(full_path):
                return full_path
    return None


def run_command(exe_path: str, *args) -> bool:
    """Run a Wallpaper Engine CLI command."""
    try:
        subprocess.Popen([exe_path] + list(args))
        return True
    except Exception as e:
        print(f"Wallpaper Engine command failed: {e}")
        return False


def pause(exe_path: str) -> bool:
    return run_command(exe_path, "-control", "pause")


def play(exe_path: str) -> bool:
    return run_command(exe_path, "-control", "play")


def mute(exe_path: str) -> bool:
    return run_command(exe_path, "-control", "mute")


def unmute(exe_path: str) -> bool:
    return run_command(exe_path, "-control", "unmute")


def stop(exe_path: str) -> bool:
    return run_command(exe_path, "-control", "stop")


def next_wallpaper(exe_path: str) -> bool:
    return run_command(exe_path, "-control", "nextWallpaper")


def hide_icons(exe_path: str) -> bool:
    return run_command(exe_path, "-control", "hideIcons")


def show_icons(exe_path: str) -> bool:
    return run_command(exe_path, "-control", "showIcons")
