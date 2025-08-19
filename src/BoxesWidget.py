"""Widget for cropping images with bounding rectangles."""

import random
from pathlib import Path

from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtGui import (
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
)

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
        self.box_current_rect = QRect()
        self.current_box_color = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.StartBox(event)
        super().mousePressEvent(event)

    def StartBox(self, event: QMouseEvent) -> None:
        self.drawing_box = True
        self.box_start_point = self.ClampPoint(event.position().toPoint())
        self.box_current_rect = QRect(self.box_start_point, QSize())

        # Pick a random unused color
        if not self.available_colors:
            self.available_colors = list(AVAILABLE_COLORS)
        self.current_box_color = random.choice(self.available_colors)
        self.available_colors.remove(self.current_box_color)
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        if self.drawing_box:
            self.box_current_rect = QRect(self.box_start_point, pos).normalized()
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.drawing_box:
            self.FinishBox()
        super().mouseReleaseEvent(event)

    def FinishBox(self) -> None:
        self.drawing_box = False

        # Only add box if it has size
        if self.box_current_rect.width() > 0 and self.box_current_rect.height() > 0:
            # Convert to image coordinates
            start = self.ScaleToImage(self.box_current_rect.topLeft())
            end = self.ScaleToImage(self.box_current_rect.bottomRight())
            rect = QRect(start, end).normalized()

            # Create rectangle in image coordinates
            poly = Polygon.FromRect(rect, self.current_box_color)
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
                painter.setPen(QPen(self.current_box_color, 2))
                painter.drawRect(self.box_current_rect)
