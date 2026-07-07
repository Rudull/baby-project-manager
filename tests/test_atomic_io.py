"""Tests for utils.atomic_io.atomic_write.

These guard the data-safety property that a crash mid-write must never corrupt
or truncate the user's existing file — the core reason the helper exists.
"""
from __future__ import annotations

import pytest

from utils.atomic_io import atomic_write


def test_writes_new_file(tmp_path):
    target = tmp_path / "new.txt"
    with atomic_write(target) as f:
        f.write("hello world")
    assert target.read_text(encoding="utf-8") == "hello world"


def test_replaces_existing_file(tmp_path):
    target = tmp_path / "data.txt"
    target.write_text("old contents", encoding="utf-8")
    with atomic_write(target) as f:
        f.write("new contents")
    assert target.read_text(encoding="utf-8") == "new contents"


def test_failure_leaves_original_intact(tmp_path):
    target = tmp_path / "data.txt"
    target.write_text("original", encoding="utf-8")

    with pytest.raises(RuntimeError):
        with atomic_write(target) as f:
            f.write("half-written")
            raise RuntimeError("simulated crash mid-write")

    # The original file must be untouched — not truncated, not the new bytes.
    assert target.read_text(encoding="utf-8") == "original"


def test_failure_cleans_up_temp_file(tmp_path):
    target = tmp_path / "data.txt"
    target.write_text("original", encoding="utf-8")

    with pytest.raises(RuntimeError):
        with atomic_write(target):
            raise RuntimeError("boom")

    # No leftover .tmp files in the directory.
    leftovers = [p.name for p in tmp_path.iterdir() if p.name != "data.txt"]
    assert leftovers == []


def test_creates_missing_parent_directory(tmp_path):
    target = tmp_path / "nested" / "dir" / "out.txt"
    with atomic_write(target) as f:
        f.write("content")
    assert target.read_text(encoding="utf-8") == "content"


def test_temp_file_is_same_directory(tmp_path):
    # os.replace is only atomic within one filesystem; the temp file must sit
    # next to the target, not in the system temp dir. Check that a temp file
    # materializes in the target directory while the write is in progress.
    target = tmp_path / "data.txt"
    tmp_names_during_write = []
    with atomic_write(target) as f:
        f.write("x")
        tmp_names_during_write = [p.name for p in tmp_path.iterdir()]
    assert any(name.endswith(".tmp") for name in tmp_names_during_write)
