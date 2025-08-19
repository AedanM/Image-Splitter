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
from PyQt6.QtWidgets import QWidget

from .Components import Polygon

AVAILABLE_COLORS = [
    QColor("red"),
    QColor("green"),
    QColor("blue"),
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
        self.pixmap: QPixmap = None
        self.scaled_pixmap: QPixmap = None
        self.image_path: Path | None = image_path
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

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls:
            self.LoadImage(urls[0].toLocalFile())

    def LoadImage(self, path: str) -> None:
        file = Path(path)
        if not file.is_file():
            return
        self.pixmap = None
        self.image_path = file
        self.pixmap = QPixmap(str(file))
        if self.pixmap.width() * self.pixmap.height() == 0:
            return

        self.available_colors = list(AVAILABLE_COLORS)
        self.zoom = 1.0
        self.offset = QPoint()
        self.image_loaded = True

        self.UpdateScaling()
        self.update()

    def RemoveLast(self) -> None:
        if self.saveBounds:
            self.saveBounds.pop()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self.pixmap:
            self.UpdateScaling()
            self.update()

    def UpdateScaling(self) -> None:
        if not self.pixmap:
            return
        w, h = self.width(), self.height()
        fit_scale: int = min(w / self.pixmap.width(), h / self.pixmap.height())
        self.baseScale = fit_scale

        scale: float = self.baseScale * self.zoom

        sw, sh = int(self.pixmap.width() * scale), int(self.pixmap.height() * scale)
        self.scaled_pixmap = self.pixmap.scaled(sw, sh, Qt.AspectRatioMode.KeepAspectRatio)
        if not self.panning:
            self.offset = QPoint((w - sw) // 2, (h - sh) // 2)

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

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.panPoint = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        if self.panning:
            delta = pos - self.panPoint
            self.offset += delta
            self.panPoint = pos
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.panning and event.button() == Qt.MouseButton.MiddleButton:
            self.panning = False

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        factor = 1.25 if delta > 0 else 0.8
        old_pos = event.position().toPoint()
        rel = old_pos - self.offset
        self.zoom *= factor
        self.UpdateScaling()
        new_rel = QPoint(int(rel.x() * factor), int(rel.y() * factor))
        self.offset = old_pos - new_rel
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(45, 45, 45))

        if self.scaled_pixmap:
            painter.drawPixmap(self.offset, self.scaled_pixmap)

    def sizeHint(self) -> QSize:
        if self.scaled_pixmap:
            return self.scaled_pixmap.size()
        return super().sizeHint()

    def reset(self) -> None:
        self.zoom = 1.0
        self.baseScale = 1.0
        self.offset = QPoint()
        self.saveBounds = []
        self.UpdateScaling()
        self.update()

    def SaveSections(self, createSubdir: bool) -> None:
        if self.image_path is None or not self.image_path.exists():
            return
        qImage = QImage(str(self.image_path))
        if qImage.isNull():
            print(f"Failed to load image: {self.image_path}")
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
                print(f"Saved box {idx} to: {output_path}")
