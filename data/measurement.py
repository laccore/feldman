'''
Created on Mar 31, 2016

@author: bgrivna

Routines and classes for the processing of measurement data files
'''

import os

import tabularImport as ti
import pandas

class AffineTransform:
    def __init__(self, identity, offset):
        self.identity = identity
        self.offset = offset

MeasurementFormat = ti.TabularFormat("Measurement Data",
                                     ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'Section', 'TopOffset', 'BottomOffset', 'Depth', 'Data'],
                                     ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'Section'])

MeasurementExportFormat = ti.TabularFormat("Spliced Measurement Data",
                                             ['Exp', 'Site', 'Hole', 'Core', 'CoreType',
                                              'Section', 'TopOffset', 'BottomOffset', 'Depth', 'Data', 'RawDepth', 'Offset'],
                                             ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'Section'])


class MeasurementData:
    def __init__(self, hole, datatype, dataframe):
        self.hole = hole
        self.datatype = datatype
        self.df = dataframe
        
    @classmethod
    def createWithFile(cls, hole, datatype, filepath):
        dataframe = ti.readFile(filepath)
        ti.forceStringDatatype(MeasurementFormat.strCols, dataframe)
        return cls(hole, datatype, dataframe)
    
    # includes depths == mindepth or maxdepth
    def getByRange(self, mindepth, maxdepth):
        return self.df[(self.df.Depth >= mindepth) & (self.df.Depth <= maxdepth)]

    # includes depths == mindepth or maxdepth
    def getByRangeAndCore(self, mindepth, maxdepth, core):
        return self.df[(self.df.Depth >= mindepth) & (self.df.Depth <= maxdepth) & (self.df.Core == core)]
    
    # sections: list of section IDs (type str) from which rows can be pulled
    def getByRangeCoreSections(self, mindepth, maxdepth, core, sections):
        return self.df[(self.df.Depth >= mindepth) & (self.df.Depth <= maxdepth) & (self.df.Core == core) & (self.df.Section.isin(sections))]
    
    def getByCore(self, core):
        return self.df[self.df.Core == core]