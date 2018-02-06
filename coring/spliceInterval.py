'''
Created on Mar 31, 2016

@author: bgrivna
'''

import os
import unittest

from tabular.csvio import createWithCSV
from tabular.columns import TabularDatatype, TabularFormat, ColumnIdentity
from columns import namesToIds, CoreIdentityCols


TopDepthCSF = ColumnIdentity("TopDepthCSF", "Depth of splice interval top", ["Top Depth CSF-A"], TabularDatatype.NUMERIC, 'm')
TopDepthCCSF = ColumnIdentity("TopDepthCCSF", "Composite depth of splice interval top", ["Top Depth CCSF-A"], TabularDatatype.NUMERIC, 'm')
BottomDepthCSF = ColumnIdentity("BottomDepthCSF", "Depth of splice interval bototm", ["Bottom Depth CSF-A"], TabularDatatype.NUMERIC, 'm')
BottomDepthCCSF = ColumnIdentity("BottomDepthCCSF", "Composite depth of splice interval bottom", ["Bottom Depth CCSF-A"], TabularDatatype.NUMERIC, 'm')
SpliceType = ColumnIdentity("SpliceType", "Type of splice operation: TIE or APPEND", [])
Gap = ColumnIdentity("Gap", "Space added before an APPEND of the next interval", [], TabularDatatype.NUMERIC, 'm', optional=True)


SITColumns = CoreIdentityCols + namesToIds(['TopSection', 'TopOffset']) + [TopDepthCSF, TopDepthCCSF] + \
    namesToIds(['BottomSection', "BottomOffset"]) + [BottomDepthCSF, BottomDepthCCSF] + \
    [SpliceType, Gap] + namesToIds(['DataUsed', 'Comment']) 
SITFormat = TabularFormat("Splice Interval Table", SITColumns)


class SpliceIntervalRow:
    def __init__(self, site, hole, core, tool, topSection, topOffset, topCSF, topCCSF, botSection, botOffset, botCSF, botCCSF, spliceType, dataUsed, comment):
        self.site = site
        self.hole = hole
        self.core = core
        self.tool = tool
        self.topSection = topSection
        self.topOffset = topOffset
        self.topCSF = topCSF
        self.topCCSF = topCCSF
        self.botSection = botSection
        self.botOffset = botOffset
        self.botCSF = botCSF
        self.botCCSF = botCCSF
        self.spliceType = spliceType
        self.dataUsed = dataUsed
        self.comment = comment
        
    def __repr__(self):
        fmt = "{}{}-{}{} top {}@{} (CSF={} CCSF={}), bot {}@{} (CSF={}, CCSF={}), {}, {}, {}" 
        return fmt.format(self.site, self.hole, self.core, self.tool, self.topSection, self.topOffset, self.topCSF, self.topCCSF,
                          self.botSection, self.botOffset, self.botCSF, self.botCCSF, self.spliceType, self.dataUsed, self.comment) 

class SpliceIntervalTable:
    def __init__(self, name, dataframe):
        self.name = name
        self.df = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = createWithCSV(filepath, SITFormat)
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
            return corerow["TopDepthCCSF"] - corerow["TopDepthCSF"]
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
        
class Tests(unittest.TestCase):
    def test_create(self):
        pass
    
if __name__ == "__main__":
    unittest.main()