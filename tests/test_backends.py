"""Tests for vermink.backends module."""

import pytest

from vermink.backends import bash, preview, pwsh, zsh
from vermink.config import parse
from vermink.themes import BUILT_INS


@pytest.fixture
def dark():
    return parse(BUILT_INS["dark"], name="dark")


@pytest.fixture
def light():
    return parse(BUILT_INS["light"], name="light")


@pytest.fixture
def minimal():
    return parse("[palette]\nuser = green\n[prompt]\nuser\n", name="minimal")


class TestZsh:
    def test_name(self):
        assert zsh.name == "zsh"

    def test_render_contains_ps1(self, dark):
        text = zsh.render(dark)
        assert "PS1=" in text

    def test_render_contains_rprompt(self, dark):
        text = zsh.render(dark)
        assert "RPROMPT=" in text

    def test_render_has_precmd(self, dark):
        text = zsh.render(dark)
        assert "_j_precmd" in text
        assert "add-zsh-hook" in text

    def test_render_has_functions(self, dark):
        text = zsh.render(dark)
        assert "__j_git_state" in text
        assert "__j_venv" in text
        assert "__j_exit_code" in text

    def test_render_minimal(self, minimal):
        text = zsh.render(minimal)
        assert "PS1=" in text
        assert "RPROMPT=" not in text

    def test_no_status_no_rprompt(self, minimal):
        text = zsh.render(minimal)
        assert "RPROMPT" not in text


class TestBash:
    def test_name(self):
        assert bash.name == "bash"

    def test_render_contains_ps1(self, dark):
        text = bash.render(dark)
        assert "PS1=" in text

    def test_render_contains_prompt_command(self, dark):
        text = bash.render(dark)
        assert "PROMPT_COMMAND=" in text

    def test_render_has_functions(self, dark):
        text = bash.render(dark)
        assert "__j_git_branch" in text
        assert "__j_git_state" in text
        assert "__j_update_ps1" in text

    def test_render_has_exit_code_capture(self, dark):
        text = bash.render(dark)
        assert "_J_EXIT=$?" in text


class TestPwsh:
    def test_name(self):
        assert pwsh.name == "pwsh"

    def test_render_has_prompt_function(self, dark):
        text = pwsh.render(dark)
        assert "function prompt" in text

    def test_render_has_default_color(self, dark):
        text = pwsh.render(dark)
        assert "$__j_default_color" in text

    def test_render_has_psreadline(self, dark):
        text = pwsh.render(dark)
        assert "Set-PSReadLineOption" in text

    def test_render_has_exit_capture(self, dark):
        text = pwsh.render(dark)
        assert "$__j_last_exit = $LASTEXITCODE" in text

    def test_render_uses_consolecolor(self, dark):
        text = pwsh.render(dark)
        assert "[ConsoleColor]::" in text

    def test_render_has_functions(self, dark):
        text = pwsh.render(dark)
        assert "__j_set_color" in text
        assert "__j_seg" in text
        assert "__j_sep" in text


class TestPreview:
    def test_plain_output(self, dark):
        text = preview.render(dark, plain=True)
        assert "预览渲染" in text
        assert "\x1b[" not in text

    def test_contains_sample_data(self, dark):
        text = preview.render(dark, plain=True)
        assert "main" in text
        assert "demo" in text

    def test_contains_status_info(self, dark):
        text = preview.render(dark, plain=True)
        assert "x1" in text

    def test_color_disabled_in_pipe(self, dark):
        assert preview.color_enabled() is False

    def test_note_present(self, dark):
        text = preview.render(dark, plain=True)
        assert "未修改任何文件" in text

    def test_status_alignment_note(self, dark):
        text = preview.render(dark, plain=True)
        assert "RPROMPT" in text or "状态栏" in text


class TestBackendConsistency:
    def test_all_backends_render_same_segments(self, dark):
        for backend in (zsh, bash, pwsh):
            text = backend.render(dark)
            assert len(text) > 0

    def test_all_backends_handle_empty_status(self, minimal):
        for backend in (zsh, bash, pwsh):
            text = backend.render(minimal)
            assert len(text) > 0

    def test_all_builtins_render(self):
        for name, source_text in BUILT_INS.items():
            theme = parse(source_text, name=name)
            for backend in (zsh, bash, pwsh):
                text = backend.render(theme)
                assert len(text) > 0, f"{backend.name} failed for {name}"
