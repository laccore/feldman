'''
Created on Feb 5, 2018

@author: bgrivna
'''

import os
import unittest

from tabular.csvio import createWithCSV
from tabular.columns import TabularDatatype, TabularFormat, ColumnIdentity

Site1 = ColumnIdentity("Site1", "Site of off-splice core", [])
Hole1 = ColumnIdentity("Hole1", "Hole of off-splice core", [])
Core1 = ColumnIdentity("Core1", "Core of off-splice core", [])
Tool1 = ColumnIdentity("Tool1", "Tool of off-splice core", [])
Section1 = ColumnIdentity("Section1", "Section of off-splice core", [])
SectionDepth1 = ColumnIdentity("SectionDepth1", "Section depth of correlation point on off-splice core", [], TabularDatatype.NUMERIC, 'cm')
Site2 = ColumnIdentity("Site2", "Site of on-splice core", [])
Hole2 = ColumnIdentity("Hole2", "Hole of on-splice core", [])
Core2 = ColumnIdentity("Core2", "Core of on-splice core", [])
Tool2 = ColumnIdentity("Tool2", "Tool of on-splice core", [])
Section2 = ColumnIdentity("Section2", "Section of on-splice core", [])
SectionDepth2 = ColumnIdentity("SectionDepth2", "Section depth of correlation point on on-splice core", [], TabularDatatype.NUMERIC, 'cm')

ManualCorrelationCols = [Site1, Hole1, Core1, Tool1, Section1, SectionDepth1, Site2, Hole2, Core2, Tool2, Section2, SectionDepth2]
ManualCorrelationFormat = TabularFormat("Manual Correlation Table", ManualCorrelationCols)


class ManualCorrelationTable:
    def __init__(self, name, dataframe):
        self.name = name
        self.df = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = createWithCSV(filepath, ManualCorrelationFormat)
        return cls(os.path.basename(filepath), dataframe)
        
    def findByOffSpliceCore(self, site, hole, core):
        df = self.df[(self.df.Site1 == site) & (self.df.Hole1 == hole) & (self.df.Core1 == core)]
        return self._forceSeriesOrNone(df)
    
    def findByOnSpliceCore(self, site, hole, core):
        df = self.df[(self.df.Site2 == site) & (self.df.Hole2 == hole) & (self.df.Core2 == core)]
        return self._forceSeriesOrNone(df)

    # force pandas.DataFrame to Series or there will be issues comparing to e.g. SIT rows!
    # specifically, a "Series lengths must match to compare" error
    def _forceSeriesOrNone(self, dataframe):
        # should only be a single row in dataframe unless it contains duplicate
        # off-splice IDs, but play it safe and grab first element 
        if len(dataframe) > 0:
            return dataframe.iloc[0] # force to Series
        return None

class Tests(unittest.TestCase):
    def test_create(self):
        mct = ManualCorrelationTable.createWithFile("../testdata/ManualCorrelationTable.csv")
        self.assertTrue(len(mct.df) == 90)
        row = mct.findByOffSpliceCore('1', 'D', '2')
        self.assertTrue(row['SectionDepth1'] == 0.5)
        self.assertTrue(row['SectionDepth2'] == 30)


if __name__ == "__main__":
    unittest.main()