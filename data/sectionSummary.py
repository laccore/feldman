'''
Created on May 1, 2016

@author: bgrivna
'''

import os

from operator import eq

import numpy
import tabularImport as ti

SectionSummaryFormat = ti.TabularFormat("Section Summary", 
                                         ['Site', 'Hole', 'Core', 'CoreType', 'Section', 'TopDepth', 'BottomDepth', 'CuratedLength'],
                                         ['Site', 'Hole', 'Core', 'CoreType', 'Section'])


class SectionSummary:
    def __init__(self, name, dataframe):
        self.name = name
        self.dataframe = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = ti.readFile(filepath, na_values=['?', '??', '???'])
        return cls(os.path.basename(filepath), dataframe)
    
    def containsCore(self, site, hole, core):
        cores = self._findCores(site, hole, core)
        return not cores.empty
    
    # get unique cores
    # TODO: assumes every core has a Section 1, which may be false - ask Anders
    def getCores(self):
        return self.dataframe[(self.dataframe.Section == '1')]
    
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
        print "Closest core top to off-splice {}{}-{} with top MBLF = {}: on-splice {}{}-{} with top MBLF = {}, diff = {}".format(site, hole, core, searchCoreTop, closestCore.Site, closestCore.Hole, closestCore.Core, closestCore.TopDepth, mindiff)
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
    
    def getSectionCoreType(self, site, hole, core, section):
        return self._getSectionValue(site, hole, core, section, 'CoreType')
    
    def getSectionAtDepth(self, site, hole, core, depth):
        sec = self._findSectionAtDepth(site, hole, core, depth)
        return sec
    
    def sectionDepthToTotal(self, site, hole, core, section, secDepth):
        top = self.getSectionTop(site, hole, core, section)
        result = top + secDepth / 100.0 # cm to m
        #print "section depth {} in section {} = {} overall".format(secDepth, section, result)        
        return result
    
    ### begin experiment with more flexible query logic
    def test(self, df, col, op, value):
        return op(df[col], value)
    
    def query(self, df, tests):
        curdf = df
        for t in tests:
            curdf = curdf[t]
        return curdf
#         if len(tests) == 1:
#             return df[tests[0]]
#         else:
#             return df[numpy.logical_and(*tests)]
    
    def match(self, df, args):
        tests = []
        if 'site' in args:
            tests.append(self.test(df, 'Site', eq, args['site']))
        if 'hole' in args:
            tests.append(self.test(df, 'Hole', eq, args['hole']))
        if 'core' in args:
            tests.append(self.test(df, 'Core', eq, args['core']))
        if 'section' in args:
            tests.append(self.test(df, 'Section', eq, args['section']))
        return self.query(df, tests)
    ### end experiment
    
    def _findCores(self, site, hole, core):
        df = self.dataframe
        cores = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core)]
        if cores.empty:
            print "SectionSummary: Could not find core {}-{}{}".format(site, hole, core)
        return cores
        

    def _findSection(self, site, hole, core, section):
        df = self.dataframe
        section = df[(df.Site == site) & (df.Hole == hole) & (df.Core == core) & (df.Section == section)]
        if section.empty:
            print "SectionSummary: Could not find {}-{}{}-{}".format(site, hole, core, section)
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