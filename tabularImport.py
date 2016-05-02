'''
Routines and classes for loading of tabular data and conversion to target formats
'''

import os

import numpy
import pandas
    
class AffineTable:
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

SampleFormat = TabularFormat("Sample Data",
                             ['Exp', 'Site', 'Hole', 'Core', 'Tool', 'Section', 'SectionDepth', 'Depth', 'Data'],
                             ['Exp', 'Site', 'Hole', 'Core', 'Tool', 'Section'])

AffineFormat = TabularFormat("Affine Table",
                             ['Site', 'Hole', 'Core', 'Core Type', 'Depth CSF (m)', 'Depth CCSF (m)', \
                              'Cumulative Offset (m)', 'Differential Offset (m)', 'Growth Rate', 'Shift Type', \
                              'Data Used', 'Quality Comment'],
                             ['Site', 'Hole', 'Core', 'Core Type', 'Shift Type', 'Data Used', 'Quality Comment'])


# Format for exported core data...may not need RunNo, RawDepth or Offset any longer?
CoreExportFormat = TabularFormat("Exported Core Data",
                                 ['Exp', 'Site', 'Hole', 'Core', 'CoreType',
                                  'Section', 'TopOffset', 'BottomOffset', 'Depth',
                                  'Data', 'RunNo', 'RawDepth', 'Offset'],
                                 ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'Section','RunNo'])


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