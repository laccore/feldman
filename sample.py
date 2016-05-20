'''
Created on Apr 11, 2016

@author: bgrivna
'''

# LacCore sampling points data

import os

import tabularImport as ti
import pandas

class AffineTransform:
    def __init__(self, identity, offset):
        self.identity = identity
        self.offset = offset

class SampleData:
    def __init__(self, hole, dataframe):
        self.hole = hole
        self.df = dataframe
        
    @classmethod
    def createWithFile(cls, hole, filepath):
        dataframe = ti.readFile(filepath)
        ti.forceStringDatatype(ti.SampleFormat.strCols, dataframe)
        return cls(hole, dataframe)
    
    # includes depths == mindepth or maxdepth
    def getByRange(self, mindepth, maxdepth):
        return self.df[(self.df.Depth >= mindepth) & (self.df.Depth <= maxdepth)]
    
    # includes depths == mindepth or maxdepth - only pulls matching samples for the specified core!
    def getByRangeAndCore(self, mindepth, maxdepth, core):
        return self.df[(self.df.Depth >= mindepth) & (self.df.Depth <= maxdepth) & (self.df.Core == core)]
    
    # includes depths == mindepth or maxdepth - only pulls matching samples for the specified core!
    def getByRangeFullID(self, mindepth, maxdepth, site, hole, core, sections):
        return self.df[(self.df.Depth >= mindepth) & (self.df.Depth <= maxdepth) & (self.df.Site == site) & (self.df.Hole == hole) & (self.df.Core == core) & (self.df.Section.isin(sections))]
    
    def getByCore(self, core):
        return self.df[self.df.Core == core]
    
    def rowCount(self):
        return len(self.df)