"""Components and utilities."""

from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtGui import QColor


class Polygon:
    """."""

    _Points: list[QPoint]
    Color: QColor

    def __init__(self, points: list[QPoint], color: QColor) -> None:
        self._Points = points
        self.Color = color

    @property
    def Points(self) -> list[QPoint]:
        return self._Points

    @Points.setter
    def Points(self, points: list[QPoint]) -> None:
        self._Points = sorted(points, key=lambda x: (x.y(), x.x()))

    @property
    def RawPoints(self) -> list[tuple[int, int]]:
        return [(x.x(), x.y()) for x in self.Points]

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
    def bounding_points(self) -> tuple[int, int, int, int] | None:
        if not self.Points:
            return None

        min_x = min(p.x() for p in self.Points)
        min_y = min(p.y() for p in self.Points)
        max_x = max(p.x() for p in self.Points)
        max_y = max(p.y() for p in self.Points)

        return (min_x, min_y, max_x, max_y)

    @property
    def bounding_rect(self) -> QRect:
        points = self.bounding_points
        if points is None:
            return QRect()
        return QRect(points[0], points[1], points[2] - points[0], points[3] - points[1])

    @property
    def isRectangle(self) -> bool:
        return len(self.Points) == 4 or (
            len(self.Points) == 2
            and self.Points[0].x() != self.Points[1].x()
            and self.Points[0].y() != self.Points[1].y()
        )

    @property
    def isVerticalLine(self) -> bool:
        return len(self.Points) == 2 and self.Points[0].x() == self.Points[1].x()

    @property
    def isHorizontalLine(self) -> bool:
        return len(self.Points) == 2 and self.Points[0].y() == self.Points[1].y()

    def BindTo(self, width: int, height: int) -> None:
        for p in self.Points:
            p.setX(max(min(p.x(), width), 0))
            p.setY(max(min(p.y(), height), 0))

    def __str__(self) -> str:
        """Use color and points for str."""  #
        pointStr = ",".join([f"({x[0]},{x[1]})" for x in sorted(self.RawPoints)])
        return f"{self.Color.value()} [{pointStr}]"

    def __repr__(self) -> str:
        """Repr is just string."""
        return str(self)

    def __hash__(self) -> int:
        """Hash based on raw points."""
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
        """Equality based on raw points and color."""
        if not isinstance(other, Polygon):
            return NotImplemented
        return sorted(self.RawPoints) == sorted(other.RawPoints) and self.Color == other.Color
