"""Theme data model and text format parser."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .colors import resolve
from .errors import ConfigError
from .segments import SEGMENT_DEFAULT_COLORS, SUPPORTED_SEGMENTS

__all__ = ["BLOCK_END", "BLOCK_START", "SECTIONS", "Theme", "load", "parse"]

BLOCK_START = "# >>> j theme"
BLOCK_END = "# <<< j theme"

SECTIONS: tuple[str, ...] = ("palette", "prompt", "status", "format")
VALUE_SECTIONS: tuple[str, ...] = ("palette", "format")
LIST_SECTIONS: tuple[str, ...] = ("prompt", "status")

DEFAULT_PROMPT: tuple[str, ...] = ("user", "dir")


@dataclass
class Theme:
    """A parsed theme: palette, segment lists and per-segment colors."""

    name: str = "custom"
    palette: dict[str, str] = field(default_factory=dict)
    prompt: list[str] = field(default_factory=list)
    status: list[str] = field(default_factory=list)
    format: dict[str, str] = field(default_factory=dict)
    separator: str = " "

    def color(self, segment: str) -> str:
        """Return the SGR parameters for a segment, honoring the format table."""
        if segment in self.format:
            palette_name = self.format[segment]
            if not palette_name:
                return ""
            return resolve(self.palette.get(palette_name, ""), f"片段 {segment}")
        return SEGMENT_DEFAULT_COLORS.get(segment, "")

    def palette_name(self, segment: str) -> str:
        """Return the palette name for a segment, or "" when using defaults."""
        return self.format.get(segment, "")

    def palette_spec(self, segment: str) -> str:
        """Return the raw palette color spec, or "" when the default is used."""
        return self.palette.get(self.palette_name(segment), "")

    def paint_parts(self, section: str) -> list[str]:
        """Return raw segment values in theme order, dropping empty ones."""
        items = self.prompt if section == "prompt" else self.status
        return [self.color(segment) for segment in items]

    def to_text(self) -> str:
        """Render the theme back to the text format."""
        lines = [f"## j theme {self.name}", "", "[palette]"]
        lines.extend(f"{name} = {spec}" for name, spec in self.palette.items())
        lines.extend(["", "[prompt]", *self.prompt, "", "[status]", *self.status])
        if self.format:
            lines.extend(["", "[format]"])
            lines.extend(f"{segment} = {palette}" for segment, palette in self.format.items())
        return "\n".join(lines).rstrip("\n") + "\n"


def parse(text: str, name: str = "custom", path: str = "") -> Theme:
    """Parse theme text, raising ConfigError with line numbers on any problem."""
    theme = Theme(name=name)
    section = ""
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            if section not in SECTIONS:
                raise ConfigError(
                    f"未知区块 [{section}]，支持 {'/'.join('[' + s + ']' for s in SECTIONS)}",
                    path,
                    lineno,
                )
            continue
        if not section:
            raise ConfigError(f"行位于任何区块之外：{line!r}", path, lineno)
        if section in VALUE_SECTIONS:
            _parse_value(theme, section, line, path, lineno)
        else:
            _parse_list(theme, section, line, path, lineno)
    if not theme.prompt:
        theme.prompt = list(DEFAULT_PROMPT)
    return theme


def _parse_value(theme: Theme, section: str, line: str, path: str, lineno: int) -> None:
    key, sep, value = line.partition("=")
    key, value = key.strip(), value.strip()
    if not sep or not key:
        raise ConfigError(f"期望 '名称 = 值'，实际为 {line!r}", path, lineno)
    if section == "palette":
        resolve(value, f"配色 {key}", path, lineno)
        theme.palette[key] = value
        return
    if key not in SUPPORTED_SEGMENTS:
        raise ConfigError(
            f"未知片段 {key!r}，支持 {', '.join(SUPPORTED_SEGMENTS)}", path, lineno
        )
    if not value or value.lower() == "none":
        theme.format[key] = ""
        return
    if value not in theme.palette:
        raise ConfigError(f"[format] 引用的配色 {value!r} 未在 [palette] 中定义", path, lineno)
    theme.format[key] = value


def _parse_list(theme: Theme, section: str, line: str, path: str, lineno: int) -> None:
    if "=" in line:
        raise ConfigError(f"区块 [{section}] 期望片段名，实际为 {line!r}", path, lineno)
    if line not in SUPPORTED_SEGMENTS:
        raise ConfigError(f"未知片段 {line!r}，支持 {', '.join(SUPPORTED_SEGMENTS)}", path, lineno)
    bucket = theme.prompt if section == "prompt" else theme.status
    if line not in bucket:
        bucket.append(line)


def load(path: str | Path) -> Theme:
    """Load a theme from disk; raises ConfigError when the file is missing."""
    target = Path(path).expanduser()
    if not target.is_file():
        raise ConfigError(f"找不到主题文件 {path}")
    return parse(target.read_text(encoding="utf-8"), name=target.stem, path=str(target))
