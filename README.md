Minimal Python Timer

This repository contains a minimal countdown timer with both **console** and **GUI** versions, using only the Python standard library.

Files
- [timer.py](timer.py): Console countdown timer with pause/resume and simple beep on completion.
- [timer_gui.py](timer_gui.py): Tkinter GUI countdown timer with graphical controls.
- [README.md](README.md): This file with usage and examples.

Requirements
- Python 3.8+ (works with newer Python versions as well)
- No external packages required (standard library only)
  - Console: Uses `argparse`, `threading`, `signal`, `time`
  - GUI: Uses `tkinter` (built-in to Python)

Quick usage

Start a 90-second timer:

```bash
python timer.py --seconds 90
```

Start a 1 minute 30 second timer:

```bash
python timer.py --time 01:30
```

Controls while running (press a key):
- `p` — pause / resume
- `s` — stop and exit
- `q` — quit immediately

GUI Usage

Launch the graphical timer interface:

```bash
python timer_gui.py
```

**Features:**
- Set time using spinner controls (minutes/seconds)
- Large, easy-to-read display (72pt font)
- Start, Pause/Resume, Stop buttons
- Toggle sound alert on completion
- Displays "Time's up!" when finished

Notes
- **Cross-platform:** Both console and GUI versions work on Windows, macOS, and Linux
- Console version uses `winsound.Beep()` on Windows if available; otherwise prints the terminal bell `\a`
- Console version uses `msvcrt` for simple keypress handling on Windows and a POSIX fallback for other systems
- GUI version uses `tkinter` which is included with Python on all major platforms
- Both versions handle Ctrl+C to exit cleanly
