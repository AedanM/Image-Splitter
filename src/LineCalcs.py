"""Calculations with lines."""

from typing import Any

from PyQt6.QtCore import QPoint, QSize

from src.Components import Polygon

TOLERANCE = 25


def SolveIntersections(image_size: QSize, line: Polygon) -> list[tuple]:
    x1, y1 = line.Points[0].x(), line.Points[0].y()
    x2, y2 = line.Points[-1].x(), line.Points[-1].y()

    dx: int = x2 - x1
    dy: int = y2 - y1

    if abs(dx) < 1e-10 and abs(dy) < 1e-10:  # Point line
        return []
    # Calculate intersection with boundaries
    intersections = []

    # Top boundary (y = 0)
    if abs(dy) > 1e-10:
        t_top: int = round(-y1 / dy)
        x_top: int = x1 + t_top * dx
        if 0 <= x_top <= image_size.width():
            intersections.append((x_top, 0, t_top))

    # Bottom boundary (y = image_size.height())
    if abs(dy) > 1e-10:
        t_bottom: int = round((image_size.height() - y1) / dy)
        x_bottom: int = x1 + t_bottom * dx
        if 0 <= x_bottom <= image_size.width():
            intersections.append((x_bottom, image_size.height(), t_bottom))

    # Left boundary (x = 0)
    if abs(dx) > 1e-10:
        t_left: int = round(-x1 / dx)
        y_left: int = y1 + t_left * dy
        if 0 <= y_left <= image_size.height():
            intersections.append((0, y_left, t_left))

    # Right boundary (x = image_size.width())
    if abs(dx) > 1e-10:
        t_right: int = round((image_size.width() - x1) / dx)
        y_right: int = y1 + t_right * dy
        if 0 <= y_right <= image_size.height():
            intersections.append((image_size.width(), y_right, t_right))
    intersections.sort(key=lambda x: x[2])

    return intersections


def ExtendLines(line: Polygon, image_size: QSize) -> Polygon | None:
    """Extend a line to the image boundaries."""
    # Find the two intersection points with the smallest and largest t values
    intersections = SolveIntersections(image_size, line)

    # Use the two extreme intersection points
    start_x, start_y, _ = intersections[0]
    end_x, end_y, _ = intersections[-1]

    return Polygon(
        [QPoint(int(start_x), int(start_y)), QPoint(int(end_x), int(end_y))],
        line.Color,
    )


def MatchTuple(pixel: tuple, reference: tuple) -> bool:
    return all(abs(pixel[i] - reference[i]) <= TOLERANCE for i in range(len(reference)))


def DetermineBoundary(
    pixels: Any,
    corners: tuple[int, int, int, int],
    padding: int,
) -> list[QPoint]:
    s_left, s_top, s_right, s_bottom = corners
    left, top, right, bottom = corners

    s_right -= 1
    s_bottom -= 1
    right -= 1
    bottom -= 1

    while top < bottom:
        if any(not MatchTuple(pixels[x, top], pixels[left, top]) for x in range(left, right)):
            break
        top += 1

    while bottom > top:
        if any(not MatchTuple(pixels[x, bottom], pixels[left, bottom]) for x in range(left, right)):
            break
        bottom -= 1

    while left < right:
        if any(not MatchTuple(pixels[left, y], pixels[left, top]) for y in range(top, bottom)):
            break
        left += 1

    while right > left:
        if any(not MatchTuple(pixels[right, y], pixels[right, top]) for y in range(top, bottom)):
            break
        right -= 1

    top = max(top - padding, s_top)
    bottom = min(bottom + padding, s_bottom)
    left = max(left - padding, s_left)
    right = min(right + padding, s_right)
    print(corners, "->", (left, top, right, bottom))
    return [QPoint(left, top), QPoint(right + 1, bottom + 1)]
