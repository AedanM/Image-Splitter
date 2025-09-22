"""Widget for cropping images with bounding lines."""

import random
from pathlib import Path

import send2trash
from numpy import median
from PIL import Image
from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPaintEvent, QPen

from src.AutoDraw import SliceImage
from src.Components import Polygon
from src.ImageWidget import AVAILABLE_COLORS, ImageWidget
from src.LineCalcs import ExtendLines, TrimOrthoLines


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
        self.currentColor: QColor = QColor("blue")

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
                painter.setPen(QPen(self.currentColor, 2))
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
        self.currentColor = random.choice(self.available_colors)
        self.available_colors.remove(self.currentColor)
        self.update()

    def FinishLine(self) -> None:
        self.drawing_line = False

        # Only add line if start and end points are different
        if self.line_start_point != self.line_current_end_point:
            start = self.ScaleToImage(self.line_start_point)
            end = self.ScaleToImage(self.line_current_end_point)

            # FOR NOW snap to straight lines
            isVertical = abs(start.x() - end.x()) < abs(start.y() - end.y())
            if isVertical:
                medianX = round(median([start.x(), end.x()]))
                start.setX(medianX)
                end.setX(medianX)
            else:
                medianY = round(median([start.y(), end.y()]))
                start.setY(medianY)
                end.setY(medianY)

            # Create line in image coordinates
            line = Polygon([start, end], self.currentColor)
            line.BindTo(width=self.pixmap.width(), height=self.pixmap.height())
            self.saveBounds.append(line)

        self.update()

    # endregion

    def LoadImage(self, path: str | Path, keepPolygons: bool = False) -> None:
        super().LoadImage(path, keepPolygons)
        if not self.pixmap:
            return
        self.update()

    def PreviewLines(self, painter: QPainter) -> None:
        """Draw extended lines and boundary lines for visualization."""
        if not self.pixmap:
            return

        image_size = QSize(self.pixmap.width(), self.pixmap.height())

        for line in self.saveBounds:
            pen = QPen(line.Color, 3)
            painter.setPen(pen)
            extended_line = ExtendLines(line, image_size)
            if extended_line:
                display_start = self.ScaleToDisplay(extended_line.Points[0])
                display_end = self.ScaleToDisplay(extended_line.Points[1])
                painter.drawLine(display_start, display_end)

    def AddGrid(self, vert: int, horz: int) -> None:
        vertSpacing = round(self.pixmap.width() / vert)
        horzSpacing = round(self.pixmap.height() / horz)
        offset = 0
        for _ in range(horz + 1):
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
        offset = 0
        for _ in range(vert + 1):
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

    def AutoDraw(self) -> None:
        if self.image_path:
            self.saveBounds.extend(SliceImage(self.image_path, True))
        self.saveBounds = list(set(self.saveBounds))
        self.update()

    def Trim(self, padding: int) -> None:
        newBounds = self.saveBounds.copy()
        if self.image_path is not None:
            im = Image.open(self.image_path)
            newBounds = [
                Polygon(line, poly.Color)
                for poly in self.saveBounds
                for line in TrimOrthoLines(
                    poly.Points,
                    im.load(),
                    padding,
                    [self.pixmap.width(), self.pixmap.height()],
                )
            ]
        self.saveBounds = newBounds
        self.update()

    @property
    def ReadyToCrop(self) -> bool:
        return (
            len([x for x in self.saveBounds if x.isVerticalLine]) == 2
            or len([x for x in self.saveBounds if x.isHorizontalLine]) == 2
        )

    def Crop(self, keepBounds: bool = False) -> None:
        if not self.image_path or not self.saveBounds or not self.ReadyToCrop:
            return
        im = Image.open(self.image_path)
        width, height = im.size
        bounds = self.saveBounds if keepBounds else []

        xs = [pt.x() for poly in self.saveBounds for pt in poly.Points]
        ys = [pt.y() for poly in self.saveBounds for pt in poly.Points]

        min_x, max_x = max(0, min(xs)), min(width, max(xs))
        min_y, max_y = max(0, min(ys)), min(height, max(ys))

        cropped = im.crop((min_x, min_y, max_x, max_y))
        send2trash.send2trash(self.image_path)
        cropped.save(self.image_path)

        self.LoadImage(self.image_path)
        self.saveBounds = bounds
        self.update()

    def SaveSections(self, createSubdir: bool = False) -> None:
        if not self.image_path or not self.saveBounds:
            return
        im = Image.open(self.image_path)
        width, height = im.size
        edges = [
            Polygon([QPoint(0, 0), QPoint(0, height - 1)], QColor(Qt.GlobalColor.red)),
            Polygon([QPoint(0, 0), QPoint(width - 1, 0)], QColor(Qt.GlobalColor.red)),
            Polygon(
                [QPoint(0, height - 1), QPoint(width - 1, height - 1)],
                QColor(Qt.GlobalColor.red),
            ),
            Polygon(
                [QPoint(width - 1, 0), QPoint(width - 1, height - 1)],
                QColor(Qt.GlobalColor.red),
            ),
        ]

        for e in edges:
            if e.RawPoints not in [p.RawPoints for p in self.saveBounds]:
                self.saveBounds.append(e)

        verts = [poly.Points[0].x() for poly in self.saveBounds if poly.isVerticalLine]
        horz = [poly.Points[0].y() for poly in self.saveBounds if poly.isHorizontalLine]
        if len(verts) < 2 and len(horz) < 2:
            return

        dst: Path = (
            (self.image_path.parent / self.image_path.stem)
            if createSubdir
            else self.image_path.parent
        )
        dst.mkdir(exist_ok=True)
        qImage = QImage(str(self.image_path))
        for vertIdx in range(len(verts) - 1):
            for horIdx in range(len(horz) - 1):
                startX, startY = verts[vertIdx], horz[horIdx]
                endX, endY = verts[vertIdx + 1], horz[horIdx + 1]
                if startX == endX or startY == endY:
                    continue
                rect = QRect(startX, startY, endX - startX, endY - startY)
                if rect.width() > 0 and rect.height() > 0:
                    cropped = qImage.copy(rect)

                    # check if entire section is equal to first pixel
                    first_pixel = cropped.pixel(0, 0)
                    all_same = True
                    for y in range(cropped.height()):
                        for x in range(cropped.width()):
                            if cropped.pixel(x, y) != first_pixel:
                                all_same = False
                                break
                        if not all_same:
                            break
                    if all_same:
                        continue  # all pixels are the same, skip saving

                    cropped = qImage.copy(rect)
                    cropped.save(
                        str(
                            dst / f"{self.image_path.stem} "
                            f"{vertIdx + 1:02d}_y{horIdx + 1:02d}"
                            f"{self.image_path.suffix}",
                        ),
                    )
