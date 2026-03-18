#!/usr/bin/env python3
"""Simple console countdown timer with pause/resume and optional beep.

Usage examples:
  python timer.py --seconds 90
  python timer.py --time 01:30

Controls (press while running):
  p - pause/resume
  s - stop and exit
  q - quit immediately

Written to be minimal and use only the Python standard library.
"""
from __future__ import annotations

import argparse
import sys
import time
import threading
import signal
import platform

try:
    import winsound
except Exception:
    winsound = None

try:
    import msvcrt
    _HAS_MSVCRT = True
except Exception:
    import select
    _HAS_MSVCRT = False


def parse_time_arg(value: str) -> int:
    if ":" in value:
        parts = value.split(":")
        if len(parts) == 2:
            m, s = parts
            return int(m) * 60 + int(s)
        raise argparse.ArgumentTypeError("Time must be MM:SS")
    return int(value)


def format_seconds(sec: int) -> str:
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"


class KeyListener(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.paused = False
        self.stopped = False
        self.quit = False

    def run(self):
        while not self.stopped and not self.quit:
            ch = self._get_char_nonblocking()
            if ch is None:
                time.sleep(0.05)
                continue
            ch = ch.lower()
            if ch == "p":
                self.paused = not self.paused
            elif ch == "s":
                self.stopped = True
            elif ch == "q":
                self.quit = True

    def _get_char_nonblocking(self) -> str | None:
        if _HAS_MSVCRT:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                return ch
            return None
        # POSIX fallback
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if dr:
            return sys.stdin.read(1)
        return None


def beep(duration: float):
    """Play a beep pattern for approximately `duration` seconds.

    On Windows we loop the system Beep call; on other platforms we emit
    terminal bell characters repeatedly.
    """
    end = time.time() + duration
    if winsound and platform.system() == "Windows":
        try:
            # use a fixed beep frequency/pulse and repeat
            while time.time() < end:
                winsound.Beep(1000, 400)
                # brief pause to avoid a continuous tone
                time.sleep(0.1)
        except Exception:
            # fallback to bell if Beep fails
            while time.time() < end:
                sys.stdout.write("\a")
                sys.stdout.flush()
                time.sleep(0.5)
    else:
        # Fallback: emit bells until time is up
        while time.time() < end:
            sys.stdout.write("\a")
            sys.stdout.flush()
            time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser(description="Minimal console countdown timer")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--seconds", "-s", type=int, help="Duration in seconds")
    group.add_argument("--time", "-t", type=parse_time_arg, help="Duration as MM:SS")
    parser.add_argument("--label", "-l", default="Timer", help="Optional label shown when finished")
    args = parser.parse_args()

    duration = args.seconds if args.seconds is not None else args.time
    if duration <= 0:
        print("Duration must be positive")
        sys.exit(2)

    listener = KeyListener()
    listener.start()

    stopped = False

    def _signal_handler(signum, frame):
        listener.stopped = True
        print("\nInterrupted. Exiting...")
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)

    start = time.monotonic()
    end_time = start + duration

    try:
        while True:
            if listener.quit:
                print("\nQuit requested.")
                stopped = True
                break
            if listener.stopped:
                print("\nStopped by user.")
                stopped = True
                break
            if listener.paused:
                remaining = int(max(0, end_time - time.monotonic()))
                sys.stdout.write(f"\rPAUSED {format_seconds(remaining)}  (press 'p' to resume, 's' stop)")
                sys.stdout.flush()
                time.sleep(0.2)
                continue

            now = time.monotonic()
            remaining = int(max(0, end_time - now))
            sys.stdout.write(f"\r{format_seconds(remaining)}  (p=pause s=stop q=quit)")
            sys.stdout.flush()

            if remaining <= 0:
                break
            time.sleep(0.2)

        if not stopped:
            print(f"\n{args.label} finished!")
            # choose beep duration based on which CLI option was used
            length = 5.0 if args.seconds is not None else 10.0
            beep(length)

    finally:
        listener.stopped = True


if __name__ == "__main__":
    main()
