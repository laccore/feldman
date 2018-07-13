'''
Created on Jul 30, 2017

@author: bgrivna
'''

import os, sys, user, logging, traceback

from PyQt5 import QtWidgets, QtCore

import feldman
import gui
import prefs
import tabular.pandasutils as PU
import tracker

class InvalidPathError(Exception):
    pass

        
def validatePath(path, filetype):
    if not os.path.exists(path):
        raise InvalidPathError("{} file '{}' does not exist".format(filetype, path))
    
def getFloatCols(filepath):
    df = PU.readFileMinimal(filepath)
    cols = [c for c in df.columns if df[c].dtype == 'float64']
    return cols

class MainWindow(QtWidgets.QWidget):
    def __init__(self, app):
        QtWidgets.QWidget.__init__(self)
        self.app = app
        self.outputVocabDict = {"IODP": "IODP (Core Type)", "LacCore": "LacCore (Tool)"}

        self.initGUI()
        self.initPrefs()
        self.pingTracker()
            
    def updateVocabulary(self, text):
        vocabkey = [k for k,v in self.outputVocabDict.items() if v == text][0]
        feldman.OutputVocabulary = vocabkey

    def initGUI(self):
        self.setWindowTitle("Feldman {}".format(feldman.FeldmanVersion))
        
        vlayout = QtWidgets.QVBoxLayout(self)
        self.orgLabel = QtWidgets.QLabel("Output Vocabulary:")
        self.orgCombo = QtWidgets.QComboBox()
        self.orgCombo.addItems(self.outputVocabDict.values())
        self.orgCombo.currentTextChanged.connect(self.updateVocabulary)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addStretch(1) # center label + combo
        hlayout.addWidget(self.orgLabel)
        hlayout.addWidget(self.orgCombo)
        hlayout.addStretch(1) # center label + combo
        vlayout.addLayout(hlayout)
        self.sparseToSitButton = QtWidgets.QPushButton("Convert Sparse Splice to SIT")
        self.sparseToSitButton.clicked.connect(self.sparseToSit)
        self.spliceDataButton = QtWidgets.QPushButton("Splice Measurement Data")
        self.spliceDataButton.clicked.connect(self.spliceData)
        btnlayout = QtWidgets.QHBoxLayout()
        btnlayout.addWidget(self.sparseToSitButton)
        btnlayout.addWidget(self.spliceDataButton)
        vlayout.addLayout(btnlayout)
        vlayout.layout()
        
    def initPrefs(self):
        prefDir = os.path.join(user.home, ".feldman")
        if not os.path.exists(prefDir):
            os.mkdir(prefDir)
        prefPath = os.path.join(prefDir, "prefs.pk")
        self.prefs = prefs.Prefs(prefPath)
        self.installPrefs()
        
    def installPrefs(self):
        geom = self.prefs.get("windowGeometry", None)
        if geom is not None:
            self.setGeometry(geom)
        vocab = self.prefs.get("outputVocabulary", "IODP")
        self.orgCombo.setCurrentText(self.outputVocabDict[vocab])

    def pingTracker(self):
        uuidPath = os.path.join(user.home, ".feldman", "uuid.p") # .feldman dir created in initPrefs()
        gatracker = tracker.Tracker(uuidPath, ["UA", "116679909", "1"])
        gatracker.ping()
    
    def savePrefs(self):
        self.prefs.set("windowGeometry", self.geometry())
        self.prefs.set("outputVocabulary", feldman.OutputVocabulary)
        self.prefs.write()
        
    def sparseToSit(self):
        dlg = ConvertSparseToSITDialog(self)
        dlg.exec_()# == QtWidgets.QDialog.Accepted
                
    def spliceData(self):
        dlg = SpliceMeasurementDataDialog(self)
        dlg.exec_()# == QtWidgets.QDialog.Accepted
                
    def warnbox(self, title, message):
        gui.warnbox(self, title, message)
        
    # override QWidget.closeEvent()
    def closeEvent(self, event):
        self.savePrefs()
        event.accept() # allow window to close - event.ignore() to veto close
        

class ConvertSparseToSITDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        self.parent = parent
        self.initGUI()
        self.installPrefs()
        
    def initGUI(self):
        self.setWindowTitle("Convert Sparse Splice to SIT")
        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.setSpacing(20)
        
        self.secSummFile = gui.SingleFilePanel("Section Summary")
        self.sparseFile = gui.SingleFilePanel("Sparse Splice")
        self.manCorrFile = gui.SingleFilePanel("Manual Correlation")
        vlayout.addWidget(self.secSummFile)
        vlayout.addWidget(self.sparseFile)
        vlayout.addLayout(gui.HelpTextDecorator(self.manCorrFile, "Optional. User-defined ties or offsets for off-splice cores override default affine shifts. See manual for details.", spacing=0))

        self.useScaledDepths = QtWidgets.QCheckBox("Use Scaled Depths")
        self.lazyAppend = QtWidgets.QCheckBox("Lazy Append")
        vlayout.addLayout(gui.HelpTextDecorator(self.useScaledDepths, "Use section summary's scaled depths to map section depth to total depth. Unscaled depths are the default."))
        vlayout.addLayout(gui.HelpTextDecorator(self.lazyAppend, "Always use previous core's affine shift for the current APPEND core operation."))
        
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
        self.secSummFile.setPathIfExists(self.parent.prefs.get("lastSectionSummaryPath"))
        self.sparseFile.setPathIfExists(self.parent.prefs.get("lastSparseSplicePath"))
        geom = self.parent.prefs.get("convertSparseWindowGeometry", None)
        if geom is not None:
            self.setGeometry(geom)
     
    def savePrefs(self):
        self.parent.prefs.set("lastSectionSummaryPath", self.secSummFile.getPath())
        self.parent.prefs.set("lastSparseSplicePath", self.sparseFile.getPath())
        self.parent.prefs.set("convertSparseWindowGeometry", self.geometry())
        
    def convert(self):
        try:
            secSummPath = self.secSummFile.getPath()
            validatePath(secSummPath, "Section Summary")
            
            sparsePath = self.sparseFile.getPath()
            validatePath(sparsePath, "Sparse Splice")
            
            manCorrPath = None
            if len(self.manCorrFile.getPath()) > 0:
                validatePath(self.manCorrFile.getPath(), "Manual Correlation")
                manCorrPath = self.manCorrFile.getPath()
                
        except InvalidPathError as err:
            gui.warnbox(self, "Invalid Path", err.message)
            return
        
        useScaledDepths = self.useScaledDepths.isChecked()
        lazyAppend = self.lazyAppend.isChecked()
        
        basePath, ext = os.path.splitext(sparsePath)
        affineOutPath = basePath + "-Affine" + ext
        sitOutPath = basePath + "-SIT" + ext
        
        self.closeButton.setEnabled(False) # prevent close of dialog
        self.convertButton.setText("Converting...")
        self.convertButton.setEnabled(False)
        
        try:
            logging.getLogger().addHandler(self.logText)
            self.logText.setLevel(logging.DEBUG if self.logText.isVerbose() else logging.INFO)
            self.logText.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            self.logText.logText.clear()
            feldman.convertSparseSplice(secSummPath, sparsePath, affineOutPath, sitOutPath, useScaledDepths, lazyAppend, manCorrPath)
        except KeyError as err:
            gui.warnbox(self, "Process failed", "{}".format("Expected column {} not found".format(err)))
            logging.error(traceback.format_exc())
        except:
            err = sys.exc_info()
            gui.warnbox(self, "Process failed", "{}".format("Unhandled error {}: {}".format(err[0], err[1])))
            logging.error(traceback.format_exc())
        finally:
            logging.getLogger().removeHandler(self.logText)
            self.closeButton.setEnabled(True)
            self.convertButton.setText("Convert")
            self.convertButton.setEnabled(True)
        
    def closeEvent(self, event):
        self.savePrefs()
        self.accept()


class SpliceMeasurementDataDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        
        self.parent = parent
        
        self.initGUI()
        self.installPrefs()
        
    def initGUI(self):
        self.setWindowTitle("Splice Measurement Data")
        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.setSpacing(20)
        
        self.affineFile = gui.SingleFilePanel("Affine Table", fileType=gui.SingleFilePanel.OpenFile)
        self.sitFile = gui.SingleFilePanel("Splice Interval Table", fileType=gui.SingleFilePanel.OpenFile)
        vlayout.addLayout(gui.HelpTextDecorator(self.affineFile, "Affine shifts to apply to data. Should correspond to applied splice.", spacing=0))
        vlayout.addLayout(gui.HelpTextDecorator(self.sitFile, "Splice to apply to data.", spacing=0))
        
        self.mdList = gui.FileTablePanel("Measurement Data to be Spliced", getFloatCols)
        vlayout.addWidget(self.mdList)
        
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
        
        # gather and validate paths
        try:
            affinePath = self.affineFile.getPath()
            validatePath(affinePath, "Affine")
            
            sitPath = self.sitFile.getPath()
            validatePath(sitPath, "Splice Interval Table")
            
            spliceParams = self.mdList.getFiles()
            
        except InvalidPathError as err:
            gui.warnbox(self, "Invalid Path", err.message)
            return
        
        self.closeButton.setEnabled(False) # prevent close of dialog
        self.spliceButton.setText("Splicing Data...")
        self.spliceButton.setEnabled(False)
        
        # splice measurement data
        try:
            logging.getLogger().addHandler(self.logText)
            self.logText.setLevel(logging.DEBUG if self.logText.isVerbose() else logging.INFO)
            self.logText.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            self.logText.logText.clear()
            for mdPath, depthColumn, includeOffSplice, wholeSpliceSection in spliceParams:
                outPath = os.path.splitext(mdPath)[0] + "-spliced.csv"
                feldman.exportMeasurementData(affinePath, sitPath, mdPath, outPath, depthColumn, includeOffSplice, wholeSpliceSection)
        except KeyError as err:
            gui.warnbox(self, "Process failed", "{}".format("Expected column {} not found".format(err)))
            logging.error(traceback.format_exc())
        except:
            err = sys.exc_info()
            gui.warnbox(self, "Process failed", "{}".format("Unhandled error {}: {}".format(err[0], err[1])))
            logging.error(traceback.format_exc())
        finally:
            logging.getLogger().removeHandler(self.logText)
            self.closeButton.setEnabled(True)
            self.spliceButton.setText("Splice Data")
            self.spliceButton.setEnabled(True)

    def installPrefs(self):
        geom = self.parent.prefs.get("spliceMeasurementDataWindowGeometry", None)
        if geom is not None:
            self.setGeometry(geom)
        self.affineFile.setPathIfExists(self.parent.prefs.get("affineTable"))
        self.sitFile.setPathIfExists(self.parent.prefs.get("spliceIntervalTable"))
        mdPaths = self.parent.prefs.get("measurementDataPaths")
        self.mdList.addFiles([path for path in mdPaths if os.path.exists(path)])
     
    def savePrefs(self):
        self.parent.prefs.set("spliceMeasurementDataWindowGeometry", self.geometry())
        self.parent.prefs.set("affineTable", self.affineFile.getPath())
        self.parent.prefs.set("spliceIntervalTable", self.sitFile.getPath())
        self.parent.prefs.set("measurementDataPaths", [p[0] for p in self.mdList.getFiles()])

    def closeEvent(self, event):
        self.savePrefs()
        self.accept()    


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec_())