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
    
class TabularFormat:
    def __init__(self, name, cols):
        self.name = name
        self.cols = cols # list of ColumnIdentitys
        
    def getColumnNames(self):
        return [c.name for c in self.cols]

class ColumnIdentity:
    def __init__(self, name, desc, synonyms, datatype=TabularDatatype.STRING, unit="", optional=False):
        self.name = name # standard name
        self.desc = desc
        self.synonyms = synonyms
        self.unit = unit # expected unit e.g. 'm' or None
        self.datatype = datatype # expected datatype
        self.optional = optional
        
    def names(self):
        return [self.name] + self.synonyms
    
    def match(self, colname):
        return match_column(colname, self.names())
    
    def isString(self):
        return self.datatype == TabularDatatype.STRING
    
    def isNumeric(self):
        return self.datatype == TabularDatatype.NUMERIC
    
    def getDefaultValue(self):
        return "" if self.isString() else float('nan')
    
    def __repr__(self):
        return "cid:" + self.name


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

# does las'd colname match any las'd column name in names?
def match_column(colname, names):
    return las(colname) in [las(name) for name in names]

# return raw (non-las'd) string of first name in names matching colname
# or None if no match is found
def find_match(colname, names):
    match = None
    for name in names:
        if las(colname) == las(name):
            match = name
            break
    return match

# fmtcolids - list of ColumnIdentitys required by format
# inputcols - list of column names to be mapped to format
def map_columns(fmtcols, inputcols):
    colmap = {}
    for fc in fmtcols:
        for ic in inputcols:
            if fc.match(ic):
                colmap[fc.name] = ic
    return colmap


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
        FooCol = ColumnIdentity("Foo", "", ["Fu", "Phooey"])
        BarCol = ColumnIdentity("Bar", "", ["Bear", "Tavern"])
        BazCol = ColumnIdentity("Baz", "", ["Bizarre", "Boz"])
        TestFormat = [FooCol, BarCol, BazCol]

        icols = ["Foo", "Bar", "Baz"] # standard column names
        m = map_columns(TestFormat, icols)
        self.assertTrue(len(m) == 3)
        icols = [" phooey ", "TAVERN (m)", "biz arre"] # handle synonyms, funky case, spacing, unit
        m = map_columns(TestFormat, icols)
        self.assertTrue(len(m) == 3)
    
    def test_split_caps(self):
        self.assertTrue(split_caps("AbeBobCarl") == ["Abe", "Bob", "Carl"])
        self.assertTrue(split_caps("abeBobcarL") == ["abe", "Bobcar", "L"])
        self.assertTrue(split_caps("noupper") == ["noupper"])
        self.assertTrue(split_caps("ABC") == ["ABC"])
        self.assertTrue(split_caps("Abe Bob") == ["Abe", "Bob"])
        self.assertTrue(split_caps("") == [""])
        
if __name__ == "__main__":
    unittest.main()