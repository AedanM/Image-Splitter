"""Main module for image splitter."""

import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImageReader, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from send2trash import send2trash

from src.BoxesWidget import BoxWidget
from src.Components import Polygon
from src.ImageWidget import ImageWidget
from src.LinesWidget import LineWidget
from src.Utility import RestoreFromRecycle

QImageReader.setAllocationLimit(0)


class MainWindow(QWidget):
    """Main window widget."""

    ImageViewer: ImageWidget

    # region Setup
    def __init__(self) -> None:
        """Build base widget."""
        super().__init__()
        self.setWindowTitle("Image Splitter")
        self.setStyleSheet(
            """
            QFrame {max-width: 250px}
            QWidget { background-color: #2b2b2b; color: #f0f0f0; }
            QCheckBox, QPushButton {background-color: #3c3f41; border: none; padding: 5px;}
            QPushButton:hover, QCheckBox:hover { background-color: #4b4f51; }
        """,
        )

        self.ImageViewer = LineWidget()
        self.imageLabel = QLabel()
        self.imageLabel.setStyleSheet("min-width: 350px")

        # Mode toggle button
        self.modeToggle = QPushButton("Switch to Box Mode")
        self.modeToggle.setStyleSheet("background-color: #4CAF50; font-weight: bold;")

        # Control buttons
        self.saveBtn = QPushButton("Save Subsections")
        self.deleteLastBtn = QPushButton("Delete Last")
        self.deleteImgBtn = QPushButton("Delete IMG")
        self.resetBtn = QPushButton("Reset")

        # Checkboxes
        self.polygonViewCheck = QCheckBox("View Polygons")
        self.keepPolygonsCheck = QCheckBox("Keep Polygons")
        self.loadNextCheck = QCheckBox("Load Next")
        self.loadNextCheck.setChecked(True)
        self.subfolderCheck = QCheckBox("Save to subfolder")
        self.previewLinesCheck = QCheckBox("Preview Lines")
        self.previewLinesCheck.setChecked(True)
        self.trimBtn = QPushButton("Trim Bounds")
        self.addGridBtn = QPushButton("Add Grid")
        self.trimPad = QSpinBox()
        self.trimPad.setValue(0)
        self.trimPad.setRange(-1000, 1000)
        self.gridEntry = QLineEdit()
        self.gridEntry.setText("1x1")
        self.gridEntry.setStyleSheet("max-width: 50px ")

        # Connect signals
        self.modeToggle.clicked.connect(self.ToggleMode)
        self.saveBtn.clicked.connect(self.Save)
        self.deleteLastBtn.clicked.connect(self.DeleteLastPolygon)
        self.deleteImgBtn.clicked.connect(self.DeleteIMG)
        self.resetBtn.clicked.connect(self.reset)
        self.previewLinesCheck.toggled.connect(self.ToggleLinePreview)
        self.polygonViewCheck.toggled.connect(self.DisplayPolygons)
        self.addGridBtn.clicked.connect(self.AddGrid)
        self.trimBtn.clicked.connect(self.Trim)

        # Layout setup
        self.SetupLayout()
        self.resize(1200, 800)
        self.ToggleMode()

        if sys.argv and len(sys.argv) > 1:
            imgPath = Path(sys.argv[1])
            if imgPath.is_file():
                self.ImageViewer.LoadImage(imgPath)

    def SetupLayout(self) -> None:
        """Define buttons and layouts."""
        # Top row: Mode controls
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.polygonViewCheck)
        top_layout.addWidget(self.keepPolygonsCheck)
        top_layout.addWidget(self.modeToggle)
        top_layout.addStretch()
        top_layout.addWidget(self.imageLabel)
        top_layout.addStretch()
        top_layout.addWidget(self.deleteLastBtn)
        top_layout.addWidget(self.trimBtn)
        top_layout.addWidget(self.trimPad)
        top_layout.addWidget(self.addGridBtn)
        top_layout.addWidget(self.gridEntry)

        # Middle row: Image widget
        self.middle_layout = QHBoxLayout()
        self.middle_layout.addWidget(self.ImageViewer)

        # Bottom row: Controls
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.subfolderCheck)
        bottom_layout.addWidget(self.previewLinesCheck)
        bottom_layout.addWidget(self.loadNextCheck)
        bottom_layout.addStretch()
        for btn in (
            self.resetBtn,
            self.deleteImgBtn,
            self.saveBtn,
        ):
            bottom_layout.addWidget(btn)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(self.middle_layout)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    # endregion
    # region InputHandlers
    def keyPressEvent(self, a0: QKeyEvent | None) -> None:  # noqa: C901
        """Handle all the keypresses."""
        if a0 is None:
            return
        match a0.key():
            case Qt.Key.Key_Q:
                self.ImageViewer.LoadNext(
                    self.ImageViewer.image_path,
                    reverse=True,
                    keepPolygons=self.keepPolygonsCheck.isChecked(),
                )
            case Qt.Key.Key_W:
                self.DeleteIMG()
            case Qt.Key.Key_E:
                self.ImageViewer.LoadNext(
                    self.ImageViewer.image_path,
                    keepPolygons=self.keepPolygonsCheck.isChecked(),
                )
            case Qt.Key.Key_T:
                self.Trim()
            case Qt.Key.Key_U:
                RestoreFromRecycle(self)
            case Qt.Key.Key_A:
                self.ImageViewer.AutoDraw()
            case Qt.Key.Key_B:
                self.ToggleMode()
            case Qt.Key.Key_P:
                # open image in ms paint
                subprocess.Popen(["mspaint", str(self.ImageViewer.image_path)])
            case Qt.Key.Key_S:
                self.AddGrid()
            case Qt.Key.Key_L:
                self.ImageViewer.Translate()
            case Qt.Key.Key_M:
                self.ImageViewer.Translate(False)
            case Qt.Key.Key_K:
                self.keepPolygonsCheck.setChecked(not self.keepPolygonsCheck.isChecked())
            case Qt.Key.Key_V:
                self.polygonViewCheck.setChecked(not self.polygonViewCheck.isChecked())
            case Qt.Key.Key_C:
                self.ImageViewer.Crop(
                    self.keepPolygonsCheck.isChecked(),
                ) if self.ImageViewer.ReadyToCrop else self.Save()
            case Qt.Key.Key_Escape:
                self.clear()
            case Qt.Key.Key_G:
                self.gridEntry.setFocus()
                self.gridEntry.selectAll()
            case Qt.Key.Key_R:
                self.reset()
            case Qt.Key.Key_Return | Qt.Key.Key_Enter:
                self.Save()
            case Qt.Key.Key_F2:
                self.ImageViewer.Rename()
            case Qt.Key.Key_Backspace:
                self.DeleteLastPolygon()
            case Qt.Key.Key_O:
                if self.ImageViewer.image_path and self.ImageViewer.image_path.parent.exists():
                    bounds = self.ImageViewer.saveBounds
                    start = self.ImageViewer.image_path
                    for file in self.ImageViewer.image_path.parent.iterdir():
                        print(file)
                        if file.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]:
                            self.ImageViewer.LoadImage(file)
                            self.ImageViewer.saveBounds = bounds
                            self.ImageViewer.SaveSections(self.subfolderCheck.isChecked())
                    self.ImageViewer.LoadImage(start)
                    self.ImageViewer.saveBounds = bounds
                    self.update()
            case (
                Qt.Key.Key_0
                | Qt.Key.Key_1
                | Qt.Key.Key_2
                | Qt.Key.Key_3
                | Qt.Key.Key_4
                | Qt.Key.Key_5
                | Qt.Key.Key_6
                | Qt.Key.Key_7
                | Qt.Key.Key_8
                | Qt.Key.Key_9
            ):
                self.gridEntry.setText(
                    "1x" + chr(a0.key())
                    if self.ImageViewer.image_obj.size[0] < self.ImageViewer.image_obj.size[1]
                    else chr(a0.key()) + "x1",
                )
                if a0.key() == Qt.Key.Key_0:
                    self.gridEntry.setText(self.gridEntry.text().replace("0", "10"))
                self.AddGrid()
        self.update()

    def ToggleMode(self) -> None:
        """Toggle between line and box modes."""
        self.middle_layout.removeWidget(self.ImageViewer)
        if isinstance(self.ImageViewer, BoxWidget):
            self.previewLinesCheck.setEnabled(False)
            self.modeToggle.setText("Switch to Box Mode")
            self.modeToggle.setStyleSheet("background-color: #4CAF50; font-weight: bold;")
            self.previewLinesCheck.setEnabled(True)
            self.ImageViewer = LineWidget(
                self.ImageViewer.image_path,
                self.ImageViewer.saveBounds,
            )
        else:
            self.modeToggle.setText("Switch to Line Mode")
            self.modeToggle.setStyleSheet("background-color: #b350af; font-weight: bold;")
            self.ImageViewer = BoxWidget(
                self.ImageViewer.image_path,
                self.ImageViewer.saveBounds,
            )
        self.middle_layout.addWidget(self.ImageViewer)
        self.ImageViewer.update()
        self.update()
        self.reset()
        self.DisplayPolygons()

    def DeleteLastPolygon(self) -> None:
        """Pop the last save bound."""
        iw = self.ImageViewer
        iw.RemoveLast()
        self.update()

    def DisplayPolygons(self) -> None:
        """Render the current save bounds."""
        if item := self.middle_layout.itemAt(0):
            item = item.widget()
        else:
            return
        if isinstance(item, QFrame):
            item.deleteLater()
        if self.polygonViewCheck.isChecked() and self.ImageViewer.saveBounds:
            polygonViewer = QFrame()
            layout = QVBoxLayout()
            for idx, polygon in enumerate(self.ImageViewer.saveBounds):
                p_frame = QFrame()
                p_layout = QHBoxLayout()
                deleteBtn = QPushButton("❌")

                points = "</p><p>".join([f"({x.x():03d},{x.y():03d})" for x in polygon.Points])

                p_layout.addWidget(QLabel(f'<font color="{polygon.Color.name()}">#{idx}</font'))
                p_layout.addWidget(QLabel(f"<p>{points}</p>"))
                p_layout.addWidget(deleteBtn)
                p_layout.addStretch()

                def DeletePoly(element: Polygon) -> None:
                    self.ImageViewer.RemovePolygon(element)
                    self.DisplayPolygons()

                deleteBtn.clicked.connect(lambda _, p=polygon: DeletePoly(p))
                p_frame.setLayout(p_layout)
                layout.addWidget(p_frame)

            polygonViewer.setLayout(layout)
            polygonViewer.setMaximumWidth(250)
            self.middle_layout.insertWidget(0, polygonViewer)
        self.update()

    def DeleteIMG(self) -> None:
        """Recycle Image and potentially load next."""
        im = self.ImageViewer.image_path
        if im is None:
            return
        saveBounds = self.ImageViewer.saveBounds
        self.ImageViewer.reset()
        if self.loadNextCheck.isChecked():
            self.ImageViewer.LoadNext(im)
            self.ImageViewer.saveBounds = saveBounds if self.keepPolygonsCheck.isChecked() else []

        if im and im.exists():
            send2trash(im)
        self.update()

    def Trim(self) -> None:
        """Trim border from image."""
        self.ImageViewer.Trim(self.trimPad.value())

    def reset(self) -> None:
        """Reset the entire widget."""
        self.ImageViewer.reset(self.keepPolygonsCheck.isChecked())
        self.gridEntry.setText("1x1")
        self.trimPad.setValue(0)
        self.polygonViewCheck.setChecked(False)
        self.ToggleLinePreview(self.previewLinesCheck.isChecked())

    def clear(self) -> None:
        """Clear all save bounds and set focus to main widget"""
        self.ImageViewer.saveBounds = []
        self.setFocus()
        self.update()

    def ToggleLinePreview(self, checked: bool) -> None:
        """Toggle the display of extended lines and boundaries."""
        self.ImageViewer.previewLines = checked
        self.ImageViewer.update()

    def Save(self) -> None:
        """Save the image as sections, defined by imageviewer boxes"""
        newBounds = [] if not self.keepPolygonsCheck.isChecked() else self.ImageViewer.saveBounds
        self.ImageViewer.SaveSections(self.subfolderCheck.isChecked())
        if self.ImageViewer.isFullyCovered:
            self.DeleteIMG()
        self.ImageViewer.saveBounds = newBounds

    def AddGrid(self) -> None:
        """Add defined grid to image viewer"""
        numerics: list[int] = [
            int(x) for x in self.gridEntry.text().split("x", maxsplit=1) if x.isnumeric()
        ]
        if "x" not in self.gridEntry.text() or len(numerics) != 2:
            return
        vert, horz = numerics
        self.ImageViewer.AddGrid(vert, horz)

    # endregion


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Material")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
