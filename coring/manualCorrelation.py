'''
Created on Feb 5, 2018

Manual correlations are applied after a sparse splice has been converted to a
full Splice Interval Table - they override the default method of shifting off-splice
cores.

@author: bgrivna
'''

import os
import unittest

from tabular.csvio import createWithCSV, canCreateWithFile
from tabular.columns import TabularDatatype, TabularFormat, ColumnIdentity
from .columns import namesToIds

Site1 = ColumnIdentity("Site1", desc="Site of off-splice core")
Hole1 = ColumnIdentity("Hole1", desc="Hole of off-splice core")
Core1 = ColumnIdentity("Core1", desc="Core of off-splice core")
Tool1 = ColumnIdentity("Tool1", desc="Tool of off-splice core")
Section1 = ColumnIdentity("Section1", desc="Section of off-splice core")
SectionDepth1 = ColumnIdentity("SectionDepth1", desc="Section depth of correlation point on off-splice core", datatype=TabularDatatype.NUMERIC, unit='cm')
Site2 = ColumnIdentity("Site2", desc="Site of on-splice core")
Hole2 = ColumnIdentity("Hole2", desc="Hole of on-splice core")
Core2 = ColumnIdentity("Core2", desc="Core of on-splice core")
Tool2 = ColumnIdentity("Tool2", desc="Tool of on-splice core")
Section2 = ColumnIdentity("Section2", desc="Section of on-splice core")
SectionDepth2 = ColumnIdentity("SectionDepth2", desc="Section depth of correlation point on on-splice core", datatype=TabularDatatype.NUMERIC, unit='cm')

ManualCorrelationCols = [Site1, Hole1, Core1, Tool1, Section1, SectionDepth1, Site2, Hole2, Core2, Tool2, Section2, SectionDepth2]
ManualCorrelationFormat = TabularFormat("Manual Correlation Tie Table", ManualCorrelationCols)

Offset = ColumnIdentity("Offset", ["Cumulative Offset", "Shift Distance"], desc="Affine shift for the associated core", datatype=TabularDatatype.NUMERIC)
ManualOffsetCols = namesToIds(["Site", "Hole", "Core"]) + [Offset]
ManualOffsetFormat = TabularFormat("Manual Offset Table", ManualOffsetCols)

# create the appropriate type of manual correlation depending on file type
def loadManualCorrelation(mcpath):
    if canCreateWithFile(mcpath, ManualCorrelationFormat):
        return ManualCorrelationTable.createWithFile(mcpath)
    elif canCreateWithFile(mcpath, ManualOffsetFormat):
        return ManualOffsetTable.createWithFile(mcpath)
    else:
        return None


# Table with each row containing two core IDs and the section depths at which the
# off-splice core (Site1...) and an on-splice core (Site2...) should be TIEd.
class ManualCorrelationTable:
    def __init__(self, name, dataframe):
        self.name = name
        self.df = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = createWithCSV(filepath, ManualCorrelationFormat)
        return cls(os.path.basename(filepath), dataframe)

    def hasOffSpliceCore(self, site, hole, core):
        return self.findByOffSpliceCore(site, hole, core) is not None

    def findByOffSpliceCore(self, site, hole, core):
        df = self.df[(self.df.Site1 == site) & (self.df.Hole1 == hole) & (self.df.Core1 == core)]
        return self._forceSeriesOrNone(df)
    
    def findByOnSpliceCore(self, site, hole, core):
        df = self.df[(self.df.Site2 == site) & (self.df.Hole2 == hole) & (self.df.Core2 == core)]
        return self._forceSeriesOrNone(df)

    def includesOnSpliceCore(self):
        return True

    def getOffset(self, site, hole, core):
        raise NotImplementedError("This method is unimplemented for ManualCorrelationTable")

    # force pandas.DataFrame to Series or there will be issues comparing to e.g. SIT rows!
    # specifically, a "Series lengths must match to compare" error
    def _forceSeriesOrNone(self, dataframe):
        # should only be a single row in dataframe unless it contains duplicate
        # off-splice IDs, but play it safe and grab first element 
        if len(dataframe) > 0:
            return dataframe.iloc[0] # force to Series
        return None


# Table with each row containing a Site, Hole, Core, and an Offset in meters.
# Creates "SET" type affine shifts for off-splice cores.
class ManualOffsetTable:
    def __init__(self, name, dataframe):
        self.name = name
        self.df = dataframe

    @classmethod
    def createWithFile(cls, filepath):
        dataframe = createWithCSV(filepath, ManualOffsetFormat)
        return cls(os.path.basename(filepath), dataframe)

    def hasOffSpliceCore(self, site, hole, core):
        return self.findByOffSpliceCore(site, hole, core) is not None

    def findByOffSpliceCore(self, site, hole, core):
        df = self.df[(self.df.Site == site) & (self.df.Hole == hole) & (self.df.Core == core)]
        return self._forceSeriesOrNone(df)
    
    def findByOnSpliceCore(self, site, hole, core):
        raise NotImplementedError("This method is unimplemented for ManualOffsetTable")

    def includesOnSpliceCore(self):
        return False

    def getOffset(self, site, hole, core):
        return self.df[(self.df.Site == site) & (self.df.Hole == hole) & (self.df.Core == core)].iloc[0]["Offset"]

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