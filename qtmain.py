'''
Created on Jul 30, 2017

@author: bgrivna
'''

import os, sys

from PyQt5 import QtWidgets

import feldman

def chooseDirectory(parent, title="Choose directory", path=""):
    dlg = QtWidgets.QFileDialog(parent, title, path)
    selectedDir = dlg.getExistingDirectory(parent)
    return selectedDir

def chooseFile(parent, title="Choose file", path=""):
    dlg = QtWidgets.QFileDialog(parent, title, path)
    chosenFile = dlg.getOpenFileName(parent)
    return chosenFile

def chooseFiles(parent, title="Choose file(s)", path=""):
    dlg = QtWidgets.QFileDialog(parent, title, path)
    chosenFiles = dlg.getOpenFileNames(parent)
    return chosenFiles

def chooseSaveFile(parent, title="Save file", path=""):
    dlg = QtWidgets.QFileDialog(parent, title, path)
    saveFile = dlg.getSaveFileName(parent)
    return saveFile    

class FileListPanel(QtWidgets.QWidget):
    def __init__(self, title):
        QtWidgets.QWidget.__init__(self)
        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.addWidget(QtWidgets.QLabel(title))
        self.sslist = QtWidgets.QListWidget()
        vlayout.addWidget(self.sslist)
        arlayout = QtWidgets.QHBoxLayout()
        self.addButton = QtWidgets.QPushButton("Add")
        self.addButton.clicked.connect(self.onAdd)
        self.delButton = QtWidgets.QPushButton("Delete")
        self.delButton.clicked.connect(self.onDel)
        arlayout.addWidget(self.addButton)
        arlayout.addWidget(self.delButton)
        vlayout.setSpacing(0)
        vlayout.addLayout(arlayout)
        
    def onAdd(self):
        files = chooseFiles(self)
        for f in files[0]:
            self.sslist.addItem(QtWidgets.QListWidgetItem(f))
        
    def onDel(self):
        for sel in self.sslist.selectedItems():
            self.sslist.takeItem(self.sslist.row(sel))
            
class SingleFilePanel(QtWidgets.QWidget):
    OpenFile = 1
    SaveFile = 2
    Directory = 3
    
    def __init__(self, title, fileType=OpenFile):
        QtWidgets.QWidget.__init__(self)
        self.fileType = fileType
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel(title + ':', self))
        self.filePath = QtWidgets.QLineEdit(self)
        layout.addWidget(self.filePath)
        self.browseButton = QtWidgets.QPushButton("...", self)
        self.browseButton.clicked.connect(self.onBrowse)
        layout.addWidget(self.browseButton)
        
    def getPath(self):
        return self.filePath.text()

    def onBrowse(self):
        if self.fileType == self.OpenFile:
            f = chooseFile(self)
            if f[0] != "":
                self.filePath.setText(f[0])
        elif self.fileType == self.SaveFile:
            f = chooseSaveFile(self)
            if f[0] != "":
                self.filePath.setText(f[0])                
        elif self.fileType == self.Directory:
            f = chooseDirectory(self)
            if f != "":
                self.filePath.setText(f)


class MainWindow(QtWidgets.QWidget):
    def __init__(self, app):
        QtWidgets.QWidget.__init__(self)
        self.app = app
        self.lastFileDialogPath = os.path.expanduser("~")
        self.setWindowTitle("Feldman 0.0.1")
        
        vlayout = QtWidgets.QVBoxLayout(self)
        self.ssFile = SingleFilePanel("Section Summary")
        self.sparseFile = SingleFilePanel("Sparse Splice")
        self.affineFile = SingleFilePanel("Affine Table")
        self.sitFile = SingleFilePanel("Splice Interval Table")
        self.mdList = FileListPanel("Measurement Data")
        self.outputDir = SingleFilePanel("Output Directory", SingleFilePanel.Directory)
        vlayout.addWidget(self.ssFile)
        vlayout.addWidget(self.sparseFile)
        vlayout.addWidget(self.affineFile)
        vlayout.addWidget(self.sitFile)
        vlayout.addWidget(self.mdList)
        vlayout.addWidget(self.outputDir)
        
        self.sparseToSitButton = QtWidgets.QPushButton("Convert Sparse Splice to SIT")
        self.sparseToSitButton.clicked.connect(self.sparseToSit)
        self.spliceDataButton = QtWidgets.QPushButton("Splice Measurement Data")
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.sparseToSitButton)
        hlayout.addWidget(self.spliceDataButton)
        vlayout.addLayout(hlayout)
        
    def sparseToSit(self):
        ssPath = self.ssFile.getPath()
        if not os.path.exists(ssPath):
            self._warnbox("Invalid path", "Section Summary file '{}' does not exist".format(ssPath))
            return
        sparsePath = self.sparseFile.getPath()
        if not os.path.exists(sparsePath):
            self._warnbox("Invalid path", "Sparse Splice file '{}' does not exist".format(sparsePath))
            return
        
        outFilePrefix = os.path.basename(sparsePath)
        
        feldman.convertSectionSpliceToSIT(sparsePath, ssPath, affineOutPath, sitOutPath)
        
        
    def _warnbox(self, title, message):
        QtWidgets.QMessageBox.warning(self, title, message)        
        

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec_())