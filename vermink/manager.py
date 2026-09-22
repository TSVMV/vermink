"""Install, uninstall and list vermink themes inside shell startup files."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .config import BLOCK_END, BLOCK_START, Theme, load, parse
from .errors import ConfigError, VerminkError
from .themes import BUILT_INS

__all__ = [
    "SHELLS",
    "atomic_write",
    "block",
    "config_dir",
    "current_theme",
    "install",
    "load_theme",
    "rc_path",
    "remove_block",
    "theme_dir",
    "theme_names",
    "theme_path",
    "uninstall",
    "write_theme",
]

SHELLS: tuple[str, ...] = ("zsh", "bash", "pwsh")
MARKER = "theme="


def config_dir(root: str | Path | None = None) -> Path:
    base = Path(root).expanduser() if root else Path(os.environ.get("XDG_CONFIG_HOME") or "~/.config").expanduser()
    return base / "vermink"


def theme_dir(root: str | Path | None = None) -> Path:
    return config_dir(root) / "themes"


def theme_path(name: str, root: str | Path | None = None) -> Path:
    return theme_dir(root) / f"{name}.conf"


def rc_path(shell: str, home: str | Path | None = None) -> Path:
    """Return the startup file for a shell."""
    if shell not in SHELLS:
        raise VerminkError(f"未知 shell {shell!r}，支持 {', '.join(SHELLS)}")
    root = Path(home).expanduser() if home else Path("~").expanduser()
    if shell == "zsh":
        return root / ".zshrc"
    if shell == "bash":
        return root / ".bashrc"
    profile = os.environ.get("PROFILE")
    if profile:
        return Path(profile)
    if os.name == "nt":
        return root / "Documents" / "PowerShell" / "profile.ps1"
    return root / ".config" / "PowerShell" / "profile.ps1"


def load_theme(name: str, root: str | Path | None = None) -> Theme:
    """Load a built-in theme or a saved theme from the config directory."""
    if name in BUILT_INS:
        return parse(BUILT_INS[name], name=name, path=f"内置主题 {name}")
    target = theme_path(name, root)
    if not target.is_file():
        raise ConfigError(f"找不到主题 {name!r}，现有主题：{', '.join(theme_names(root))}")
    return load(target)


def theme_names(root: str | Path | None = None) -> list[str]:
    names = list(BUILT_INS)
    target = theme_dir(root)
    if target.is_dir():
        names.extend(sorted(path.stem for path in target.glob("*.conf")))
    return names


def write_theme(name: str, text: str, root: str | Path | None = None) -> Path:
    target = theme_path(name, root)
    atomic_write(target, text)
    return target


def remove_block(text: str) -> str:
    lines = text.splitlines(keepends=True)
    kept: list[str] = []
    inside = False
    for line in lines:
        if BLOCK_START in line:
            inside = True
            continue
        if BLOCK_END in line:
            inside = False
            continue
        if not inside:
            kept.append(line)
    return "".join(kept)


def block(theme_name: str, script: str) -> str:
    return f"{BLOCK_START} {MARKER}{theme_name}\n{script.rstrip()}\n{BLOCK_END}\n"


def current_theme(shell: str, home: str | Path | None = None, rc: str | Path | None = None) -> str:
    """Return the theme name recorded in the startup file, or ""."""
    path = Path(rc).expanduser() if rc else rc_path(shell, home)
    if not path.is_file():
        return ""
    marker = f"{BLOCK_START} {MARKER}"
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(marker):
            return line[len(marker) :].strip()
    return ""


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(  # noqa: SIM115
        "w", encoding="utf-8", dir=str(path.parent), prefix=".vermink-", delete=False
    )
    tmp = handle.name
    try:
        handle.write(content)
        handle.close()
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def install(
    theme: Theme,
    shell: str,
    script: str,
    home: str | Path | None = None,
    rc: str | Path | None = None,
) -> dict:
    """Write a theme block into the startup file, backing it up first."""
    path = Path(rc).expanduser() if rc else rc_path(shell, home)
    existing = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    stripped = remove_block(existing)
    backup = path.with_name(path.name + ".vermink.bak")
    backed_up = ""
    if not backup.is_file() and existing.strip():
        atomic_write(backup, existing)
        backed_up = str(backup)
    content = stripped.rstrip("\n")
    if content:
        content += "\n\n"
    content += block(theme.name, script)
    atomic_write(path, content)
    return {
        "shell": shell,
        "theme": theme.name,
        "rc": str(path),
        "backup": backed_up or str(backup),
    }


def uninstall(shell: str, home: str | Path | None = None, rc: str | Path | None = None) -> dict:
    """Remove the theme block, restoring the backup when one exists."""
    path = Path(rc).expanduser() if rc else rc_path(shell, home)
    if not path.is_file():
        return {"shell": shell, "rc": str(path), "restored": "", "status": "no_rc"}
    backup = path.with_name(path.name + ".vermink.bak")
    if backup.is_file():
        atomic_write(path, backup.read_text(encoding="utf-8"))
        return {"shell": shell, "rc": str(path), "restored": str(backup), "status": "restored"}
    atomic_write(path, remove_block(path.read_text(encoding="utf-8", errors="replace")))
    return {"shell": shell, "rc": str(path), "restored": "", "status": "removed"}
