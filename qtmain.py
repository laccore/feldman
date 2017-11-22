'''
Created on Jul 30, 2017

@author: bgrivna
'''

import os, sys, user, logging

from PyQt5 import QtWidgets

import feldman
import gui
import prefs

class InvalidPathError(Exception):
    pass

        
def validatePath(path, filetype):
    if not os.path.exists(path):
        raise InvalidPathError("{} file '{}' does not exist".format(filetype, path))

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
        self.affineFile = gui.SingleFilePanel("Affine Table")
        self.sitFile = gui.SingleFilePanel("Splice Interval Table")
        self.mdList = gui.FileListPanel("Measurement Data")
        vlayout.addWidget(self.secSummFile)
        vlayout.addWidget(self.affineFile)
        vlayout.addWidget(self.sitFile)
        vlayout.addWidget(self.mdList)
        
        self.sparseToSitButton = QtWidgets.QPushButton("Convert Sparse Splice to SIT")
        self.sparseToSitButton.clicked.connect(self.sparseToSit)
        self.spliceDataButton = QtWidgets.QPushButton("Splice Measurement Data")
        self.spliceDataButton.clicked.connect(self.spliceData)
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
        self.affineFile.setPath(self.prefs.get("lastAffinePath"))
        self.sitFile.setPath(self.prefs.get("lastSITPath"))
        mdList = self.prefs.get("lastMeasurementDataPathsList", [])
        for md in mdList:
            self.mdList.addFile(md)
        geom = self.prefs.get("windowGeometry", None)
        if geom is not None:
            self.setGeometry(geom)
    
    def savePrefs(self):
        self.prefs.set("lastSectionSummaryPath", self.secSummFile.getPath())
        self.prefs.set("lastAffinePath", self.affineFile.getPath())
        self.prefs.set("lastSITPath", self.sitFile.getPath())
        self.prefs.set("lastMeasurementDataPathsList", self.mdList.getFiles())
        self.prefs.set("windowGeometry", self.geometry())
        self.prefs.write()
        
    def sparseToSit(self):
        secSummPath = self.secSummFile.getPath()
        if not os.path.exists(secSummPath):
            self.warnbox("Invalid path", "Section Summary file '{}' does not exist".format(secSummPath))
            return
        
        dlg = ConvertSparseToSITDialog(self, secSummPath)
        accepted = dlg.exec_() == QtWidgets.QDialog.Accepted
        if accepted:
            if len(self.affineFile.getPath()) == 0:
                self.affineFile.setPath(dlg.affineOutPath)
            if len(self.sitFile.getPath()) == 0:
                self.sitFile.setPath(dlg.sitOutPath)
                
    def spliceData(self):
        dlg = SpliceMeasurementDataDialog(self, self.affineFile.getPath(), self.sitFile.getPath(), self.mdList.getFiles())
        dlg.exec_()# == QtWidgets.QDialog.Accepted
                
    def warnbox(self, title, message):
        gui.warnbox(self, title, message)
        
    # override QWidget.closeEvent()
    def closeEvent(self, event):
        self.savePrefs()
        event.accept() # allow window to close - event.ignore() to veto close
        

