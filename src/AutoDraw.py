"""Automatically slice image."""

from collections.abc import Iterable
from itertools import islice
from pathlib import Path

from PIL import Image
from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QColor

from .Components import Polygon
from .LineCalcs import PADDING, MatchTuple

MIN_SECTION = 150


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
    return [x for x in Chunk(out, 2) if len(x) == 2]


def Chunk(toBeSplit: Iterable, chunkSize: int) -> list:
    toBeSplit = iter(toBeSplit)
    return list(iter(lambda: tuple(islice(toBeSplit, chunkSize)), ()))


def SliceImage(p: Path, useLines: bool = False) -> list[Polygon]:
    out = []
    img = Image.open(p)
    width, height = img.size
    rows, cols = GetSolidGrid(img)
    rows = GetBlocks(rows, height)
    cols = GetBlocks(cols, width)
    print(rows, cols)
    if useLines:
        out = (
            [
                Polygon(
                    [
                        QPoint(0, r[0]),
                        QPoint(width, r[0]),
                    ],
                    QColor("purple"),
                )
                for r in rows
            ]
            + [
                Polygon(
                    [
                        QPoint(0, r[1]),
                        QPoint(width, r[1]),
                    ],
                    QColor("purple"),
                )
                for r in rows
            ]
            + [
                Polygon(
                    [
                        QPoint(c[0], 0),
                        QPoint(c[0], height),
                    ],
                    QColor("purple"),
                )
                for c in cols
            ]
            + [
                Polygon(
                    [
                        QPoint(c[1], 0),
                        QPoint(c[1], height),
                    ],
                    QColor("purple"),
                )
                for c in cols
            ]
        )
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
