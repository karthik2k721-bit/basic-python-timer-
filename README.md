Minimal Python GUI Timer

This repository contains a Tkinter-based countdown timer app implemented in `timer_gui.py`.
It uses only the Python standard library.

## Requirements

- Python 3.8+
- No third-party packages
- `tkinter` available in your Python installation

## Run

From the project folder:

```bash
python timer_gui.py
```

## Features

- Minutes/seconds selection (00-59) using in-app dropdown pickers
- Responsive timer display that scales with window size
- Start, Pause/Resume, and Stop controls
- Light mode / Dark mode toggle
- In-app "Time's up!" modal when countdown reaches zero
- Audible alert for about 2 seconds on completion:
	- Windows: uses `winsound.Beep` when available
	- Other systems or fallback path: terminal bell (`\a`)

## Behavior Notes

- Timer inputs are disabled while counting down and re-enabled after stop/reset.
- If one time field is left blank (`____`) and the other is set, the blank field is normalized to `00`.
- A countdown only starts when total time is greater than `00:00`.
- On Windows, the app attempts to update title-bar appearance to match the selected theme.

## Build Artifacts

This repo includes PyInstaller spec files and generated build outputs:

- `timer_gui.spec`
- `Timer.spec`
- `Timerv1.spec`
- `build/`
- `dist/`
