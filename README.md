# Wallpaper-Changer

A Python-based wallpaper changer with global hotkey support and auto-change intervals.

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

**Option 1: Run the executable (recommended)**
```bash
./WallpaperChanger.exe
```

**Option 2: Run from source**
```bash
python -m src.gui.main_window
```

## Features

- Change wallpapers from selected directories
- Global hotkey support for quick actions
- Auto-change wallpapers at specified intervals
- System tray integration
- Persistent hotkey and path configurations

## Project Structure

```
.
├── WallpaperChanger.exe    # Standalone executable
├── src/
│   ├── core/               # Core wallpaper logic
│   ├── gui/                # User interface components
│   └── config/             # Configuration constants
├── tests/                  # Test suite
└── docs/                   # Documentation
```