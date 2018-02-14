'''
Created on May 6, 2016

@author: bgrivna
'''

import logging as log
import os
import unittest

from tabular.csvio import createWithCSV
from tabular.columns import TabularDatatype, TabularFormat, ColumnIdentity
from columns import namesToIds, CoreIdentityCols


DepthCSF = ColumnIdentity("DepthCSF", ["Depth CSF-A", "Depth MBSF", "Depth MBLF"], orgNames={'IODP':'Depth CSF-A'}, desc="Depth below sea floor", datatype=TabularDatatype.NUMERIC, unit='m')
DepthCCSF = ColumnIdentity("DepthCCSF", ["Depth CCSF-A", "Depth MCD"], orgNames={'IODP':'Depth CCSF-A'}, desc="Composite depth below sea floor", datatype=TabularDatatype.NUMERIC, unit='m')
Offset = ColumnIdentity("Offset", ["Cumulative Offset", "Total Offset"], orgNames={'IODP':'Cumulative Offset'}, desc="Difference between a core's CSF-A and CCSF-A depth", datatype=TabularDatatype.NUMERIC, unit='m')
DifferentialOffset = ColumnIdentity("DifferentialOffset", orgNames={'IODP':"Differential Offset"}, desc="Difference between offset of current core and preceding core in hole", datatype=TabularDatatype.NUMERIC, unit='m', optional=True)
GrowthRate = ColumnIdentity("GrowthRate", desc="Ratio of core's CSF-A : CCSF-A depths", datatype=TabularDatatype.NUMERIC, optional=True)
ShiftType = ColumnIdentity("ShiftType", ["Affine Type", "Shift"], desc="Core's affine shift type: TIE, SET, REL or ANCHOR")
FixedCore = ColumnIdentity("FixedCore", desc="For a core shifted by a TIE, the Hole + Core (e.g. B13) of the fixed core", optional=True)
FixedTieCSF =  ColumnIdentity("FixedTieCSF", ["Fixed Tie CSF-A"], orgNames={'IODP':"Fixed Tie CSF-A"}, desc="CSF depth of the TIE point on the fixed core", datatype=TabularDatatype.NUMERIC, unit='m', optional=True)
ShiftedTieCSF = ColumnIdentity("ShiftedTieCSF", ["Shifted Tie CSF-A"], orgNames={'IODP':'Shifted Tie CSF-A'}, desc="CSF depth of the TIE point on the shifted core", datatype=TabularDatatype.NUMERIC, unit='m', optional=True)

FormatSpecificCols = [DepthCSF, DepthCCSF, Offset, DifferentialOffset, GrowthRate, ShiftType, FixedCore, FixedTieCSF, ShiftedTieCSF]

AffineColumns = CoreIdentityCols + FormatSpecificCols + namesToIds(["DataUsed", "Comment"])
AffineFormat = TabularFormat("Affine Table", AffineColumns)


class AffineTable:
    def __init__(self, name, dataframe):
        self.name = name
        self.dataframe = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = createWithCSV(filepath, AffineFormat)
        return cls(os.path.basename(filepath), dataframe)
    
    def getSites(self):
        return list(set(self.dataframe['Site']))
    
    def getOffset(self, site, hole, core, tool):
        df = self.dataframe
        cores = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core) & (df.Tool == tool)]
        if cores.empty:
            log.warn("AffineTable: Could not find core {}{}-{}{}".format(site, hole, core, tool))
        elif len(cores) > 1:
            log.warn("AffineTable: Found multiple matches for core {}{}-{}{}".format(site, hole, core, tool))
        return cores.iloc[0]['Offset']
    
    def allRows(self):
        allrows = []
        for _, row in self.dataframe.iterrows():
            ar = AffineRow.createWithRow(row)
            allrows.append(ar)
        return allrows
            

class AffineRow:
    def __init__(self, site, hole, core, tool, csf, ccsf, cumOffset, diffOffset=0, growthRate='', shiftType='TIE', fixedCore='', fixedTieCsf='', shiftedTieCsf='', dataUsed='', comment=''):
        self.site = site
        self.hole = hole
        self.core = core
        self.tool = tool
        self.csf = csf
        self.ccsf = ccsf
        self.cumOffset = cumOffset 
        self.diffOffset = diffOffset
        self.growthRate = growthRate
        self.shiftType = shiftType
        self.fixedCore = fixedCore
        self.fixedTieCsf = fixedTieCsf
        self.shiftedTieCsf = shiftedTieCsf
        self.dataUsed = dataUsed
        self.comment = comment
        
    @classmethod
    # INCOMPLETE AffineRows created here...
    def createWithRow(cls, row):
#         if len(row) != 1:
#             raise Exception("AffineRow can only be created from a single Pandas row, row count = {}".format(len(row)))
        return cls(str(row['Site']), row['Hole'], str(row['Core']), row['Tool'], row['DepthCSF'], row["DepthCCSF"], row['Offset'])
        
    def asDict(self):
        return {'Site':self.site, 'Hole':self.hole, 'Core':self.core, 'Tool':self.tool, DepthCSF.name:self.csf,
                DepthCCSF.name:self.ccsf, Offset.name:self.cumOffset, DifferentialOffset.name:self.diffOffset,
                GrowthRate.name:self.growthRate, ShiftType.name:self.shiftType, FixedCore.name:self.fixedCore,
                FixedTieCSF.name:self.fixedTieCsf, ShiftedTieCSF.name:self.shiftedTieCsf, 'DataUsed':self.dataUsed, 'Comment':self.comment}
        
    def __repr__(self):
        return "{}{}-{}{} CSF = {}, CCSF = {}, Offset = {}".format(self.site, self.hole, self.core, self.tool, self.csf, self.ccsf, self.cumOffset)
    
    
class Tests(unittest.TestCase):
    def test_create(self):
        aff = AffineTable.createWithFile("../testdata/GLAD9_Site1_Affine.csv")
        self.assertTrue(len(aff.dataframe) == 94)
        self.assertTrue(sorted(aff.getSites()) == ['1'])
        self.assertTrue(aff.getOffset('1', 'B', '2', 'H') == 0.298)
        
if __name__ == "__main__":
    unittest.main()    
