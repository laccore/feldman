'''
Created on Mar 31, 2016

@author: bgrivna
'''

import os

import tabularImport as ti
import pandas

# Splice Interval Table headers: 2.0.2 b8 and earlier
# brg 1/18/2016: keeping for now, may want to convert from this format
SITFormat_202_b8 = ti.TabularFormat("Splice Interval Table 2.0.2 b8 and earlier",
                          ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'TopSection', 'TopOffset', \
                           'TopDepthCSF', 'TopDepthCCSF', 'BottomSection', 'BottomOffset', 'BottomDepthCSF', \
                           'BottomDepthCCSF', 'SpliceType', 'DataUsed', 'Comment'],
                          ['Exp', 'Site', 'Hole', 'Core', 'CoreType', 'TopSection', 'BottomSection', 'SpliceType', 'DataUsed', 'Comment'])

SITFormat = ti.TabularFormat("Splice Interval Table",
                          ['Site', 'Hole', 'Core', 'Core Type', 'Top Section', 'Top Offset', \
                           'Top Depth CSF-A', 'Top Depth CCSF-A', 'Bottom Section', 'Bottom Offset', 'Bottom Depth CSF-A', \
                           'Bottom Depth CCSF-A', 'Splice Type', 'Data Used', 'Comment'],
                          ['Site', 'Hole', 'Core', 'Core Type', 'Top Section', 'Bottom Section', 'Splice Type', 'Data Used', 'Comment'])


class SpliceIntervalRow:
    def __init__(self, site, hole, core, coreType, topSection, topOffset, topMBSF, topMCD, botSection, botOffset, botMBSF, botMCD, spliceType, dataUsed, comment):
        self.site = site
        self.hole = hole
        self.core = core
        self.coreType = coreType
        self.topSection = topSection
        self.topOffset = topOffset
        self.topMBSF = topMBSF
        self.topMCD = topMCD
        self.botSection = botSection
        self.botOffset = botOffset
        self.botMBSF = botMBSF
        self.botMCD = botMCD
        self.spliceType = spliceType
        self.dataUsed = dataUsed
        self.comment = comment
        
    def __repr__(self):
        fmt = "{}{}-{}{} top {}@{} (mbsf={} mcd={}), bot {}@{} (mbsf={}, mcd={}), {}, {}, {}" 
        return fmt.format(self.site, self.hole, self.core, self.coreType, self.topSection, self.topOffset, self.topMBSF, self.topMCD,
                          self.botSection, self.botOffset, self.botMBSF, self.botMCD, self.spliceType, self.dataUsed, self.comment) 

class SpliceIntervalTable:
    def __init__(self, name, dataframe):
        self.name = name
        self.df = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = ti.readFile(filepath)
        ti.forceStringDatatype(SITFormat.strCols, dataframe)
        return cls(os.path.basename(filepath), dataframe)
    
    def getSites(self):
        sites = self.df['Site']
        return list(set(sites))
    
    def getIntervals(self):
        rows = []
        for t in self.df.itertuples():
            row = SpliceIntervalRow(t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10], t[11], t[12], t[13], t[14], t[15])
            rows.append(row)
        return rows
        
    def getCoreOffset(self, site, hole, core):
        corerow = self.getCoreRow(site, hole, core)
        if corerow is not None:
            return corerow["Top Depth CCSF-A"] - corerow["Top Depth CSF-A"]
        return None
    
    def containsCore(self, site, hole, core):
        corerow = self.getCore(site, hole, core)
        if corerow is None or len(corerow) == 0:
            return False
        if len(corerow) > 1:
            print "SIT {} contains more than one matching core, WTF???".format(core)
        return True
    
    def getCore(self, site, hole, core):
        result = self.df[(self.df.Site == site) & (self.df.Hole == hole) & (self.df.Core == core)]
        #print "SpliceIntervalTable.getCore(): {}{}-{}".format(site, hole, core),
        if len(result) == 0:
            return None
        elif len(result) > 1:
            print "WARNING: {} matches found for {}{}-{}".format(len(result), site, hole, core)
        return result
    
    def getCoreRow(self, site, hole, core):
        c = self.getCore(site, hole, core)
        if len(c) == 0:
            return None
        else:
            return c.iloc[0]
        

    # todo: get table summary information