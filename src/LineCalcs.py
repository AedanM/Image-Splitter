from PyQt6.QtCore import QPoint, QSize

from src.Components import Polygon


def ExtendLines(line: Polygon, image_size: QSize) -> Polygon | None:
    """Extend a line to the image boundaries."""
    x1, y1 = line.Points[0].x(), line.Points[0].y()
    x2, y2 = line.Points[-1].x(), line.Points[-1].y()

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

    return Polygon(
        [QPoint(int(start_x), int(start_y)), QPoint(int(end_x), int(end_y))],
        line.Color,
    )
