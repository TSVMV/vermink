"""Command line interface for j."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .backends import bash, preview, pwsh, zsh
from .config import Theme
from .errors import ConfigError, JError
from .manager import SHELLS, current_theme, install, load_theme, rc_path, theme_names, uninstall
from .themes import BUILT_INS, default, source

__all__ = ["detect_shell", "main", "shell_backend"]

BACKENDS: dict[str, object] = {"zsh": zsh, "bash": bash, "pwsh": pwsh}

USAGES = {
    "zsh": "source ~/.zshrc",
    "bash": "source ~/.bashrc",
    "pwsh": ". profile.ps1",
}


def detect_shell() -> str:
    """Guess the current shell from the SHELL environment variable."""
    shell = (os.environ.get("SHELL") or "").lower()
    if "zsh" in shell:
        return "zsh"
    if "bash" in shell:
        return "bash"
    if "powershell" in shell or "pwsh" in shell:
        return "pwsh"
    if os.name == "nt":
        return "pwsh"
    return "zsh"


def shell_backend(shell: str):
    """Return the rendering backend for a shell name, raising on unknown shells."""
    if shell not in BACKENDS:
        raise JError(f"不支持的 shell {shell!r}，支持 {', '.join(BACKENDS)}")
    return BACKENDS[shell]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="j", description="零依赖终端美化引擎：把纯文本主题编译成 shell 提示符"
    )
    parser.add_argument("--version", action="version", version=f"j {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="生成默认主题并安装到启动文件")
    init.add_argument("--theme", default=default(), choices=sorted(BUILT_INS), help="默认主题名")
    init.add_argument("--name", default=None, help="主题保存名，默认与主题同名")
    init.add_argument("--shell", default=detect_shell(), choices=SHELLS)
    init.add_argument("--no-install", action="store_true", help="只保存主题，不写入启动文件")
    init.add_argument("--dir", default=None, help="主题目录，默认 ~/.config/j/themes")
    init.add_argument("--rc", default=None, help="启动文件路径，默认按 shell 推断")

    show = sub.add_parser("show", help="打印主题源配置")
    show.add_argument("theme")
    show.add_argument("--dir", default=None)

    preview = sub.add_parser("preview", help="在终端预览主题效果，不修改任何文件")
    preview.add_argument("theme")
    preview.add_argument("--plain", action="store_true", help="禁用颜色，输出纯文本")
    preview.add_argument("--dir", default=None)

    install_cmd = sub.add_parser("install", help="安装主题到 shell 启动文件（自动备份）")
    install_cmd.add_argument("theme")
    install_cmd.add_argument("--shell", default=detect_shell(), choices=SHELLS)
    install_cmd.add_argument("--rc", default=None, help="启动文件路径，默认按 shell 推断")
    install_cmd.add_argument("--dir", default=None)

    uninstall_cmd = sub.add_parser("uninstall", help="卸载主题并还原备份")
    uninstall_cmd.add_argument("--shell", default=detect_shell(), choices=SHELLS)
    uninstall_cmd.add_argument("--rc", default=None)

    listing = sub.add_parser("list", help="列出主题与当前生效主题")
    listing.add_argument("--shell", default=detect_shell(), choices=SHELLS)
    listing.add_argument("--dir", default=None)
    listing.add_argument("--rc", default=None, help="启动文件路径，默认按 shell 推断")

    return parser


def _render(theme: Theme, shell: str) -> str:
    return str(shell_backend(shell).render(theme))


def cmd_init(args: argparse.Namespace) -> int:
    text = source(args.theme)
    theme_name = args.name or args.theme
    theme_path = Path(args.dir) / f"{theme_name}.conf" if args.dir else None
    if theme_path is not None:
        theme_path.parent.mkdir(parents=True, exist_ok=True)
        theme_path.write_text(text, encoding="utf-8")
        print(f"主题已保存到 {theme_path}")
    if args.no_install:
        return 0
    theme = load_theme(theme_name)
    info = install(theme, args.shell, _render(theme, args.shell), rc=args.rc)
    print(f"已安装 {args.theme} 到 {info['rc']}")
    if info["backup"]:
        print(f"原文件已备份到 {info['backup']}")
    print(f"生效命令：{USAGES[args.shell]}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    print(load_theme(args.theme, root=args.dir).to_text(), end="")
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    theme = load_theme(args.theme, root=args.dir)
    print(preview.render(theme, plain=args.plain), end="")
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    theme = load_theme(args.theme, root=args.dir)
    info = install(theme, args.shell, _render(theme, args.shell), rc=args.rc)
    print(f"已安装 {theme.name} 到 {info['rc']}")
    if info["backup"]:
        print(f"原文件已备份到 {info['backup']}")
    print(f"生效命令：{USAGES[args.shell]}")
    return 0


def cmd_uninstall(args: argparse.Namespace) -> int:
    info = uninstall(args.shell, rc=args.rc)
    print(f"已卸载 {args.shell} 主题，启动文件：{info['rc']}")
    if info["restored"]:
        print(f"已还原备份 {info['restored']}")
    print(f"生效命令：{USAGES[args.shell]}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    names = theme_names(args.dir)
    print("可用主题：")
    for name in names:
        marker = "（内置）" if name in BUILT_INS else ""
        print(f"  - {name}{marker}")
    current = current_theme(args.shell, rc=args.rc)
    if current:
        print(f"当前 {args.shell} 生效主题：{current}")
    else:
        print(f"当前 {args.shell} 未安装主题，启动文件：{rc_path(args.shell)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "init": cmd_init,
        "show": cmd_show,
        "preview": cmd_preview,
        "install": cmd_install,
        "uninstall": cmd_uninstall,
        "list": cmd_list,
    }
    try:
        return handlers[args.command](args)
    except (JError, ConfigError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("已取消", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
