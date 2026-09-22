"""Tests for vermink.manager module."""

import pytest

from vermink.config import parse
from vermink.errors import ConfigError, VerminkError
from vermink.manager import (
    block,
    config_dir,
    current_theme,
    install,
    load_theme,
    rc_path,
    remove_block,
    theme_dir,
    theme_names,
    theme_path,
    uninstall,
    write_theme,
)
from vermink.themes import BUILT_INS


class TestPaths:
    def test_config_dir_default(self):
        result = config_dir()
        assert result.name == "vermink"
        assert result.parent.name == ".config" or "XDG" in str(result)

    def test_config_dir_custom_root(self, tmp_path):
        result = config_dir(tmp_path)
        assert result == tmp_path / "vermink"

    def test_theme_dir(self, tmp_path):
        result = theme_dir(tmp_path)
        assert result == tmp_path / "vermink" / "themes"

    def test_theme_path(self, tmp_path):
        result = theme_path("dark", tmp_path)
        assert result == tmp_path / "vermink" / "themes" / "dark.conf"

    def test_rc_path_zsh(self, tmp_path):
        result = rc_path("zsh", tmp_path)
        assert result.name == ".zshrc"

    def test_rc_path_bash(self, tmp_path):
        result = rc_path("bash", tmp_path)
        assert result.name == ".bashrc"

    def test_rc_path_pwsh(self, tmp_path):
        result = rc_path("pwsh", tmp_path)
        assert result.name == "profile.ps1"

    def test_rc_path_unknown_shell(self):
        with pytest.raises(VerminkError, match="未知 shell"):
            rc_path("fish")


class TestRemoveBlock:
    def test_removes_block(self):
        text = "before\n# >>> vermink theme theme=dark\ncontent\n# <<< vermink theme\nafter\n"
        assert remove_block(text) == "before\nafter\n"

    def test_no_block(self):
        text = "just some text\n"
        assert remove_block(text) == text

    def test_multiple_blocks(self):
        text = "a\n# >>> vermink theme theme=dark\nx\n# <<< vermink theme\nb\n# >>> vermink theme theme=light\ny\n# <<< vermink theme\nc\n"
        assert remove_block(text) == "a\nb\nc\n"

    def test_empty_input(self):
        assert remove_block("") == ""


class TestBlock:
    def test_format(self):
        result = block("dark", "echo hello")
        assert BLOCK_START in result
        assert BLOCK_END in result
        assert "theme=dark" in result
        assert "echo hello" in result


BLOCK_START = "# >>> vermink theme"
BLOCK_END = "# <<< vermink theme"


class TestCurrentTheme:
    def test_finds_theme(self, tmp_path):
        rc = tmp_path / ".zshrc"
        rc.write_text("alias ll='ls -la'\n# >>> vermink theme theme=dark\nstuff\n# <<< vermink theme\n")
        assert current_theme("zsh", rc=rc) == "dark"

    def test_no_theme(self, tmp_path):
        rc = tmp_path / ".zshrc"
        rc.write_text("alias ll='ls -la'\n")
        assert current_theme("zsh", rc=rc) == ""

    def test_no_rc_file(self, tmp_path):
        assert current_theme("zsh", rc=tmp_path / ".zshrc") == ""


class TestLoadTheme:
    def test_loads_builtin(self):
        theme = load_theme("dark")
        assert theme.name == "dark"
        assert "user" in theme.prompt

    def test_unknown_theme_raises(self):
        with pytest.raises(ConfigError, match="找不到主题"):
            load_theme("nonexistent")

    def test_loads_custom_theme(self, tmp_path):
        conf = theme_path("custom", tmp_path)
        conf.parent.mkdir(parents=True, exist_ok=True)
        conf.write_text("[palette]\nuser = green\n[prompt]\nuser\n")
        theme = load_theme("custom", tmp_path)
        assert theme.name == "custom"


class TestThemeNames:
    def test_includes_builtins(self):
        names = theme_names()
        for name in BUILT_INS:
            assert name in names

    def test_includes_custom(self, tmp_path):
        conf = theme_path("mytheme", tmp_path)
        conf.parent.mkdir(parents=True, exist_ok=True)
        conf.write_text("[palette]\nuser = green\n[prompt]\nuser\n")
        names = theme_names(tmp_path)
        assert "mytheme" in names


class TestWriteTheme:
    def test_writes_file(self, tmp_path):
        path = write_theme("test", "[palette]\nuser = green\n", tmp_path)
        assert path.exists()
        assert "user = green" in path.read_text()


class TestInstallUninstall:
    @pytest.fixture
    def theme(self):
        return parse(BUILT_INS["dark"], name="dark")

    def test_install_creates_rc(self, tmp_path, theme):
        rc = tmp_path / ".zshrc"
        result = install(theme, "zsh", "echo hello", rc=rc)
        assert result["theme"] == "dark"
        assert rc.exists()
        content = rc.read_text()
        assert "theme=dark" in content
        assert "echo hello" in content

    def test_install_backs_up_existing(self, tmp_path, theme):
        rc = tmp_path / ".zshrc"
        rc.write_text("existing content\n")
        install(theme, "zsh", "echo hello", rc=rc)
        backup = tmp_path / ".zshrc.vermink.bak"
        assert backup.exists()
        assert "existing content" in backup.read_text()

    def test_install_replaces_old_theme(self, tmp_path, theme):
        rc = tmp_path / ".zshrc"
        rc.write_text("# >>> vermink theme theme=old\nold content\n# <<< vermink theme\nother\n")
        install(theme, "zsh", "echo new", rc=rc)
        content = rc.read_text()
        assert "theme=dark" in content
        assert "old content" not in content
        assert "other" in content

    def test_uninstall_removes_block(self, tmp_path, theme):
        rc = tmp_path / ".zshrc"
        rc.write_text("before\n# >>> vermink theme theme=dark\nstuff\n# <<< vermink theme\nafter\n")
        result = uninstall("zsh", rc=rc)
        assert result["status"] == "removed"
        content = rc.read_text()
        assert "theme=dark" not in content
        assert "before" in content
        assert "after" in content

    def test_uninstall_restores_backup(self, tmp_path, theme):
        rc = tmp_path / ".zshrc"
        rc.write_text("# >>> vermink theme theme=dark\nstuff\n# <<< vermink theme\n")
        backup = tmp_path / ".zshrc.vermink.bak"
        backup.write_text("original content\n")
        result = uninstall("zsh", rc=rc)
        assert result["status"] == "restored"
        assert "original content" in rc.read_text()

    def test_uninstall_no_rc(self, tmp_path):
        result = uninstall("zsh", rc=tmp_path / ".zshrc")
        assert result["status"] == "no_rc"
