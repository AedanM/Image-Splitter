"""Main module for image splitter."""

import sys

from PyQt6.QtGui import QImageReader
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from send2trash import send2trash

from src.BoxesWidget import BoxWidget
from src.LinesWidget import LineWidget

QImageReader.setAllocationLimit(0)


class MainWindow(QWidget):
    """Main window widget."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Image Splitter")
        self.setStyleSheet(
            """
            QSpinBox {max-width: 50px }
            QWidget { background-color: #2b2b2b; color: #f0f0f0; }
            QCheckBox, QPushButton, QLabel {background-color: #3c3f41; border: none; padding: 5px;}
            QPushButton:hover, QCheckBox:hover { background-color: #4b4f51; }
            QLabel { padding: 10px; font-weight: bold; }
        """,
        )

        self.imageViewer = LineWidget()

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
        self.resetBtn = QPushButton("Reset")

        # Checkboxes
        self.subfolderCheck = QCheckBox("Save to subfolder")
        self.subfolderCheck.setChecked(True)
        self.previewLinesCheck = QCheckBox("Preview Lines")
        self.previewLinesCheck.setChecked(True)
        self.addGridBtn = QPushButton("Add Grid")
        self.gridWidth = QSpinBox()
        self.gridWidth.setValue(1)
        self.gridWidth.setRange(1, 100)
        self.gridHeight = QSpinBox()
        self.gridHeight.setValue(1)
        self.gridHeight.setRange(1, 100)

        # Connect signals
        self.modeToggle.clicked.connect(self.ToggleMode)
        self.saveBtn.clicked.connect(self.Save)
        self.deleteLastBtn.clicked.connect(self.removeLast)
        self.deleteImgBtn.clicked.connect(self.deleteIMG)
        self.resetBtn.clicked.connect(self.reset)
        self.previewLinesCheck.toggled.connect(self.ToggleLinePreview)
        self.addGridBtn.clicked.connect(self.AddGrid)

        # Layout setup
        self.SetupLayout()
        self.resize(1200, 800)

    def SetupLayout(self) -> None:
        # Top row: Mode controls
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.modeLabel)
        top_layout.addWidget(self.modeToggle)
        top_layout.addStretch()
        top_layout.addWidget(self.addGridBtn)
        top_layout.addWidget(self.gridWidth)
        top_layout.addWidget(self.gridHeight)

        # Middle row: Image widget
        self.middle_layout = QVBoxLayout()
        self.middle_layout.addWidget(self.imageViewer)

        # Bottom row: Controls
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.subfolderCheck)
        bottom_layout.addWidget(self.previewLinesCheck)
        bottom_layout.addStretch()
        for btn in (
            self.deleteLastBtn,
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

    def ToggleMode(self) -> None:
        """Toggle between line and box modes."""
        self.middle_layout.removeWidget(self.imageViewer)
        if isinstance(self.imageViewer, BoxWidget):
            self.previewLinesCheck.setEnabled(False)
            self.modeToggle.setText("Switch to Box Mode")
            self.modeToggle.setStyleSheet("background-color: #4CAF50; font-weight: bold;")
            self.modeLabel.setText("Current Mode: LINE SPLITTER")
            self.modeLabel.setStyleSheet(
                "background-color: #2196F3; color: white; font-weight: bold;",
            )
            self.previewLinesCheck.setEnabled(True)
            self.imageViewer = LineWidget(
                self.imageViewer.image_path,
                self.imageViewer.saveBounds,
            )
        else:
            self.modeToggle.setText("Switch to Line Mode")
            self.modeToggle.setStyleSheet("background-color: #FF9800; font-weight: bold;")
            self.modeLabel.setText("Current Mode: BOX CROPPER")
            self.modeLabel.setStyleSheet(
                "background-color: #FF9800; color: white; font-weight: bold;",
            )
            self.imageViewer = BoxWidget(
                self.imageViewer.image_path,
                self.imageViewer.saveBounds,
            )
        self.middle_layout.addWidget(self.imageViewer)

        self.imageViewer.update()
        self.update()
        self.reset()

    def removeLast(self) -> None:
        iw = self.imageViewer
        iw.RemoveLast()
        self.update()

    def deleteIMG(self) -> None:
        im = self.imageViewer.image_path
        if im and im.exists():
            send2trash(im)
        self.imageViewer.reset()
        self.update()

    def reset(self) -> None:
        self.imageViewer.reset()
        self.gridWidth.setValue(1)
        self.gridHeight.setValue(1)
        self.ToggleLinePreview(self.previewLinesCheck.isChecked())

    def ToggleLinePreview(self, checked: bool) -> None:
        """Toggle the display of extended lines and boundaries."""
        self.imageViewer.show_extended_lines = checked
        self.imageViewer.update()

    def Save(self) -> None:
        self.imageViewer.SaveSections(self.subfolderCheck.isChecked())

    def AddGrid(self) -> None:
        self.imageViewer.AddGrid(self.gridWidth.value(), self.gridHeight.value())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
