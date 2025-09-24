"""Calculations with lines."""

# removed unused imports
from typing import Any

import numpy as np
from PIL import Image as PILImage
from PyQt6.QtCore import QPoint, QSize

from src.Components import Polygon

TOLERANCE = 25


def MakeNumpy(pixels: Any) -> np.ndarray | None:
    """Try to convert `pixels` to a (H, W, C) uint8 NumPy array.

    Returns None if conversion isn't supported; callers should fall back to
    the original pixel-access loops in that case.
    """
    # Already an ndarray
    if isinstance(pixels, np.ndarray):
        return pixels
    # PIL Image
    if isinstance(pixels, PILImage.Image):
        return np.asarray(pixels.convert("RGB"))
    # Can't convert (e.g. PixelAccess) — caller will use fallback
    return None


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
    image: Any,
    corners: tuple[int, int, int, int],
    padding: int,
) -> list[QPoint]:
    s_left, s_top, s_right, s_bottom = corners
    left, top, right, bottom = corners

    # Try vectorized path first
    arr = MakeNumpy(pixels=image)
    if arr is None:
        raise TypeError(
            "pixels must be a PIL.Image.Image or numpy.ndarray for vectorized operations",
        )
    # normalize exclusive indices as callers expect
    right -= 1
    bottom -= 1

    # Move inward while matching the reference pixels
    while top < bottom:
        seg = arr[top, left:right, :]
        ref = arr[top, left, :]
        if not (np.abs(seg - ref) <= TOLERANCE).all(axis=1).all():
            break
        top += 1

    while bottom > top:
        seg = arr[bottom, left:right, :]
        ref = arr[bottom, left, :]
        if not (np.abs(seg - ref) <= TOLERANCE).all(axis=1).all():
            break
        bottom -= 1

    while left < right:
        seg = arr[top:bottom, left, :]
        ref = arr[top, left, :]
        if not (np.abs(seg - ref) <= TOLERANCE).all(axis=1).all():
            break
        left += 1

    while right > left:
        seg = arr[top:bottom, right, :]
        ref = arr[top, right, :]
        if not (np.abs(seg - ref) <= TOLERANCE).all(axis=1).all():
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
    # size is passed through to FindVerticals/FindHorizontals when needed
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
    image: Any,
    padding: int,
) -> list[list[QPoint]]:
    _width, _height = size
    width = _width
    height = _height
    out = []
    top = max(min(points[0].y(), height - 1), 0)
    bot = top

    arr = MakeNumpy(image)
    if arr is None:
        raise TypeError(
            "pixels must be a PIL.Image.Image or numpy.ndarray for vectorized operations",
        )
    height = arr.shape[0]
    # expand upward
    while top > 0:
        row = arr[top, :, :]
        ref = arr[top, 0, :]
        if not (np.abs(row - ref) <= TOLERANCE).all(axis=1).all():
            break
        top -= 1
    # expand downward
    while bot < height:
        row = arr[bot, :, :]
        ref = arr[bot, 0, :]
        if not (np.abs(row - ref) <= TOLERANCE).all(axis=1).all():
            break
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
    image: Any,
    padding: int,
) -> list[list[QPoint]]:
    width, height = size
    out = []
    left = max(min(points[0].y(), width - 1), 0)
    right = left
    arr = MakeNumpy(image)
    if arr is None:
        raise TypeError(
            "pixels must be a PIL.Image.Image or numpy.ndarray for vectorized operations",
        )
    width = arr.shape[1]
    # move left
    while left > 0:
        col = arr[:, left, :]
        ref = arr[0, left, :]
        if not (np.abs(col - ref) <= TOLERANCE).all(axis=1).all():
            break
        left -= 1
    # move right
    while right < width:
        col = arr[:, right, :]
        ref = arr[0, right, :]
        if not (np.abs(col - ref) <= TOLERANCE).all(axis=1).all():
            break
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
