'''
Created on Jan 10, 2017

@author: bgrivna

Definitions of standard columns used in geological tabular data; related logic and tests
'''

import re
import unittest

class TabularDatatype:
    STRING = 0
    NUMERIC = 1
    # FLOAT?
    
class TabularFormat:
    cols = [] # list of ColumnIdentitys
    def __init__(self, name, cols):
        self.name = name
        self.cols = cols

class ColumnIdentity:
    def __init__(self, name, desc, synonyms, datatype, unit=""):
        self.name = name # standard name
        self.desc = desc
        self.synonyms = synonyms
        self.unit = unit # expected unit e.g. 'm' or None
        self.datatype = datatype # expected/forced datatype???
        
    def names(self):
        return [self.name] + self.synonyms
    
    def match(self, colname):
        return las(colname) in [las(name) for name in self.names()]
    
    def __repr__(self):
        return "cid:" + self.name

# Column whose name and data is the combination of two or more columns,
# most commonly SiteHole, which match()es on 'Site' or 'Hole'
class CompoundColumnIdentity(ColumnIdentity):
    def match(self, colname):
        return las(colname) in [las(name) for name in self.names()]
    
    def names(self):
        return split_caps(self.name) + self.synonyms
        

# core identity elements
ProjectCol = ColumnIdentity("Project", "Project, expedition, cruise or another high-level identifier", ["Exp", "Expedition", "Proj", "Cruise"], TabularDatatype.STRING)
SiteCol = ColumnIdentity("Site", "Location of core collection", ["Location"], TabularDatatype.STRING)
HoleCol = ColumnIdentity("Hole", "Penetration from which one or more cores are collected", ["Track"], TabularDatatype.STRING)
CoreCol = ColumnIdentity("Core", "Material collected in a single drive", ["Drive"], TabularDatatype.STRING)
ToolCol = ColumnIdentity("Tool", "Identifier of tool used to collect a core", ["Core Type", "Type"], TabularDatatype.STRING)
SectionCol = ColumnIdentity("Section", "Subdivision of core performed post-extraction", [], TabularDatatype.STRING)

shsyns = HoleCol.synonyms + SiteCol.synonyms
SiteHoleCol = CompoundColumnIdentity("SiteHole", "Combined Site and Hole fields", shsyns, TabularDatatype.STRING)

StandardIdentityColumns = [SiteCol, HoleCol, CoreCol, ToolCol, SectionCol]

# common columns
TopDepthCol = ColumnIdentity("TopDepth", "Top drilled depth of a core (CSF-A)", [], TabularDatatype.NUMERIC, 'm')
BotDepthCol = ColumnIdentity("BottomDepth", "Bottom drilled depth of a core (CSF-A)", [], TabularDatatype.NUMERIC, 'm')
TopDepthScaledCol = ColumnIdentity("TopDepthScaled", "Top drilled depth of a core, scaled (CSF-B)", [], TabularDatatype.NUMERIC, 'm')
BotDepthScaledCol = ColumnIdentity("BottomDepthScaled", "Bottom drilled depth of a core, scaled (CSF-B)", [], TabularDatatype.NUMERIC, 'm')
CuratedLengthCol = ColumnIdentity("CuratedLength", "Length of core or section as measured post-extraction", [], TabularDatatype.NUMERIC, 'm')

SectionSummaryColumns = StandardIdentityColumns + [TopDepthCol, BotDepthCol, TopDepthScaledCol, BotDepthScaledCol, CuratedLengthCol]


def split_caps(colname):
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", colname) # aA -> a A
    return spaced.split(" ")

def strip_unit(colname):
    return re.sub(r'\([^)]*\)', '', colname)

def find_unit(colname):
    m = re.search(r"\([^\)].*\)", colname)
    return None if m is None else m.group()[1:-1] # strip parentheses

def lowerstrip(colname):
    return colname.replace(' ', '').lower()

# lowerstrip and strip_unit
def las(colname):
    return lowerstrip(strip_unit(colname))

def map_columns(fmtcols, inputcols):
    colmap = {}
    for fc in fmtcols:
        for ic in inputcols:
            if fc.match(ic):
                colmap[fc.name] = ic
    return colmap

# next: more tests of map_columns
# then: SiteHole "Compo[und/site] Identity" handling
# then: hook up SectionSummary and test


class Tests(unittest.TestCase):
    def test_strip_unit(self):
        self.assertTrue(strip_unit("Column") == "Column")
        self.assertTrue(strip_unit("Column(m)") == "Column")
        self.assertTrue(strip_unit("Column()") == "Column")
        self.assertTrue(strip_unit("(m)Column") == "Column")
        self.assertTrue(strip_unit("Column(crazy-units&xxx#*(&$)") == "Column")
        
    def test_find_unit(self):
        self.assertTrue(find_unit("Column") is None)
        self.assertTrue(find_unit("Column()") is None)        
        self.assertTrue(find_unit("Column(m)") == 'm')
        self.assertTrue(find_unit("Column (counts/sec)") == 'counts/sec')
        self.assertTrue(find_unit("Column(crazy-units&xxx#*(&$)") == "crazy-units&xxx#*(&$")
        
    def test_lowerstrip(self):
        self.assertTrue(lowerstrip("columnname") == "columnname")
        self.assertTrue(lowerstrip("Column Name") == "columnname")
        self.assertTrue(lowerstrip(" Column Name ") == "columnname")
        
    def test_las(self):
        self.assertTrue(las("Column (counts/sec)") == 'column')
        self.assertTrue(las("  Column (counts/sec) () ") == 'column')
        
    def test_map_columns(self):
        TestFormat = [ProjectCol, SiteCol, HoleCol]

        icols = ["Project", "Site", "Hole"] # standard column names
        m = map_columns(TestFormat, icols)
        self.assertTrue(len(m) == 3)
        icols = [" cruise ", "SITE (m)", " t rac k"] # handle synonyms, funky case, spacing, unit
        m = map_columns(TestFormat, icols)
        self.assertTrue(len(m) == 3)
        
    def test_compound_column_id(self):
        self.assertTrue(SiteHoleCol.match("Site"))
        self.assertTrue(SiteHoleCol.match("Hole"))
        self.assertTrue(SiteHoleCol.match(" site"))
        self.assertTrue(SiteHoleCol.match(" location"))
        self.assertTrue(SiteHoleCol.match("track"))        
        self.assertFalse(SiteHoleCol.match("SiteHole"))        
    
    def test_split_caps(self):
        self.assertTrue(split_caps("AbeBobCarl") == ["Abe", "Bob", "Carl"])
        self.assertTrue(split_caps("abeBobcarL") == ["abe", "Bobcar", "L"])
        self.assertTrue(split_caps("noupper") == ["noupper"])
        self.assertTrue(split_caps("ABC") == ["ABC"])
        self.assertTrue(split_caps("") == [""])
        
if __name__ == "__main__":
    unittest.main()