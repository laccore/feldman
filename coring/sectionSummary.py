'''
Created on May 1, 2016

@author: bgrivna
'''

import logging as log
import math
import os
import unittest

from tabular.csvio import createWithCSV, FormatError
from tabular.columns import TabularDatatype, TabularFormat, ColumnIdentity
import tabular.pandasutils as PU
from columns import SectionIdentityCols

# format-specific columns
TopDepth = ColumnIdentity("TopDepth", ["TopDepthUnscaled", "Top Depth CSF-A"], desc="Top drilled depth of a core (CSF-A)", datatype=TabularDatatype.NUMERIC, unit='m')
BottomDepth = ColumnIdentity("BottomDepth", ["BottomDepthUnscaled", "Bottom Depth CSF-A"], desc="Bottom drilled depth of a core (CSF-A)", datatype=TabularDatatype.NUMERIC, unit='m')
TopDepthScaled = ColumnIdentity("TopDepthScaled", ["Top Depth CSF-B"], desc="Top drilled depth of a core, scaled (CSF-B)", datatype=TabularDatatype.NUMERIC, unit='m')
BottomDepthScaled = ColumnIdentity("BottomDepthScaled", ["Bottom Depth CSF-B"], desc="Bottom drilled depth of a core, scaled (CSF-B)", datatype=TabularDatatype.NUMERIC, unit='m')
CuratedLength = ColumnIdentity("CuratedLength", ["Length"], desc="Length of core or section as measured post-extraction", datatype=TabularDatatype.NUMERIC, unit='m')
Gaps = ColumnIdentity("Gaps", desc="Section intervals to be treated as gaps: 0+ pairs of form top1-bot1 top2-bot2...", unit='cm', optional=True)

SectionSummaryColumns = SectionIdentityCols + [TopDepth, BottomDepth, TopDepthScaled, BottomDepthScaled, CuratedLength, Gaps]
SectionSummaryFormat = TabularFormat("Section Summary", SectionSummaryColumns)


