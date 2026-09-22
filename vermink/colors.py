"""Resolve palette color specs into terminal SGR parameters."""

from __future__ import annotations

import re

from .errors import ConfigError

__all__ = ["COLORS", "POWERSHELL_COLORS", "name_for_sgr", "powershell_color", "resolve"]

COLORS: dict[str, str] = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
    "bright_black": "90",
    "bright_red": "91",
    "bright_green": "92",
    "bright_yellow": "93",
    "bright_blue": "94",
    "bright_magenta": "95",
    "bright_cyan": "96",
    "bright_white": "97",
    "gray": "90",
    "grey": "90",
    "light_gray": "90",
    "light_grey": "90",
    "dark_gray": "30",
}

MODIFIERS: dict[str, str] = {
    "bold": "1",
    "dim": "2",
    "underline": "4",
    "italic": "3",
    "strike": "9",
}

POWERSHELL_COLORS: dict[str, str] = {
    "black": "DarkGray",
    "red": "DarkRed",
    "green": "DarkGreen",
    "yellow": "DarkYellow",
    "blue": "DarkBlue",
    "magenta": "DarkMagenta",
    "cyan": "DarkCyan",
    "white": "Gray",
    "bright_black": "DarkGray",
    "bright_red": "Red",
    "bright_green": "Green",
    "bright_yellow": "Yellow",
    "bright_blue": "Blue",
    "bright_magenta": "Magenta",
    "bright_cyan": "Cyan",
    "bright_white": "White",
    "gray": "Gray",
    "grey": "Gray",
    "light_gray": "Gray",
    "light_grey": "Gray",
    "dark_gray": "DarkGray",
}

HEX_RE = re.compile(r"^#([0-9a-fA-F]{6})$")


def _one(piece: str, context: str, path: str, line: int | None) -> str:
    if piece in COLORS:
        return COLORS[piece]
    if piece in MODIFIERS:
        return MODIFIERS[piece]
    if piece.isdigit() and 0 <= int(piece) <= 255:
        return f"38;5;{piece}"
    match = HEX_RE.match(piece)
    if match:
        raw = match.group(1)
        red, green, blue = (int(raw[i : i + 2], 16) for i in (0, 2, 4))
        return f"38;2;{red};{green};{blue}"
    raise ConfigError(f"未知颜色 {piece!r}（{context}）", path, line)


def resolve(spec: str, context: str = "配色", path: str = "", line: int | None = None) -> str:
    """Turn a palette color spec into SGR parameters, or "" for plain text."""
    text = spec.strip()
    if text == "" or text.lower() == "none":
        return ""
    parts: list[str] = []
    for piece in text.split(","):
        piece = piece.strip().lower()
        if piece:
            parts.append(_one(piece, context, path, line))
    return ";".join(parts)


def powershell_color(spec: str) -> str:
    """Map a color spec to a ConsoleColor name, or "" when the spec needs ANSI."""
    piece = spec.strip().split(",")[0].strip().lower()
    return POWERSHELL_COLORS.get(piece, "")


def name_for_sgr(sgr: str) -> str:
    """Return a named color producing the same SGR, or "" when there is none."""
    for name, code in COLORS.items():
        if code == sgr:
            return name
    return ""
