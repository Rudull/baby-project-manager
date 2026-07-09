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


# --- Folder (onedir) archive assets ---------------------------------------

def test_asset_picker_windows_uses_zip_when_no_exe(manager, monkeypatch):
    monkeypatch.setattr("platform.system", lambda: "Windows")
    data = _release(["baby-project-manager-windows.zip", "SHA256SUMS"])
    url = manager._find_asset_url(data)
    assert url.endswith("baby-project-manager-windows.zip")


def test_asset_picker_prefers_single_exe_over_zip(manager, monkeypatch):
    # A onefile .exe wins over an archive so existing releases keep swapping fast.
    monkeypatch.setattr("platform.system", lambda: "Windows")
    data = _release(["BabyProjectManager.exe", "baby-project-manager-windows.zip"])
    url = manager._find_asset_url(data)
    assert url.endswith("BabyProjectManager.exe")


def test_asset_picker_linux_prefers_targz_over_zip(manager, monkeypatch):
    # Tarballs preserve the exec bit and symlinks; zip does not.
    monkeypatch.setattr("platform.system", lambda: "Linux")
    data = _release(["app-linux.zip", "app-linux.tar.gz", "SHA256SUMS"])
    url = manager._find_asset_url(data)
    assert url.endswith("app-linux.tar.gz")


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://example.com/app.zip", ".zip"),
        ("https://example.com/app.tar.gz", ".tar.gz"),
        ("https://example.com/app.tgz?token=abc", ".tgz"),
        ("https://example.com/BabyProjectManager.exe", None),
        ("https://github.com/x/y/releases/tag/v1", None),
        (None, None),
    ],
)
def test_url_archive_suffix(url, expected):
    assert UpdateManager._url_archive_suffix(url) == expected


# --- Safe extraction and root normalization -------------------------------

def test_safe_extract_zip_rejects_traversal(manager, tmp_path):
    import zipfile

    bad = tmp_path / "evil.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("../escape.txt", "pwned")

    dest = tmp_path / "out"
    dest.mkdir()
    with zipfile.ZipFile(bad) as zf:
        with pytest.raises(Exception, match="Unsafe path"):
            manager._safe_extract_zip(zf, dest)
    assert not (tmp_path / "escape.txt").exists()


def test_extract_zip_roundtrip(manager, tmp_path):
    import zipfile

    archive = tmp_path / "app.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("app/baby_project_manager", "binary")
        zf.writestr("app/lib/qt.so", "lib")

    dest = tmp_path / "staging"
    dest.mkdir()
    manager._extract_archive(archive, dest)
    assert (dest / "app" / "baby_project_manager").read_text() == "binary"
    assert (dest / "app" / "lib" / "qt.so").read_text() == "lib"


def test_normalize_root_descends_into_single_wrapper(manager, tmp_path):
    # The real archives wrap files in a folder named like the exe itself; the
    # wrapper directory must not be mistaken for the executable file at the top.
    wrapper = tmp_path / "baby_project_manager"
    wrapper.mkdir()
    (wrapper / "baby_project_manager").write_text("x")
    (wrapper / "lib.so").write_text("y")
    root = manager._normalize_extracted_root(tmp_path, "baby_project_manager")
    assert root == wrapper


def test_normalize_root_uses_staging_when_exe_at_top(manager, tmp_path):
    (tmp_path / "baby_project_manager").write_text("x")
    (tmp_path / "lib").mkdir()
    root = manager._normalize_extracted_root(tmp_path, "baby_project_manager")
    assert root == tmp_path
