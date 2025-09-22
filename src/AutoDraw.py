"""Automatically slice image."""

from collections.abc import Iterable
from itertools import islice
from pathlib import Path

import numpy as np
from PIL import Image
from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QColor

from .Components import Polygon
from .LineCalcs import MatchTuple

MIN_SECTION = 150
PADDING = 0


def RunMedian(numbers: list) -> list[int]:
    if not numbers:
        return []

    runs = []
    run = [numbers[0]]

    for num in numbers[1:]:
        if num == run[-1] + 1:
            run.append(num)
        else:
            runs.append(run)
            run = [num]

    runs.append(run)

    return [int(np.median(run)) for run in runs]


def GetSolidGrid(image: Image.Image) -> tuple[list, list]:
    """Create a list of x indices where the entire column matches the target color."""
    width, height = image.size
    rows: list[int] = []
    cols: list[int] = []
    pixels = image.load()
    if pixels:
        cols = [
            x
            for x in range(width)
            if all(MatchTuple(pixels[x, 0], pixels[x, y]) for y in range(height))
        ]
        rows = [
            y
            for y in range(height)
            if all(MatchTuple(pixels[0, y], pixels[x, y]) for x in range(width))
        ]

    return (rows, cols)


def GetBlocks(numList: list, maxVal: int) -> list[tuple]:
    if not numList:
        return []
    values: list[int] = sorted(set(numList))
    start: int = -1
    prev: int = values[0]
    out: list[int] = []

    for num in values[1:]:
        if num != prev + 1 and abs(num - prev) > MIN_SECTION:
            if start != -1:
                start = num
            else:
                out.append(prev - PADDING)
                out.append(num + PADDING)
                start = -1
        prev = num

    if 0 not in values:
        out.append(0)
    if maxVal not in values:
        out.append(values[-1])
        out.append(maxVal)
    out = sorted(set(out))
    print(out)
    return [x for x in Chunk(out, 2) if len(x) == 2]


def Chunk(toBeSplit: Iterable, chunkSize: int) -> list:
    toBeSplit = iter(toBeSplit)
    return list(iter(lambda: tuple(islice(toBeSplit, chunkSize)), ()))


def Pairwise(seq: Iterable) -> list[tuple]:
    """Return consecutive overlapping pairs from seq.

    Example: [a, b, c] -> [(a, b), (b, c)]
    """
    lst = list(seq)
    if len(lst) < 2:
        return []
    return [(lst[i], lst[i + 1]) for i in range(len(lst) - 1)]


def AddBounds(lines: list, maxVal: int) -> list:
    if not lines:
        return [(0, maxVal)]
    if 0 not in lines:
        lines = [0, *lines]
    if lines != maxVal:
        lines = [*lines, maxVal]
    return sorted(lines)


def SliceImage(p: Path, useLines: bool = False) -> list[Polygon]:
    """Detect solid rows/cols and return polygons.

    Detailed behaviour:
    Args:
        p: Path to image file.
        useLines: If True, return line-style polygons (pairs of points representing lines).
        prefer_grid: If True and both row and column splits are detected, return
            full grid rectangles (useful for box-based slicing). If False, behaviour
            falls back to lines or single-dimension boxes.
    """
    out: list[Polygon] = []
    img = Image.open(p)
    width, height = img.size
    rows, cols = GetSolidGrid(img)
    # Convert solid lines into continuous ranges and pair them
    rows = Pairwise(RunMedian(AddBounds(rows, height)))
    cols = Pairwise(RunMedian(AddBounds(cols, width)))

    # If the detection produced ranges smaller than two boundaries, treat as empty
    if len(cols) < 2:
        cols = []
    if len(rows) < 2:
        rows = []

    if useLines:
        row_lines = [
            Polygon([QPoint(0, r[0]), QPoint(width, r[0])], QColor(255, 0, 0)) for r in rows
        ] + [Polygon([QPoint(0, r[1]), QPoint(width, r[1])], QColor(255, 0, 0)) for r in rows]
        col_lines = [
            Polygon([QPoint(c[0], 0), QPoint(c[0], height)], QColor(255, 0, 0)) for c in cols
        ] + [Polygon([QPoint(c[1], 0), QPoint(c[1], height)], QColor(255, 0, 0)) for c in cols]
        out = row_lines + col_lines
    else:
        if rows:
            for r in rows:
                if cols:
                    out.extend(
                        [
                            Polygon([QPoint(c[0], r[0]), QPoint(c[1], r[1])], QColor("red"))
                            for c in cols
                        ],
                    )
                else:
                    out.append(Polygon([QPoint(0, r[0]), QPoint(width, r[1])], QColor("red")))
        elif cols:
            out.extend(
                [Polygon([QPoint(c[0], 0), QPoint(c[1], height)], QColor("red")) for c in cols],
            )

    return out
