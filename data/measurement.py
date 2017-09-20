'''
Created on Mar 31, 2016

@author: bgrivna

Routines and classes for the processing of measurement data files
'''

import tabularImport as ti
import pandas

class AffineTransform:
    def __init__(self, identity, offset):
        self.identity = identity
        self.offset = offset

MeasurementFormat = ti.TabularFormat("Measurement Data",
                                     ['Site', 'Hole', 'Core', 'Tool', 'Section', 'TopOffset', 'BottomOffset', 'Depth', 'Data'],
                                     ['Site', 'Hole', 'Core', 'Tool', 'Section'])

MeasurementExportFormat = ti.TabularFormat("Spliced Measurement Data",
                                             ['Exp', 'Site', 'Hole', 'Core', 'CoreType',
                                              'Section', 'TopOffset', 'BottomOffset', 'Depth', 'Data', 'RawDepth', 'Offset'],
                                             ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'Section'])

def _splitSiteHole(dataframe):
    mergedDF = dataframe
    if 'SiteHole' in dataframe:
        # split SiteHole column into separate Site and Hole columns
        splitSiteHoleDF = dataframe.SiteHole.str.extract("(?P<Site>[0-9]+)(?P<Hole>[A-Z]+)")
        # add those columns to original dataframe with same index
        mergedDF = pandas.concat([dataframe, splitSiteHoleDF], axis=1, join_axes=[dataframe.index])
    return mergedDF

class MeasurementData:
    def __init__(self, dataframe):
        self.df = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = ti.readFile(filepath)
        ti.forceStringDatatype(MeasurementFormat.strCols, dataframe)
        return cls(dataframe)
    
    @classmethod
    def createWithCombinedSiteHoleFile(cls,filepath):
        dataframe = ti.readFile(filepath)
        dataframe = _splitSiteHole(dataframe)
        ti.forceStringDatatype(MeasurementFormat.strCols, dataframe)
        return cls(dataframe)    
    
    # includes depths == mindepth or maxdepth
    def getByRange(self, mindepth, maxdepth):
        return self.df[(self.df.Depth >= mindepth) & (self.df.Depth <= maxdepth)]

    # includes depths == mindepth or maxdepth
    def getByRangeAndCore(self, mindepth, maxdepth, core):
        return self.df[(self.df.Depth >= mindepth) & (self.df.Depth <= maxdepth) & (self.df.Core == core)]
    
    # sections: list of section IDs (type str) from which rows can be pulled
    def getByRangeCoreSections(self, mindepth, maxdepth, core, sections):
        return self.df[(self.df.Depth >= mindepth) & (self.df.Depth <= maxdepth) & (self.df.Core == core) & (self.df.Section.isin(sections))]

    def getByRangeFullID(self, mindepth, maxdepth, site, hole, core, sections):
        return self.df[(self.df.Depth >= mindepth) & (self.df.Depth <= maxdepth) & (self.df.Site == site) & (self.df.Hole == hole) & (self.df.Core == core) & (self.df.Section.isin(sections))]

    def getByFullID(self, site, hole, core, sections):
        return self.df[(self.df.Site == site) & (self.df.Hole == hole) & (self.df.Core == core) & (self.df.Section.isin(sections))]

    def getByCore(self, core):
        return self.df[self.df.Core == core]