class SectionSummary:
    def __init__(self, name, dataframe):
        self.name = name
        self.dataframe = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = createWithCSV(filepath, SectionSummaryFormat)
        return cls(os.path.basename(filepath), dataframe)
    
    def containsCore(self, site, hole, core):
        cores = self._findCores(site, hole, core)
        return not cores.empty
    
    # return list of unique cores
    def getCores(self):
        return self.dataframe[(self.dataframe.Section == '1')]
    
    # return list of unique sites
    def getSites(self):
        sites = self.dataframe['Site']
        return list(set(sites))

    # get total depth of a section offset using SectionSummary data and curated lengths if available
    def getOffsetDepth(self, site, hole, core, section, offset, scaledDepth=False):
        secTop = self.getSectionTop(site, hole, core, section) if not scaledDepth else self.getScaledSectionTop(site, hole, core, section) 
        secBot = self.getSectionBot(site, hole, core, section) if not scaledDepth else self.getScaledSectionBot(site, hole, core, section)
        scaledTxt = "scaled " if scaledDepth else ""
        sectionId = "{}{}-{}-{}".format(site, hole, core, section)
        log.debug("   {}section: {}, top = {}m, bot = {}m".format(scaledTxt, sectionId, secTop, secBot))
        log.debug("   {}section offset = {}cm + {}m = {}m".format(scaledTxt, offset, secTop, secTop + offset/100.0))

        curatedLength = self.getSectionLength(site, hole, core, section)
        if offset/100.0 > curatedLength:
            log.warning("   section {}: offset {}cm is beyond curated length of section {}m".format(sectionId, offset, curatedLength))

        depth = secTop + (offset/100.0) - (self.getTotalGapAboveSectionDepth(site, hole, core, section, offset)/100.0)
            
        # if using scaled depths, compress depth to drilled interval
        drilledLength = (secBot - secTop) * 100.0 # cm
        if scaledDepth and curatedLength > drilledLength:
            compressionFactor = drilledLength / curatedLength
            compressedDepth = secTop + (offset/100.0 * compressionFactor)
            log.warning("   section {}: curated length {}cm exceeds drilled length {}cm, compressing depth {}m to {}m".format(sectionId, curatedLength, drilledLength, depth, compressedDepth))
            depth = compressedDepth
            
        return depth        
    
    # return depth of top of top section, bottom of bottom section
    def getCoreRange(self, site, hole, core):
        cores = self._findCores(site, hole, core)
        cores = cores[(cores.Section != "CC")] # omit CC section for time being
        if not cores.empty:
            coremin = cores['TopDepth'].min()
            coremax = cores['BottomDepth'].max()
            return round(coremin, 3), round(coremax, 3)
        return None
    
    # find core in coreList with top depth closest to that of the passed core
    def getCoreWithClosestTop(self, site, hole, core, coreList):
        searchCoreTop = self.getSectionTop(site, hole, core, '1')
        closestCore = None
        mindiff = None
        for corerow in coreList:#self.getCores().iterrows():
            if corerow.Site == site and corerow.Hole == hole and corerow.Core == core: # skip search core - TODO shouldn't be in list since it's not on-splice!
                continue
            diff = abs(corerow.TopDepth - searchCoreTop)
            if mindiff is None or diff < mindiff:
                mindiff = diff
                closestCore = corerow
        log.debug("Closest core top to off-splice {}{}-{} with top MBLF = {}: on-splice {}{}-{} with top MBLF = {}, diff = {}".format(site, hole, core, searchCoreTop, closestCore.Site, closestCore.Hole, closestCore.Core, closestCore.TopDepth, mindiff))
        return closestCore
        
    def getCoreTop(self, site, hole, core):
        return self.getSectionTop(site, hole, core, '1')
    
    def getSectionTop(self, site, hole, core, section):
        val = self._getSectionValue(site, hole, core, section, 'TopDepth')
        return round(val, 3)
    
    def getSectionBot(self, site, hole, core, section):
        val = self._getSectionValue(site, hole, core, section, 'BottomDepth')
        return round(val, 3)
    
    def getScaledSectionTop(self, site, hole, core, section):
        val = self._getSectionValue(site, hole, core, section, 'TopDepthScaled')
        return round(val, 3)

    def getScaledSectionBot(self, site, hole, core, section):
        val = self._getSectionValue(site, hole, core, section, 'BottomDepthScaled')
        return round(val, 3)
        
    def getSectionLength(self, site, hole, core, section):
        val = self._getSectionValue(site, hole, core, section, 'CuratedLength')
        return round(val, 3)
    
    def getSectionTool(self, site, hole, core, section):
        return self._getSectionValue(site, hole, core, section, 'Tool')
    
    def getSectionAtDepth(self, site, hole, core, depth):
        sec = self._findSectionAtDepth(site, hole, core, depth)
        return sec
    
    def getGaps(self, site, hole, core, section):
        gapList = []
        if 'Gaps' in self.dataframe:
            gapStr = self._getSectionValue(site, hole, core, section, 'Gaps') # list of space-delimited gaps, each of form 'top-bottom'
            if gapStr != "":
                for gapInterval in [gap.split('-') for gap in gapStr.split(' ')]:
                    top, bot = float(gapInterval[0]), float(gapInterval[1])
                    gapList.append((top, bot))
        return gapList
    
    # return total length (in cm) of gaps above sectionDepth if 'Gaps' column
    # is present and specified section has gaps, otherwise 0.
    # - sectionDepth must be in cm
    def getTotalGapAboveSectionDepth(self, site, hole, core, section, sectionDepth):
        gapTotal = 0
        for gap in self.getGaps(site, hole, core, section):
            if sectionDepth > gap[0]:
                gapTotal += gap[1] - gap[0]
        return gapTotal
    
    def sectionDepthToTotal(self, site, hole, core, section, secDepth):
        top = self.getSectionTop(site, hole, core, section)
        result = top + secDepth / 100.0 # cm to m
        #print "section depth {} in section {} = {} overall".format(secDepth, section, result)        
        return result

    def _findCores(self, site, hole, core):
        df = self.dataframe
        cores = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core)]
        if cores.empty:
            log.warn("SectionSummary: Could not find core {}-{}{}".format(site, hole, core))
        return cores
        

    def _findSection(self, site, hole, core, section):
        df = self.dataframe
        section = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core) & (df.Section == section)]
        if section.empty:
            log.warn("SectionSummary: Could not find {}-{}{}-{}".format(site, hole, core, section))
        return section
    
    def _findSectionAtDepth(self, site, hole, core, depth):
        df = self.dataframe
        section = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core) & (depth >= df.TopDepth) & (depth <= df.BottomDepth)]
        if not section.empty:
            return section.iloc[0]['Section']
        return None
    
    def _getSectionValue(self, site, hole, core, section, columnName):
        section = self._findSection(site, hole, core, section)
        return section.iloc[0][columnName]

        
