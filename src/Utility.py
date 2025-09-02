"""Utility functions."""

import traceback
from pathlib import Path
from typing import Any

import winshell
from PyQt6.QtWidgets import QMessageBox, QWidget


def RestoreFromRecycle(parent: Any) -> None:
    files = sorted(winshell.recycle_bin(), key=lambda x: x.recycle_date())
    file = files[-1].original_filename()
    dlg = QMessageBox(parent)
    dlg.setWindowTitle("File Restored")
    dlg.setText(f"Restore {Path(file).name}?")
    dlg.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    btn = dlg.exec()
    if btn == QMessageBox.StandardButton.Yes:
        winshell.undelete(file)
        parent.imageViewer.LoadImage(file)


def GetImageFiles(p: Path) -> list[Path]:
    ALLOWED_EXTS = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]
    if p is None or not p.exists():
        return []
    files = sorted(
        [f for f in p.glob("*") if f.suffix.lower() in ALLOWED_EXTS],
    )
    return files


def ThrowNotImplemented(parent: QWidget) -> None:
    dlg = QMessageBox(parent)
    dlg.setWindowTitle("Not implemented")
    dlg.setText(f"{list(traceback.format_stack())[-2]} Not Implemented Yet")
    dlg.exec()