class ConvertSparseToSITDialog(QtWidgets.QDialog):
    def __init__(self, parent, secSummPath):
        QtWidgets.QDialog.__init__(self, parent)
        
        self.secSummPath = secSummPath
        self.parent = parent
        self.affineOutPath = ""
        self.sitOutPath = ""
        
        self.initGUI()
        self.installPrefs()
        
    def initGUI(self):
        self.setWindowTitle("Convert Sparse Splice to SIT")
        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.setSpacing(20)
        
        self.sparseFile = gui.SingleFilePanel("Sparse Splice")
        self.manCorrFile = gui.SingleFilePanel("Manual Correlation File")
        vlayout.addWidget(self.sparseFile)
        vlayout.addLayout(gui.HelpTextDecorator(self.manCorrFile, "Optional user-defined correlations for off-splice cores. Used in affine table generation.", spacing=0))

        self.useScaledDepths = QtWidgets.QCheckBox("Use Scaled Depths")
        self.lazyAppend = QtWidgets.QCheckBox("Lazy Append")
        vlayout.addLayout(gui.HelpTextDecorator(self.useScaledDepths, "Use section summary's scaled depths to map section depth to total depth."))
        vlayout.addLayout(gui.HelpTextDecorator(self.lazyAppend, "Always use previous core's affine shift for the current APPEND core operation."))
        
        self.affineOutFile = gui.SingleFilePanel("Affine Table", fileType=gui.SingleFilePanel.SaveFile)
        self.sitOutFile = gui.SingleFilePanel("Splice Interval Table", fileType=gui.SingleFilePanel.SaveFile)
        vlayout.addLayout(gui.HelpTextDecorator(self.affineOutFile, "Destination of generated affine file.", spacing=0))
        vlayout.addLayout(gui.HelpTextDecorator(self.sitOutFile, "Destination of generated splice interval table file.", spacing=0))
        
        self.logText = gui.LogTextArea(self.parent, "Log")
        vlayout.addLayout(self.logText.layout)
        
        self.convertButton = QtWidgets.QPushButton("Convert")
        self.convertButton.clicked.connect(self.convert)
        self.closeButton = QtWidgets.QPushButton("Close")
        self.closeButton.clicked.connect(self.close)
        self.closeButton.setDefault(True)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.convertButton)
        hlayout.addWidget(self.closeButton)
        vlayout.addLayout(hlayout)
        
    def installPrefs(self):
        self.sparseFile.setPath(self.parent.prefs.get("lastSparseSplicePath"))
        geom = self.parent.prefs.get("convertSparseWindowGeometry", None)
        if geom is not None:
            self.setGeometry(geom)
     
    def savePrefs(self):
        self.parent.prefs.set("lastSparseSplicePath", self.sparseFile.getPath())
        self.parent.prefs.set("convertSparseWindowGeometry", self.geometry())
        
    def convert(self):
        try:
            validatePath(self.secSummPath, "Section Summary")
            
            sparsePath = self.sparseFile.getPath()
            validatePath(sparsePath, "Sparse Splice")
            
            manCorrPath = None
            if len(self.manCorrFile.getPath()) > 0:
                validatePath(self.manCorrFile.getPath(), "Manual Correlation")
                manCorrPath = self.manCorrFile.getPath()
                
            if len(self.affineOutFile.getPath()) == 0 or len(self.sitOutFile.getPath()) == 0:
                gui.warnbox(self, "Invalid Path", "Specify destination of generated affine and splice files.")
                return
        except InvalidPathError as err:
            gui.warnbox(self, "Invalid Path", err.message)
            return
        
        useScaledDepths = self.useScaledDepths.isChecked()
        lazyAppend = self.lazyAppend.isChecked()
        
        self.affineOutPath = self.affineOutFile.getPath()
        self.sitOutPath = self.sitOutFile.getPath()
        
        self.closeButton.setEnabled(False) # prevent close of dialog
        self.convertButton.setText("Converting...")
        self.convertButton.setEnabled(False)
        
        try:
            logging.getLogger().addHandler(self.logText)
            self.logText.setLevel(logging.DEBUG if self.logText.isVerbose() else logging.INFO)
            self.logText.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            self.logText.logText.clear()
            feldman.convertSparseSplice(self.secSummPath, sparsePath, self.affineOutPath, self.sitOutPath, useScaledDepths, lazyAppend, manCorrPath)
        except KeyError as err:
            gui.warnbox(self, "Process failed", "{}".format("Expected column {} not found".format(err)))
        except:
            err = sys.exc_info()
            gui.warnbox(self, "Process failed", "{}".format("Unhandled error {}: {}".format(err[0], err[1])))
        finally:
            logging.getLogger().removeHandler(self.logText)
            self.closeButton.setEnabled(True)
            self.convertButton.setText("Convert")
            self.convertButton.setEnabled(True)
        
    def closeEvent(self, event):
        self.savePrefs()
        self.accept()


