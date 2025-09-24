"""Automatically slice image."""

import sys
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
    if len(numList) == 1:
        return numList
    print(numList, "start")
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
    print(out)
    out = sorted(set(out))
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


def SimplifyRuns(lines: list[int], maxVal: int) -> list[tuple]:
    minRun = round(maxVal * 0.1)
    out = []
    hold = []
    for block in GetBlocks(lines, maxVal):
        start, end = block[:2]
        if hold:
            start = hold[0][0]
            hold = []
        if (end - start) >= minRun:
            out.append((start, end))
        else:
            hold = [(start, end)]
    if hold:
        out.append(hold[0])
    return out


def SliceImage(p: Path, useLines: bool = False) -> list[Polygon]:
    out = []
    img = Image.open(p)
    width, height = img.size
    rows, cols = GetSolidGrid(img)
    rows = SimplifyRuns(AddBounds(rows, height), height)
    cols = SimplifyRuns(AddBounds(cols, width), width)

    # rows = Pairwise(RunMedian(rows))
    # cols = Pairwise(RunMedian(cols))
    if len(cols) < 2:
        cols = []
    if len(rows) < 2:
        rows = []
    if useLines:
        rowBoxes = [
            Polygon(
                [
                    QPoint(0, r[0]),
                    QPoint(width, r[0]),
                ],
                QColor("purple"),
            )
            for r in rows
        ] + [
            Polygon(
                [
                    QPoint(0, r[1]),
                    QPoint(width, r[1]),
                ],
                QColor("purple"),
            )
            for r in rows
        ]
        colboxes = [
            Polygon(
                [
                    QPoint(c[0], 0),
                    QPoint(c[0], height),
                ],
                QColor("purple"),
            )
            for c in cols
        ] + [
            Polygon(
                [
                    QPoint(c[1], 0),
                    QPoint(c[1], height),
                ],
                QColor("purple"),
            )
            for c in cols
        ]
        out = rowBoxes + colboxes
    else:
        out = [
            Polygon(
                [
                    QPoint(0, r[0]),
                    QPoint(width, r[1]),
                ],
                QColor("purple"),
            )
            for r in rows
        ] + [
            Polygon(
                [
                    QPoint(c[0], 0),
                    QPoint(c[1], height),
                ],
                QColor("purple"),
            )
            for c in cols
        ]
    return out


if __name__ == "__main__":
    p = Path(sys.argv[1])
    SliceImage(p, useLines=False)
