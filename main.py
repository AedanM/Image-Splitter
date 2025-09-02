"""Main module for image splitter."""

import sys
from pathlib import Path
from pprint import pp

import winshell
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImageReader, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from send2trash import send2trash

from src.BoxesWidget import BoxWidget
from src.Components import Polygon
from src.LinesWidget import LineWidget

QImageReader.setAllocationLimit(0)


class MainWindow(QWidget):
    """Main window widget."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Image Splitter")
        self.setStyleSheet(
            """
            QFrame {max-width: 250px}
            QSpinBox {max-width: 50px }
            QWidget { background-color: #2b2b2b; color: #f0f0f0; }
            QCheckBox, QPushButton, QLabel {background-color: #3c3f41; border: none; padding: 5px;}
            QPushButton:hover, QCheckBox:hover { background-color: #4b4f51; }
            QLabel { padding: 10px; font-weight: bold; }
        """,
        )

        self.imageViewer = BoxWidget()
        self.imageLabel = QLabel("")
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
        self.nextBtn = QPushButton("Next Image")

        # Checkboxes
        self.polygonViewCheck = QCheckBox("View Polygons")
        self.loadNextCheck = QCheckBox("Load Next")
        self.loadNextCheck.setChecked(True)
        self.subfolderCheck = QCheckBox("Save to subfolder")
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
        self.polygonViewCheck.toggled.connect(self.LoadPolygonView)
        self.addGridBtn.clicked.connect(self.AddGrid)
        self.nextBtn.clicked.connect(lambda: self.imageViewer.LoadNext(self.imageViewer.image_path))

        # Layout setup
        self.SetupLayout()
        self.resize(1200, 800)

        if sys.argv and len(sys.argv) > 1:
            imgPath = Path(sys.argv[1])
            if imgPath.is_file():
                self.imageViewer.LoadImage(imgPath)

    def SetupLayout(self) -> None:
        # Top row: Mode controls
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.modeLabel)
        top_layout.addWidget(self.modeToggle)
        top_layout.addStretch()
        top_layout.addWidget(self.imageLabel)
        top_layout.addStretch()
        top_layout.addWidget(self.deleteLastBtn)
        top_layout.addWidget(self.addGridBtn)
        top_layout.addWidget(self.gridWidth)
        top_layout.addWidget(self.gridHeight)

        # Middle row: Image widget
        self.middle_layout = QHBoxLayout()
        self.middle_layout.addWidget(self.imageViewer)

        # Bottom row: Controls
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.subfolderCheck)
        bottom_layout.addWidget(self.previewLinesCheck)
        bottom_layout.addWidget(self.polygonViewCheck)
        bottom_layout.addWidget(self.loadNextCheck)
        bottom_layout.addStretch()
        for btn in (
            self.resetBtn,
            self.nextBtn,
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

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0 is None:
            return
        match a0.key():
            case Qt.Key.Key_W:
                self.deleteIMG()
            case Qt.Key.Key_E:
                self.imageViewer.LoadNext(self.imageViewer.image_path)
            case Qt.Key.Key_Q:
                self.imageViewer.LoadNext(self.imageViewer.image_path, reverse=True)
            case Qt.Key.Key_Escape:
                self.reset()
            case Qt.Key.Key_Return | Qt.Key.Key_Enter:
                self.Save()
            case Qt.Key.Key_U:
                files = sorted(winshell.recycle_bin(), key=lambda x: x.recycle_date())
                file = files[-1].original_filename()
                pp(files)
                dlg = QMessageBox(self)
                dlg.setWindowTitle("File Restored")
                dlg.setText(f"Restore {Path(file).name}?")
                dlg.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                btn = dlg.exec()
                if btn == QMessageBox.StandardButton.Yes:
                    winshell.undelete(file)
                    self.imageViewer.LoadImage(file)
            case Qt.Key.Key_F2:
                if self.imageViewer.image_path:
                    text, ok = QInputDialog.getText(
                        self,
                        "Enter New Name",
                        self.imageViewer.image_path.name,
                        text=self.imageViewer.image_path.stem,
                    )

                    if ok and text:
                        dst = (
                            self.imageViewer.image_path.parent
                            / f"{text}{self.imageViewer.image_path.suffix}"
                        )
                        self.imageViewer.image_path.rename(dst)
                        self.imageViewer.LoadNext(self.imageViewer.image_path)

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
        self.LoadPolygonView()

    def removeLast(self) -> None:
        iw = self.imageViewer
        iw.RemoveLast()
        self.update()

    def LoadPolygonView(self) -> None:
        item = self.middle_layout.itemAt(0).widget()
        if isinstance(item, QFrame):
            item.deleteLater()
        if self.polygonViewCheck.isChecked() and self.imageViewer.saveBounds:
            polygonViewer = QFrame()
            layout = QVBoxLayout()
            for idx, polygon in enumerate(self.imageViewer.saveBounds):
                p_frame = QFrame()
                p_layout = QHBoxLayout()
                deleteBtn = QPushButton("❌")

                points = "</p><p>".join([f"({x.x():03d},{x.y():03d})" for x in polygon.Points])

                p_layout.addWidget(QLabel(f'<font color="{polygon.Color.name()}">#{idx}</font'))
                p_layout.addWidget(QLabel(f"<p>{points}</p>"))
                p_layout.addWidget(deleteBtn)
                p_layout.addStretch()

                def DeletePoly(element: Polygon) -> None:
                    self.imageViewer.RemovePolygon(element)
                    self.LoadPolygonView()

                deleteBtn.clicked.connect(lambda _self, p=polygon: DeletePoly(p))
                p_frame.setLayout(p_layout)
                layout.addWidget(p_frame)

            polygonViewer.setLayout(layout)
            polygonViewer.setMaximumWidth(250)
            self.middle_layout.insertWidget(0, polygonViewer)
        self.update()

    def deleteIMG(self) -> None:
        im = self.imageViewer.image_path
        if im is None:
            return
        self.imageViewer.reset()
        if self.loadNextCheck.isChecked():
            self.imageViewer.LoadNext(im)

        if im and im.exists():
            send2trash(im)
        self.update()

    def reset(self) -> None:
        self.imageViewer.reset()
        self.gridWidth.setValue(1)
        self.gridHeight.setValue(1)
        self.polygonViewCheck.setChecked(False)
        self.ToggleLinePreview(self.previewLinesCheck.isChecked())

    def ToggleLinePreview(self, checked: bool) -> None:
        """Toggle the display of extended lines and boundaries."""
        self.imageViewer.show_extended_lines = checked
        self.imageViewer.update()

    def Save(self) -> None:
        self.imageViewer.SaveSections(self.subfolderCheck.isChecked())
        if self.imageViewer.isFullyCovered:
            self.deleteIMG()

    def AddGrid(self) -> None:
        self.imageViewer.AddGrid(self.gridWidth.value(), self.gridHeight.value())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
