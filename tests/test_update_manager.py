"""Tests for the auto-updater's version comparison and asset selection."""
from __future__ import annotations

import re

import pytest

from updater.update_manager import UpdateManager
from version import __version__


@pytest.fixture
def manager(qapp):
    return UpdateManager(current_version="0.5.1", github_repo="Rudull/baby-project-manager")


def test_version_string_is_valid_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__), __version__


@pytest.mark.parametrize(
    "current,remote,expected",
    [
        ("0.5.1", "0.5.2", True),
        ("0.5.1", "0.6.0", True),
        ("0.5.1", "1.0.0", True),
        ("0.9.0", "0.10.0", True),   # numeric, not lexicographic
        ("0.5.1", "0.5.1", False),
        ("0.5.2", "0.5.1", False),
        ("1.0.0", "0.9.9", False),
    ],
)
def test_is_newer_version(manager, current, remote, expected):
    assert manager.is_newer_version(current, remote) is expected


def test_is_newer_version_handles_garbage(manager):
    assert manager.is_newer_version("1.0.0", "not-a-version") is False


def _release(names):
    return {
        "assets": [
            {"name": n, "browser_download_url": f"https://example.com/{n}"} for n in names
        ],
        "html_url": "https://github.com/Rudull/baby-project-manager/releases/latest",
    }


def test_asset_picker_skips_checksum_file(manager, monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Linux")
    data = _release(["SHA256SUMS", "baby-project-manager-linux"])
    url = manager._find_asset_url(data)
    assert url.endswith("baby-project-manager-linux")


def test_asset_picker_skips_signature_and_notes(manager, monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Linux")
    data = _release(["baby-project-manager-linux.sig", "notes.txt", "baby-project-manager-linux"])
    url = manager._find_asset_url(data)
    assert url.endswith("baby-project-manager-linux")


def test_asset_picker_windows_prefers_exe(manager, monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Windows")
    data = _release(["baby-project-manager-linux", "BabyProjectManager.exe", "SHA256SUMS"])
    url = manager._find_asset_url(data)
    assert url.endswith("BabyProjectManager.exe")


def test_asset_picker_falls_back_to_release_page_when_no_binary(manager, monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Linux")
    data = _release(["SHA256SUMS", "notes.txt"])
    url = manager._find_asset_url(data)
    assert "releases/latest" in url
