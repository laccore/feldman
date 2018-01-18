'''
Created on Jan 11, 2018

Utility logic for Pandas, to which the software remains tightly coupled. 

@author: bgrivna
'''

import unittest

import numpy
import pandas

from coreIdentity import parseIdentity

def readFile(filepath, nrows=None, na_values=None, sep=None, skipinitialspace=True, engine='python', mode='rU'):
    with open(filepath, mode) as srcfile:
    # todo: 4/29/2016 add na_values = ['?','??'...] - this forced ?s to NaN, allowing
    # depth columns to be loaded as type float64. Otherwise, manual deletion of such rows
    # is required. Unfortunately there's no way to warn user of such rows. Pre-processing
    # CSVs with python built-in library, then handing those rows off to pandas is one way
    # to address this, but for now the na_values should be purt good.  
        dataframe = pandas.read_csv(srcfile, nrows=nrows, sep=sep, skipinitialspace=skipinitialspace, na_values=na_values, engine=engine)
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

def splitSectionID(dataframe, sidcol='SectionID'):
    coreids = []
    for _, row in dataframe.iterrows():
        coreids.append(parseIdentity(row[sidcol]))
        
    sidIndex = dataframe.columns.get_loc(sidcol)
    
    nameValues = [] # elt is tuple (column name, list of column values)

    if coreids[0].name: # assume first CoreIdentity is representative
        nameValues.append(('Name', [c.name for c in coreids]))
    nameValues.append(('Site', [c.site for c in coreids]))
    nameValues.append(('Hole', [c.hole for c in coreids]))
    nameValues.append(('Core', [c.core for c in coreids]))
    nameValues.append(('Tool', [c.tool for c in coreids]))
    nameValues.append(('Section', [c.section for c in coreids]))
    insert_contiguous(dataframe, sidIndex + 1, nameValues)
    
def insert_contiguous(dataframe, index, nameValuesList):
    for count, nvtup in enumerate(nameValuesList):
        dataframe.insert(index + count, nvtup[0], nvtup[1])

def isNumeric(dtype):
    return isFloat(dtype) or isInteger(dtype)

def isFloat(dtype):
    return dtype == numpy.float64

def isInteger(dtype):
    return dtype == numpy.int64

# For each column in list cols, force pandas column dtype and convert values to object (string)
def forceStringDatatype(cols, dataframe):
    for col in cols:
        dataframe[col] = dataframe[col].astype(object)
        dataframe[col] = dataframe[col].apply(lambda x: str(x)) # todo: if x != NaN? to avoid line below?
        
        # forced string conversion forces all NaN values to the string "nan" - remove these
        dataframe[col] = dataframe[col].apply(lambda x: "" if x == "nan" else x)


class Tests(unittest.TestCase):
    def test_readFile(self):
        df = readFile("../testdata/GLAD9_SectionSummary.csv")
        self.assertFalse(df.empty)
        
    def test_readHeaders(self):
        hs = readHeaders("../testdata/GLAD9_SectionSummary.csv")
        self.assertTrue(len(hs) == 9)
        self.assertTrue('Site' in hs)
        self.assertTrue('CuratedLength' in hs)
        
if __name__ == "__main__":
    unittest.main()