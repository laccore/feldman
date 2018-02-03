'''
Created on Feb 2, 2018

@author: bgrivna
'''

from identity import parseIdentity
from tabular.pandasutils import insertColumns

"""
Parse SectionID column in dataframe, add column for each ID component
"""
def splitSectionID(dataframe, sidcol='SectionID'):
    coreids = []
    for _, row in dataframe.iterrows():
        coreids.append(parseIdentity(row[sidcol]))
        
    sidIndex = dataframe.columns.get_loc(sidcol)
    
    nameValues = [] # elt is tuple (column name, list of column values)

    if coreids[0].name: # assume first CoreIdentity is representative
        nameValues.append(('Name', [c.name for c in coreids]))
    nameValues.append(('Site', [c.site for c in coreids]))
    nameValues.append(('Hole', [c.hole for c in coreids]))
    nameValues.append(('Core', [c.core for c in coreids]))
    nameValues.append(('Tool', [c.tool for c in coreids]))
    nameValues.append(('Section', [c.section for c in coreids]))
    insertColumns(dataframe, sidIndex + 1, nameValues)

