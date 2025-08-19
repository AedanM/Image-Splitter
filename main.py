"""Main module for image splitter."""

import sys

from PyQt6.QtGui import QImageReader
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
            QWidget { background-color: #2b2b2b; color: #f0f0f0; }
            QCheckBox, QPushButton, QLabel {background-color: #3c3f41; border: none; padding: 5px;}
            QPushButton:hover, QCheckBox:hover { background-color: #4b4f51; }
            QLabel { padding: 10px; font-weight: bold; }
        """,
        )

        self.image_widget = LineWidget()

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

        # Connect signals
        self.modeToggle.clicked.connect(self.ToggleMode)
        self.saveBtn.clicked.connect(self.Save)
        self.deleteLastBtn.clicked.connect(self.removeLast)
        self.deleteImgBtn.clicked.connect(self.deleteIMG)
        self.resetBtn.clicked.connect(self.reset)
        self.previewLinesCheck.toggled.connect(self.ToggleLinePreview)

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
        self.middle_layout = QVBoxLayout()
        self.middle_layout.addWidget(self.image_widget)

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
        self.middle_layout.removeWidget(self.image_widget)
        if isinstance(self.image_widget, BoxWidget):
            self.previewLinesCheck.setEnabled(False)
            self.modeToggle.setText("Switch to Box Mode")
            self.modeToggle.setStyleSheet("background-color: #4CAF50; font-weight: bold;")
            self.modeLabel.setText("Current Mode: LINE SPLITTER")
            self.modeLabel.setStyleSheet(
                "background-color: #2196F3; color: white; font-weight: bold;",
            )
            self.previewLinesCheck.setEnabled(True)
            self.image_widget = LineWidget(
                self.image_widget.image_path,
                self.image_widget.saveBounds,
            )
        else:
            self.modeToggle.setText("Switch to Line Mode")
            self.modeToggle.setStyleSheet("background-color: #FF9800; font-weight: bold;")
            self.modeLabel.setText("Current Mode: BOX CROPPER")
            self.modeLabel.setStyleSheet(
                "background-color: #FF9800; color: white; font-weight: bold;",
            )
            self.image_widget = BoxWidget(
                self.image_widget.image_path,
                self.image_widget.saveBounds,
            )
        self.middle_layout.addWidget(self.image_widget)

        self.image_widget.update()
        self.update()
        self.reset()

    def removeLast(self) -> None:
        iw = self.image_widget
        iw.RemoveLast()
        self.update()

    def deleteIMG(self) -> None:
        im = self.image_widget.image_path
        if im and im.exists():
            send2trash(im)
        self.image_widget.reset()
        self.update()

    def reset(self) -> None:
        self.image_widget.reset()

    def ToggleLinePreview(self, checked: bool) -> None:
        """Toggle the display of extended lines and boundaries."""
        self.image_widget.show_extended_lines = checked
        self.image_widget.update()

    def Save(self) -> None:
        self.image_widget.SaveSections(self.subfolderCheck.isChecked())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
