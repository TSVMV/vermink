"""Tests for vermink.colors module."""

import pytest

from vermink.colors import (
    COLORS,
    MODIFIERS,
    POWERSHELL_COLORS,
    name_for_sgr,
    powershell_color,
    resolve,
)


class TestResolve:
    def test_named_color(self):
        assert resolve("red") == "31"

    def test_bright_color(self):
        assert resolve("bright_green") == "92"

    def test_modifier(self):
        assert resolve("bold") == "1"

    def test_256_color(self):
        assert resolve("208") == "38;5;208"

    def test_hex_color(self):
        assert resolve("#ff8800") == "38;2;255;136;0"

    def test_composite(self):
        assert resolve("bright_blue,bold") == "94;1"

    def test_empty(self):
        assert resolve("") == ""

    def test_none_keyword(self):
        assert resolve("none") == ""

    def test_case_insensitive(self):
        assert resolve("RED") == "31"
        assert resolve("Bright_Green") == "92"

    def test_unknown_color_raises(self):
        with pytest.raises(Exception, match="未知颜色"):
            resolve("not_a_color")

    def test_invalid_hex_raises(self):
        with pytest.raises(Exception, match="未知颜色"):
            resolve("#gg0000")

    def test_context_in_error(self):
        with pytest.raises(Exception, match="配色 foo"):
            resolve("bad", context="配色 foo")

    def test_path_and_line_in_error(self):
        with pytest.raises(Exception, match="theme.conf:42"):
            resolve("bad", path="theme.conf", line=42)


class TestPowershellColor:
    def test_named_color(self):
        assert powershell_color("red") == "DarkRed"

    def test_bright_color(self):
        assert powershell_color("bright_green") == "Green"

    def test_alias(self):
        assert powershell_color("grey") == "Gray"

    def test_unknown_returns_empty(self):
        assert powershell_color("208") == ""

    def test_hex_returns_empty(self):
        assert powershell_color("#ff0000") == ""

    def test_composite_returns_first(self):
        assert powershell_color("bright_blue,bold") == "Blue"


class TestNameForSgr:
    def test_basic_colors(self):
        assert name_for_sgr("31") == "red"
        assert name_for_sgr("92") == "bright_green"

    def test_unknown_returns_empty(self):
        assert name_for_sgr("999") == ""

    def test_composite_returns_empty(self):
        assert name_for_sgr("94;1") == ""


class TestConstants:
    def test_colors_is_subset_of_powershell(self):
        for name in COLORS:
            assert name in POWERSHELL_COLORS, f"{name} missing from POWERSHELL_COLORS"

    def test_modifiers_not_in_colors(self):
        for name in MODIFIERS:
            assert name not in COLORS
