"""Components and utilities."""

from PyQt6.QtCore import QPoint, QRect, QSize
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

    def __init__(self, points: list[QPoint], color: QColor) -> None:
        self.points = points
        self.color = color

    @classmethod
    def FromRect(cls, bbox: QRect, color: QColor) -> "Polygon":
        # todo USE QPOINT DUMBASS
        poly = cls([bbox.x(), bbox.y(), bbox.width(), bbox.height()], color)
        return poly

    @property
    def bounding_rect(self) -> QRect:
        if not self.points:
            return QRect()

        min_x = min(p.x for p in self.points)
        min_y = min(p.y for p in self.points)
        max_x = max(p.x for p in self.points)
        max_y = max(p.y for p in self.points)

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


class LineSplitter:
    """Handles the complex logic of splitting an image by lines and creating subsections."""

    @staticmethod
    def line_intersection(line1: Line, line2: Line) -> None | QPoint:
        """Find intersection point of two lines."""
        x1, y1 = line1.start.x(), line1.start.y()
        x2, y2 = line1.end.x(), line1.end.y()
        x3, y3 = line2.start.x(), line2.start.y()
        x4, y4 = line2.end.x(), line2.end.y()

        denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denominator) < 1e-10:  # Lines are parallel
            return None

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denominator
        _u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denominator

        # For extended lines, we don't need to check if t and u are between 0 and 1
        # since lines are extended to boundaries
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        return QPoint(int(x), int(y))

    @staticmethod
    def create_polygons_from_lines(lines: list[Line], image_size: QSize) -> list[Polygon]:
        """Create polygons from lines by finding intersections and creating bounded regions"""
        if len(lines) < 1:
            print("Need at least 1 line to create polygons")
            return []

        print(f"Processing {len(lines)} user lines...")

        # Create boundary lines for the image
        boundary_lines = [
            Line(QPoint(0, 0), QPoint(image_size.width(), 0), QColor("white")),  # Top
            Line(
                QPoint(image_size.width(), 0),
                QPoint(image_size.width(), image_size.height()),
                QColor("white"),
            ),  # Right
            Line(
                QPoint(image_size.width(), image_size.height()),
                QPoint(0, image_size.height()),
                QColor("white"),
            ),  # Bottom
            Line(QPoint(0, image_size.height()), QPoint(0, 0), QColor("white")),  # Left
        ]
        print(f"Created {len(boundary_lines)} boundary lines")

        # Extend all user lines to image boundaries
        extended_lines = []
        for line in lines:
            extended_line = LineSplitter._extend_line_to_boundaries(line, image_size)
            if extended_line:
                extended_lines.append(extended_line)
        print(f"Extended {len(extended_lines)} lines to boundaries")

        # Combine user lines with boundary lines
        all_lines = extended_lines + boundary_lines
        print(f"Total lines to process: {len(all_lines)}")

        # Find all intersection points between all lines
        intersections = []
        for i, line1 in enumerate(all_lines):
            for j, line2 in enumerate(all_lines[i + 1 :], i + 1):
                intersection = LineSplitter.line_intersection(line1, line2)
                if intersection:
                    intersections.append(intersection)
        print(f"Found {len(intersections)} intersection points")

        # Create polygons from the intersection points and line segments
        polygons = LineSplitter._create_polygons_from_intersections(
            all_lines, intersections, image_size
        )
        print(f"Created {len(polygons)} polygons")

        return polygons

    @staticmethod
    def _extend_line_to_boundaries(line: Line, image_size: QSize) -> Line:
        """Extend a line to the image boundaries"""
        x1, y1 = line.start.x(), line.start.y()
        x2, y2 = line.end.x(), line.end.y()

        # Calculate line direction vector
        dx = x2 - x1
        dy = y2 - y1

        if abs(dx) < 1e-10 and abs(dy) < 1e-10:  # Point line
            return None

        # Calculate intersection with boundaries
        intersections = []

        # Top boundary (y = 0)
        if abs(dy) > 1e-10:
            t_top = -y1 / dy
            x_top = x1 + t_top * dx
            if 0 <= x_top <= image_size.width():
                intersections.append((x_top, 0, t_top))

        # Bottom boundary (y = image_size.height())
        if abs(dy) > 1e-10:
            t_bottom = (image_size.height() - y1) / dy
            x_bottom = x1 + t_bottom * dx
            if 0 <= x_bottom <= image_size.width():
                intersections.append((x_bottom, image_size.height(), t_bottom))

        # Left boundary (x = 0)
        if abs(dx) > 1e-10:
            t_left = -x1 / dx
            y_left = y1 + t_left * dy
            if 0 <= y_left <= image_size.height():
                intersections.append((0, y_left, t_left))

        # Right boundary (x = image_size.width())
        if abs(dx) > 1e-10:
            t_right = (image_size.width() - x1) / dx
            y_right = y1 + t_right * dy
            if 0 <= y_right <= image_size.height():
                intersections.append((image_size.width(), y_right, t_right))

        if not intersections:
            return line

        # Find the two intersection points with the smallest and largest t values
        intersections.sort(key=lambda x: x[2])

        # Use the two extreme intersection points
        start_x, start_y, _ = intersections[0]
        end_x, end_y, _ = intersections[-1]

        return Line(
            QPoint(int(start_x), int(start_y)),
            QPoint(int(end_x), int(end_y)),
            line.color,
        )

    @staticmethod
    def _create_polygons_from_intersections(
        lines: list[Line], intersections: list[QPoint], image_size: QSize
    ) -> list[Polygon]:
        """Create polygons from lines and their intersections"""
        if len(lines) < 2:  # Need at least 2 lines (including boundaries)
            return []

        print(f"Creating polygons from {len(lines)} lines and {len(intersections)} intersections")

        # Collect all unique points (line endpoints and intersections)
        all_points = set()
        for line in lines:
            all_points.add((line.start.x(), line.start.y()))
            all_points.add((line.end.x(), line.end.y()))
        for intersection in intersections:
            all_points.add((intersection.x(), intersection.y()))

        # Convert to list and sort for consistent ordering
        all_points = list(all_points)
        all_points.sort(key=lambda p: (p[1], p[0]))  # Sort by y, then x

        print(f"Total unique points: {len(all_points)}")

        # Create regions based on line intersections
        polygons = []

        # For now, create a simple approach: split the image into regions
        # based on the lines that intersect with boundaries

        # Find all vertical and horizontal lines (including boundaries)
        vertical_lines = []
        horizontal_lines = []

        for line in lines:
            if abs(line.end.x() - line.start.x()) < abs(line.end.y() - line.start.y()):
                # More vertical than horizontal
                vertical_lines.append(line.start.x())
            else:
                # More horizontal than vertical
                horizontal_lines.append(line.start.y())

        # Remove duplicates and sort
        vertical_lines = sorted(list(set(vertical_lines)))
        horizontal_lines = sorted(list(set(horizontal_lines)))

        print(f"Vertical lines at x-coordinates: {vertical_lines}")
        print(f"Horizontal lines at y-coordinates: {horizontal_lines}")

        # Create grid regions
        if len(vertical_lines) >= 2 and len(horizontal_lines) >= 2:
            for i in range(len(vertical_lines) - 1):
                for j in range(len(horizontal_lines) - 1):
                    x = vertical_lines[i]
                    y = horizontal_lines[j]
                    w = vertical_lines[i + 1] - x
                    h = horizontal_lines[j + 1] - y

                    if w > 0 and h > 0:
                        region_points = [
                            QPoint(x, y),
                            QPoint(x + w, y),
                            QPoint(x + w, y + h),
                            QPoint(x, y + h),
                        ]

                        # Assign different colors to different regions
                        color_idx = (i + j) % 8
                        colors = [
                            QColor("red"),
                            QColor("green"),
                            QColor("blue"),
                            QColor("yellow"),
                            QColor("magenta"),
                            QColor("cyan"),
                            QColor("orange"),
                            QColor("purple"),
                        ]
                        color = colors[color_idx]

                        polygons.append(Polygon(region_points, color))
                        print(f"Created region {len(polygons)}: ({x}, {y}, {w}, {h})")

        # If we couldn't create grid regions, create at least one region
        if not polygons:
            print("Creating fallback region")
            # Create a simple rectangular region covering the image
            region_points = [
                QPoint(0, 0),
                QPoint(image_size.width(), 0),
                QPoint(image_size.width(), image_size.height()),
                QPoint(0, image_size.height()),
            ]
            color = QColor(255, 255, 255, 128)  # Semi-transparent white
            polygons.append(Polygon(region_points, color))

        return polygons
