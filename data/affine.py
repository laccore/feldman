'''
Created on May 6, 2016

@author: bgrivna
'''

import os

import tabularImport as ti


AffineFormat = ti.TabularFormat("Affine Table",
                             ['Site', 'Hole', 'Core', 'Core Type', 'Depth CSF (m)', 'Depth CCSF (m)', \
                              'Cumulative Offset (m)', 'Differential Offset (m)', 'Growth Rate', 'Shift Type', \
                              'Data Used', 'Quality Comment'],
                             ['Site', 'Hole', 'Core', 'Core Type', 'Shift Type', 'Data Used', 'Quality Comment'])

class AffineTable:
    def __init__(self, name, dataframe):
        self.name = name
        self.dataframe = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = ti.readFile(filepath)
        ti.forceStringDatatype(ti.SampleFormat.strCols, dataframe)
        return cls(os.path.basename(filepath), dataframe)

class AffineRow:
    def __init__(self, site, hole, core, coreType, csf, ccsf, cumOffset, diffOffset=0, growthRate='', shiftType='TIE', dataUsed='', comment=''):
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
        self.dataUsed = dataUsed
        self.comment = comment
        
    def asDict(self):
        return {'Site':self.site, 'Hole':self.hole, 'Core':self.core, 'Core Type':self.coreType, 'Depth CSF (m)':self.csf,
                'Depth CCSF (m)':self.ccsf, 'Cumulative Offset (m)':self.cumOffset, 'Differential Offset (m)':self.diffOffset,
                'Growth Rate':self.growthRate, 'Shift Type':self.shiftType, 'Data Used':self.dataUsed, 'Quality Comment':self.comment}
