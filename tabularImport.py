'''
Routines and classes for loading of tabular data and conversion to target formats
'''

import os

import numpy
import pandas

class SectionSummary:
    def __init__(self, name, dataframe):
        self.name = name
        self.dataframe = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = readFile(filepath, na_values=['?', '??', '???'])
        return cls(os.path.basename(filepath), dataframe)
    
    def containsCore(self, site, hole, core):
        cores = self._findCores(site, hole, core)
        return not cores.empty
    
    # get unique cores
    # TODO: assumes every core has a Section 1, which may be false - ask Anders
    def getCores(self):
        return self.dataframe[(self.dataframe.Section == '1')]
    
    # return depth of top of top section, bottom of bottom section
    def getCoreRange(self, site, hole, core):
        cores = self._findCores(site, hole, core)
        cores = cores[(cores.Section != "CC")] # omit CC section for time being
        if not cores.empty:
            coremin = cores['TopDepth'].min()
            coremax = cores['BottomDepth'].max()
            return round(coremin, 3), round(coremax, 3)
        return None
    
    # find core in coreList with top depth closest to that of the passed core
    def getCoreWithClosestTop(self, site, hole, core, coreList):
        searchCoreTop = self.getSectionTop(site, hole, core, '1')
        closestCore = None
        mindiff = None
        for corerow in coreList:#self.getCores().iterrows():
            if corerow.Site == site and corerow.Hole == hole and corerow.Core == core: # skip search core - TODO shouldn't be in list since it's not on-splice!
                continue
            diff = abs(corerow.TopDepth - searchCoreTop)
            if mindiff is None or diff < mindiff:
                mindiff = diff
                closestCore = corerow
        print "Closest core top to off-splice {}{}-{} with top MBLF = {}: on-splice {}{}-{} with top MBLF = {}, diff = {}".format(site, hole, core, searchCoreTop, closestCore.Site, closestCore.Hole, closestCore.Core, closestCore.TopDepth, mindiff)
        return closestCore
        
    def getSectionTop(self, site, hole, core, section):
        val = self._getSectionValue(site, hole, core, section, 'TopDepth')
        return round(val, 3)
    
    def getSectionBot(self, site, hole, core, section):
        val = self._getSectionValue(site, hole, core, section, 'BottomDepth')
        return round(val, 3)
    
    def getSectionLength(self, site, hole, core, section):
        val = self._getSectionValue(site, hole, core, section, 'CuratedLength')
        return round(val, 3)
    
    def getSectionCoreType(self, site, hole, core, section):
        return self._getSectionValue(site, hole, core, section, 'CoreType')
    
    def getSectionAtDepth(self, site, hole, core, depth):
        sec = self._findSectionAtDepth(site, hole, core, depth)
        return sec
    
    def sectionDepthToTotal(self, site, hole, core, section, secDepth):
        top = self.getSectionTop(site, hole, core, section)
        result = top + secDepth / 100.0 # cm to m
        #print "section depth {} in section {} = {} overall".format(secDepth, section, result)        
        return result
    
    def _findCores(self, site, hole, core):
        df = self.dataframe
        cores = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core)]
        if cores.empty:
            print "SectionSummary: Could not find core {}-{}{}".format(site, hole, core)
        return cores
        

    def _findSection(self, site, hole, core, section):
        df = self.dataframe
        section = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core) & (df.Section == section)]
        if section.empty:
            print "SectionSummary: Could not find {}-{}{}-{}".format(site, hole, core, section)
        return section
    
    def _findSectionAtDepth(self, site, hole, core, depth):
        df = self.dataframe
        section = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core) & (depth >= df.TopDepth) & (depth <= df.BottomDepth)]
        if not section.empty:
            return section.iloc[0]['Section']
        return None
    
    def _getSectionValue(self, site, hole, core, section, columnName):
        section = self._findSection(site, hole, core, section)
        return section.iloc[0][columnName]
    
class AffineTable:
    def __init__(self, name, dataframe):
        self.name = name
        self.dataframe = dataframe

class SpliceIntervalTable:
    def __init__(self, name, dataframe):
        self.name = name
        self.dataframe = dataframe

""" bridge between imported tabular columns and destination format """ 
class TabularFormat:
    req = [] # list of required column names
    strCols = [] # list of columns whose pandas dtype should be forced to string
    def __init__(self, name, req, strCols):
        self.name = name
        self.req = req
        self.strCols = strCols

MeasurementFormat = TabularFormat("Measurement Data",
                                  ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'Section', 'TopOffset', 'BottomOffset', 'Depth', 'Data'],
                                  ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'Section'])
SampleFormat = TabularFormat("Sample Data",
                             ['Exp', 'Site', 'Hole', 'Core', 'Tool', 'Section', 'SectionDepth', 'Depth', 'Data'],
                             ['Exp', 'Site', 'Hole', 'Core', 'Tool', 'Section'])
SectionSummaryFormat = TabularFormat("Section Summary", 
                                     ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'Section', 'TopDepth', 'BottomDepth', 'CuratedLength'],
                                     ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'Section'])

AffineFormat = TabularFormat("Affine Table",
                             ['Site', 'Hole', 'Core', 'Core Type', 'Depth CSF (m)', 'Depth CCSF (m)', \
                              'Cumulative Offset (m)', 'Differential Offset (m)', 'Growth Rate', 'Shift Type', \
                              'Data Used', 'Quality Comment'],
                             ['Site', 'Hole', 'Core', 'Core Type', 'Shift Type', 'Data Used', 'Quality Comment'])

