"""Render a sample prompt to the terminal for preview without touching any file."""

from __future__ import annotations

import os
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

from ..config import Theme
from ..segments import abbreviate

__all__ = ["color_enabled", "render"]

NOTE = "# 预览渲染（样例数据，未修改任何文件）"
SAMPLE_DIR = Path.home() / "projects" / "demo"
SAMPLE_GIT = "main"
SAMPLE_STATE = "*"
SAMPLE_VENV = "demo"
SAMPLE_EXIT = "x1"


def color_enabled() -> bool:
    """Whether ANSI colors are safe for the current output target."""
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    return os.environ.get("TERM", "") not in ("", "dumb")


def sample(segment: str) -> str:
    """Return a preview value; user and host come from the real environment."""
    if segment == "user":
        return os.environ.get("USER") or os.environ.get("USERNAME") or ""
    if segment == "host":
        return os.environ.get("HOSTNAME") or os.environ.get("COMPUTERNAME") or "localhost"
    if segment == "dir":
        return abbreviate(os.environ.get("HOME") or "~", str(SAMPLE_DIR))
    if segment == "git":
        return SAMPLE_GIT
    if segment == "git_state":
        return SAMPLE_STATE
    if segment == "venv":
        return SAMPLE_VENV
    if segment == "time":
        return datetime.now(tz=UTC).astimezone().strftime("%H:%M")
    if segment == "exit_code":
        return SAMPLE_EXIT
    return ""


_SGR_RE = re.compile(r"\x1b\[[0-9;]*m")


def _visible(text: str) -> int:
    """Return the visible character count, ignoring ANSI escape sequences."""
    return len(_SGR_RE.sub("", text))


def _paint(theme: Theme, segment: str, use_color: bool) -> str:
    """Return a single preview segment, optionally with ANSI coloring."""
    text = sample(segment)
    if not text:
        return ""
    sgr = theme.color(segment)
    if use_color and sgr:
        return f"\x1b[{sgr}m{text}\x1b[0m"
    return text


def _join(theme: Theme, segments: list[str], use_color: bool) -> str:
    parts = [_paint(theme, segment, use_color) for segment in segments]
    return theme.separator.join(part for part in parts if part)


def render(theme: Theme, plain: bool = False) -> str:
    """Return preview text; colors are dropped when plain or not a real terminal."""
    use_color = color_enabled() and not plain
    left = _join(theme, theme.prompt, use_color)
    right = _join(theme, theme.status, use_color)
    if right:
        width = shutil.get_terminal_size(fallback=(80, 24)).columns
        line = left + " " * max(width - _visible(left) - _visible(right), 1) + right
        if use_color:
            line += "\x1b[0m"
    else:
        line = left
    extra = "\n# 状态栏片段显示在行尾（zsh 的 RPROMPT，bash 与 pwsh 合并到主提示符）" if right else ""
    return NOTE + extra + "\n" + line + "\n"