class SpliceMeasurementDataDialog(QtWidgets.QDialog):
    def __init__(self, parent, affinePath, sitPath, mdPaths):
        QtWidgets.QDialog.__init__(self, parent)
        
        self.parent = parent
        
        self.initGUI(affinePath, sitPath, mdPaths)
        self.installPrefs()
        
    def initGUI(self, affinePath, sitPath, mdPaths):
        self.setWindowTitle("Splice Measurement Data")
        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.setSpacing(20)
        
        self.affineFile = gui.SingleFilePanel("Affine Table", fileType=gui.SingleFilePanel.OpenFile)
        self.affineFile.setPath(affinePath)
        self.sitFile = gui.SingleFilePanel("Splice Interval Table", fileType=gui.SingleFilePanel.OpenFile)
        self.sitFile.setPath(sitPath)
        vlayout.addLayout(gui.HelpTextDecorator(self.affineFile, "Affine shifts to apply to data. Should correspond to applied splice.", spacing=0))
        vlayout.addLayout(gui.HelpTextDecorator(self.sitFile, "Splice to apply to data.", spacing=0))
        
        self.includeOffSplice = QtWidgets.QCheckBox("Include Off-Splice Data")
        iosHelpText = "All off-splice rows will be included in spliced data with On-Splice = FALSE."
        vlayout.addLayout(gui.HelpTextDecorator(self.includeOffSplice, iosHelpText))
        
        self.wholeSpliceSection = QtWidgets.QCheckBox("Whole Splice Sections")
        wssHelpText = "All rows in a splice interval's sections, including those outside the interval's depth range, will be included with On-Splice = TRUE."
        vlayout.addLayout(gui.HelpTextDecorator(self.wholeSpliceSection, wssHelpText))
        
        self.mdList = gui.FileListPanel("Measurement Data to be Spliced")
        self.mdList.addFiles(mdPaths)
        vlayout.addWidget(self.mdList)
        
#         self.outputDir = gui.SingleFilePanel("Destination Directory", fileType=gui.SingleFilePanel.Directory)
#         vlayout.addLayout(gui.HelpTextDecorator(self.outputDir, "Directory to which spliced data will be saved with filename [measurement data file]-spliced.csv", spacing=0))
        
        self.logText = gui.LogTextArea(self.parent, "Log")
        vlayout.addLayout(self.logText.layout)

        self.spliceButton = QtWidgets.QPushButton("Splice Data")
        self.spliceButton.clicked.connect(self.splice)
        self.closeButton = QtWidgets.QPushButton("Close")
        self.closeButton.clicked.connect(self.close)
        self.closeButton.setDefault(True)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.spliceButton)
        hlayout.addWidget(self.closeButton)
        vlayout.addLayout(hlayout)
        
    def splice(self):
        if len(self.mdList.getFiles()) == 0:
            gui.warnbox(self, "No Measurement Data", "At least one Measurement Data file is required.")
            return
        
        try:
            affinePath = self.affineFile.getPath()
            validatePath(affinePath, "Affine")
            
            sitPath = self.sitFile.getPath()
            validatePath(sitPath, "Splice Interval Table")
            
            mdPaths = self.mdList.getFiles()
            for mdPath in mdPaths:
                validatePath(mdPath, "Measurement Data")
            
        except InvalidPathError as err:
            gui.warnbox(self, "Invalid Path", err.message)
            return
        
        includeOffSplice = self.includeOffSplice.isChecked()
        wholeSpliceSection = self.wholeSpliceSection.isChecked()
        
        self.closeButton.setEnabled(False) # prevent close of dialog
        self.spliceButton.setText("Splicing Data...")
        self.spliceButton.setEnabled(False)
        
        try:
            logging.getLogger().addHandler(self.logText)
            self.logText.setLevel(logging.DEBUG if self.logText.isVerbose() else logging.INFO)
            self.logText.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            self.logText.logText.clear()
            for mdPath in mdPaths:
                outPath = os.path.splitext(mdPath)[0] + "-spliced.csv"
                feldman.exportMeasurementData(affinePath, sitPath, mdPath, outPath, includeOffSplice, wholeSpliceSection)
        except KeyError as err:
            gui.warnbox(self, "Process failed", "{}".format("Expected column {} not found".format(err)))
        except:
            err = sys.exc_info()
            gui.warnbox(self, "Process failed", "{}".format("Unhandled error {}: {}".format(err[0], err[1])))
        finally:
            logging.getLogger().removeHandler(self.logText)
            self.closeButton.setEnabled(True)
            self.spliceButton.setText("Splice Data")
            self.spliceButton.setEnabled(True)

    def installPrefs(self):
        geom = self.parent.prefs.get("spliceMeasurementDataWindowGeometry", None)
        if geom is not None:
            self.setGeometry(geom)
     
    def savePrefs(self):
        self.parent.prefs.set("spliceMeasurementDataWindowGeometry", self.geometry())

    def closeEvent(self, event):
        self.savePrefs()
        self.accept()    


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec_())