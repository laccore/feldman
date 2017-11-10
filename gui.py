'''
Created on Nov 8, 2017

Qt GUI elements

@author: bgrivna
'''

import platform

from PyQt5 import QtWidgets


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

# list of files with Add and Delete buttons
class FileListPanel(QtWidgets.QWidget):
    def __init__(self, title):
        QtWidgets.QWidget.__init__(self)
        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.addWidget(LabelFactory.makeItemLabel(title))
        self.sslist = QtWidgets.QListWidget()
        vlayout.addWidget(self.sslist)
        arlayout = QtWidgets.QHBoxLayout()
        self.addButton = QtWidgets.QPushButton("Add")
        self.addButton.clicked.connect(self.onAdd)
        self.delButton = QtWidgets.QPushButton("Delete")
        self.delButton.clicked.connect(self.onDel)
        self._enableDelete()
        arlayout.addWidget(self.addButton)
        arlayout.addWidget(self.delButton)
        vlayout.setSpacing(0)
        vlayout.addLayout(arlayout)
        
    def addFile(self, newfile):
        self.sslist.addItem(QtWidgets.QListWidgetItem(newfile))
        self._enableDelete()
        
    def addFiles(self, filelist):
        for f in filelist:
            self.addFile(f)
        
    def getFiles(self):
        return [self.sslist.item(idx).text() for idx in range(self.sslist.count())]
    
    def onAdd(self):
        files = chooseFiles(self)
        for f in files[0]:
            self.addFile(f)
        
    def onDel(self):
        for sel in self.sslist.selectedItems():
            self.sslist.takeItem(self.sslist.row(sel))
        self._enableDelete()
            
    def _enableDelete(self):
        self.delButton.setEnabled(self.sslist.count() > 0)
            

# single file path with label and browse button
class SingleFilePanel(QtWidgets.QWidget):
    OpenFile = 1
    SaveFile = 2
    Directory = 3
    
    def __init__(self, title, fileType=OpenFile):
        QtWidgets.QWidget.__init__(self)
        self.fileType = fileType
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(LabelFactory.makeItemLabel(title + ':'))
        self.filePath = QtWidgets.QLineEdit(self)
        layout.addWidget(self.filePath)
        self.browseButton = QtWidgets.QPushButton("...", self)
        self.browseButton.clicked.connect(self.onBrowse)
        layout.addWidget(self.browseButton)
        
    def getPath(self):
        return self.filePath.text()
    
    def setPath(self, newpath):
        self.filePath.setText(newpath)

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

class LabelFactory:
    # main label for an item, standard font size
    @classmethod
    def makeItemLabel(cls, text):
        label = QtWidgets.QLabel(text)
        if platform.system() == "Windows":
            label.setStyleSheet("QLabel {font-size: 11pt;}")
        return label
    
    # label with smaller font intended to be used for help text
    @classmethod
    def makeDescLabel(cls, text):
        label = QtWidgets.QLabel(text)
        ss = "QLabel {font-size: 9pt;}" if platform.system() == "Windows" else "QLabel {font-size: 11pt;}" 
        label.setStyleSheet(ss)
        return label
    