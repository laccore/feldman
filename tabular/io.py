'''
Created on Jan 24, 2018

@author: bgrivna
'''

import logging as log

import pandas

import pandasutils as PU
import columns as TC
from data.columns import namesToIds # data -> laccore?
from coreIdentity import parseIdentity


def createWithCSV(filepath, fmt):
    log.info("Creating {} with {}...".format(fmt.name, filepath))
    dataframe = PU.readFile(filepath, na_values=['?', '??', '???'])
    
    # split compounds
    dataframe = splitSiteHole(dataframe)
    
    fmtColumnIds = namesToIds(fmt.cols)
    colmap = TC.map_columns(fmtColumnIds, list(dataframe.columns))
    PU.renameColumns(dataframe, {v: k for k,v in colmap.iteritems()})
    PU.forceStringDatatype(dataframe, [col.name for col in fmtColumnIds if col.isString()])

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
    if 'SiteHole' in df and 'Site' not in df and 'Hole' not in df:
        sitehole = splitCompoundColumn(df, "SiteHole")
        df = pandas.concat([df, sitehole], axis=1, join_axes=[df.index])
    return df
        
def dropSiteHole(df):
    if "SiteHole" in df and 'Site' in df and 'Hole' in df: # remove added Site and Hole columns if necessary
        df = df.drop(["Site", 'Hole'], axis=1)
    return df

"""
Parse SectionID column in dataframe, add column for each ID component
"""
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
    PU.insert_contiguous(dataframe, sidIndex + 1, nameValues)


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