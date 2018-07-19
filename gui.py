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


# provide file drag and drop support
class DragAndDropMixin:
    def __init__(self):
        self.acceptMethod = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            paths = [u.toLocalFile() for u in event.mimeData().urls()]
            if self.acceptMethod:
                self.acceptMethod(paths)
        else:
            event.ignore()

    # client-provided method to handle a single arugment: a list of file paths
    def setAcceptMethod(self, method):
        self.acceptMethod = method


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

# table of files and options with add and remove buttons
# hard-coded to splice export process at present
# generalize to OptionsTable or the like
class FileTablePanel(QtWidgets.QWidget, DragAndDropMixin):
    def __init__(self, title, depthColumnsProvider):
        QtWidgets.QWidget.__init__(self)
        self.initUI(title)
        self.mdPaths = {} # dict of MeasurementData paths keyed on basenames
        self.count = 0
        self.depthColumnsProvider = depthColumnsProvider
        self.setAcceptDrops(True)
        self.setAcceptMethod(self.addFiles)

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

    def addFile(self, filepath):
        filename = os.path.basename(filepath)
        if filename not in self.mdPaths:
            self.mdPaths[filename] = filepath 
            self._makeRow(filename, self.depthColumnsProvider(filepath))
            self._enableRemove()
        else:
            logging.warn("File {} is already in the list".format(filename))
        
    def addFiles(self, filelist):
        for f in filelist:
            self.addFile(f)
            
    def getFiles(self):
        params = [self.getRowParams(row) for row in range(self.table.rowCount())]
        for p in params:
            p[0] = self.mdPaths[p[0]] # filename to filepath
        return params
        
    def getRowParams(self, row):
        filename = self.table.cellWidget(row, 0).text()
        depthColumn = self.table.cellWidget(row, 1).currentText()
        lazyAppend = self.table.cellWidget(row, 2).isChecked()
        wholeSectionSplice = self.table.cellWidget(row, 3).isChecked()
        return [filename, depthColumn, lazyAppend, wholeSectionSplice]
    
    def onAdd(self):
        files = chooseFiles(self)
        for f in files[0]:
            self.addFile(f)
        
    def onRemove(self):
        if self.hasSelection():
            params = self.getRowParams(self.getSelectedRow())
            self.mdPaths.pop(params[0])
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
        
    def _makeRow(self, filename, depthColumns):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setCellWidget(row, 0, QtWidgets.QLabel(filename))
        depthCombo = QtWidgets.QComboBox()
        depthCombo.addItems(depthColumns)
        self.table.setCellWidget(row, 1, depthCombo)
        offSpliceTip = "All off-splice rows will be included in spliced data with On-Splice = 'off-splice'."
        self.table.setCellWidget(row, 2, self._makeCheckboxLayout(offSpliceTip))
        wholeSpliceTip = "All rows in a splice interval's section, including those outside the interval's depth range, will be included with On-Splice = 'splice'."
        self.table.setCellWidget(row, 3, self._makeCheckboxLayout(wholeSpliceTip))
        self.table.resizeColumnToContents(1) # display full width of all dropdowns
    
    # To center a checkbox in a QTableWidget cell, courtesy of stackoverflow 
    def _makeCheckboxLayout(self, tooltip):
        widget = CheckboxAligner()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(0,0,0,0)
        widget.setLayout(layout)
        widget.setToolTip(tooltip)
        layout.addWidget(widget.cb)
        return widget
    
# simplify access to checkbox in centering layout
class CheckboxAligner(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.cb = QtWidgets.QCheckBox()
        
    def isChecked(self):
        return self.cb.isChecked()
        

# QLineEdit with drag and drop support for files
class DroppableLineEdit(QtWidgets.QLineEdit, DragAndDropMixin):
    def __init__(self, parent):
        super(DroppableLineEdit, self).__init__(parent)
        self.setAcceptDrops(True)



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
        self.filePath = DroppableLineEdit(self)
        self.filePath.setAcceptMethod(self.handleDrop)
        layout.addWidget(self.filePath)
        self.browseButton = QtWidgets.QPushButton("...", self)
        self.browseButton.clicked.connect(self.onBrowse)
        layout.addWidget(self.browseButton)
        layout.setContentsMargins(0,0,0,0)
        
    def getPath(self):
        return self.filePath.text()
    
    def setPath(self, newpath):
        self.filePath.setText(newpath)

    def handleDrop(self, paths):
        self.setPath(paths[0]) # accept only the first path in the list
        
    def setPathIfExists(self, newpath):
        if os.path.exists(newpath):
            self.setPath(newpath)

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
    # main label for an item
    # On Mac, use standard font. On Windows, bold font.
    @classmethod
    def makeItemLabel(cls, text):
        label = QtWidgets.QLabel(text)
        if platform.system() == "Windows":
            label.setStyleSheet("QLabel {font-weight: bold;}")
        return label
    
    # label for help/description text
    # On Mac, use a smaller font. On Windows, standard font.
    @classmethod
    def makeDescLabel(cls, text):
        label = QtWidgets.QLabel(text)
        if platform.system() == "Darwin":
            label.setStyleSheet("QLabel {font-size: 11pt;}")
        return label
    