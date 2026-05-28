"""Tests for the pure-logic helpers in main.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main


class TestUnquote:
    def test_strips_double_quotes(self):
        assert main._unquote('"hello"') == "hello"

    def test_strips_single_quotes(self):
        assert main._unquote("'hello'") == "hello"

    def test_strips_surrounding_whitespace(self):
        assert main._unquote("  hello  ") == "hello"

    def test_strips_whitespace_then_quotes(self):
        assert main._unquote('  "hello"  ') == "hello"

    def test_leaves_unquoted_alone(self):
        assert main._unquote("hello") == "hello"

    def test_does_not_strip_mismatched_quotes(self):
        assert main._unquote("\"hello'") == "\"hello'"

    def test_handles_empty_string(self):
        assert main._unquote("") == ""

    def test_handles_lone_quote_character(self):
        assert main._unquote('"') == '"'


class TestFindCr2Files:
    def test_finds_uppercase_cr2(self, tmp_path: Path):
        (tmp_path / "photo.CR2").touch()
        result = main.find_cr2_files(tmp_path, recursive=False)
        assert [p.name for p in result] == ["photo.CR2"]

    def test_finds_lowercase_cr2(self, tmp_path: Path):
        (tmp_path / "photo.cr2").touch()
        result = main.find_cr2_files(tmp_path, recursive=False)
        assert [p.name for p in result] == ["photo.cr2"]

    def test_ignores_non_cr2_files(self, tmp_path: Path):
        (tmp_path / "photo.CR2").touch()
        (tmp_path / "photo.jpg").touch()
        (tmp_path / "notes.txt").touch()
        result = main.find_cr2_files(tmp_path, recursive=False)
        assert [p.name for p in result] == ["photo.CR2"]

    def test_sorts_results(self, tmp_path: Path):
        for name in ("c.CR2", "a.CR2", "b.CR2"):
            (tmp_path / name).touch()
        result = main.find_cr2_files(tmp_path, recursive=False)
        assert [p.name for p in result] == ["a.CR2", "b.CR2", "c.CR2"]

    def test_non_recursive_skips_subfolders(self, tmp_path: Path):
        (tmp_path / "top.CR2").touch()
        sub = tmp_path / "subfolder"
        sub.mkdir()
        (sub / "deep.CR2").touch()
        result = main.find_cr2_files(tmp_path, recursive=False)
        assert [p.name for p in result] == ["top.CR2"]

    def test_recursive_finds_files_in_subfolders(self, tmp_path: Path):
        (tmp_path / "top.CR2").touch()
        sub = tmp_path / "subfolder"
        sub.mkdir()
        (sub / "deep.CR2").touch()
        result = main.find_cr2_files(tmp_path, recursive=True)
        names = sorted(p.name for p in result)
        assert names == ["deep.CR2", "top.CR2"]

    def test_empty_folder_returns_empty_list(self, tmp_path: Path):
        result = main.find_cr2_files(tmp_path, recursive=False)
        assert result == []
