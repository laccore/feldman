'''
Created on Apr 20, 2017

@author: bgrivna
'''


import math
import os
import unittest

from tabular.io import createWithCSV, FormatError
from tabular.columns import TabularDatatype, TabularFormat, ColumnIdentity
import tabular.pandasutils as PU
from columns import namesToIds, CoreIdentityCols

Gap = ColumnIdentity("Gap", "Space added before an APPEND of the next interval", [], TabularDatatype.NUMERIC, 'm', optional=True)
SpliceType = ColumnIdentity("SpliceType", "Type of splice operation: TIE or APPEND", [])

SparseSpliceColumns = CoreIdentityCols + namesToIds(['TopSection', 'TopOffset', 'BottomSection', "BottomOffset"]) + [SpliceType, Gap] + namesToIds(['DataUsed', 'Comment'])  
SparseSpliceFormat = TabularFormat("Sparse Splice", SparseSpliceColumns)


class SparseSplice:
    def __init__(self, name, dataframe):
        self.name = name
        self.dataframe = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = createWithCSV(filepath, SparseSpliceFormat)
        return cls(os.path.basename(filepath), dataframe)
    
    def getSites(self):
        return list(set(self.dataframe['Site']))
    
    def getHoles(self):
        return list(set(self.dataframe['Hole']))

class Tests(unittest.TestCase):
    def test_create(self):
        ss = SparseSplice.createWithFile("../testdata/GLAD9_Site1_SparseSplice.csv")
        self.assertTrue(len(ss.dataframe) == 58)
        self.assertTrue(math.isnan(ss.dataframe['Gap'].iloc[0]))
        self.assertTrue('1' in ss.getSites())
        self.assertTrue(len(ss.getHoles()) == 3)
        
if __name__ == "__main__":
    unittest.main()