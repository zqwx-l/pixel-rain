#!/usr/bin/env python3
"""
╔══════════════════════════════════════════╗
║  PIXEL RAIN - Matrix Terminal Animation  ║
║  Japanese katakana digital rain effect   ║
╚══════════════════════════════════════════╝

A mesmerizing Matrix-style rain animation in your terminal.
Zero dependencies — pure Python 3.

Controls:
  q / Ctrl+C  → Quit
  1-9         → Speed (1=slow, 9=fast)
  c           → Cycle color themes
  d           → Toggle density
  Space       → Pause/Resume
"""

import sys
import os
import time
import random
import signal
import select
import termios
import tty

# ─── Character Sets ───────────────────────────────────────────────────────────

KATAKANA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
DIGITS = "0123456789"
SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?/~"
LATIN = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ALL_CHARS = KATAKANA + DIGITS + SYMBOLS + LATIN

# ─── Color Themes ─────────────────────────────────────────────────────────────

THEMES = {
    "matrix": {
        "name": "Matrix Green",
        "head": "\033[97m",       # bright white
        "bright": "\033[92m",     # bright green
        "mid": "\033[32m",        # green
        "dim": "\033[2;32m",      # dim green
        "fade": "\033[2;90m",     # dark gray
    },
    "cyber": {
        "name": "Cyberpunk",
        "head": "\033[97m",
        "bright": "\033[96m",     # bright cyan
        "mid": "\033[36m",        # cyan
        "dim": "\033[2;36m",
        "fade": "\033[2;35m",     # dim magenta
    },
    "blood": {
        "name": "Blood Rain",
        "head": "\033[97m",
        "bright": "\033[91m",     # bright red
        "mid": "\033[31m",        # red
        "dim": "\033[2;31m",
        "fade": "\033[2;90m",
    },
    "gold": {
        "name": "Golden",
        "head": "\033[97m",
        "bright": "\033[93m",     # bright yellow
        "mid": "\033[33m",        # yellow
        "dim": "\033[2;33m",
        "fade": "\033[2;90m",
    },
    "purple": {
        "name": "Purple Haze",
        "head": "\033[97m",
        "bright": "\033[95m",     # bright magenta
        "mid": "\033[35m",        # magenta
        "dim": "\033[2;35m",
        "fade": "\033[2;34m",     # dim blue
    },
}

RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR_SCREEN = "\033[2J\033[H"

# ─── Rain Drop ────────────────────────────────────────────────────────────────

class Drop:
    def __init__(self, x, rows):
        self.x = x
        self.rows = rows
        self.reset()

    def reset(self):
        self.y = random.randint(-20, -1)
        self.speed = random.randint(1, 3)
        self.length = random.randint(5, 25)
        self.chars = [random.choice(ALL_CHARS) for _ in range(self.length)]
        self.tick = 0

    def update(self):
        self.tick += 1
        if self.tick >= (4 - self.speed):
            self.y += 1
            self.tick = 0
            # Randomly mutate a character
            if random.random() < 0.3:
                idx = random.randint(0, self.length - 1)
                self.chars[idx] = random.choice(ALL_CHARS)
        if self.y - self.length > self.rows:
            self.reset()

    def render(self, buffer, theme):
        for i in range(self.length):
            row = self.y - i
            if 0 <= row < self.rows:
                if i == 0:
                    color = theme["head"]
                elif i < 3:
                    color = theme["bright"]
                elif i < self.length // 2:
                    color = theme["mid"]
                elif i < self.length - 2:
                    color = theme["dim"]
                else:
                    color = theme["fade"]
                buffer[row][self.x] = f"{color}{self.chars[i]}{RESET}"


# ─── Main Loop ────────────────────────────────────────────────────────────────

def get_terminal_size():
    try:
        cols, rows = os.get_terminal_size()
        return rows, cols
    except OSError:
        return 24, 80


def kbhit():
    """Check if a key has been pressed (non-blocking)."""
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    return bool(dr)


def main():
    # Terminal setup
    rows, cols = get_terminal_size()
    old_settings = termios.tcgetattr(sys.stdin)

    theme_names = list(THEMES.keys())
    theme_idx = 0
    speed = 5
    density = 0.7
    paused = False

    def cleanup(sig=None, frame=None):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.write(CLEAR_SCREEN)
        sys.stdout.flush()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        tty.setcbreak(sys.stdin.fileno())
        sys.stdout.write(HIDE_CURSOR)
        sys.stdout.write(CLEAR_SCREEN)
        sys.stdout.flush()

        # Initialize drops
        num_drops = int(cols * density)
        drops = []
        for i in range(num_drops):
            x = random.randint(0, cols - 1)
            drop = Drop(x, rows)
            drop.y = random.randint(-rows, rows)  # stagger start
            drops.append(drop)

        frame_count = 0

        while True:
            # Handle input
            if kbhit():
                key = sys.stdin.read(1)
                if key == 'q':
                    break
                elif key == 'c':
                    theme_idx = (theme_idx + 1) % len(theme_names)
                elif key == 'd':
                    density = 0.4 if density >= 0.7 else 0.7 if density >= 0.4 else 1.0
                    num_drops = int(cols * density)
                    while len(drops) < num_drops:
                        x = random.randint(0, cols - 1)
                        drops.append(Drop(x, rows))
                    drops = drops[:num_drops]
                elif key == ' ':
                    paused = not paused
                elif key.isdigit() and key != '0':
                    speed = int(key)

            if paused:
                time.sleep(0.05)
                continue

            # Check terminal resize
            new_rows, new_cols = get_terminal_size()
            if new_rows != rows or new_cols != cols:
                rows, cols = new_rows, new_cols
                num_drops = int(cols * density)
                drops = [Drop(random.randint(0, cols - 1), rows) for _ in range(num_drops)]
                sys.stdout.write(CLEAR_SCREEN)

            # Create frame buffer
            buffer = [["  "] * cols for _ in range(rows)]

            # Update and render drops
            theme = THEMES[theme_names[theme_idx]]
            for drop in drops:
                drop.update()
                drop.render(buffer, theme)

            # Build frame string
            frame_str = "\033[H"  # cursor home
            for row in buffer:
                line = ""
                for cell in row:
                    if cell == "  ":
                        line += " "
                    else:
                        line += cell
                frame_str += line + "\n"

            # Status bar
            status = f" {theme['name']} | Speed: {speed} | Density: {density:.0%} | [Q]uit [C]olor [D]ensity [1-9]Speed [Space]Pause "
            frame_str += f"\033[7m{status:<{cols}}{RESET}"

            sys.stdout.write(frame_str)
            sys.stdout.flush()

            # Frame rate based on speed
            time.sleep(0.08 - (speed * 0.007))
            frame_count += 1

    finally:
        cleanup()


if __name__ == "__main__":
    main()
