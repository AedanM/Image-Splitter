"""Widget for cropping images with bounding rectangles."""

import contextlib
import random
from pathlib import Path

import send2trash
from PIL import Image
from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPaintEvent, QPen, QRegion

from src.AutoDraw import SliceImage
from src.Components import Polygon
from src.ImageWidget import AVAILABLE_COLORS, ImageWidget

from .LineCalcs import DetermineBoundary


class BoxWidget(ImageWidget):
    """Box drawing image widget."""

    def __init__(
        self,
        image_path: Path | None = None,
        polygons: list[Polygon] | None = None,
    ) -> None:
        super().__init__(image_path, polygons)

        # Box drawing state
        self.drawing_box = False
        self.box_start_point = QPoint()
        self.currentRect = QRect()
        self.currentColor: QColor = QColor("blue")

    def FinishBox(self) -> None:
        self.drawing_box = False

        # Only add box if it has size
        if self.currentRect.width() > 0 and self.currentRect.height() > 0:
            # Convert to image coordinates
            start = self.ScaleToImage(self.currentRect.topLeft())
            end = self.ScaleToImage(self.currentRect.bottomRight())
            rect = QRect(start, end).normalized()

            # Create rectangle in image coordinates
            poly = Polygon.FromRect(rect, self.currentColor)
            poly.BindTo(width=self.pixmap.width(), height=self.pixmap.height())
            self.saveBounds.append(poly)

        self.update()

    def StartBox(self, event: QMouseEvent) -> None:
        self.drawing_box = True
        self.box_start_point = self.ClampPoint(event.position().toPoint())
        self.currentRect = QRect(self.box_start_point, QSize())

        # Pick a random unused color
        if not self.available_colors:
            self.available_colors = list(AVAILABLE_COLORS)
        self.currentColor = random.choice(self.available_colors)
        self.available_colors.remove(self.currentColor)
        self.update()

    # region EventHandlers
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.StartBox(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        if self.drawing_box:
            self.currentRect = QRect(self.box_start_point, pos).normalized()
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.drawing_box:
            self.FinishBox()
        super().mouseReleaseEvent(event)

    def paintEvent(self, _event: QPaintEvent) -> None:
        super().paintEvent(_event)
        painter = QPainter(self)

        if self.scaled_pixmap:
            # Draw completed rectangles
            for poly in self.saveBounds:
                display_rect = self.ScaleRectToDisplay(poly.bounding_rect)
                painter.setPen(QPen(poly.Color, 2))
                painter.drawRect(display_rect)

            # Draw current box being drawn
            if self.drawing_box:
                painter.setPen(QPen(self.currentColor, 2))
                painter.drawRect(self.currentRect)

    # endregion
    # region Overloads
    def AddGrid(self, vert: int, horz: int) -> None:
        vertSpacing = round(self.pixmap.width() / vert)
        horzSpacing = round(self.pixmap.height() / horz)
        for horzIdx in range(horz):
            for vertIdx in range(vert):
                p1_x = max(0, vertIdx * vertSpacing)
                p1_y = max(0, horzIdx * horzSpacing)
                self.saveBounds.append(
                    Polygon.FromRect(
                        QRect(QPoint(p1_x, p1_y), QSize(vertSpacing, horzSpacing)),
                        QColor("blue"),
                    ),
                )

            self.update()

    @property
    def isFullyCovered(self) -> bool:
        """Return True if the saved rectangular polygons cover the entire image."""
        if (
            not self.pixmap
            or self.pixmap.width() == 0
            or self.pixmap.height() == 0
            or not self.saveBounds
        ):
            return False

        img_rect = QRect(0, 0, self.pixmap.width(), self.pixmap.height())
        region = QRegion()
        for poly in self.saveBounds:
            rect = getattr(poly, "bounding_rect", None)
            if rect and rect.isValid():
                region = region.united(QRegion(rect))
        return region.boundingRect() == img_rect

    def Trim(self, padding: int) -> None:
        if self.image_path is not None:
            for poly in self.saveBounds:
                with contextlib.suppress(IndexError):
                    if poly.isRectangle:
                        corners = poly.bounding_points
                        if corners is None or None in corners:
                            print("Invalid bounding points for trimming.")
                            continue
                        poly.Points = DetermineBoundary(
                            self.image_obj,
                            corners,
                            padding,
                        )
        self.update()

    def AutoDraw(self) -> None:
        if self.image_path:
            self.saveBounds.extend(SliceImage(self.image_obj))

    def Crop(self, keepBounds: bool = False) -> None:
        if self.image_path and len(self.saveBounds) == 1:
            bounds = self.saveBounds if keepBounds else []
            poly = self.saveBounds[0].bounding_points
            im = self.image_obj.crop(poly)
            send2trash.send2trash(self.image_path)
            im.save(self.image_path)
            self.LoadImage(self.image_path)
            self.saveBounds = bounds
        self.update()

    @property
    def ReadyToCrop(self) -> bool:
        return len(self.saveBounds) == 1

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
        if self.saveBounds:
            self.LoadImage(dst / f"{self.image_path.stem} 001.png")

    # endregion
