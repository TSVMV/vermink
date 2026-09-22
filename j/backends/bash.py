"""Compile a theme into a Bash prompt rebuilt by PROMPT_COMMAND."""

from __future__ import annotations

from ..config import Theme

__all__ = ["name", "render"]

name = "bash"

RAW = {
    "user": "${USER:-unknown}",
    "host": "${HOSTNAME:-unknown}",
    "dir": "${PWD/#$HOME/\\~}",
    "git": "$(__j_git_branch)",
    "git_state": "$(__j_git_state)",
    "venv": "$(__j_venv)",
    "time": "$(__j_time)",
    "exit_code": "$(__j_exit_code)",
}

FUNCTIONS = """__j_git_branch() { git rev-parse --abbrev-ref HEAD 2>/dev/null; }

__j_git_state() {
    local status state
    status="$(git status --porcelain=v1 2>/dev/null)"
    [[ -z $status ]] && return
    state="*"
    [[ "$(git status --porcelain=v1 2>/dev/null | grep -c '^?? ')" -gt 0 ]] && state="${state}+"
    printf '%s' "$state"
}

__j_venv() {
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then basename "${VIRTUAL_ENV:-}"
    elif [[ -n "${CONDA_PREFIX:-}" ]]; then basename "${CONDA_PREFIX:-}"
    fi
}

__j_time() { date +%H:%M; }

__j_exit_code() { [[ "${_J_EXIT:-0}" != "0" ]] && printf 'x%s' "${_J_EXIT}"; }

"""


def _paint(theme: Theme, segment: str) -> str:
    raw = RAW.get(segment, "")
    if not raw:
        return ""
    color = theme.color(segment)
    if not color:
        return raw
    return f"\\[\\033[{color}m\\]{raw}\\[\\033[0m\\]"


def _line(theme: Theme) -> str:
    parts = []
    for segment in list(theme.prompt) + list(theme.status):
        painted = _paint(theme, segment)
        if painted:
            parts.append(painted)
    return theme.separator.join(parts)


def render(theme: Theme) -> str:
    """Return a self-contained Bash block that rebuilds PS1 before every prompt."""
    line = _line(theme)
    script = FUNCTIONS
    script += "__j_update_ps1() {\n    _J_EXIT=$?\n"
    script += f'    PS1="{line}"\n'
    script += "}\n"
    script += 'PROMPT_COMMAND="__j_update_ps1${PROMPT_COMMAND:+;${PROMPT_COMMAND}}"\n'
    return script
