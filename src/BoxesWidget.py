"""Widget for cropping images with bounding rectangles."""

import random
from pathlib import Path

from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen

from src.Components import Polygon
from src.ImageWidget import AVAILABLE_COLORS, ImageWidget


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
        self.currentColor = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.StartBox(event)
        super().mousePressEvent(event)

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
