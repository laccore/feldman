'''
Created on Jan 11, 2018

Utility logic for Pandas, to which the software remains tightly coupled. 

@author: bgrivna
'''

import logging as log
import unittest

import numpy
import pandas

from columns import find_match, find_all_starts_with


# default utf-8-sig encoding ignores Byte Order Mark (BOM)
def readFile(filepath, nrows=None, na_values=None, sep=None, skipinitialspace=True,
             engine='python', mode='rU', encoding='utf-8-sig'):
    success = False
    with open(filepath, mode) as srcfile:
        try:
            dataframe = pandas.read_csv(srcfile, nrows=nrows, sep=sep, skipinitialspace=skipinitialspace,
                                        na_values=na_values, engine=engine, encoding=encoding)
            success = True
        except UnicodeDecodeError, msg:
            log.warn("Couldn't decode file in {} encoding: {}".format(encoding, msg))
    
    if not success:
        log.warn("Attempting to open with default encoding...")
        with open(filepath, mode) as srcfile:
            dataframe = pandas.read_csv(srcfile, nrows=nrows, sep=sep, skipinitialspace=skipinitialspace,
                                        na_values=na_values, engine=engine) # try default encoding
        
    return dataframe

# Return minimal dataframe with headers and first row of data.
# Useful for validation etc without loading every row of data,
# which can be slow with large files
def readFileMinimal(filepath):
    dataframe = readFile(filepath, nrows=1) # nrows = 1 because nrows = 0 throws StopIterator
    return dataframe

def readHeaders(filepath):
    return list(readFileMinimal(filepath).columns)

def writeToFile(dataframe, filepath):
    dataframe.to_csv(filepath, index=False)

def renameColumns(dataframe, colmap):
    dataframe.rename(columns=colmap, inplace=True)
    
def getColumnIndex(dataframe, colname):
    dfname = find_match(colname, list(dataframe.columns))
    return dataframe.columns.get_loc(dfname) if dfname else None

# return index of first column in dataframe starting with startstr
# after las() is applied to both strings
def getFirstColumnStartingWith(dataframe, startstr):
    dfname = find_all_starts_with(startstr, list(dataframe.columns))
    if len(dfname) > 0:
        maxidx = min([dataframe.columns.get_loc(n) for n in dfname])
    else:
        return None
    return maxidx

# return index of last column in dataframe starting with startstr
# after las() is applied to both strings
def getLastColumnStartingWith(dataframe, startstr):
    colnames = find_all_starts_with(startstr, list(dataframe.columns))
    if len(colnames) > 0:
        max_idx = max([dataframe.columns.get_loc(n) for n in colnames])
    else:
        return None
    return max_idx

# Insert a column into dataframe for each (column name, values) tuple in nameValuesList,
# starting at the specified index.
def insertColumns(dataframe, index, nameValuesList):
    for count, nvtup in enumerate(nameValuesList):
        dataframe.insert(index + count, nvtup[0], nvtup[1])

# Insert one column into dataframe at specified index 
def insertColumn(dataframe, index, name, valOrList):
    dataframe.insert(index, name, valOrList)

# Insert one column at end of dataframe
def appendColumn(dataframe, name, valOrList):
    insertColumn(dataframe, len(dataframe.columns), name, valOrList)

def isNumeric(dtype):
    return isFloat(dtype) or isInteger(dtype)

def isFloat(dtype):
    return dtype == numpy.float64

def isInteger(dtype):
    return dtype == numpy.int64

# For each column in list cols, force pandas column dtype and convert values to object (string)
def forceStringDatatype(dataframe, cols):
    for col in cols:
        dataframe[col] = dataframe[col].astype(object)
        dataframe[col] = dataframe[col].apply(lambda x: str(x)) # todo: if x != NaN? to avoid line below?
        
        # forced string conversion forces all NaN values to the string "nan" - remove these
        dataframe[col] = dataframe[col].apply(lambda x: "" if x == "nan" else x)
        

# legacy tabularImport methods - just in case
# """ strip whitespace from dataframe cells """ 
# def stripCells(dataframe):
#     for c in dataframe.columns:
#         try:
#             dataframe[c] = dataframe[c].str.strip()
#         except:
#             pass
# 
# def destroyStrings(col, df):
#     print "DESTROYING STRINGS"
#     df[col] = df[col].apply(lambda x: "" if type(x) is str else x)
#     print df[col]
# 
# def forceColumnFloat64(col, df):
#     try:
#         forcedCol = df[col].astype(numpy.float64)
#     except ValueError:
#         raise
#     return forcedCol
#         
# def forceColumnDtype(col, df, dtype):
#     try:
#         forcedCol = df[col].astype(dtype)
#     except ValueError:
#         pass
# 
# def forceFloatDatatype(cols, dataframe, destroy=False):
#     for col in cols:
#         forcedCol = None
#         try:
#             forcedCol = forceColumnFloat64(col, dataframe)
#         except ValueError:
#             print "Couldn't convert column {} to float64 datatype".format(col)
#             if destroy:
#                 destroyStrings(col, dataframe)
#                 forcedCol = forceColumnFloat64(col, dataframe)
#         if forcedCol is not None:
#             dataframe[col] = forcedCol
#""" returns new dataframe with columns in order specified by colmap """
# def reorderColumns(dataframe, colmap, fmt):
#     newmap = {}
#     for colName in colmap.keys():
#         index = colmap[colName]
#         if index is not None:
#             newmap[colName] = dataframe.icol(index)
#     df = pandas.DataFrame(newmap, columns=fmt.req)
#     return df


class Tests(unittest.TestCase):
    def test_readFile(self):
        df = readFile("../testdata/GLAD9_SectionSummary.csv")
        self.assertFalse(df.empty)
        
    def test_readHeaders(self):
        hs = readHeaders("../testdata/GLAD9_SectionSummary.csv")
        self.assertTrue(len(hs) == 10)
        self.assertTrue('Site' in hs)
        self.assertTrue('CuratedLength' in hs)
        
    def test_utf8err(self):
        df = readFile("../testdata/utf8err.csv")
        self.assertTrue(len(df) == 2)
        
    def test_utf8bom_blanklines(self):
        df = readFile("../testdata/utf8_bom_blanklines.csv")
        self.assertTrue(len(df) == 4)

    def test_getColumnStartingWith(self):
        df = readFile("../testdata/GLAD9_Site1_XRF.csv")
        lastidx = getFirstColumnStartingWith(df, "Sediment Depth")
        self.assertTrue(lastidx == 10)

    def test_getLastColumnStartingWith(self):
        df = readFile("../testdata/GLAD9_Site1_XRF.csv")
        lastidx = getLastColumnStartingWith(df, "Sediment Depth")
        self.assertTrue(lastidx == 11)
        
if __name__ == "__main__":
    log.basicConfig(level=log.DEBUG)
    unittest.main()