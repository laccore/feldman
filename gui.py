'''
Created on Nov 8, 2017

Qt GUI elements

@author: bgrivna
'''

import logging, os, platform

from PyQt5 import QtWidgets

def warnbox(parent, title="Warning", message=""):
    QtWidgets.QMessageBox.warning(parent, title, message)
    
def errbox(parent, title="Error", message=""):
    QtWidgets.QMessageBox.critical(parent, title, message)

def infobox(parent, title="Information", message=""):    
    QtWidgets.QMessageBox.information(parent, title, message)

def chooseDirectory(parent, path=""):
    dlg = QtWidgets.QFileDialog(parent, "Choose directory", path)
    selectedDir = dlg.getExistingDirectory(parent)
    return selectedDir

def chooseFile(parent, path=""):
    dlg = QtWidgets.QFileDialog(parent, "Choose file", path)
    chosenFile = dlg.getOpenFileName(parent)
    return chosenFile

def chooseFiles(parent, path=""):
    dlg = QtWidgets.QFileDialog(parent, "Choose file(s)", path)
    chosenFiles = dlg.getOpenFileNames(parent)
    return chosenFiles

def chooseSaveFile(parent, path=""):
    dlg = QtWidgets.QFileDialog(parent, "Save file", path)
    saveFile = dlg.getSaveFileName(parent)
    return saveFile    

# list of files with Add and Delete buttons
class FileListPanel(QtWidgets.QWidget):
    def __init__(self, title):
        QtWidgets.QWidget.__init__(self)
        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.addWidget(LabelFactory.makeItemLabel(title))
        self.sslist = QtWidgets.QListWidget()
        self.sslist.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        vlayout.addWidget(self.sslist)
        arlayout = QtWidgets.QHBoxLayout()
        self.addButton = QtWidgets.QPushButton("Add")
        self.addButton.clicked.connect(self.onAdd)
        self.rmButton = QtWidgets.QPushButton("Remove")
        self.rmButton.clicked.connect(self.onRemove)
        self._enableRemove()
        arlayout.addWidget(self.addButton)
        arlayout.addWidget(self.rmButton)
        vlayout.setSpacing(0)
        vlayout.addLayout(arlayout)
        vlayout.setContentsMargins(0,0,0,0)
        
    def addFile(self, newfile):
        self.sslist.addItem(QtWidgets.QListWidgetItem(newfile))
        self._enableRemove()
        
    def addFiles(self, filelist):
        for f in filelist:
            self.addFile(f)
        
    def getFiles(self):
        return [self.sslist.item(idx).text() for idx in range(self.sslist.count())]
    
    def onAdd(self):
        files = chooseFiles(self)
        for f in files[0]:
            self.addFile(f)
        
    def onRemove(self):
        for sel in self.sslist.selectedItems():
            self.sslist.takeItem(self.sslist.row(sel))
        self._enableRemove()
            
    def _enableRemove(self):
        self.rmButton.setEnabled(self.sslist.count() > 0)
            

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
        layout.setContentsMargins(0,0,0,0)
        
    def getPath(self):
        return self.filePath.text()
    
    def setPath(self, newpath):
        self.filePath.setText(newpath)

    def onBrowse(self):
        if self.fileType == self.OpenFile:
            f = chooseFile(self, self.getPath())
            if f[0] != "":
                self.filePath.setText(f[0])
        elif self.fileType == self.SaveFile:
            f = chooseSaveFile(self, self.getPath())
            if f[0] != "":
                self.filePath.setText(f[0])                
        elif self.fileType == self.Directory:
            f = chooseDirectory(self, self.getPath())
            if f != "":
                self.filePath.setText(f)
                

# Handler to direct python logging output to QTextEdit control
class LogTextArea(logging.Handler):
    def __init__(self, parent, label):
        self.parent = parent
        self.layout = QtWidgets.QVBoxLayout()
        logging.Handler.__init__(self)
        self.logText = QtWidgets.QTextEdit(parent)
        self.logText.setReadOnly(True)
        self.logText.setToolTip("It's all happening.")
        
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)
        self.layout.addWidget(QtWidgets.QLabel(label))
        self.layout.addWidget(self.logText)
        
        self.verboseCheckbox = QtWidgets.QCheckBox("Include Debugging Information")
        self.layout.addWidget(self.verboseCheckbox)
        
    def isVerbose(self):
        return self.verboseCheckbox.isChecked()

    def emit(self, record):
        msg = self.format(record)
        self.logText.insertPlainText(msg + "\n")
        self.parent.app.processEvents()

    def write(self, m):
        pass
    
# add help text below widget
def HelpTextDecorator(widget, helpText, spacing=5):
    layout = QtWidgets.QVBoxLayout()
    layout.setSpacing(spacing)
    layout.setContentsMargins(0,0,0,0)
    layout.addWidget(widget)
    layout.addWidget(LabelFactory.makeDescLabel(helpText))
    return layout

# create appropriately-sized labels for the current OS
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
    