# Splice Interval Table headers: 2.0.2 b8 and earlier
# brg 1/18/2016: keeping for now, may want to convert from this format
SITFormat_202_b8 = TabularFormat("Splice Interval Table 2.0.2 b8 and earlier",
                          ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'TopSection', 'TopOffset', \
                           'TopDepthCSF', 'TopDepthCCSF', 'BottomSection', 'BottomOffset', 'BottomDepthCSF', \
                           'BottomDepthCCSF', 'SpliceType', 'DataUsed', 'Comment'],
                          ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'TopSection', 'BottomSection', 'SpliceType', 'DataUsed', 'Comment'])

SITFormat = TabularFormat("Splice Interval Table",
                          ['Site', 'Hole', 'Core', 'Core Type', 'Top Section', 'Top Offset', \
                           'Top Depth CSF-A', 'Top Depth CCSF-A', 'Bottom Section', 'Bottom Offset', 'Bottom Depth CSF-A', \
                           'Bottom Depth CCSF-A', 'Splice Type', 'Data Used', 'Comment'],
                          ['Site', 'Hole', 'Core', 'Core Type', 'Top Section', 'Bottom Section', 'Splice Type', 'Data Used', 'Comment'])


# Format for exported core data...may not need RunNo, RawDepth or Offset any longer?
CoreExportFormat = TabularFormat("Exported Core Data",
                                 ['Exp', 'Site', 'Hole', 'Core', 'CoreType',
                                  'Section', 'TopOffset', 'BottomOffset', 'Depth',
                                  'Data', 'RunNo', 'RawDepth', 'Offset'],
                                 ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'Section','RunNo'])

MeasurementExportFormat = TabularFormat("Spliced Measurement Data",
                                 ['Exp', 'Site', 'Hole', 'Core', 'CoreType',
                                  'Section', 'TopOffset', 'BottomOffset', 'Depth', 'Data', 'RawDepth', 'Offset'],
                                 ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'Section'])

SampleExportFormat = TabularFormat("Spliced Sample Data",
                                 ['Exp', 'Site', 'Hole', 'Core', 'Tool',
                                  'Section', 'SectionDepth', 'Depth', 'Data', 'Offset'],
                                 ['Exp', 'Site', 'Hole', 'Core', 'Tool', 'Section'])


def readFile(filepath, na_values=None):
    srcfile = open(filepath, 'rU')
    # todo: 4/29/2016 add na_values = ['?','??'...] - this forced ?s to NaN, allowing
    # depth columns to be loaded as type float64. Otherwise, manual deletion of such rows
    # is required. Unfortunately there's no way to warn user of such rows. Pre-processing
    # CSVs with python built-in library, then handing those rows off to pandas is one way
    # to address this, but for now the na_values should be purt good.  
    dataframe = pandas.read_csv(srcfile, sep=None, skipinitialspace=True, na_values=na_values, engine='python')
    srcfile.close()
    return dataframe

def writeToFile(dataframe, filepath):
    dataframe.to_csv(filepath, index=False)

""" find column names in dataframe matching those required by format """
def findFormatColumns(dataframe, format):
    colmap = dict().fromkeys(format.req)
    for key in colmap.keys():
        if key in dataframe.dtypes.keys():
            colmap[key] = dataframe.columns.get_loc(key)
    return colmap

""" returns new dataframe with columns in order specified by colmap """
def reorderColumns(dataframe, colmap, format):
    newmap = {}
    for colName in colmap.keys():
        index = colmap[colName]
        if index is not None:
            newmap[colName] = dataframe.icol(index)
    df = pandas.DataFrame(newmap, columns=format.req)
    return df

""" strip whitespace from dataframe cells """ 
def stripCells(dataframe):
    for c in dataframe.columns:
        try:
            dataframe[c] = dataframe[c].str.strip()
        except:
            pass

def destroyStrings(col, df):
    print "DESTROYING STRINGS"
    df[col] = df[col].apply(lambda x: "" if type(x) is str else x)
    print df[col]

def forceColumnFloat64(col, df):
    try:
        forcedCol = df[col].astype(numpy.float64)
    except ValueError:
        raise
    return forcedCol
        
def forceColumnDtype(col, df, dtype):
    try:
        forcedCol = df[col].astype(dtype)
    except ValueError:
        pass

def forceFloatDatatype(cols, dataframe, destroy=False):
    for col in cols:
        forcedCol = None
        try:
            forcedCol = forceColumnFloat64(col, dataframe)
        except ValueError:
            print "Couldn't convert column {} to float64 datatype".format(col)
            if destroy:
                destroyStrings(col, dataframe)
                forcedCol = forceColumnFloat64(col, dataframe)
        if forcedCol is not None:
            dataframe[col] = forcedCol

# force pandas column dtype and convert values to object (string)
def forceStringDatatype(cols, dataframe):
    for col in cols:
        dataframe[col] = dataframe[col].astype(object)
        dataframe[col] = dataframe[col].apply(lambda x: str(x)) # todo: if x != NaN? to avoid line below?
        
        # forced string conversion forces all NaN values to the string "nan" - remove these
        dataframe[col] = dataframe[col].apply(lambda x: "" if x == "nan" else x)