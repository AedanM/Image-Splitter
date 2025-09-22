"""Calculations with lines."""

import contextlib
from email.charset import QP
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
    if len(intersections) < 2:
        return None
    # Use the two extreme intersection points
    start_x, start_y, _ = intersections[0]
    end_x, end_y, _ = intersections[-1]

    return Polygon(
        [QPoint(int(start_x), int(start_y)), QPoint(int(end_x), int(end_y))],
        line.Color,
    )


def MatchTuple(pixel: tuple, reference: tuple) -> bool:
    if isinstance(pixel, int):
        pixel = ((pixel,) * len(reference)) if isinstance(reference, tuple) else (pixel,)
    if isinstance(reference, int):
        reference = (reference,) * len(pixel)
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
    return [QPoint(left, top), QPoint(right + 1, bottom + 1)]


def TrimOrthoLines(
    points: list[QPoint],
    pixels: Any,
    padding: int,
    size: list[int],
) -> list[list[QPoint]]:
    width, height = size
    out: list[list[QPoint]] = []
    vertical = len({x.x() for x in points}) == 1
    horizontal = len({x.y() for x in points}) == 1
    if vertical:
        out.extend(FindVerticals(points, size, pixels, padding))
    elif horizontal:
        out.extend(FindHorizontals(points, size, pixels, padding))
    return out if out else [points]


def FindHorizontals(
    points: list[QPoint],
    size: list[int],
    pixels: Any,
    padding: int,
) -> list[list[QPoint]]:
    width, height = size
    out = []
    top = max(min(points[0].y(), height - 1), 0)
    bot = top

    while top > 0 and all(MatchTuple(pixels[y, top], pixels[0, top]) for y in range(width)):
        top -= 1
    while bot < height and all(MatchTuple(pixels[y, bot], pixels[0, bot]) for y in range(width)):
        bot += 1

    if top != points[0].y():
        top += 1

    bot = max(bot - padding, top)
    top = min(top + padding, bot)

    if top == bot or bot < top:
        out.append([QPoint(0, points[0].y()), QPoint(width, points[0].y())])
    else:
        if top != 0 or top == bot:
            out.append([QPoint(0, top), QPoint(width, top)])
        if top != bot and bot != height:
            out.append([QPoint(0, bot), QPoint(width, bot)])
    return out


def FindVerticals(
    points: list[QPoint],
    size: list[int],
    pixels: Any,
    padding: int,
) -> list[list[QPoint]]:
    width, height = size
    out = []
    left = max(min(points[0].y(), width - 1), 0)
    right = left
    while left > 0 and all(MatchTuple(pixels[left, y], pixels[left, 0]) for y in range(height)):
        left -= 1
    while right < width and all(
        MatchTuple(pixels[right, y], pixels[right, 0]) for y in range(height)
    ):
        right += 1
    right = min(right - padding, left)
    left = max(left + padding, right)
    if left > right:
        left = max(min(points[0].y(), width - 1), 0)
        right = left
    if left != 0 or left == right:
        out.append([QPoint(left, 0), QPoint(left, height)])
    if left != right and right != width:
        out.append([QPoint(right, 0), QPoint(right, height)])
    if not out:
        out.append([QPoint(points[0].x(), 0), QPoint(points[0].x(), height)])
    return out
