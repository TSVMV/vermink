"""Prompt segments: definitions, default colors and Python-side value lookups."""

from __future__ import annotations

import os
import socket
import subprocess
from datetime import UTC, datetime
from pathlib import Path

__all__ = [
    "SEGMENT_DEFAULT_COLORS",
    "SEGMENT_LABELS",
    "SUPPORTED_SEGMENTS",
    "abbreviate",
    "value",
]

SEGMENT_DEFAULT_COLORS: dict[str, str] = {
    "user": "32",
    "host": "36",
    "dir": "34",
    "git": "35",
    "git_state": "33",
    "venv": "92",
    "time": "90",
    "exit_code": "31",
}

SUPPORTED_SEGMENTS: tuple[str, ...] = (
    "user",
    "host",
    "dir",
    "git",
    "git_state",
    "venv",
    "time",
    "exit_code",
)

SEGMENT_LABELS: dict[str, str] = {
    "user": "用户",
    "host": "主机",
    "dir": "目录",
    "git": "Git 分支",
    "git_state": "Git 状态",
    "venv": "虚拟环境",
    "time": "时间",
    "exit_code": "退出码",
}


def abbreviate(home: str, path: str) -> str:
    """Shorten a path so the home directory is written as ~."""
    home = home.rstrip("/") or "/"
    if path == home:
        return "~"
    prefix = home + "/"
    if path.startswith(prefix):
        return "~" + path[len(prefix) - 1 :]
    return path


def _run(args: list[str], cwd: str | None) -> str:
    if cwd and not os.path.isdir(cwd):
        return ""
    try:
        proc = subprocess.run(
            args, cwd=cwd or os.getcwd(), capture_output=True, text=True, timeout=3, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def value(
    name: str,
    env: dict[str, str] | None = None,
    cwd: str | None = None,
    git_dir: str | None = None,
) -> str:
    """Return the real current value of a segment, or "" when it should be hidden."""
    env = os.environ if env is None else env
    directory = cwd or os.getcwd()
    work_dir = git_dir if git_dir else directory
    if name == "user":
        return env.get("USER") or env.get("USERNAME") or ""
    if name == "host":
        return env.get("HOSTNAME") or env.get("COMPUTERNAME") or _hostname()
    if name == "dir":
        return abbreviate(env.get("HOME") or "~", directory)
    if name == "git":
        return _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], work_dir)
    if name == "git_state":
        return _git_state(work_dir)
    if name == "venv":
        return _venv_name(env)
    if name == "time":
        return datetime.now(tz=UTC).astimezone().strftime("%H:%M")
    if name == "exit_code":
        code = env.get("J_EXIT_CODE", "0")
        return f"x{code}" if code.isdigit() and code != "0" else ""
    return ""


def _hostname() -> str:
    try:
        return socket.gethostname()
    except OSError:
        return ""


def _git_state(work_dir: str) -> str:
    status = _run(["git", "status", "--porcelain=v1"], work_dir)
    if not status:
        return ""
    state = "*"
    if any(line.startswith("?? ") for line in status.splitlines()):
        state += "+"
    return state


def _venv_name(env: dict[str, str]) -> str:
    for key in ("VIRTUAL_ENV", "CONDA_PREFIX"):
        target = env.get(key, "")
        if target:
            return Path(target).name
    return ""
