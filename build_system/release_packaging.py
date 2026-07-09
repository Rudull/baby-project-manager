#!/usr/bin/env python3
"""
Shared release packaging for one-directory (folder) builds.

A onedir build is a whole folder — the launcher plus its DLLs/shared objects, Qt
plugins and bundled data. To ship it (and to let the in-app auto-updater apply
it), that folder must be published as a single archive. The updater
(``src/updater/update_manager.py``) selects a release asset purely by extension:

* Windows       -> ``.zip``
* Linux / macOS -> ``.tar.gz``  (tarballs preserve the executable bit and the
                                 symlinks that a .zip would silently drop)

On download it extracts the archive and replaces the install folder wholesale.
Because its ``_normalize_extracted_root`` descends into a single wrapping
directory, every archive here is built with one stable top-level folder
(:data:`BUNDLE_TOP`) regardless of what the builder named its output.

This module is imported by the per-platform build scripts and depends only on
the standard library.
"""
from __future__ import annotations

import hashlib
import platform
import re
import tarfile
import zipfile
from pathlib import Path

# Stable top-level directory name inside every archive. Nuitka emits
# ``main.dist`` / ``baby_project_manager.dist``; normalising to one name keeps
# downloads predictable for both the updater and anyone extracting by hand.
BUNDLE_TOP = "baby_project_manager"

# One-directory bundle folder names produced by the supported builders.
_ONEDIR_CANDIDATES = ("baby_project_manager.dist", "main.dist", "baby_project_manager")


def read_version(project_root: Path) -> str:
    """Read ``__version__`` from ``src/version.py`` (the single source of truth)."""
    version_file = Path(project_root) / "src" / "version.py"
    text = version_file.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)
    if not match:
        raise ValueError(f"Could not find __version__ in {version_file}")
    return match.group(1)


def _holds_executable(folder: Path) -> bool:
    return (folder / "baby_project_manager").exists() or \
           (folder / "baby_project_manager.exe").exists()


def find_onedir_folder(dist_dir: Path) -> Path | None:
    """Return the one-directory bundle folder inside ``dist_dir``, or ``None``.

    A one-file build leaves a *file* named ``baby_project_manager`` here; the
    ``is_dir`` check skips it so packaging safely no-ops on onefile output.
    """
    dist_dir = Path(dist_dir)
    for name in _ONEDIR_CANDIDATES:
        candidate = dist_dir / name
        if candidate.is_dir() and _holds_executable(candidate):
            return candidate
    return None


def _arch_tag() -> str:
    machine = platform.machine().lower()
    return {
        "amd64": "x64", "x86_64": "x64",
        "aarch64": "arm64", "arm64": "arm64",
    }.get(machine, machine or "x64")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _make_zip(source: Path, archive: Path) -> None:
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                arcname = f"{BUNDLE_TOP}/{path.relative_to(source).as_posix()}"
                zf.write(path, arcname=arcname)


def _make_targz(source: Path, archive: Path) -> None:
    # tarfile.add recurses and preserves permissions and symlinks.
    with tarfile.open(archive, "w:gz") as tf:
        tf.add(source, arcname=BUNDLE_TOP)


def package_onedir(dist_dir: Path, project_root: Path, *,
                   archive_format: str | None = None,
                   os_label: str | None = None) -> Path | None:
    """Archive the onedir bundle found in ``dist_dir`` for release.

    ``archive_format`` (``"zip"`` / ``"tar.gz"``) and ``os_label``
    (``"windows"`` / ``"linux"`` / ``"macos"``) default to the host platform,
    which is what these on-target builds want. The archive is written next to
    the bundle as ``baby-project-manager-<version>-<os>-<arch>.<ext>`` with a
    matching ``.sha256`` sidecar, and its path is returned (``None`` if no
    onedir bundle is present).
    """
    dist_dir = Path(dist_dir)
    source = find_onedir_folder(dist_dir)
    if source is None:
        print(f"[!] Packaging skipped: no one-directory bundle found in {dist_dir}")
        return None

    system = platform.system()
    if os_label is None:
        os_label = {"Windows": "windows", "Darwin": "macos"}.get(system, "linux")
    if archive_format is None:
        archive_format = "zip" if system == "Windows" else "tar.gz"

    version = read_version(project_root)
    stem = f"baby-project-manager-{version}-{os_label}-{_arch_tag()}"

    if archive_format == "zip":
        archive = dist_dir / f"{stem}.zip"
        builder = _make_zip
    elif archive_format == "tar.gz":
        archive = dist_dir / f"{stem}.tar.gz"
        builder = _make_targz
    else:
        raise ValueError(f"Unsupported archive_format: {archive_format!r}")

    if archive.exists():
        archive.unlink()

    print(f"[*] Packaging {source.name}/ -> {archive.name} ...")
    builder(source, archive)

    checksum = _sha256(archive)
    sidecar = archive.with_name(archive.name + ".sha256")
    sidecar.write_text(f"{checksum}  {archive.name}\n", encoding="utf-8")

    size_mb = archive.stat().st_size / (1024 * 1024)
    print(f"[OK] Release archive: {archive}")
    print(f"     Size:   {size_mb:.1f} MB")
    print(f"     SHA256: {checksum}")
    print("     Upload this archive as the GitHub Release asset for auto-update.")
    return archive
