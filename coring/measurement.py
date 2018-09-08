'''
Created on Mar 31, 2016

@author: bgrivna

Routines and classes for the processing of measurement data files
'''

import os
import unittest

from tabular.csvio import createWithCSV
from tabular.columns import TabularFormat
from .columns import SectionIdentityCols

        
MeasurementCols =  SectionIdentityCols # client is responsible for renaming Depth column
MeasurementFormat = TabularFormat("Measurement Data", MeasurementCols)

class MeasurementData:
    def __init__(self, name, depthColumn, dataframe):
        self.name = name
        self.depthColumn = depthColumn
        self.df = dataframe
        
    @classmethod
    def createWithFile(cls, filepath, depthColumn):
        dataframe = createWithCSV(filepath, MeasurementFormat)
        return cls(os.path.basename(filepath), depthColumn, dataframe)
    
    # includes depths == mindepth or maxdepth
    def getByRange(self, mindepth, maxdepth):
        return self.df[(self._depth() >= mindepth) & (self._depth() <= maxdepth)]

    def _depth(self): # shorten expressions a bit
        return self.df[self.depthColumn]

    # includes depths == mindepth or maxdepth
    def getByRangeAndCore(self, mindepth, maxdepth, core):
        return self.df[(self._depth() >= mindepth) & (self._depth() <= maxdepth) & (self.df.Core == core)]
    
    # sections: list of section IDs (type str) from which rows can be pulled
    def getByRangeCoreSections(self, mindepth, maxdepth, core, sections):
        return self.df[(self._depth() >= mindepth) & (self._depth() <= maxdepth) & (self.df.Core == core) & (self.df.Section.isin(sections))]

    def getByRangeFullID(self, mindepth, maxdepth, site, hole, core, sections):
        return self.df[(self._depth() >= mindepth) & (self._depth() <= maxdepth) & (self.df.Site == site) & (self.df.Hole == hole) & (self.df.Core == core) & (self.df.Section.isin(sections))]

    def getByFullID(self, site, hole, core, sections):
        return self.df[(self.df.Site == site) & (self.df.Hole == hole) & (self.df.Core == core) & (self.df.Section.isin(sections))]

    def getByCore(self, core):
        return self.df[self.df.Core == core]
    
    
class Tests(unittest.TestCase):
    def test_create(self):
        md = MeasurementData.createWithFile("../testdata/GLAD9_Site1_XRF.csv", depthColumn="Sediment Depth, scaled (MBS / CSF-B)")
        self.assertTrue('Tool' in md.df)
        self.assertTrue(len(md.getByRange(74.0, 75.0)) == 185)
        self.assertTrue(len(md.getByRangeAndCore(74.0, 75.0, '25')) == 84)
        self.assertTrue(len(md.getByRangeFullID(74.0, 76.0, '1', 'A', '25', ['1'])) == 148)
        self.assertTrue(len(md.getByRangeFullID(74.0, 78.0, '1', 'A', '25', ['2', '3'])) == 141)
        self.assertTrue(len(md.getByRangeFullID(74.0, 78.0, '1', 'A', '25', ['1', '2', '3'])) == 289)
        self.assertTrue(len(md.getByFullID('1', 'A', '25', ['1', '2', '3'])) == 289)
        self.assertTrue(len(md.getByCore('25')) == 643)
if __name__ == "__main__":
    unittest.main()