# utility to convert Laccore DB gaps format to SectionSummary format    
# sspath - path to Section Summary with gap data in separate columns named
# Gap 1 T, Gap 1 B, Gap 2 T, Gap 2 B...
# outpath - path to write dataframe including a column 'Gaps' with
# [gap top]-[gap bottom] space-delimited pairs
# maxGapCols - number of gap columns
def convertSSGapColumnsToSingle(sspath, outpath, maxGapCols):
    mergedGaps = []
    ss = PU.readFile(sspath)
    for _, row in ss.iterrows():
        gaps = []
        for gapNum in range(maxGapCols):
            tcol = "Gap {} T".format(gapNum + 1)
            bcol = "Gap {} B".format(gapNum + 1)
            if not math.isnan(row[tcol]) and not math.isnan(row[bcol]):
                gaps.append(str(row[tcol]) + "-" + str(row[bcol]))
        mergedGaps.append(' '.join(gaps))
        
    ss.insert(len(ss.columns), 'Gaps', mergedGaps)
    PU.writeToFile(ss, outpath)
    
    
    ### experimental: flexible query logic
#    from operator import eq
#     def test(self, df, col, op, value):
#         return op(df[col], value)
#     
#     def query(self, df, tests):
#         curdf = df
#         for t in tests:
#             curdf = curdf[t]
#         return curdf
# #         if len(tests) == 1:
# #             return df[tests[0]]
# #         else:
# #             return df[numpy.logical_and(*tests)]
#     
#     def match(self, df, args):
#         tests = []
#         if 'site' in args:
#             tests.append(self.test(df, 'Site', eq, args['site']))
#         if 'hole' in args:
#             tests.append(self.test(df, 'Hole', eq, args['hole']))
#         if 'core' in args:
#             tests.append(self.test(df, 'Core', eq, args['core']))
#         if 'section' in args:
#             tests.append(self.test(df, 'Section', eq, args['section']))
#         return self.query(df, tests)
# 
# simple flex query tests pulled from old 'foo.py'
# import time
# from data.sectionSummary import SectionSummary
# 
# def time_it(f, *args):
#     start = time.clock()
#     f(*args)
#     print "Elapsed time of {}: {}".format(f.__name__, (time.clock() - start) * 1000)
# 
# def combined(df):
#     foodf = df[(df.Site == 1) & (df.Hole == 'A') & (df.Core == 2)]
#     print len(foodf)
#     return df
#     
# def separate(df):
#     newdf = df[df.Site == 1]
#     newdf = newdf[df.Hole == 'A']
#     newdf = newdf[df.Core == 2]
#     print len(newdf)
#     return newdf    


class TestSectionSummary(unittest.TestCase):    
    def test_create(self):
        ss = SectionSummary.createWithFile("../testdata/GLAD9_SectionSummary.csv")
        self.assertTrue(len(ss.getSites()) == 7)        
        self.assertTrue(ss.containsCore('1', 'A', '33'))
        self.assertFalse(ss.containsCore('1', 'A', '34'))
        self.assertTrue(ss.getSectionTop('1', 'A', '33', '9') == 92.73)
        self.assertTrue(ss.getSectionAtDepth('1', 'B', '2', 4.4) == '3')
    
    def test_gaps(self):
        ss = SectionSummary.createWithFile("../testdata/SectionSummaryWithGaps.csv")
        self.assertTrue(ss.getGaps('1', 'A', '2', '1') == [])
        self.assertTrue(ss.getGaps('1', 'A', '3', '2') == [(0.0, 2.5)])
        self.assertTrue(ss.getTotalGapAboveSectionDepth('1', 'A', '3', '2', 0.0) == 0.0)
        self.assertTrue(ss.getTotalGapAboveSectionDepth('1', 'A', '3', '2', 1.0) == 2.5)
        self.assertTrue(ss.getGaps('1', 'A', '18', '1') == [(0.0, 0.5), (94.5, 96.0), (151.0, 152.5)])
        self.assertTrue(ss.getTotalGapAboveSectionDepth('1', 'A', '18', '1', 95.0) == 2.0)
        self.assertTrue(ss.getTotalGapAboveSectionDepth('1', 'A', '18', '1', 152.5) == 3.5)
        
    # confirm optional Gaps column is added if missing
    def test_gaps_column(self):
        ss = SectionSummary.createWithFile("../testdata/SectionSummaryNoGaps.csv")
        self.assertTrue('Gaps' in ss.dataframe)
        self.assertTrue(ss.getGaps('1', 'A', '2', '1') == [])
    
    # confirm FormatError if any required column is missing 
    def test_missing_req_column(self):
        self.assertRaises(FormatError, SectionSummary.createWithFile, "../testdata/SectionSummaryNoSite.csv")
    
if __name__ == "__main__":
    for testcase in [TestSectionSummary]:
        suite = unittest.TestLoader().loadTestsFromTestCase(testcase)
        unittest.TextTestRunner(verbosity=2).run(suite)