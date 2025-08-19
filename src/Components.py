"""Components and utilities."""

from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtGui import QColor


class Line:
    """."""

    def __init__(self, start: QPoint, end: QPoint, color: QColor) -> None:
        self.start = start
        self.end = end
        self.color = color

    def get_points(self) -> tuple[QPoint, QPoint]:
        return (self.start, self.end)


class Rectangle:
    """."""

    def __init__(self, rect: QRect, color: QColor) -> None:
        self.rect = rect
        self.color = color

    def get_bounding_rect(self) -> QRect:
        return self.rect


class Polygon:
    """."""

    Points: list[QPoint]
    Color: QColor

    def __init__(self, points: list[QPoint], color: QColor) -> None:
        self.Points = points
        self.Color = color

    @classmethod
    def FromRect(cls, bbox: QRect, color: QColor) -> "Polygon":
        topLeft = QPoint()
        bottomRight = QPoint()
        topLeft.setX(bbox.x())
        topLeft.setY(bbox.y())
        bottomRight.setX(bbox.x() + bbox.width())
        bottomRight.setY(bbox.y() + bbox.height())
        poly = cls([topLeft, bottomRight], color)
        return poly

    @property
    def bounding_rect(self) -> QRect:
        if not self.Points:
            return QRect()

        min_x = min(p.x() for p in self.Points)
        min_y = min(p.y() for p in self.Points)
        max_x = max(p.x() for p in self.Points)
        max_y = max(p.y() for p in self.Points)

        return QRect(min_x, min_y, max_x - min_x, max_y - min_y)

    @classmethod
    def FromLines(cls, lines: list[Line], color: QColor) -> "Polygon | None":
        if len(lines) < 2:
            return None
        points = set()
        for line in lines:
            points.add(line.start)
            points.add(line.end)
        return cls(list(points), color)

    def BindTo(self, width: int, height: int) -> None:
        for p in self.Points:
            p.setX(max(min(p.x(), width), 0))
            p.setY(max(min(p.y(), height), 0))
