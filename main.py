"""Main module for image splitter."""

import os
import sys
from pathlib import Path

from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QColor, QImage, QImageReader
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from send2trash import send2trash

from src.Components import LineSplitter, Polygon
from src.ImageWidget import ImageWidget

QImageReader.setAllocationLimit(0)


class MainWindow(QWidget):
    """Main window widget."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Image Splitter")
        self.setStyleSheet(
            """
            QWidget { background-color: #2b2b2b; color: #f0f0f0; }
            QCheckBox, QPushButton, QLabel {background-color: #3c3f41; border: none; padding: 5px;}
            QPushButton:hover, QCheckBox:hover { background-color: #4b4f51; }
            QLabel { padding: 10px; font-weight: bold; }
        """,
        )

        self.image_widget = ImageWidget()

        # Mode toggle button
        self.modeToggle = QPushButton("Switch to Box Mode")
        self.modeToggle.setStyleSheet("background-color: #4CAF50; font-weight: bold;")

        # Mode indicator label
        self.modeLabel = QLabel("Current Mode: LINE SPLITTER")
        self.modeLabel.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")

        # Control buttons
        self.saveBtn = QPushButton("Save Subsections")
        self.deleteLastBtn = QPushButton("Delete Last")
        self.deleteImgBtn = QPushButton("Delete IMG")
        self.reset = QPushButton("Reset")

        # Checkboxes
        self.subfolderCheck = QCheckBox("Save to subfolder")
        self.subfolderCheck.setChecked(True)
        self.previewLinesCheck = QCheckBox("Preview Lines")
        self.previewLinesCheck.setChecked(True)

        # Connect signals
        self.modeToggle.clicked.connect(self.ReplaceMode)
        self.saveBtn.clicked.connect(self.save_subsections)
        self.deleteLastBtn.clicked.connect(self.remove_last)
        self.deleteImgBtn.clicked.connect(self.remove_img)
        self.reset.clicked.connect(self.reset_all)
        self.previewLinesCheck.toggled.connect(self.toggle_extended_lines)

        # Layout setup
        self.SetupLayout()
        self.resize(1200, 800)

    def SetupLayout(self) -> None:
        # Top row: Mode controls
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.modeLabel)
        top_layout.addWidget(self.modeToggle)
        top_layout.addStretch()

        # Middle row: Image widget
        middle_layout = QVBoxLayout()
        middle_layout.addWidget(self.image_widget)

        # Bottom row: Controls
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.subfolderCheck)
        bottom_layout.addWidget(self.previewLinesCheck)
        bottom_layout.addStretch()
        for btn in (
            self.deleteLastBtn,
            self.reset,
            self.deleteImgBtn,
            self.saveBtn,
        ):
            bottom_layout.addWidget(btn)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(middle_layout)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def ReplaceMode(self) -> None:
        """Toggle between line and box modes."""
        if self.image_widget.mode == "line":
            self.image_widget.set_mode("box")
            self.modeToggle.setText("Switch to Line Mode")
            self.modeToggle.setStyleSheet("background-color: #FF9800; font-weight: bold;")
            self.modeLabel.setText("Current Mode: BOX CROPPER")
            self.modeLabel.setStyleSheet(
                "background-color: #FF9800; color: white; font-weight: bold;",
            )
            self.previewLinesCheck.setEnabled(False)
        else:
            self.image_widget.set_mode("line")
            self.modeToggle.setText("Switch to Box Mode")
            self.modeToggle.setStyleSheet("background-color: #4CAF50; font-weight: bold;")
            self.modeLabel.setText("Current Mode: LINE SPLITTER")
            self.modeLabel.setStyleSheet(
                "background-color: #2196F3; color: white; font-weight: bold;",
            )
            self.previewLinesCheck.setEnabled(True)

        self.image_widget.update()

    def remove_last(self) -> None:
        iw = self.image_widget
        self.update()

    def remove_img(self) -> None:
        im = self.image_widget.image_path
        if im and im.exists():
            send2trash(im)
        self.image_widget.reset()
        self.update()

    def reset_all(self) -> None:
        self.image_widget.reset()

    def toggle_extended_lines(self, checked: bool) -> None:
        """Toggle the display of extended lines and boundaries."""
        self.image_widget.show_extended_lines = checked
        self.image_widget.update()

    def save_subsections(self) -> None:
        iw = self.image_widget
        if not iw.pixmap:
            print("No image loaded")
            return
        iw.SaveSections(self.subfolderCheck.isChecked())

    def _save_line_subsections(self, iw: ImageWidget) -> None:
        """Save subsections created by lines."""
        if len(iw.lines) < 1:
            print(f"Need at least 1 line, got {len(iw.lines)}")
            return
        input_file = iw.image_path
        if input_file is None:
            return
        parent_dir = input_file.parent
        base_name = input_file.stem

        # Decide output directory
        if self.subfolderCheck.isChecked():
            output_dir = parent_dir / f"{base_name}"
            if output_dir.exists():
                output_dir = parent_dir / f"{base_name} {len(iw.lines)}"
            try:
                output_dir.mkdir(exist_ok=True)
                print(f"Created output directory: {output_dir}")
            except Exception as e:
                print(f"Failed to create output directory: {e}")
                return
        else:
            output_dir = parent_dir
            print(f"Using output directory: {output_dir}")

        # Check if output directory is writable
        if not output_dir.exists() or not os.access(output_dir, os.W_OK):
            print(f"Output directory is not writable: {output_dir}")
            return

        # Load the image
        qImage = QImage(str(input_file))
        if qImage.isNull():
            print(f"Failed to load image: {input_file}")
            return
        image_size = qImage.size()
        print(f"Loaded image: {image_size.width()}x{image_size.height()}")

        # Create subsections using the line splitter
        print(f"Creating polygons from {len(iw.lines)} lines...")
        for i, line in enumerate(iw.lines):
            print(
                f"Line {i}: ({line.start.x()}, {line.start.y()}) to ({line.end.x()}, {line.end.y()})"
            )

        polygons = LineSplitter.create_polygons_from_lines(iw.lines, image_size)

        if not polygons:
            print("No Polygons created, using fallback method")
            # Fallback: create simple rectangular regions
            self._create_simple_regions(qImage, output_dir, base_name)
        else:
            print(f"Created {len(polygons)} polygons")
            # Save each polygon as a separate image
            for idx, polygon in enumerate(polygons, start=1):
                self._save_polygon_image(qImage, polygon, output_dir, base_name, idx)

    def _save_box_subsections(self, iw):
        """Save subsections created by boxes"""
        if len(iw.rectangles) < 1:
            print(f"Need at least 1 box, got {len(iw.rectangles)}")
            return

        input_file = iw.image_path
        parent_dir = input_file.parent
        base_name = input_file.stem

        # Decide output directory
        if self.subfolderCheck.isChecked():
            output_dir = parent_dir / f"{base_name}"
            if output_dir.exists():
                output_dir = parent_dir / f"{base_name} {len(iw.rectangles)}"
            try:
                output_dir.mkdir(exist_ok=True)
                print(f"Created output directory: {output_dir}")
            except Exception as e:
                print(f"Failed to create output directory: {e}")
                return
        else:
            output_dir = parent_dir
            print(f"Using output directory: {output_dir}")

        # Check if output directory is writable
        if not output_dir.exists() or not os.access(output_dir, os.W_OK):
            print(f"Output directory is not writable: {output_dir}")
            return

        # Load the image
        qImage = QImage(str(input_file))
        if qImage.isNull():
            print(f"Failed to load image: {input_file}")
            return

        # Save each rectangle as a separate image
        print(f"Saving {len(iw.rectangles)} box crops...")
        for idx, rect in enumerate(iw.rectangles, start=1):
            bbox = rect.get_bounding_rect()
            print(f"Box {idx}: ({bbox.x()}, {bbox.y()}, {bbox.width()}, {bbox.height()})")

            if bbox.width() > 0 and bbox.height() > 0:
                cropped = qImage.copy(bbox)
                output_path = output_dir / f"{base_name}_box_{idx:03d}.png"
                cropped.save(str(output_path))
                print(f"Saved box {idx} to: {output_path}")

    def _create_simple_regions(self, qImage: QImage, output_dir: Path, base_name: str):
        """Create simple rectangular regions when complex polygon creation fails"""
        width, height = qImage.width(), qImage.height()

        # Create a simple grid split based on line positions
        lines = self.image_widget.lines

        # Find vertical and horizontal lines
        vertical_lines = []
        horizontal_lines = []

        for line in lines:
            if abs(line.end.x() - line.start.x()) < abs(line.end.y() - line.start.y()):
                # More vertical than horizontal
                vertical_lines.append(line.start.x())
            else:
                # More horizontal than vertical
                horizontal_lines.append(line.start.y())

        # Sort lines and add boundaries
        vertical_lines.sort()
        horizontal_lines.sort()

        # Add image boundaries
        vertical_lines = [0] + vertical_lines + [width]
        horizontal_lines = [0] + horizontal_lines + [height]

        # Create regions from the grid
        regions = []
        for i in range(len(vertical_lines) - 1):
            for j in range(len(horizontal_lines) - 1):
                x = vertical_lines[i]
                y = horizontal_lines[j]
                w = vertical_lines[i + 1] - x
                h = horizontal_lines[j + 1] - y

                if w > 0 and h > 0:
                    regions.append((x, y, w, h))

        # Save each region
        print(f"Creating {len(regions)} regions...")
        for idx, (x, y, w, h) in enumerate(regions, start=1):
            if w > 0 and h > 0:
                print(f"Saving region {idx}: ({x}, {y}, {w}, {h})")
                cropped = qImage.copy(x, y, w, h)
                output_path = output_dir / f"{base_name} {idx:03d}.png"
                cropped.save(str(output_path))
                print(f"Saved to: {output_path}")

    def _save_polygon_image(
        self,
        qImage: QImage,
        polygon: Polygon,
        output_dir: Path,
        base_name: str,
        idx: int,
    ):
        """Save a polygon region as an image"""
        # For now, save the bounding rectangle
        # In a full implementation, you'd clip the image to the polygon shape
        bbox = polygon.bounding_rect()
        print(
            f"Polygon {idx} bounding box: ({bbox.x()}, {bbox.y()}, {bbox.width()}, {bbox.height()})"
        )
        if bbox.width() > 0 and bbox.height() > 0:
            cropped = qImage.copy(bbox)
            output_path = output_dir / f"{base_name} {idx:03d}.png"
            cropped.save(str(output_path))
            print(f"Saved polygon {idx} to: {output_path}")
        else:
            print(f"Polygon {idx} has invalid dimensions: {bbox.width()}x{bbox.height()}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
