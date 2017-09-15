'''
Created on May 6, 2016

@author: bgrivna
'''

import os

import tabularImport as ti


AffineFormat = ti.TabularFormat("Affine Table",
                             ['Site', 'Hole', 'Core', 'CoreType', 'Depth CSF (m)', 'Depth CCSF (m)', \
                              'Offset', 'Differential Offset (m)', 'Growth Rate', 'Shift Type', \
                              'Fixed Core', 'Fixed Tie CSF', 'Shifted Tie CSF', 'Data Used', 'Quality Comment'],
                             ['Site', 'Hole', 'Core', 'CoreType', 'Shift Type', 'Data Used', 'Quality Comment'])

class AffineTable:
    def __init__(self, name, dataframe):
        self.name = name
        self.dataframe = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = ti.readFile(filepath)
        ti.forceStringDatatype(ti.TabularFormat.strCols, dataframe)
        return cls(os.path.basename(filepath), dataframe)
    
    def getOffset(self, site, hole, core, coreType):
        df = self.dataframe
        cores = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core) & (df.CoreType == coreType)]
        if cores.empty:
            print "AffineTable: Could not find core {}{}-{}{}".format(site, hole, core, coreType)
        elif len(cores) > 1:
            print "AffineTable: Found multiple matches for core {}{}-{}{}".format(site, hole, core, coreType)
        return cores.iloc[0]['Offset']
    
    def allRows(self):
        allrows = []
        for index, row in self.dataframe.iterrows():
            ar = AffineRow.createWithRow(row)
            allrows.append(ar)
        #allrows = [AffineRow.createWithRow(row) for index, row in self.dataframe.iterrows()]
        return allrows
        #for index, row in self.dataframe.iterrows():
            

class AffineRow:
    def __init__(self, site, hole, core, coreType, csf, ccsf, cumOffset, diffOffset=0, growthRate='', shiftType='TIE', fixedCore='', fixedTieCsf='', shiftedTieCsf='', dataUsed='', comment=''):
        self.site = site
        self.hole = hole
        self.core = core
        self.coreType = coreType
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
        return cls(str(row['Site']), row['Hole'], str(row['Core']), row['CoreType'], row['Depth CSF (m)'], row["Depth CCSF (m)"], row['Offset'])
        
    def asDict(self):
        return {'Site':self.site, 'Hole':self.hole, 'Core':self.core, 'CoreType':self.coreType, 'Depth CSF (m)':self.csf,
                'Depth CCSF (m)':self.ccsf, 'Offset':self.cumOffset, 'Differential Offset (m)':self.diffOffset,
                'Growth Rate':self.growthRate, 'Shift Type':self.shiftType, 'Fixed Core':self.fixedCore,
                'Fixed Tie CSF':self.fixedTieCsf, 'Shifted Tie CSF':self.shiftedTieCsf, 'Data Used':self.dataUsed, 'Quality Comment':self.comment}
        
    def __repr__(self):
        return "{}{}-{}{} CSF = {}, CCSF = {}, Offset = {}".format(self.site, self.hole, self.core, self.coreType, self.csf, self.ccsf, self.cumOffset)
