from collections import deque
from pathlib import Path

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QThread

from .ui.file_renamer import Ui_Window
from .rename import Renamer

FILTERS = ";;".join(
    (
        "PNG Files (*.png)",
        "JPEG Files (*.jpeg)",
        "JPG Files (*.jpg)",
        "GIF Files (*.gif)",
        "Text Files (*.txt)",
        "Python Files (*.py)",
    )
)

class Window(QWidget, Ui_Window):
    def __init__(self):
        super().__init__()
        self._files = deque()
        self._filesCount = len(self._files)
        self._setupUI()
        self._connectSignalsSlots()

    def _setupUI(self):
        self.setupUi(self)

        self.dirPathEdit = self.lineEdit
        self.prefixEdit = self.lineEdit_2
        self.sourceList = self.listWidget
        self.renamedList = self.listWidget_2
        self.extensionLabel = self.label_5
        self.loadButton = self.pushButton
        self.renameButton = self.pushButton_2

    def _connectSignalsSlots(self):
        self.loadButton.clicked.connect(self.loadFiles)
        self.renameButton.clicked.connect(self.renameFiles)

    def renameFiles(self):
        self._runRenamerThread()
    
    def _runRenamerThread(self):
        prefix = self.prefixEdit.text()
        
        self._thread = QThread()
        self._renamer = Renamer(
            files=tuple(self._files),
            prefix=prefix,
        )
        
        self._renamer.moveToThread(self._thread)
        self._thread.started.connect(self._renamer.renameFiles)
        self._renamer.renamedFile.connect(self._updateStateWhenFileRenamed)
        self._renamer.progressed.connect(self._updateProgressBar)

        self._renamer.finished.connect(self._thread.quit)
        self._renamer.finished.connect(self._renamer.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _updateStateWhenFileRenamed(self, newFile):
        self._files.popleft()
        self.sourceList.takeItem(0)
        self.renamedList.addItem(str(newFile))

    def _updateProgressBar(self, fileNumber):
        progressPercent = int(fileNumber / self._filesCount * 100)
        self.progressBar.setValue(progressPercent)

    def loadFiles(self):
        self.renamedList.clear()
        
        if self.dirPathEdit.text():
            initDir = self.dirPathEdit.text()
        else:
            initDir = str(Path.home())
        
        files, filter = QFileDialog.getOpenFileNames(
            self, "Choose Files to Rename", initDir, filter=FILTERS
        )
        
        if len(files) > 0:
            fileExtension = filter[filter.index("*") : -1]
            self.extensionLabel.setText(fileExtension)
            srcDirName = str(Path(files[0]).parent)
            self.dirPathEdit.setText(srcDirName)

            self._files.clear()
            self.sourceList.clear()
            
            for file in files:
                self._files.append(Path(file))
                self.sourceList.addItem(str(Path(file).name))
            
            self._filesCount = len(self._files)
            self.progressBar.setValue(0)