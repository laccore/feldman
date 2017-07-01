'''
Created on Apr 20, 2017

@author: bgrivna
'''


import os

import tabularImport as ti

#import pandas

SparseSpliceFormat = ti.TabularFormat("Sparse Splice", 
                                         ['Site', 'Hole', 'Core', 'Core Type', 'Top Section', 'Top Offset', 'Bottom Section', 'Bottom Offset', 'Splice Type', 'Gap'],
                                         ['Site', 'Hole', 'Core', 'Core Type', 'Top Section', 'Bottom Section', 'Splice Type'])


class SparseSplice:
    def __init__(self, name, dataframe):
        self.name = name
        self.dataframe = dataframe
        
    @classmethod
    def createWithFile(cls, filepath):
        dataframe = ti.readFile(filepath, na_values=['?', '??', '???'])
        
        # get formatColumn to fileColumn mapping
        
        ti.forceStringDatatype(SparseSpliceFormat.strCols, dataframe)
        return cls(os.path.basename(filepath), dataframe)
