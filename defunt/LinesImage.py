import random
from pathlib import Path

from PyQt6.QtCore import QPoint, QSize
from PyQt6.QtGui import QColor, QImage, QImageReader, QRect
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from LineSplitter import LineSplitter
from src.Components import Line, Rectangle


class ImageWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.pixmap = None
        self.scaled_pixmap = None
        self.image_path = None

        self.mode = "line"

        # Store lines and rectangles
        self.lines: list[Line] = []
        self.rectangles: list[Rectangle] = []

        self.available_colors = [
            QColor("red"),
            QColor("green"),
            QColor("blue"),
            QColor("yellow"),
            QColor("magenta"),
            QColor("cyan"),
            QColor("orange"),
            QColor("purple"),
        ]

        # Line drawing state
        self.drawing_line = False
        self.line_start_point = QPoint()
        self.line_current_end_point = QPoint()
        self.current_line_color = None

        # Box drawing state
        self.drawing_box = False
        self.box_start_point = QPoint()
        self.box_current_rect = QRect()
        self.current_box_color = None

        # Navigation state
        self.offset = QPoint()
        self.base_scale = 1.0
        self.zoom_factor = 1.0
        self.panning = False
        self.pan_start = QPoint()
        self.show_extended_lines = True

    def set_mode(self, mode: str):
        """Set the drawing mode: 'line' or 'box'"""
        self.mode = mode
        self.update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            self.load_image(urls[0].toLocalFile())

    def load_image(self, path):
        file = Path(path)
        if not file.is_file():
            return
        self.pixmap = None
        self.image_path = file
        self.pixmap = QPixmap(str(file))
        if self.pixmap.width() * self.pixmap.height() == 0:
            return
        self.lines.clear()
        self.rectangles.clear()
        self.available_colors = [
            QColor("red"),
            QColor("green"),
            QColor("blue"),
            QColor("yellow"),
            QColor("magenta"),
            QColor("cyan"),
            QColor("orange"),
            QColor("purple"),
        ]
        self.zoom_factor = 1.0
        self.offset = QPoint()
        self._update_scaled()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.pixmap:
            self._update_scaled()
            self.update()

    def _update_scaled(self):
        w, h = self.width(), self.height()
        if not self.pixmap:
            return
        fit_scale = min(w / self.pixmap.width(), h / self.pixmap.height())
        self.base_scale = fit_scale
        scale = self.base_scale * self.zoom_factor
        sw, sh = int(self.pixmap.width() * scale), int(self.pixmap.height() * scale)
        self.scaled_pixmap = self.pixmap.scaled(sw, sh, Qt.AspectRatioMode.KeepAspectRatio)
        if not self.panning:
            self.offset = QPoint((w - sw) // 2, (h - sh) // 2)

    def _clamp_point_to_image(self, point: QPoint) -> QPoint:
        # Clamp point to image display bounds
        x = min(
            max(point.x(), self.offset.x()),
            self.offset.x() + self.scaled_pixmap.width(),  # type: ignore[reportOptionalMemberAccess]
        )
        y = min(
            max(point.y(), self.offset.y()),
            self.offset.y() + self.scaled_pixmap.height(),  # type: ignore[reportOptionalMemberAccess]
        )
        return QPoint(x, y)

    def _display_to_image(self, display_point: QPoint) -> QPoint:
        inv = 1 / (self.base_scale * self.zoom_factor)
        x = max(int((display_point.x() - self.offset.x()) * inv), 0)
        y = max(int((display_point.y() - self.offset.y()) * inv), 0)
        return QPoint(x, y)

    def _image_to_display(self, img_point: QPoint) -> QPoint:
        scale = self.base_scale * self.zoom_factor
        x = int(img_point.x() * scale) + self.offset.x()
        y = int(img_point.y() * scale) + self.offset.y()
        return QPoint(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.mode == "line":
                self._start_line_drawing(event)
            elif self.mode == "box":
                self._start_box_drawing(event)
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.pan_start = event.position().toPoint()

    def _start_line_drawing(self, event):
        self.drawing_line = True
        self.line_start_point = self._clamp_point_to_image(event.position().toPoint())
        self.line_current_end_point = self.line_start_point

        # Pick a random unused color
        if not self.available_colors:
            self.available_colors = [
                QColor("red"),
                QColor("green"),
                QColor("blue"),
                QColor("yellow"),
                QColor("magenta"),
                QColor("cyan"),
                QColor("orange"),
                QColor("purple"),
            ]
        self.current_line_color = random.choice(self.available_colors)
        self.available_colors.remove(self.current_line_color)
        self.update()

    def _start_box_drawing(self, event):
        self.drawing_box = True
        self.box_start_point = self._clamp_point_to_image(event.position().toPoint())
        self.box_current_rect = QRect(self.box_start_point, QSize())

        # Pick a random unused color
        if not self.available_colors:
            self.available_colors = [
                QColor("red"),
                QColor("green"),
                QColor("blue"),
                QColor("yellow"),
                QColor("magenta"),
                QColor("cyan"),
                QColor("orange"),
                QColor("purple"),
            ]
        self.current_box_color = random.choice(self.available_colors)
        self.available_colors.remove(self.current_box_color)
        self.update()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        if self.drawing_line:
            self.line_current_end_point = self._clamp_point_to_image(pos)
            self.update()
        elif self.drawing_box:
            self.box_current_rect = QRect(self.box_start_point, pos).normalized()
            self.update()
        elif self.panning:
            delta = pos - self.pan_start
            self.offset += delta
            self.pan_start = pos
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.drawing_line:
                self._finish_line_drawing()
            elif self.drawing_box:
                self._finish_box_drawing()
        elif self.panning and event.button() == Qt.MouseButton.MiddleButton:
            self.panning = False

    def _finish_line_drawing(self):
        self.drawing_line = False

        # Only add line if start and end points are different
        if self.line_start_point != self.line_current_end_point:
            # Convert to image coordinates
            img_start = self._display_to_image(self.line_start_point)
            img_end = self._display_to_image(self.line_current_end_point)

            # Create line in image coordinates
            line = Line(img_start, img_end, self.current_line_color)
            self.lines.append(line)

        self.update()

    def _finish_box_drawing(self):
        self.drawing_box = False

        # Only add box if it has size
        if self.box_current_rect.width() > 0 and self.box_current_rect.height() > 0:
            # Convert to image coordinates
            img_start = self._display_to_image(self.box_current_rect.topLeft())
            img_end = self._display_to_image(self.box_current_rect.bottomRight())
            img_rect = QRect(img_start, img_end).normalized()

            # Create rectangle in image coordinates
            rect = Rectangle(img_rect, self.current_box_color)
            self.rectangles.append(rect)

        self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        factor = 1.25 if delta > 0 else 0.8
        old_pos = event.position().toPoint()
        rel = old_pos - self.offset
        self.zoom_factor *= factor
        self._update_scaled()
        new_rel = QPoint(int(rel.x() * factor), int(rel.y() * factor))
        self.offset = old_pos - new_rel
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(45, 45, 45))

        if self.scaled_pixmap:
            painter.drawPixmap(self.offset, self.scaled_pixmap)

            # Draw completed lines
            for line in self.lines:
                display_start = self._image_to_display(line.start)
                display_end = self._image_to_display(line.end)
                painter.setPen(QPen(line.color, 2))
                painter.drawLine(display_start, display_end)

            # Draw completed rectangles
            for rect in self.rectangles:
                display_rect = self._image_to_display_rect(rect.rect)
                painter.setPen(QPen(rect.color, 2))
                painter.drawRect(display_rect)

            # Draw current line being drawn
            if self.drawing_line:
                painter.setPen(QPen(self.current_line_color, 2))
                painter.drawLine(self.line_start_point, self.line_current_end_point)

            # Draw current box being drawn
            if self.drawing_box:
                painter.setPen(QPen(self.current_box_color, 2))
                painter.drawRect(self.box_current_rect)

            # Draw extended lines and boundaries (for line mode)
            if (
                self.mode == "line"
                and hasattr(self, "show_extended_lines")
                and self.show_extended_lines
                and self.lines
            ):
                self._draw_extended_lines(painter)

    def _image_to_display_rect(self, img_rect: QRect) -> QRect:
        scale = self.base_scale * self.zoom_factor
        x = int(img_rect.x() * scale) + self.offset.x()
        y = int(img_rect.y() * scale) + self.offset.y()
        w = int(img_rect.width() * scale)
        h = int(img_rect.height() * scale)
        return QRect(x, y, w, h)

    def _draw_extended_lines(self, painter):
        """Draw extended lines and boundary lines for visualization"""
        if not self.pixmap:
            return

        image_size = QSize(self.pixmap.width(), self.pixmap.height())

        # Create boundary lines
        boundary_lines = [
            Line(QPoint(0, 0), QPoint(image_size.width(), 0), QColor("white")),
            Line(
                QPoint(image_size.width(), 0),
                QPoint(image_size.width(), image_size.height()),
                QColor("white"),
            ),
            Line(
                QPoint(image_size.width(), image_size.height()),
                QPoint(0, image_size.height()),
                QColor("white"),
            ),
            Line(QPoint(0, image_size.height()), QPoint(0, 0), QColor("white")),
        ]

        # Draw boundary lines with dashed style
        pen = QPen(QColor("red"), 5, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        for line in boundary_lines:
            display_start = self._image_to_display(line.start)
            display_end = self._image_to_display(line.end)
            painter.drawLine(display_start, display_end)

        # Draw extended user lines
        pen = QPen(QColor("yellow"), 5, Qt.PenStyle.DotLine)
        painter.setPen(pen)
        for line in self.lines:
            extended_line = LineSplitter._extend_line_to_boundaries(line, image_size)
            if extended_line:
                display_start = self._image_to_display(extended_line.start)
                display_end = self._image_to_display(extended_line.end)
                painter.drawLine(display_start, display_end)

    def sizeHint(self):
        if self.scaled_pixmap:
            return self.scaled_pixmap.size()
        return super().sizeHint()

    def reset(self):
        self.pixmap = QPixmap()
        self.zoom_factor = 1
