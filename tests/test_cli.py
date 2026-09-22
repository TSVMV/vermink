"""Tests for j.cli module."""

import pytest

from j.cli import main


class TestVersion:
    def test_version(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0
        assert "0.1.0" in capsys.readouterr().out


class TestList:
    def test_list_includes_builtins(self, capsys):
        main(["list", "--shell", "zsh"])
        out = capsys.readouterr().out
        assert "dark" in out
        assert "light" in out
        assert "内置" in out

    def test_list_no_rc(self, capsys, tmp_path):
        main(["list", "--shell", "zsh", "--rc", str(tmp_path / ".zshrc")])
        out = capsys.readouterr().out
        assert "未安装" in out


class TestShow:
    def test_show_builtin(self, capsys):
        main(["show", "dark"])
        out = capsys.readouterr().out
        assert "[palette]" in out
        assert "bright_green" in out

    def test_show_unknown(self, capsys):
        result = main(["show", "nonexistent"])
        assert result == 1
        assert "找不到" in capsys.readouterr().err


class TestPreview:
    def test_preview_plain(self, capsys):
        main(["preview", "dark", "--plain"])
        out = capsys.readouterr().out
        assert "预览渲染" in out
        assert "main" in out


class TestInit:
    def test_init_no_install(self, capsys, tmp_path):
        theme_dir = tmp_path / "themes"
        theme_dir.mkdir()
        result = main(["init", "--theme", "dark", "--no-install", "--dir", str(theme_dir)])
        assert result == 0
        out = capsys.readouterr().out
        assert "已保存" in out

    def test_init_with_install(self, capsys, tmp_path):
        rc = tmp_path / ".zshrc"
        result = main(["init", "--theme", "dark", "--shell", "zsh", "--rc", str(rc)])
        assert result == 0
        assert rc.exists()
        out = capsys.readouterr().out
        assert "已安装" in out


class TestInstall:
    def test_install_theme(self, capsys, tmp_path):
        rc = tmp_path / ".zshrc"
        result = main(["install", "dark", "--shell", "zsh", "--rc", str(rc)])
        assert result == 0
        assert rc.exists()
        out = capsys.readouterr().out
        assert "已安装" in out


class TestUninstall:
    def test_uninstall(self, capsys, tmp_path):
        rc = tmp_path / ".zshrc"
        rc.write_text("# >>> j theme theme=dark\ncontent\n# <<< j theme\n")
        result = main(["uninstall", "--shell", "zsh", "--rc", str(rc)])
        assert result == 0
        out = capsys.readouterr().out
        assert "已卸载" in out


class TestErrorHandling:
    def test_unknown_command(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["badcmd"])
        assert exc.value.code == 2

    def test_missing_theme_arg(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["show"])
        assert exc.value.code == 2
