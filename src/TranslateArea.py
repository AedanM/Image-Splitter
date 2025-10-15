"""Translation and text rendering utilities for images."""

import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont
from translate import Translator

from .Components import Polygon


def ExtractText(image: Image.Image, polygons: list[Polygon]) -> list[str]:
    results = []
    for poly in polygons:
        # Get bounding box for the polygon
        bbox = poly.bounding_rect
        # Crop the region from the image
        region = image.crop((bbox.x(), bbox.y(), bbox.x() + bbox.width(), bbox.y() + bbox.height()))
        # Run OCR on the cropped region
        text = pytesseract.image_to_string(region, lang="jpn")
        results.append(text.strip())
    return results


def TranslateText(texts: list[str], target_language: str = "en") -> list[str]:
    translator = Translator(
        provider="mymemory",
        from_lang="zh",
        to_lang=target_language,
        email="aedan.mchale@gmail.com",
    )
    translated_texts = [translator.translate(text) for text in texts]
    print([f"{t}-> {translator.translate(t)}" for t in texts])
    return translated_texts


def GetLuminance(rgb: tuple[int, ...]) -> float:
    # Calculate luminance (perceived brightness)
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def ContrastRatio(rgb1: tuple[int, ...], rgb2: tuple[int, ...]) -> float:
    # Calculate contrast ratio between two colors (WCAG)
    l1 = (GetLuminance(rgb1) + 0.05) / 255
    l2 = (GetLuminance(rgb2) + 0.05) / 255
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def WrapText(
    text: str,
    max_width: int,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
    draw: ImageDraw.ImageDraw,
) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for word in words[1:]:
        test_line = current + " " + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current = test_line
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def PutTextOnPolygon(image: Image.Image, polygon: Polygon, text: str) -> Image.Image:
    # Get bounding box
    bbox = polygon.bounding_rect
    x, y, w, h = bbox.x(), bbox.y(), bbox.width(), bbox.height()

    # Crop the region and analyze colors using numpy
    region = image.crop((x, y, x + w, y + h)).convert("RGB")
    arr = np.array(region)
    pixels = arr.reshape(-1, arr.shape[2]) if len(arr.shape) == 3 else arr.reshape(-1, 1)
    colors, counts = np.unique(pixels, axis=0, return_counts=True)
    sorted_idx = np.argsort(-counts)
    most_common = colors[sorted_idx[0]] if len(sorted_idx) > 0 else np.array([0, 0, 0])
    bg_color = tuple(int(c) for c in most_common)
    fg_color = tuple(
        int(c) for c in (colors[sorted_idx[1]] if len(sorted_idx) > 1 else (255, 255, 255))
    )
    white = (255, 255, 255)
    black = (0, 0, 0)
    min_contrast = 4.5
    if ContrastRatio(fg_color, bg_color) < min_contrast:
        fg_color = max([white, black], key=lambda c: ContrastRatio(c, bg_color))

    # Draw background rectangle on the image
    img_draw = image.copy()

    draw = ImageDraw.Draw(img_draw)
    draw.rectangle([x, y, x + w, y + h], fill=bg_color)

    # Try to use a truetype font, fallback to default
    try:
        font_size: int = int(h * 0.5)
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()
        font_size: int = int(font.size) if hasattr(font, "size") else 12  # pyright: ignore[reportAttributeAccessIssue]

    font, lines, line_heights, total_height = ResizeFont(
        text,
        w,
        h,
        draw,
        font_size,
        font,
    )

    # Draw each line centered horizontally, stacked vertically
    y_offset = y + (h - total_height) // 2
    for line, _ in zip(lines, line_heights, strict=True):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = x + (w - text_w) // 2
        text_y = y_offset
        draw.text((text_x, text_y), line, font=font, fill=fg_color)
        y_offset += text_h + 5

    return img_draw


def ResizeFont(
    text: str,
    w: int,
    h: int,
    draw: ImageDraw.ImageDraw,
    font_size: int,
    font: ImageFont.ImageFont | ImageFont.FreeTypeFont,
) -> tuple:
    min_font_size = 8
    max_attempts = 40
    attempt = 0
    while True:
        lines = WrapText(text, w, font, draw)
        line_bboxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
        line_widths = [bbox[2] - bbox[0] for bbox in line_bboxes]
        line_heights = [bbox[3] - bbox[1] for bbox in line_bboxes]
        total_height = sum(line_heights) + (len(lines) - 1) * 5
        max_line_width = max(line_widths) if line_widths else 0
        if (
            (total_height <= h and max_line_width <= w)
            or font_size <= min_font_size
            or attempt > max_attempts
        ):
            break
        font_size = max(int(font_size * 0.95), min_font_size)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        attempt += 1
    return font, lines, line_heights, total_height
