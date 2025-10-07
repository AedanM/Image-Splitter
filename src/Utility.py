"""Utility functions."""

import logging
import os
import traceback
from collections import OrderedDict
from pathlib import Path
from typing import Any

import winshell
from PyQt6.QtWidgets import QMessageBox, QWidget


def RestoreFromRecycle(parent: Any) -> None:
    files = sorted(winshell.recycle_bin(), key=lambda x: x.recycle_date())  # pyright: ignore[reportAttributeAccessIssue]
    file = files[-1].original_filename()  # pyright: ignore[reportAttributeAccessIssue]
    dlg = QMessageBox(parent)
    dlg.setWindowTitle("File Restored")
    dlg.setText(f"Restore {Path(file).name}?")
    dlg.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    btn = dlg.exec()
    if btn == QMessageBox.StandardButton.Yes:
        if Path(file).exists():
            Path(file).rename(
                Path(file).parent / ((Path(file).stem + " (edited)") + Path(file).suffix),
            )
        file = files[-1].original_filename()  # pyright: ignore[reportAttributeAccessIssue]
        winshell.undelete(file)
        parent.ImageViewer.LoadImage(file)


ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}

# simple module-level LRU cache for directory listings
DIR_FILES_CACHE: OrderedDict[str, tuple[list[Path], float | None]] = OrderedDict()
DIR_FILES_CACHE_MAX = 1024


def GetImageFiles(p: Path, use_cache: bool = True) -> list[Path]:
    """Return sorted image files in directory `p`.

    Uses `os.scandir` for speed and a small LRU cache keyed by directory
    modification time (mtime). If `use_cache` is False the directory will be
    scanned unconditionally.
    """
    if p is None or not p.exists():
        return []

    dir_key = str(p)

    try:
        mtime = p.stat().st_mtime
    except Exception:
        logging.exception("Failed to stat directory %s", p)
        mtime = None

    # return cached value early when mtime matches
    if use_cache:
        cached = DIR_FILES_CACHE.get(dir_key)
        if cached and cached[1] == mtime:
            DIR_FILES_CACHE.pop(dir_key)
            DIR_FILES_CACHE[dir_key] = cached
            return list(cached[0])

    files = ScanDir(p)

    if use_cache:
        UpdateDirCache(dir_key, files, mtime)

    return files


def ScanDir(p: Path) -> list[Path]:
    """Scan directory `p` and return sorted image Path list."""
    files: list[Path] = []
    try:
        with os.scandir(p) as it:
            for entry in it:
                try:
                    if not entry.is_file():
                        continue
                except Exception as exc:  # pragma: no cover - defensive
                    logging.debug("Skipping entry in %s: %s", p, exc)
                    continue
                entry_path = Path(entry.path)
                if entry_path.suffix.lower() in ALLOWED_EXTS:
                    files.append(entry_path)
    except Exception:
        logging.exception("Failed to scandir %s", p)

    files.sort()
    return files


def UpdateDirCache(dir_key: str, files: list[Path], mtime: float | None) -> None:
    """Safely update the module-level directory listing cache."""
    try:
        DIR_FILES_CACHE[dir_key] = (list(files), mtime)
        if len(DIR_FILES_CACHE) > DIR_FILES_CACHE_MAX:
            DIR_FILES_CACHE.popitem(last=False)
    except Exception:
        logging.exception("Failed to update dir cache for %s", dir_key)


def ThrowNotImplemented(parent: QWidget) -> None:
    dlg = QMessageBox(parent)
    dlg.setWindowTitle("Not implemented")
    dlg.setText(f"{list(traceback.format_stack())[-2]} Not Implemented Yet")
    dlg.exec()
