"""Compile a theme into a Zsh prompt script using PS1 and RPROMPT."""

from __future__ import annotations

from ..config import Theme

__all__ = ["name", "render"]

name = "zsh"

STATIC = {
    "user": "%n",
    "host": "%m",
    "dir": "%~",
    "time": "%T",
}

DYNAMIC = {
    "git": "%{$(git rev-parse --abbrev-ref HEAD 2>/dev/null)%}",
    "git_state": "%{$(__j_git_state)%}",
    "venv": "%{$(__j_venv)%}",
    "exit_code": "%{$(__j_exit_code)%}",
}

FUNCTIONS = """_j_precmd() { _J_EXIT=$?; }
autoload -Uz add-zsh-hook
add-zsh-hook precmd _j_precmd

__j_git_state() {
    local status state
    status="$(git status --porcelain=v1 2>/dev/null)"
    [[ -z $status ]] && return
    state="*"
    [[ "$(git status --porcelain=v1 2>/dev/null | grep -c '^?? ')" -gt 0 ]] && state="${state}+"
    print -n "$state"
}

__j_venv() {
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then print -n "${VIRTUAL_ENV:t}"
    elif [[ -n "${CONDA_PREFIX:-}" ]]; then print -n "${CONDA_PREFIX:t}"
    fi
}

__j_exit_code() {
    (( ${_J_EXIT:-0} != 0 )) && print -n "x${_J_EXIT}"
}

"""


def _paint(theme: Theme, segment: str) -> str:
    raw = STATIC.get(segment, DYNAMIC.get(segment, ""))
    if not raw:
        return ""
    color = theme.color(segment)
    return f"%F{{{color}}}{raw}%f" if color else raw


def _line(theme: Theme, section: str) -> str:
    items = theme.prompt if section == "prompt" else theme.status
    parts = [painted for painted in (_paint(theme, segment) for segment in items) if painted]
    return theme.separator.join(parts)


def render(theme: Theme) -> str:
    """Return a self-contained Zsh block that sets PS1 and RPROMPT."""
    prompt = _line(theme, "prompt") or "%~"
    script = FUNCTIONS + f'PS1="{prompt}"\n'
    right = _line(theme, "status")
    if right:
        script += f'RPROMPT="{right}"\n'
    return script
