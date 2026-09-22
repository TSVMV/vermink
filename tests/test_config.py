"""Tests for vermink.config module."""

import pytest

from vermink.config import parse
from vermink.errors import ConfigError


class TestParse:
    def test_minimal_theme(self):
        theme = parse("[palette]\nuser = green\n[prompt]\nuser\n")
        assert theme.palette == {"user": "green"}
        assert theme.prompt == ["user"]

    def test_default_prompt_when_empty(self):
        theme = parse("[palette]\nuser = green\n")
        assert theme.prompt == ["user", "dir"]

    def test_full_theme(self):
        text = """[palette]
user = bright_green
dir = blue
time_color = grey
exit_color = red

[prompt]
user
host
dir

[status]
time
exit_code

[format]
user = user
dir = dir
time = time_color
exit_code = exit_color
"""
        theme = parse(text, name="test")
        assert theme.name == "test"
        assert theme.palette["user"] == "bright_green"
        assert "user" in theme.prompt
        assert "time" in theme.status
        assert theme.format["user"] == "user"

    def test_comments_and_blanks_ignored(self):
        text = """# comment

[palette]
user = green

# another comment
[prompt]
user
"""
        theme = parse(text)
        assert theme.prompt == ["user"]

    def test_unknown_section_raises(self):
        with pytest.raises(ConfigError, match="未知区块"):
            parse("[unknown]\nfoo = bar\n")

    def test_line_outside_section_raises(self):
        with pytest.raises(ConfigError, match="位于任何区块之外"):
            parse("foo = bar\n")

    def test_invalid_format_in_list(self):
        with pytest.raises(ConfigError, match="期望片段名"):
            parse("[prompt]\nfoo = bar\n")

    def test_unknown_segment_in_list(self):
        with pytest.raises(ConfigError, match="未知片段"):
            parse("[prompt]\nnot_a_segment\n")

    def test_unknown_segment_in_format(self):
        with pytest.raises(ConfigError, match="未知片段"):
            parse("[palette]\nfoo = green\n[format]\nnot_a_segment = foo\n")

    def test_format_references_undefined_palette(self):
        with pytest.raises(ConfigError, match="未在"):
            parse("[palette]\nfoo = green\n[format]\ndir = missing\n")

    def test_format_none_means_plain(self):
        theme = parse("[palette]\nfoo = green\n[format]\ndir = none\n")
        assert theme.color("dir") == ""

    def test_duplicate_segment_in_list(self):
        theme = parse("[prompt]\nuser\nuser\n")
        assert theme.prompt.count("user") == 1


class TestThemeColor:
    def test_format_maps_to_palette(self):
        theme = parse("[palette]\nfoo = red\n[format]\nuser = foo\n")
        assert theme.color("user") == "31"

    def test_format_empty_means_plain(self):
        theme = parse("[palette]\nfoo = green\n[format]\nuser = none\n")
        assert theme.color("user") == ""

    def test_default_color_when_no_format(self):
        theme = parse("[palette]\nfoo = green\n[prompt]\nuser\n")
        assert theme.color("user") == "32"

    def test_palette_name(self):
        theme = parse("[palette]\nfoo = green\n[format]\nuser = foo\n")
        assert theme.palette_name("user") == "foo"

    def test_palette_name_default(self):
        theme = parse("[palette]\nfoo = green\n[prompt]\nuser\n")
        assert theme.palette_name("user") == ""

    def test_palette_spec(self):
        theme = parse("[palette]\nfoo = bright_green\n[format]\nuser = foo\n")
        assert theme.palette_spec("user") == "bright_green"

    def test_palette_spec_default(self):
        theme = parse("[palette]\nfoo = green\n[prompt]\nuser\n")
        assert theme.palette_spec("user") == ""


class TestThemeToText:
    def test_roundtrip(self):
        text = """## vermink theme test

[palette]
user = green

[prompt]
user

[status]
time
"""
        theme = parse(text, name="test")
        assert theme.to_text() == text

    def test_format_included(self):
        text = """## vermink theme test

[palette]
foo = green
time_color = grey

[prompt]
user

[status]
time

[format]
user = foo
time = time_color
"""
        theme = parse(text, name="test")
        assert theme.to_text() == text


class TestLoad:
    def test_load_nonexistent_raises(self, tmp_path):
        from vermink.config import load

        with pytest.raises(ConfigError, match="找不到"):
            load(tmp_path / "missing.conf")

    def test_load_valid_file(self, tmp_path):
        from vermink.config import load

        conf = tmp_path / "test.conf"
        conf.write_text("[palette]\nuser = green\n[prompt]\nuser\n")
        theme = load(conf)
        assert theme.name == "test"
        assert "user" in theme.prompt
