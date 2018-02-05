'''
Created on Jan 24, 2018

@author: bgrivna
'''

import logging as log

import pandas

import pandasutils as PU
import columns as TC

class FormatError(Exception):
    pass

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
    
    PU.renameColumns(dataframe, {v: k for k,v in colmap.iteritems()}) # use format column names
    PU.forceStringDatatype(dataframe, [col.name for col in fmt.cols if col.isString()])

    return dataframe

def writeToCSV(dataframe, filepath):
    dataframe = dropSiteHole(dataframe)
    PU.writeToFile(dataframe, filepath)


def splitCompoundColumn(df, colname):
    cols = TC.split_caps(colname)
    splitPattern = "(?P<{}>[0-9]+)(?P<{}>[A-Z]+)".format(cols[0], cols[1])
    return df[colname].str.extract(splitPattern)


# split SiteHole column into separate Site and Hole columns
def splitSiteHole(df):
    shName = TC.find_match("SiteHole", list(df.columns))
    if shName is not None and 'Site' not in df and 'Hole' not in df:
        sitehole = splitCompoundColumn(df, shName)
        df = pandas.concat([df, sitehole], axis=1, join_axes=[df.index])
    return df
        
def dropSiteHole(df):
    shName = TC.find_match("SiteHole", list(df.columns))
    if shName is not None and shName in df and 'Site' in df and 'Hole' in df: # remove added Site and Hole columns if necessary
        df = df.drop(["Site", 'Hole'], axis=1)
    return df


# TODO: validation methods
def canCreateWithFile(self, filepath, fmt):
    canCreate = False
    # read headers
    headers = PU.readHeaders(filepath)
    colmap = TC.map_columns(fmt, headers)
    # can columns be mapped to format?
    if len(colmap) == len(fmt):
        canCreate = True
    return canCreate

def validData(self, filepath, fmt, colmap):
    valid = False
    # read full file
    df = PU.readFile(filepath)
    colmap = TC.map_columns(fmt, list(df.columns))
    # apply colmap
    PU.renameColumns(df, {v: k for k,v in colmap.iteritems()})
    # validate contents of columns
    for fmtcol in fmt:
        if fmtcol.name in df:
            pass
    # perform format-specific validation (e.g. TopDepth >= BottomDepth for each row of a SectionSummary)
    return valid
