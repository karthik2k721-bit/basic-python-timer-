#!/usr/bin/env python3
"""Simple Tkinter GUI countdown timer with pause/resume and optional beep.

Usage:
  python timer_gui.py

Written to be minimal and use only the Python standard library.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import time
import threading
import platform
import sys

try:
    import winsound
except Exception:
    winsound = None


def format_seconds(sec: int) -> str:
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"


def beep(duration: float):
    """Play a beep pattern for approximately `duration` seconds."""
    end = time.time() + duration
    if winsound and platform.system() == "Windows":
        try:
            while time.time() < end:
                winsound.Beep(1000, 400)
                time.sleep(0.1)
        except Exception:
            while time.time() < end:
                sys.stdout.write("\a")
                sys.stdout.flush()
                time.sleep(0.5)
    else:
        while time.time() < end:
            sys.stdout.write("\a")
            sys.stdout.flush()
            time.sleep(0.5)


class TimerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Timer")
        self.root.geometry("550x500")
        self.root.resizable(False, False)

        self.running = False
        self.paused = False
        self.total_seconds = 0
        self.remaining_seconds = 0
        self.end_time = None
        self.pause_start = None
        self.sound_enabled = tk.BooleanVar(value=True)
        self.dark_mode = tk.BooleanVar(value=False)
        self.timer_thread = None
        
        # Theme colors
        self.light_theme = {
            "bg": "#f0f0f0",
            "fg": "#2c3e50",
            "button_bg": "#e8e8e8",
            "button_fg": "#000000"
        }
        self.dark_theme = {
            "bg": "#1e1e1e",
            "fg": "#ffffff",
            "button_bg": "#333333",
            "button_fg": "#ffffff"
        }
        self.current_theme = self.light_theme
        
        # Setup ttk style
        self.style = ttk.Style()
        self._configure_light_theme()
        
        # Frames references for theme updates
        self.frames_to_update = []
        self.labels_to_update = []

        # Display
        display_frame = ttk.Frame(root)
        display_frame.pack(pady=20)
        self.frames_to_update.append(display_frame)

        self.display_label = tk.Label(
            display_frame,
            text="00:00",
            font=("Arial", 72, "bold"),
            fg="#2c3e50",
            bg="#f0f0f0"
        )
        self.display_label.pack()

        # Input Frame
        self.input_frame = ttk.LabelFrame(root, text="Set Time", padding=10, style="TLabelframe")
        self.input_frame.pack(padx=20, pady=10, fill="x")
        self.frames_to_update.append(self.input_frame)

        ttk.Label(self.input_frame, text="Minutes:").grid(row=0, column=0, padx=5, pady=5)
        self.minutes_var = tk.StringVar(value="1")
        self.minutes_spinbox = ttk.Spinbox(
            self.input_frame,
            from_=0,
            to=59,
            textvariable=self.minutes_var,
            width=5,
            state="normal"
        )
        self.minutes_spinbox.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self.input_frame, text="Seconds:").grid(row=0, column=2, padx=5, pady=5)
        self.seconds_var = tk.StringVar(value="0")
        self.seconds_spinbox = ttk.Spinbox(
            self.input_frame,
            from_=0,
            to=59,
            textvariable=self.seconds_var,
            width=5,
            state="normal"
        )
        self.seconds_spinbox.grid(row=0, column=3, padx=5, pady=5)

        # Settings Frame
        self.settings_frame = ttk.Frame(root, style="TFrame")
        self.settings_frame.pack(padx=20, pady=5, fill="x")
        self.frames_to_update.append(self.settings_frame)

        ttk.Checkbutton(
            self.settings_frame,
            text="Sound on complete",
            variable=self.sound_enabled
        ).pack(anchor="w")
        
        ttk.Checkbutton(
            self.settings_frame,
            text="Dark Mode",
            variable=self.dark_mode,
            command=self.apply_theme
        ).pack(anchor="w")

        # Buttons Frame
        button_frame = ttk.Frame(root)
        button_frame.pack(pady=20)

        self.start_button = ttk.Button(
            button_frame,
            text="Start",
            command=self.start_timer,
            width=10
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.pause_button = ttk.Button(
            button_frame,
            text="Pause",
            command=self.pause_timer,
            width=10,
            state="disabled"
        )
        self.pause_button.grid(row=0, column=1, padx=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="Stop",
            command=self.stop_timer,
            width=10,
            state="disabled"
        )
        self.stop_button.grid(row=0, column=2, padx=5)

    def start_timer(self):
        if self.running:
            return

        try:
            minutes = int(self.minutes_var.get())
            seconds = int(self.seconds_var.get())
        except ValueError:
            return

        self.total_seconds = minutes * 60 + seconds
        if self.total_seconds <= 0:
            return

        self.running = True
        self.paused = False
        self.remaining_seconds = self.total_seconds
        self.end_time = time.time() + self.total_seconds

        self.start_button.config(state="disabled")
        self.pause_button.config(state="normal")
        self.stop_button.config(state="normal")
        self.minutes_spinbox.config(state="disabled")
        self.seconds_spinbox.config(state="disabled")

        self.timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self.timer_thread.start()

    def _run_timer(self):
        while self.running:
            if not self.paused:
                remaining = int(max(0, self.end_time - time.time()))
                self.remaining_seconds = remaining
                self.display_label.config(text=format_seconds(remaining))

                if remaining <= 0:
                    self.running = False
                    time_up_text = "⏱ Time's up!"
                    text_color = self.current_theme["fg"]
                    self.display_label.config(
                        text=time_up_text,
                        fg=text_color,
                        font=("Arial", 28, "bold")
                    )
                    if self.sound_enabled.get():
                        beep(2.0)
                    self.root.after(0, self._reset_ui)
                    break
            time.sleep(0.1)

    def pause_timer(self):
        if not self.running:
            return

        if self.paused:
            # Resume
            self.paused = False
            self.end_time = time.time() + self.remaining_seconds
            self.pause_button.config(text="Pause")
        else:
            # Pause
            self.paused = True
            self.pause_button.config(text="Resume")

    def stop_timer(self):
        self.running = False
        self.paused = False
        self.remaining_seconds = 0
        self.display_label.config(
            text="00:00",
            fg=self.current_theme["fg"],
            font=("Arial", 72, "bold")
        )
        self._reset_ui()

    def apply_theme(self):
        if self.dark_mode.get():
            theme = self.dark_theme
            self._configure_dark_theme()
        else:
            theme = self.light_theme
            self._configure_light_theme()
        
        self.current_theme = theme
        
        # Apply theme to window and display label
        self.root.config(bg=theme["bg"])
        self.display_label.config(
            fg=theme["fg"],
            bg=theme["bg"]
        )
        
        # Update all frames
        for frame in self.frames_to_update:
            frame.config(style="TFrame")

    def _configure_light_theme(self):
        self.style.theme_use('clam')
        self.style.configure(
            "TFrame",
            background="#f0f0f0",
            foreground="#2c3e50"
        )
        self.style.configure(
            "TLabelframe",
            background="#f0f0f0",
            foreground="#2c3e50"
        )
        self.style.configure(
            "TLabelframe.Label",
            background="#f0f0f0",
            foreground="#2c3e50"
        )
        self.style.configure(
            "TLabel",
            background="#f0f0f0",
            foreground="#2c3e50"
        )
        self.style.configure(
            "TCheckbutton",
            background="#f0f0f0",
            foreground="#2c3e50"
        )
        self.style.configure(
            "TSpinbox",
            fieldbackground="white",
            background="#f0f0f0",
            foreground="#2c3e50"
        )

    def _configure_dark_theme(self):
        self.style.theme_use('clam')
        self.style.configure(
            "TFrame",
            background="#1e1e1e",
            foreground="#ffffff"
        )
        self.style.configure(
            "TLabelframe",
            background="#1e1e1e",
            foreground="#ffffff"
        )
        self.style.configure(
            "TLabelframe.Label",
            background="#1e1e1e",
            foreground="#ffffff"
        )
        self.style.configure(
            "TLabel",
            background="#1e1e1e",
            foreground="#ffffff"
        )
        self.style.configure(
            "TCheckbutton",
            background="#1e1e1e",
            foreground="#ffffff"
        )
        self.style.configure(
            "TSpinbox",
            fieldbackground="#333333",
            background="#1e1e1e",
            foreground="#ffffff"
        )

    def _reset_ui(self):
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="Pause")
        self.stop_button.config(state="disabled")
        self.minutes_spinbox.config(state="normal")
        self.seconds_spinbox.config(state="normal")
        self.display_label.config(font=("Arial", 72, "bold"))


if __name__ == "__main__":
    root = tk.Tk()
    app = TimerGUI(root)
    root.mainloop()
