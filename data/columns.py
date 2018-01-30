'''
Created on Jan 24, 2018

@author: bgrivna
'''

from tabular.columns import TabularDatatype, ColumnIdentity

# core identity elements
ColumnDict = {'Project': ColumnIdentity("Project", "Project, expedition, cruise or another high-level identifier", ["Exp", "Name", "Expedition", "Proj", "Cruise"], TabularDatatype.STRING),
              'Site': ColumnIdentity("Site", "Location of core collection", ["Location"]),
              'Hole': ColumnIdentity("Hole", "Penetration from which one or more cores are collected", ["Track"]),
              'Core': ColumnIdentity("Core", "Material collected in a single drive", ["Drive"]),
              'Tool': ColumnIdentity("Tool", "Identifier of tool used to collect a core", ["Core Type", "Type"]),
              'Section': ColumnIdentity("Section", "Subdivision of core performed post-extraction", [])
}

StandardIdentityColumns = [ColumnDict[col] for col in ['Site', 'Hole', 'Core', 'Tool', 'Section']]

def getId(colname):
    return ColumnDict[colname]

def namesToIds(colnames):
    return [ColumnDict[colname] for colname in colnames]