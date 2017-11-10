'''
Created on Jul 30, 2017

@author: bgrivna
'''

import os, sys

from PyQt5 import QtWidgets

import feldman
import gui
import prefs


class MainWindow(QtWidgets.QWidget):
    def __init__(self, app):
        QtWidgets.QWidget.__init__(self)
        self.app = app
        self.initGUI()
        self.initPrefs()
        
    def initGUI(self):
        self.setWindowTitle("Feldman 0.0.1")
        
        vlayout = QtWidgets.QVBoxLayout(self)
        self.secSummFile = gui.SingleFilePanel("Section Summary")
        self.sparseFile = gui.SingleFilePanel("Sparse Splice")
        self.affineFile = gui.SingleFilePanel("Affine Table")
        self.sitFile = gui.SingleFilePanel("Splice Interval Table")
        self.mdList = gui.FileListPanel("Measurement Data")
        self.workingDir = gui.SingleFilePanel("Working Directory", gui.SingleFilePanel.Directory)
        vlayout.addWidget(self.secSummFile)
        vlayout.addWidget(self.sparseFile)
        vlayout.addWidget(self.affineFile)
        vlayout.addWidget(self.sitFile)
        vlayout.addWidget(self.mdList)
        vlayout.addWidget(self.workingDir)
        
        self.sparseToSitButton = QtWidgets.QPushButton("Convert Sparse Splice to SIT")
        self.sparseToSitButton.clicked.connect(self.sparseToSit)
        self.spliceDataButton = QtWidgets.QPushButton("Splice Measurement Data")
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.sparseToSitButton)
        hlayout.addWidget(self.spliceDataButton)
        vlayout.addLayout(hlayout)
        
    def initPrefs(self):
        prefPath = os.path.join(user.home, ".feldman/prefs.pk")
        self.prefs = prefs.Prefs(prefPath)
        self.installPrefs()
        
    def installPrefs(self):
        self.secSummFile.setPath(self.prefs.get("lastSectionSummaryPath"))
        self.sparseFile.setPath(self.prefs.get("lastSparseSplicePath"))
        self.affineFile.setPath(self.prefs.get("lastAffinePath"))
        self.sitFile.setPath(self.prefs.get("lastSITPath"))
        mdList = self.prefs.get("lastMeasurementDataPathsList", [])
        for md in mdList:
            self.mdList.addFile(md)
        self.workingDir.setPath(self.prefs.get("lastWorkingDirPath"))
    
    def savePrefs(self):
        self.prefs.set("lastSectionSummaryPath", self.secSummFile.getPath())
        self.prefs.set("lastSparseSplicePath", self.sparseFile.getPath())
        self.prefs.set("lastAffinePath", self.affineFile.getPath())
        self.prefs.set("lastSITPath", self.sitFile.getPath())
        self.prefs.set("lastMeasurementDataPathsList", self.mdList.getFiles())
        self.prefs.set("lastWorkingDirPath", self.workingDir.getPath())
        self.prefs.write()
        
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
        
    # override QWidget.closeEvent()
    def closeEvent(self, event):
        self.savePrefs()
        event.accept() # allow window to close - event.ignore() to veto close        
        

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec_())