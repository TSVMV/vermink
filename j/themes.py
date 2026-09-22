"""Built-in theme sources: dark and light."""

from __future__ import annotations

__all__ = ["BUILT_INS", "default", "source"]

DARK = """## j theme dark

[palette]
user = bright_green
host = bright_cyan
dir = bright_blue
git = bright_magenta
git_state = yellow
venv = bright_green
time = grey
exit_code = red

[prompt]
user
host
dir
git
git_state

[status]
venv
time
exit_code

[format]
user = user
host = host
dir = dir
git = git
git_state = git_state
venv = venv
time = time
exit_code = exit_code
"""

LIGHT = """## j theme light

[palette]
user = blue
host = cyan
dir = green
git = magenta
git_state = yellow
venv = green
time = dark_gray
exit_code = red

[prompt]
user
host
dir
git
git_state

[status]
venv
time
exit_code

[format]
user = user
host = host
dir = dir
git = git
git_state = git_state
venv = venv
time = time
exit_code = exit_code
"""

BUILT_INS: dict[str, str] = {"dark": DARK, "light": LIGHT}


def default() -> str:
    """Return the default theme name used by j init."""
    return "dark"


def source(name: str) -> str:
    """Return the text of a built-in theme or raise KeyError."""
    if name not in BUILT_INS:
        raise KeyError(name)
    return BUILT_INS[name]
