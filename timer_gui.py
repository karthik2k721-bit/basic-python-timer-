#!/usr/bin/env python3
"""Simple Tkinter GUI countdown timer with pause/resume and optional beep.

Usage:
  python timer_gui.py

Written to be minimal and use only the Python standard library.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import time
import threading
import platform
import sys
import ctypes
import ctypes.wintypes as wintypes

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
        self.root.geometry("700x560")
        self.root.minsize(420, 380)
        self.root.resizable(True, True)

        self.running = False
        self.paused = False
        self.total_seconds = 0
        self.remaining_seconds = 0
        self.end_time = None
        self.pause_start = None
        self.dark_mode = tk.BooleanVar(value=False)
        self.timer_thread = None
        self.time_inputs_enabled = True
        self.dropdown_popup = None
        self.timeup_popup = None
        self._display_font_family = "Arial"
        self._base_display_font = 72
        self._base_input_font = 16

        # Theme colors
        self.light_theme = {
            "bg": "#FAF9F6",
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

        self.main_container = ttk.Frame(root, style="TFrame")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=12)
        self.frames_to_update.append(self.main_container)

        # Top bar with theme toggle button
        self.top_bar = ttk.Frame(self.main_container, style="TFrame")
        self.top_bar.pack(fill="x", pady=(0, 8))
        self.frames_to_update.append(self.top_bar)

        self.theme_toggle_frame = ttk.Frame(self.top_bar, style="TFrame")
        self.theme_toggle_frame.pack(anchor="e")
        self.frames_to_update.append(self.theme_toggle_frame)

        self.light_mode_label = tk.Label(
            self.theme_toggle_frame,
            text="Light Mode",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        )
        self.light_mode_label.pack(side="left", padx=(0, 6))

        self.theme_switch_var = tk.DoubleVar(value=0.0)
        self.theme_switch = ttk.Scale(
            self.theme_toggle_frame,
            from_=0.0,
            to=1.0,
            variable=self.theme_switch_var,
            orient="horizontal",
            length=44,
            cursor="hand2",
            style="ThemeSwitch.Horizontal.TScale"
        )
        self.theme_switch.pack(side="left")
        self.theme_switch.bind("<ButtonRelease-1>", self._on_theme_switch_release)

        self.dark_mode_label = tk.Label(
            self.theme_toggle_frame,
            text="Dark Mode",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        )
        self.dark_mode_label.pack(side="left", padx=(6, 0))

        self.theme_toggle_frame.bind("<Button-1>", self._toggle_theme_from_click)
        self.theme_switch.bind("<Button-1>", self._toggle_theme_from_click)
        self.light_mode_label.bind("<Button-1>", self._toggle_theme_from_click)
        self.dark_mode_label.bind("<Button-1>", self._toggle_theme_from_click)

        # Display
        display_frame = ttk.Frame(self.main_container, style="TFrame")
        display_frame.pack(fill="x", expand=True, pady=(8, 14))
        self.frames_to_update.append(display_frame)

        self.display_label = tk.Label(
            display_frame,
            text="00:00",
            font=("Arial", 72, "bold"),
            fg="#2c3e50",
            bg="#FAF9F6"
        )
        self.display_label.pack()

        # Input Frame
        self.input_frame = ttk.Frame(self.main_container, padding=10, style="TFrame")
        self.input_frame.pack(fill="x", pady=(0, 10))
        self.frames_to_update.append(self.input_frame)
        self.input_frame.columnconfigure(0, weight=1)

        time_values = [f"{i:02d}" for i in range(60)]

        self.time_row = ttk.Frame(self.input_frame, style="TFrame")
        self.time_row.grid(row=0, column=0, pady=8)
        self.frames_to_update.append(self.time_row)

        self.minutes_label = ttk.Label(
            self.time_row,
            text="Minutes",
            font=("Arial", 16, "bold")
        )
        self.minutes_label.grid(row=0, column=0, padx=(0, 10), pady=10)

        self.minutes_var = tk.StringVar(value="____")
        self.minutes_selector = tk.Button(
            self.time_row,
            textvariable=self.minutes_var,
            font=("Arial", 16, "bold"),
            padx=6,
            pady=2,
            cursor="hand2",
            bd=0,
            highlightthickness=0,
            relief="flat",
            command=lambda: self._open_time_dropdown(self.minutes_selector, self.minutes_var)
        )
        self.minutes_selector.grid(row=0, column=1, padx=(0, 28), pady=10)

        self.seconds_label = ttk.Label(
            self.time_row,
            text="Seconds",
            font=("Arial", 16, "bold")
        )
        self.seconds_label.grid(row=0, column=2, padx=(0, 10), pady=10)

        self.seconds_var = tk.StringVar(value="____")
        self.seconds_selector = tk.Button(
            self.time_row,
            textvariable=self.seconds_var,
            font=("Arial", 16, "bold"),
            padx=6,
            pady=2,
            cursor="hand2",
            bd=0,
            highlightthickness=0,
            relief="flat",
            command=lambda: self._open_time_dropdown(self.seconds_selector, self.seconds_var)
        )
        self.seconds_selector.grid(row=0, column=3, padx=(0, 0), pady=10)

        self.time_values = time_values

        # Settings Frame
        self.settings_frame = ttk.Frame(self.main_container, style="TFrame")
        self.settings_frame.pack(fill="x", pady=(0, 8))
        self.frames_to_update.append(self.settings_frame)

        # Buttons Frame
        button_frame = ttk.Frame(self.main_container, style="TFrame")
        button_frame.pack(fill="x", pady=(6, 8))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(3, weight=1)

        self.start_button = ttk.Button(
            button_frame,
            text="Start",
            command=self.start_timer,
            width=10,
            style="Action.TButton"
        )
        self.start_button.grid(row=0, column=1, columnspan=2, padx=5)

        self.pause_button = ttk.Button(
            button_frame,
            text="Pause",
            command=self.pause_timer,
            width=10,
            style="Action.TButton",
            state="disabled"
        )
        self.pause_button.grid(row=0, column=1, padx=5)

        self.stop_button = ttk.Button(
            button_frame,
            text="Stop",
            command=self.stop_timer,
            width=10,
            style="Action.TButton",
            state="disabled"
        )
        self.stop_button.grid(row=0, column=2, padx=5)

        # Show only Start before a timer begins.
        self.pause_button.grid_remove()
        self.stop_button.grid_remove()

        self.apply_theme()
        self.root.after(100, self._update_window_chrome)
        self.root.bind("<Configure>", self._on_resize)
        self._on_resize()

    def toggle_theme(self):
        self.set_theme(not self.dark_mode.get())

    def _toggle_theme_from_click(self, _event=None):
        self.toggle_theme()
        return "break"

    def set_theme(self, dark: bool):
        self.dark_mode.set(dark)
        self.theme_switch_var.set(1.0 if dark else 0.0)
        self.apply_theme()

    def _on_theme_switch_release(self, _event=None):
        self.set_theme(float(self.theme_switch_var.get()) >= 0.5)

    def _update_theme_toggle_visuals(self):
        is_dark = self.dark_mode.get()
        theme_bg = self.current_theme["bg"]

        track_color = "#ff4da6" if is_dark else "#ff9dcb"
        knob_color = "#f7f7f7" if is_dark else "#2c3e50"
        self.style.configure(
            "ThemeSwitch.Horizontal.TScale",
            background=theme_bg,
            troughcolor=track_color,
            sliderlength=16,
            sliderthickness=13,
            relief="flat",
            borderwidth=0,
            bordercolor=knob_color,
            lightcolor=knob_color,
            darkcolor=knob_color
        )
        self.style.map(
            "ThemeSwitch.Horizontal.TScale",
            background=[("active", theme_bg), ("!active", theme_bg)]
        )
        self.theme_switch_var.set(1.0 if is_dark else 0.0)

        active_color = self.current_theme["fg"]
        muted_color = "#8e8e8e"

        self.light_mode_label.config(
            bg=theme_bg,
            fg=muted_color if is_dark else active_color
        )
        self.dark_mode_label.config(
            bg=theme_bg,
            fg=active_color if is_dark else muted_color
        )

    def _hex_to_colorref(self, color_hex: str) -> int:
        color_hex = color_hex.lstrip("#")
        r = int(color_hex[0:2], 16)
        g = int(color_hex[2:4], 16)
        b = int(color_hex[4:6], 16)
        return (b << 16) | (g << 8) | r

    def _update_window_chrome(self):
        if platform.system() != "Windows":
            return

        try:
            self.root.update_idletasks()
            hwnd = wintypes.HWND(self.root.winfo_id())
            user32 = ctypes.windll.user32
            dwmapi = ctypes.windll.dwmapi

            root_hwnd = user32.GetAncestor(hwnd, 2)
            if root_hwnd:
                hwnd = wintypes.HWND(root_hwnd)

            DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            DWMWA_CAPTION_COLOR = 35
            DWMWA_TEXT_COLOR = 36

            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004
            SWP_NOOWNERZORDER = 0x0200
            SWP_FRAMECHANGED = 0x0020

            is_dark = 1 if self.dark_mode.get() else 0
            dark_mode_val = ctypes.c_int(is_dark)

            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE_OLD,
                ctypes.byref(dark_mode_val),
                ctypes.sizeof(dark_mode_val)
            )
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(dark_mode_val),
                ctypes.sizeof(dark_mode_val)
            )

            caption_hex = "#1e1e1e" if self.dark_mode.get() else "#FAF9F6"
            text_hex = "#ffffff" if self.dark_mode.get() else "#1a1a1a"

            caption_color = ctypes.c_int(self._hex_to_colorref(caption_hex))
            text_color = ctypes.c_int(self._hex_to_colorref(text_hex))

            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_CAPTION_COLOR,
                ctypes.byref(caption_color),
                ctypes.sizeof(caption_color)
            )
            dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_TEXT_COLOR,
                ctypes.byref(text_color),
                ctypes.sizeof(text_color)
            )

            user32.SetWindowPos(
                hwnd,
                0,
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOOWNERZORDER | SWP_FRAMECHANGED
            )
        except Exception:
            pass

    def _on_resize(self, _event=None):
        width = max(self.root.winfo_width(), 1)
        height = max(self.root.winfo_height(), 1)
        scale_basis = min(width, height)

        display_size = max(36, min(110, int(scale_basis * 0.16)))
        input_size = max(12, min(22, int(scale_basis * 0.036)))

        current_text = self.display_label.cget("text")
        if "Time's up" in current_text:
            self.display_label.config(font=(self._display_font_family, max(20, int(display_size * 0.42)), "bold"))
        else:
            self.display_label.config(font=(self._display_font_family, display_size, "bold"))

        self.minutes_label.config(font=(self._display_font_family, input_size, "bold"))
        self.seconds_label.config(font=(self._display_font_family, input_size, "bold"))
        self.minutes_selector.config(font=(self._display_font_family, input_size, "bold"))
        self.seconds_selector.config(font=(self._display_font_family, input_size, "bold"))

    def _normalize_time_placeholders(self):
        minutes = self.minutes_var.get()
        seconds = self.seconds_var.get()

        if minutes == "____" and seconds == "____":
            return False
        if minutes == "____":
            self.minutes_var.set("00")
        if seconds == "____":
            self.seconds_var.set("00")
        return True

    def _open_time_dropdown(self, target_widget: tk.Widget, target_var: tk.StringVar):
        if not self.time_inputs_enabled:
            return

        self._close_time_dropdown()
        self.root.update_idletasks()

        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()

        visible_rows = min(10, len(self.time_values))
        value_font = tkfont.Font(family="Arial", size=12)
        text_w = value_font.measure("00")
        popup_w = max(52, text_w + 26)
        popup_h = 6 + (visible_rows * 22)

        x = target_widget.winfo_rootx()
        y = target_widget.winfo_rooty() + target_widget.winfo_height() + 4

        min_x = root_x + 8
        max_x = root_x + root_w - popup_w - 8
        x = max(min_x, min(x, max_x))

        if y + popup_h > root_y + root_h - 8:
            y = target_widget.winfo_rooty() - popup_h - 4
        y = max(root_y + 8, y)

        self.dropdown_popup = tk.Toplevel(self.root)
        self.dropdown_popup.overrideredirect(True)
        self.dropdown_popup.transient(self.root)
        self.dropdown_popup.geometry(f"{popup_w}x{popup_h}+{x}+{y}")

        border_color = "#1e90ff"
        bg_color = "#ffffff" if not self.dark_mode.get() else "#2b2b2b"
        fg_color = "#2c3e50" if not self.dark_mode.get() else "#ffffff"

        outer = tk.Frame(self.dropdown_popup, bg=border_color, bd=0)
        outer.pack(fill="both", expand=True)

        inner = tk.Frame(outer, bg=bg_color, bd=0)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        scrollbar = tk.Scrollbar(inner, orient="vertical")
        listbox = tk.Listbox(
            inner,
            font=("Arial", 12),
            yscrollcommand=scrollbar.set,
            bg=bg_color,
            fg=fg_color,
            selectbackground="#ff69b4",
            selectforeground="#ffffff",
            highlightthickness=0,
            bd=0,
            activestyle="none",
            height=visible_rows
        )
        scrollbar.config(command=listbox.yview)
        scrollbar.config(width=10)

        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for value in self.time_values:
            listbox.insert("end", value)

        current = target_var.get()
        if current in self.time_values:
            idx = self.time_values.index(current)
            listbox.selection_set(idx)
            listbox.see(idx)

        def choose_value(_event=None):
            sel = listbox.curselection()
            if sel:
                target_var.set(listbox.get(sel[0]))
            self._close_time_dropdown()

        listbox.bind("<ButtonRelease-1>", choose_value)
        listbox.bind("<Return>", choose_value)
        listbox.bind("<Escape>", lambda _event: self._close_time_dropdown())
        self.dropdown_popup.lift()
        listbox.focus_set()

    def _close_time_dropdown(self):
        if self.dropdown_popup is not None:
            self.dropdown_popup.destroy()
            self.dropdown_popup = None

    def _show_timeup_popup(self):
        if self.timeup_popup is not None and self.timeup_popup.winfo_exists():
            self.timeup_popup.lift()
            return

        popup_bg = "#2b2b2b" if self.dark_mode.get() else "#ffffff"
        popup_fg = "#ffffff" if self.dark_mode.get() else "#2c3e50"

        # In-app modal overlay so popup always appears inside the timer window.
        self.timeup_popup = tk.Frame(self.main_container, bg=self.current_theme["bg"], bd=0, highlightthickness=0)
        self.timeup_popup.place(relx=0.5, rely=0.5, anchor="center")

        body = tk.Frame(
            self.timeup_popup,
            bg=popup_bg,
            padx=18,
            pady=18,
            bd=0,
            highlightthickness=1,
            highlightbackground="#ff4da6"
        )
        body.pack(fill="both", expand=True)

        message = tk.Label(
            body,
            text="Time's up!",
            font=("Arial", 16, "bold"),
            fg=popup_fg,
            bg=popup_bg
        )
        message.pack(pady=(6, 14))

        close_btn = tk.Button(
            body,
            text="Close",
            command=self._close_timeup_popup_and_reset,
            bg="#ff4da6",
            activebackground="#ff2f98",
            fg="#ffffff",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            font=("Arial", 10, "bold")
        )
        close_btn.pack()

        self.timeup_popup.lift()
        close_btn.focus_set()

    def _handle_timer_complete(self):
        self.running = False
        self.paused = False
        self._show_timeup_popup()
        threading.Thread(target=beep, args=(2.0,), daemon=True).start()

    def _close_timeup_popup_and_reset(self):
        if self.timeup_popup is not None and self.timeup_popup.winfo_exists():
            self.timeup_popup.destroy()
        self.timeup_popup = None

        self.display_label.config(
            text="00:00",
            fg=self.current_theme["fg"],
            font=(self._display_font_family, self._base_display_font, "bold")
        )
        self._on_resize()
        self._reset_ui()

    def start_timer(self):
        if self.running:
            return

        if not self._normalize_time_placeholders():
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
        self.display_label.config(
            text=format_seconds(self.remaining_seconds),
            fg=self.current_theme["fg"],
            font=(self._display_font_family, self._base_display_font, "bold")
        )
        self._on_resize()

        self.start_button.config(state="disabled")
        self.pause_button.config(state="normal")
        self.stop_button.config(state="normal")
        self.start_button.grid_remove()
        self.pause_button.grid()
        self.stop_button.grid()
        self.time_inputs_enabled = False
        self._close_time_dropdown()
        self.minutes_selector.config(fg="#8e8e8e", cursor="arrow")
        self.seconds_selector.config(fg="#8e8e8e", cursor="arrow")

        self.timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self.timer_thread.start()

    def _run_timer(self):
        while self.running:
            if not self.paused:
                remaining = int(max(0, self.end_time - time.time()))
                self.remaining_seconds = remaining
                self.display_label.config(text=format_seconds(remaining))

                if remaining <= 0:
                    self.root.after(0, self._handle_timer_complete)
                    break
            time.sleep(0.1)

    def pause_timer(self):
        if not self.running:
            return

        if self.paused:
            self.paused = False
            self.end_time = time.time() + self.remaining_seconds
            self.pause_button.config(text="Pause")
        else:
            self.paused = True
            self.pause_button.config(text="Resume")

    def stop_timer(self):
        self.running = False
        self.paused = False
        self.remaining_seconds = 0
        if self.timeup_popup is not None and self.timeup_popup.winfo_exists():
            self.timeup_popup.destroy()
        self.timeup_popup = None
        self.display_label.config(
            text="00:00",
            fg=self.current_theme["fg"],
            font=(self._display_font_family, self._base_display_font, "bold")
        )
        self._on_resize()
        self._reset_ui()

    def apply_theme(self):
        if self.dark_mode.get():
            theme = self.dark_theme
            self._configure_dark_theme()
        else:
            theme = self.light_theme
            self._configure_light_theme()

        self.current_theme = theme

        self.root.config(bg=theme["bg"])
        self.display_label.config(
            fg=theme["fg"],
            bg=theme["bg"]
        )
        self._update_theme_toggle_visuals()
        self._update_window_chrome()
        self.minutes_selector.config(bg=theme["bg"])
        self.seconds_selector.config(bg=theme["bg"])
        if self.time_inputs_enabled:
            self.minutes_selector.config(fg=theme["fg"], cursor="hand2")
            self.seconds_selector.config(fg=theme["fg"], cursor="hand2")
        else:
            self.minutes_selector.config(fg="#8e8e8e", cursor="arrow")
            self.seconds_selector.config(fg="#8e8e8e", cursor="arrow")

        for frame in self.frames_to_update:
            frame.config(style="TFrame")

    def _configure_light_theme(self):
        self.style.theme_use('clam')
        self.style.configure(
            "TFrame",
            background="#FAF9F6",
            foreground="#2c3e50"
        )
        self.style.configure(
            "TLabelframe",
            background="#FAF9F6",
            foreground="#2c3e50"
        )
        self.style.configure(
            "TLabelframe.Label",
            background="#FAF9F6",
            foreground="#2c3e50"
        )
        self.style.configure(
            "TLabel",
            background="#FAF9F6",
            foreground="#2c3e50"
        )
        self.style.configure(
            "TCheckbutton",
            background="#FAF9F6",
            foreground="#2c3e50"
        )
        self.style.configure(
            "Action.TButton",
            background="#ff4da6",
            foreground="#ffffff",
            borderwidth=0,
            relief="flat",
            padding=(16, 8),
            font=("Arial", 10, "bold")
        )
        self.style.map(
            "Action.TButton",
            background=[("active", "#ff2f98"), ("disabled", "#d68aac")],
            foreground=[("disabled", "#f7f7f7")]
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
            "Action.TButton",
            background="#ff4da6",
            foreground="#ffffff",
            borderwidth=0,
            relief="flat",
            padding=(16, 8),
            font=("Arial", 10, "bold")
        )
        self.style.map(
            "Action.TButton",
            background=[("active", "#ff2f98"), ("disabled", "#944a6b")],
            foreground=[("disabled", "#f0d4e2")]
        )

    def _reset_ui(self):
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="Pause")
        self.stop_button.config(state="disabled")
        self.start_button.grid()
        self.pause_button.grid_remove()
        self.stop_button.grid_remove()
        self.time_inputs_enabled = True
        self._close_time_dropdown()
        self.minutes_selector.config(fg=self.current_theme["fg"], cursor="hand2")
        self.seconds_selector.config(fg=self.current_theme["fg"], cursor="hand2")


if __name__ == "__main__":
    root = tk.Tk()
    app = TimerGUI(root)
    root.mainloop()
