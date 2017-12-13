'''
Created on Nov 8, 2017

Qt GUI elements

@author: bgrivna
'''

import logging, os, platform

from PyQt5 import QtWidgets, QtCore

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
        self.initUI(title)
        
    def initUI(self, title):
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


class FileTablePanel(QtWidgets.QWidget):
    def __init__(self, title, depthColumnsProvider):
        QtWidgets.QWidget.__init__(self)
        self.initUI(title)
        self.count = 0
        self.depthColumnsProvider = depthColumnsProvider

    def initUI(self, title):
        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.addWidget(LabelFactory.makeItemLabel(title))
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["File", "Depth Column", "Off Splice", "Whole Section Splice"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)        
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        vlayout.addWidget(self.table)
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
        self._makeRow(newfile, self.depthColumnsProvider(newfile))
        self._enableRemove()
        
    def addFiles(self, filelist):
        for f in filelist:
            self.addFile(f)
            
    def getFiles(self):
        files = [self.getFileAndOptions(row) for row in range(self.table.rowCount())]
        return files
        
    def getFileAndOptions(self, row):
        path = self.table.cellWidget(row, 0).text()
        depthColumn = self.table.cellWidget(row, 1).currentText()
        lazyAppend = self.table.cellWidget(row, 2).isChecked()
        wholeSectionSplice = self.table.cellWidget(row, 3).isChecked()
        return [path, depthColumn, lazyAppend, wholeSectionSplice]
    
    def onAdd(self):
        files = chooseFiles(self)
        for f in files[0]:
            self.addFile(f)
        
    def onRemove(self):
        if self.hasSelection():
            self.table.removeRow(self.getSelectedRow())
            self._enableRemove()
            
    def getSelectedRow(self):
        ranges = self.table.selectedRanges()
        if len(ranges) > 0: 
            return ranges[0].topRow()
        return None
        
    def hasSelection(self):
        return self.getSelectedRow() is not None
            
    def _enableRemove(self):
        self.rmButton.setEnabled(self.table.rowCount() > 0)
        
    def _makeRow(self, filepath, depthColumns):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setCellWidget(row, 0, QtWidgets.QLabel(filepath))
        depthCombo = QtWidgets.QComboBox()
        depthCombo.addItems(depthColumns)
        self.table.setCellWidget(row, 1, depthCombo) 
        self.table.setCellWidget(row, 2, self._makeCheckboxLayout())
        self.table.setCellWidget(row, 3, self._makeCheckboxLayout())
        
    def _makeCheckboxLayout(self):
        widget = CheckboxAligner()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(0,0,0,0)
        widget.setLayout(layout)
        layout.addWidget(widget.cb)
        return widget
    
class CheckboxAligner(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.cb = QtWidgets.QCheckBox()
        
    def isChecked(self):
        return self.cb.isChecked()
        


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
    