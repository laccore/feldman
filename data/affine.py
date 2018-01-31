'''
Created on May 6, 2016

@author: bgrivna
'''

import os
import unittest

from tabular.io import createWithCSV, FormatError
from tabular.columns import TabularDatatype, TabularFormat, ColumnIdentity
import tabular.pandasutils as PU
from columns import namesToIds, CoreIdentityCols


DepthCSF = ColumnIdentity("DepthCSF", "Depth below sea floor", ["Depth CSF-A"], TabularDatatype.NUMERIC, 'm')
DepthCCSF = ColumnIdentity("DepthCCSF", "Composite depth below sea floor", ["Depth CCSF-A"], TabularDatatype.NUMERIC, 'm')
Offset = ColumnIdentity("Offset", "Difference between a core's CSF-A and CCSF-A depth", ["Cumulative Offset", "Total Offset"], TabularDatatype.NUMERIC, 'm')
DifferentialOffset = ColumnIdentity("DifferentialOffset", "Difference between offset of current core and preceding core in hole", [], TabularDatatype.NUMERIC, 'm')
GrowthRate = ColumnIdentity("GrowthRate", "Ratio of core's CSF-A : CCSF-A depths", [], TabularDatatype.NUMERIC)
ShiftType = ColumnIdentity("ShiftType", "Core's affine shift type: TIE, SET, REL or ANCHOR", ["Affine Type", "Shift"])
FixedCore = ColumnIdentity("FixedCore", "For a core shifted by a TIE, the Hole + Core (e.g. B13) of the fixed core", [])
FixedTieCSF =  ColumnIdentity("FixedTieCSF", "CSF depth of the TIE point on the fixed core", ["Fixed Tie CSF-A"], TabularDatatype.NUMERIC, 'm')
ShiftedTieCSF = ColumnIdentity("ShiftedTieCSF", "CSF depth of the TIE point on the shifted core", ["Shifted Tie CSF-A"], TabularDatatype.NUMERIC, 'm')

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
    
    def getOffset(self, site, hole, core, tool):
        df = self.dataframe
        cores = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core) & (df.Tool == tool)]
        if cores.empty:
            print "AffineTable: Could not find core {}{}-{}{}".format(site, hole, core, tool)
        elif len(cores) > 1:
            print "AffineTable: Found multiple matches for core {}{}-{}{}".format(site, hole, core, tool)
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
        return "{}{}-{}{} CSF = {}, CCSF = {}, Offset = {}".format(self.site, self.hole, self.core, self.coreType, self.csf, self.ccsf, self.cumOffset)
    
    
class Tests(unittest.TestCase):
    def test_create(self):
        ss = AffineTable.createWithFile("/Users/bgrivna/Desktop/LacCore/TDP Towuti/January 2018/TDP_Site1_AffineTable_20161130.csv")
#         self.assertTrue(len(ss.dataframe) == 58)
#         self.assertTrue(math.isnan(ss.dataframe['Gap'].iloc[0]))
#         self.assertTrue('1' in ss.getSites())
#         self.assertTrue(len(ss.getHoles()) == 3)
        
if __name__ == "__main__":
    unittest.main()    
