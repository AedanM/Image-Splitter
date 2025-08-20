"""Widget for cropping images with bounding lines."""

import random
from pathlib import Path

from PyQt6.QtCore import QPoint, QSize, Qt
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen

from src.Components import Polygon
from src.ImageWidget import AVAILABLE_COLORS, ImageWidget
from src.LineCalcs import ExtendLines


class LineWidget(ImageWidget):
    """Line drawing image widget."""

    def __init__(
        self,
        image_path: Path | None = None,
        polygons: list[Polygon] | None = None,
    ) -> None:
        super().__init__(image_path, polygons)

        # line drawing state
        self.drawing_line = False
        self.line_start_point = QPoint()
        self.line_current_end_point = QPoint()
        self.current_line_color = None

    # region EventHandlers
    # region MouseEvents
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.StartLine(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        if self.drawing_line:
            self.line_current_end_point = self.ClampPoint(pos)
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.drawing_line:
            self.FinishLine()
        super().mouseReleaseEvent(event)

    # endregion

    def paintEvent(self, _event: QPaintEvent) -> None:
        super().paintEvent(_event)
        painter = QPainter(self)

        if self.scaled_pixmap:
            # Draw completed lines
            for line in self.saveBounds:
                display_start = self.ScaleToDisplay(line.Points[0])
                display_end = self.ScaleToDisplay(line.Points[-1])
                painter.setPen(QPen(line.Color, 2))
                painter.drawLine(display_start, display_end)

            # Draw current line being drawn
            if self.drawing_line:
                painter.setPen(QPen(self.current_line_color, 2))
                painter.drawLine(self.line_start_point, self.line_current_end_point)

            if self.previewLines and self.saveBounds:
                self.PreviewLines(painter)

    # endregion

    # region Drawing
    def StartLine(self, event: QMouseEvent) -> None:
        self.drawing_line = True
        self.line_start_point = self.ClampPoint(event.position().toPoint())
        self.line_current_end_point = self.line_start_point

        # Pick a random unused color
        if not self.available_colors:
            self.available_colors = list(AVAILABLE_COLORS)
        self.current_line_color = random.choice(self.available_colors)
        self.available_colors.remove(self.current_line_color)
        self.update()

    def FinishLine(self) -> None:
        self.drawing_line = False

        # Only add line if start and end points are different
        if self.line_start_point != self.line_current_end_point:
            # Convert to image coordinates
            start = self.ScaleToImage(self.line_start_point)
            end = self.ScaleToImage(self.line_current_end_point)
            # Create line in image coordinates
            line = Polygon([start, end], self.current_line_color)
            self.saveBounds.append(line)

        self.update()

    # endregion

    def LoadImage(self, path: str) -> None:
        super().LoadImage(path)
        if not self.pixmap:
            return

        image_size = QSize(self.pixmap.width(), self.pixmap.height())
        self.saveBounds = list(
            {
                *self.saveBounds,
                Polygon([QPoint(0, 0), QPoint(image_size.width(), 0)], QColor("red")),
                Polygon(
                    [
                        QPoint(image_size.width(), 0),
                        QPoint(image_size.width(), image_size.height()),
                    ],
                    QColor("red"),
                ),
                Polygon(
                    [
                        QPoint(image_size.width(), image_size.height()),
                        QPoint(0, image_size.height()),
                    ],
                    QColor("red"),
                ),
                Polygon([QPoint(0, image_size.height()), QPoint(0, 0)], QColor("red")),
            },
        )

    def PreviewLines(self, painter: QPainter) -> None:
        """Draw extended lines and boundary lines for visualization."""
        if not self.pixmap:
            return

        image_size = QSize(self.pixmap.width(), self.pixmap.height())

        for line in self.saveBounds:
            pen = QPen(line.Color, 5, Qt.PenStyle.DotLine)
            painter.setPen(pen)
            extended_line = ExtendLines(line, image_size)
            if extended_line:
                display_start = self.ScaleToDisplay(extended_line.Points[0])
                display_end = self.ScaleToDisplay(extended_line.Points[1])
                painter.drawLine(display_start, display_end)

    def SaveSections(self, createSubdir: bool) -> None:
        super().SaveSections(createSubdir)

    def AddGrid(self, vert: int, horz: int) -> None:
        vertSpacing = round(self.pixmap.width() / vert)
        horzSpacing = round(self.pixmap.height() / horz)
        offset = horzSpacing
        for _ in range(horz - 1):
            self.saveBounds.append(
                Polygon(
                    [
                        QPoint(0, offset),
                        QPoint(self.pixmap.width(), offset),
                    ],
                    QColor("blue"),
                ),
            )
            offset += horzSpacing
        offset = vertSpacing
        for _ in range(vert - 1):
            self.saveBounds.append(
                Polygon(
                    [
                        QPoint(offset, 0),
                        QPoint(offset, self.pixmap.height()),
                    ],
                    QColor("blue"),
                ),
            )
            offset += vertSpacing
        self.update()
