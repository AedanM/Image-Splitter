"""Base module for image widget."""

from pathlib import Path

from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QImage,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPixmap,
    QResizeEvent,
    QWheelEvent,
)
from PyQt6.QtWidgets import QInputDialog, QWidget

from .Components import Polygon
from .Utility import GetImageFiles, ThrowNotImplemented

AVAILABLE_COLORS = [
    # reserve for bounds QColor("red"),
    QColor("green"),
    # reserve for grid QColor("blue"),
    QColor("yellow"),
    QColor("magenta"),
    QColor("cyan"),
    QColor("orange"),
    QColor("purple"),
]


class ImageWidget(QWidget):
    """Base image widget."""

    def __init__(
        self,
        image_path: Path | None = None,
        polygons: list[Polygon] | None = None,
    ) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.pixmap: QPixmap = QPixmap()
        self.scaled_pixmap: QPixmap = QPixmap()
        self.image_path: Path | None = image_path
        self.last_path: Path | None = None
        self.image_loaded: bool = False
        self.available_colors: list[QColor] = list(AVAILABLE_COLORS)
        self.offset: QPoint = QPoint()
        self.baseScale: float = 1.0
        self.zoom: float = 1.0
        self.panning: bool = False
        self.panPoint: QPoint = QPoint()
        self.previewLines: bool = True

        self.saveBounds: list[Polygon] = [] if polygons is None else polygons
        if isinstance(image_path, Path):
            self.LoadImage(str(self.image_path))

    # region ScalingControls
    def UpdateScaling(self) -> None:
        if self.pixmap.width() == 0 or self.pixmap.height() == 0:
            return
        w, h = self.width(), self.height()
        fit_scale: float = min(w / self.pixmap.width(), h / self.pixmap.height())
        self.baseScale = fit_scale

        scale: float = self.baseScale * self.zoom

        sw, sh = int(self.pixmap.width() * scale), int(self.pixmap.height() * scale)
        self.scaled_pixmap = self.pixmap.scaled(sw, sh, Qt.AspectRatioMode.KeepAspectRatio)
        if not self.panning:
            self.offset = QPoint((w - sw) // 2, (h - sh) // 2)

    def ScaleToImage(self, display_point: QPoint) -> QPoint:
        inv = 1 / (self.baseScale * self.zoom)
        x = max(int((display_point.x() - self.offset.x()) * inv), 0)
        y = max(int((display_point.y() - self.offset.y()) * inv), 0)
        return QPoint(x, y)

    def ScaleToDisplay(self, display_point: QPoint) -> QPoint:
        scale = self.baseScale * self.zoom
        x = int(display_point.x() * scale) + self.offset.x()
        y = int(display_point.y() * scale) + self.offset.y()
        return QPoint(x, y)

    def ScaleRectToDisplay(self, img_rect: QRect) -> QRect:
        scale = self.baseScale * self.zoom
        x = int(img_rect.x() * scale) + self.offset.x()
        y = int(img_rect.y() * scale) + self.offset.y()
        w = int(img_rect.width() * scale)
        h = int(img_rect.height() * scale)
        return QRect(x, y, w, h)

    # endregion

    # region EventHandlers
    # region MouseEvents
    def mousePressEvent(self, event: QMouseEvent) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        if event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.panPoint = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        pos = event.position().toPoint()
        if self.panning:
            delta = pos - self.panPoint
            self.offset += delta
            self.panPoint = pos
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        if self.panning and event.button() == Qt.MouseButton.MiddleButton:
            self.panning = False

    def wheelEvent(self, event: QWheelEvent) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        delta = event.angleDelta().y()
        factor = 1.25 if delta > 0 else 0.8
        old_pos = event.position().toPoint()
        rel = old_pos - self.offset
        self.zoom *= factor
        self.UpdateScaling()
        new_rel = QPoint(int(rel.x() * factor), int(rel.y() * factor))
        self.offset = old_pos - new_rel
        self.update()

    # endregion
    def paintEvent(self, _event: QPaintEvent) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(45, 45, 45))

        if self.scaled_pixmap:
            painter.drawPixmap(self.offset, self.scaled_pixmap)

    def resizeEvent(self, event: QResizeEvent) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        super().resizeEvent(event)
        if self.pixmap:
            self.UpdateScaling()
            self.update()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        if mimeData := event.mimeData():
            if mimeData.hasUrls():
                event.acceptProposedAction()
            else:
                event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        urls: list = []
        if mimeData := event.mimeData():
            urls = mimeData.urls()
        if urls:
            self.LoadImage(urls[0].toLocalFile())

    # endregion

    # region Utility
    def Rename(self) -> None:
        if self.image_path:
            text, ok = QInputDialog.getText(
                self,
                "Enter New Name",
                self.image_path.name,
                text=self.image_path.stem,
            )

            if ok and text:
                dst = self.image_path.parent / f"{text}{self.image_path.suffix}"
                self.image_path.rename(dst)
                self.LoadNext(self.image_path)

    def sizeHint(self) -> QSize:
        if self.scaled_pixmap:
            return self.scaled_pixmap.size()
        return super().sizeHint()

    def reset(self, preservePolygons: bool = False) -> None:
        self.zoom = 1.0
        self.baseScale = 1.0
        self.offset = QPoint()
        if not preservePolygons:
            self.saveBounds = []
        self.UpdateScaling()
        self.update()

    def update(self) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        super().update()

    def ClampPoint(self, point: QPoint) -> QPoint:
        # Clamp point to image display bounds
        if self.scaled_pixmap is None:
            return QPoint(0, 0)

        x = min(
            max(point.x(), self.offset.x()),
            self.offset.x() + self.scaled_pixmap.width(),
        )
        y = min(
            max(point.y(), self.offset.y()),
            self.offset.y() + self.scaled_pixmap.height(),
        )
        return QPoint(x, y)

    # endregion

    def LoadImage(self, path: str | Path, keepPolygons: bool = False) -> None:
        file = Path(path)
        if not file.is_file():
            return
        if self.image_path != path and self.image_path is not None:
            self.last_path = self.image_path
        self.image_path = file
        self.pixmap = QPixmap(str(file))
        if self.pixmap.width() * self.pixmap.height() == 0:
            return

        self.available_colors = list(AVAILABLE_COLORS)
        self.zoom = 1.0
        self.offset = QPoint()
        self.image_loaded = True
        if (
            self.parent() is not None
            and hasattr(self.parent(), "imageLabel")
            and self.image_path is not None
        ):
            files = GetImageFiles(self.image_path.parent)
            idx = files.index(self.image_path) + 1

            self.parent().imageLabel.setText(f"{self.image_path.name} ({idx}/{len(files)})")  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
        if not keepPolygons:
            self.saveBounds = []
        self.UpdateScaling()
        self.update()

    def SaveSections(self, createSubdir: bool) -> None:
        if self.image_path is None or not self.image_path.exists():
            return
        qImage = QImage(str(self.image_path))
        if qImage.isNull():
            return
        if self.saveBounds == []:
            return

        dst: Path = (
            (self.image_path.parent / self.image_path.stem)
            if createSubdir
            else self.image_path.parent
        )
        dst.mkdir(exist_ok=True)
        # Save each rectangle as a separate image
        for idx, poly in enumerate(self.saveBounds, start=1):
            rect = poly.bounding_rect
            if rect.width() > 0 and rect.height() > 0:
                cropped = qImage.copy(rect)
                output_path = dst / f"{self.image_path.stem} {idx:03d}.png"
                cropped.save(str(output_path))

    def AddGrid(self, _vert: int, _horz: int) -> None:
        ThrowNotImplemented(self)

    def Trim(self) -> None:
        ThrowNotImplemented(self)

    def AutoDraw(self) -> None:
        ThrowNotImplemented(self)

    def Crop(self) -> None:
        ThrowNotImplemented(self)

    def RemoveLast(self) -> None:
        if self.saveBounds:
            self.saveBounds.pop()

    def RemovePolygon(self, poly: Polygon) -> None:
        if poly in self.saveBounds:
            self.saveBounds.remove(poly)
        self.update()

    def LoadNext(self, p: Path | None, reverse: bool = False, keepPolygons: bool = False) -> None:
        if p is None:
            return
        files = GetImageFiles(p.parent)
        idx = -10
        if p.exists():
            idx = files.index(p)
        elif p.parent.exists():
            position = [x for x in files if x > p]
            idx = files.index(position[0]) - 1 if position else -1
        if idx >= -1:
            if idx + 1 < len(files) and reverse is False:
                self.LoadImage(str(files[idx + 1]), keepPolygons=keepPolygons)
            elif idx - 1 >= 0 and reverse is True:
                self.LoadImage(str(files[idx - 1]), keepPolygons=keepPolygons)
            elif idx + 1 >= len(files):
                self.LoadImage(str(files[0]), keepPolygons=keepPolygons)
            elif idx - 1 < 0:
                self.LoadImage(str(files[len(files) - 1]), keepPolygons=keepPolygons)

    @property
    def isFullyCovered(self) -> bool:
        return False
