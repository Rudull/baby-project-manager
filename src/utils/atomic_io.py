"""atomic_io.py
Helpers for writing files atomically.

A direct ``open(path, "w")`` truncates the target the moment it is opened, so a
crash, power loss, or full disk midway through the write leaves the user with a
truncated, unrecoverable file. Writing to a temporary file in the same
directory and then ``os.replace``-ing it into place makes the update atomic:
the file at ``path`` is either the complete old version or the complete new
version, never a half-written mix.
"""
from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TextIO


@contextmanager
def atomic_write(path: str | Path, encoding: str = "utf-8") -> Iterator[TextIO]:
    """Yield a text handle whose contents replace ``path`` atomically on success.

    The data is written to a temporary file in the same directory (so the final
    ``os.replace`` stays on one filesystem and is therefore atomic), flushed and
    ``fsync``-ed, then moved into place. If the body raises, the temporary file
    is removed and the original ``path`` is left untouched.
    """
    path = Path(path)
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(dir=directory, prefix=f".{path.name}.", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as tmp_file:
            yield tmp_file
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise
