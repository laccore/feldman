'''
Created on Jan 24, 2018

@author: bgrivna
'''

import logging as log
import unittest

import pandas

import pandasutils as PU
import columns as TC

class FormatError(Exception):
    pass

# read CSV from filepath, map columns to given format, and split SiteHole column if needed
def createWithCSV(filepath, fmt):
    log.info("Creating {} with {}...".format(fmt.name, filepath))
    dataframe = PU.readFile(filepath, na_values=['?', '??', '???'])
    
    # split compounds
    dataframe = splitSiteHole(dataframe)
    
    # map format columns to input columns
    colmap = TC.map_columns(fmt.cols, list(dataframe.columns))
    
    if len(colmap) != len(fmt.cols):
        # if required columns are missing, bail out
        missingReq = [c.name for c in fmt.cols if not c.optional and c.name not in colmap]
        if len(missingReq) > 0:
            raise FormatError("Format {} requires missing columns {}".format(fmt.name, missingReq))
        
        # if optional columns are missing, add them and fill with column default value 
        missingOpt = [c for c in fmt.cols if c.optional and c.name not in colmap]
        for cid in missingOpt:
            PU.appendColumn(dataframe, cid.name, cid.getDefaultValue())
            colmap[cid.name] = cid.name
    
    reverseColmap = {v: k for k,v in colmap.iteritems()}
    PU.renameColumns(dataframe, reverseColmap) # use format column names
    log.info("Column map: {}".format(["{} -> {}".format(k,v) for k,v in reverseColmap.iteritems()]))
    PU.forceStringDatatype(dataframe, [col.name for col in fmt.cols if col.isString()])

    return dataframe

# write a DataFrame to a CSV at the given path, removing Site and Hole
# columns if a SiteHole column is present
def writeToCSV(dataframe, filepath):
    dataframe = dropSiteHole(dataframe)
    PU.writeToFile(dataframe, filepath)

# split data of form [numeric][alphabetic] into separate columns
def splitCompoundColumn(df, colname):
    cols = TC.split_caps(colname)
    splitPattern = "(?P<{}>[0-9]+)(?P<{}>[A-Z]+)".format(cols[0], cols[1])
    return df[colname].str.extract(splitPattern)

# split compound SiteHole column into separate Site and Hole columns
def splitSiteHole(df):
    shName = TC.find_match("SiteHole", list(df.columns))
    if shName is not None and 'Site' not in df and 'Hole' not in df:
        sitehole = splitCompoundColumn(df, shName)
        df = pandas.concat([df, sitehole], axis=1, join_axes=[df.index])
        log.info("Split {} column into Site and Hole".format(shName))
    return df

# remove split Site and Hole columns if they and compound SiteHole are present
def dropSiteHole(df):
    shName = TC.find_match("SiteHole", list(df.columns))
    if shName is not None and shName in df and 'Site' in df and 'Hole' in df: # remove added Site and Hole columns if necessary
        df = df.drop(["Site", 'Hole'], axis=1)
    return df

# can the given filepath be used to create TabularFormat fmt?
# TODO: account for splitting of SiteHole
def canCreateWithFile(filepath, fmt):
    headers = PU.readHeaders(filepath)
    colmap = TC.map_columns(fmt.cols, headers)
    missingRequiredColumns = [c.name for c in fmt.cols if not c.optional and c.name not in colmap]
    canCreate = len(missingRequiredColumns) == 0
    return canCreate

def validData(filepath, fmt, colmap):
    valid = False
    # read full file
    df = PU.readFile(filepath)
    colmap = TC.map_columns(fmt.cols, list(df.columns))
    # apply colmap
    PU.renameColumns(df, {v: k for k,v in colmap.iteritems()})
    # validate contents of columns
    for fmtcol in fmt.cols:
        if fmtcol.name in df:
            pass
    # TODO: perform format-specific validation (e.g. TopDepth >= BottomDepth for each row of a SectionSummary)
    return valid


class Tests(unittest.TestCase):
    def test_compound(self):
        df = pandas.DataFrame({'SiteHole': ['1A', '2B']})
        splitdf = splitCompoundColumn(df, 'SiteHole')
        self.assertTrue(splitdf['Site'][0] == '1')
        self.assertTrue(splitdf['Site'][1] == '2')
        self.assertTrue(splitdf['Hole'][0] == 'A')
        self.assertTrue(splitdf['Hole'][1] == 'B')
    
    def test_sitehole(self):
        df = pandas.DataFrame({'Site': ['1','2'], 'Hole': ['A', 'B']})
        self.assertTrue(len(splitSiteHole(df).columns) == 2) # no split needed
        PU.appendColumn(df, 'SiteHole', '3C')
        self.assertTrue(len(splitSiteHole(df).columns) == 3) # still not needed, has Site and Hole
        df.drop(['Site', 'Hole'], axis=1)
        self.assertTrue(len(splitSiteHole(df).columns) == 3) # Site and Hole re-added
        self.assertTrue(len(dropSiteHole(df).columns) == 1) # Site and Hole dropped
    
if __name__ == "__main__":
    log.basicConfig(level=log.DEBUG)
    unittest.main()
