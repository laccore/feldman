'''
Created on Mar 31, 2016

@author: bgrivna

Routines and classes for the processing of measurement data files
'''

import os
import unittest

from tabular.io import createWithCSV
from tabular.columns import TabularFormat
from columns import SectionIdentityCols

        
MeasurementCols =  SectionIdentityCols # client is responsible for renaming Depth column
MeasurementFormat = TabularFormat("Measurement Data", MeasurementCols)


class MeasurementData:
    def __init__(self, name, dataframe):
        self.name = name
        self.df = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = createWithCSV(filepath, MeasurementFormat)
        return cls(os.path.basename(filepath), dataframe)
    
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
    
    
class Tests(unittest.TestCase):
    def test_create(self):
        md = MeasurementData.createWithFile("../testdata/GLAD9_Site1_XRF.csv")
        self.assertTrue('Tool' in md.df)
        self.assertTrue(len(md.getByRange(74.0, 75.0)) == 185)
        self.assertTrue(len(md.getByRangeAndCore(74.0, 75.0, '25')) == 84)
        
if __name__ == "__main__":
    unittest.main()