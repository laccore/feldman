'''
Created on Jan 24, 2018

@author: bgrivna
'''

from tabular.columns import TabularDatatype, ColumnIdentity

# core identity elements
ColumnDict = {'Project': ColumnIdentity("Project", "Project, expedition, cruise or another high-level identifier", ["Exp", "Name", "Expedition", "Proj", "Cruise"]),
              'Site': ColumnIdentity("Site", "Location of core collection", ["Location"]),
              'Hole': ColumnIdentity("Hole", "Penetration from which one or more cores are collected", ["Track"]),
              'Core': ColumnIdentity("Core", "Material collected in a single drive", ["Drive"]),
              'Tool': ColumnIdentity("Tool", "Identifier of tool used to collect a core", ["Core Type", "Type"]),
              'Section': ColumnIdentity("Section", "Subdivision of core performed post-extraction", []),
              'TopSection': ColumnIdentity("TopSection", "Top section of an interval", []),
              'BottomSection': ColumnIdentity("BottomSection", "Bottom section of an interval", []),
              'TopOffset': ColumnIdentity("TopOffset", "Section depth at the top of an interval", [], TabularDatatype.NUMERIC, 'cm'),
              'BottomOffset': ColumnIdentity("BottomOffset", "Section depth at the top of an interval", [], TabularDatatype.NUMERIC, 'cm'),
              'Comment': ColumnIdentity("Comment", "Comments", ["Quality Comment", "Quality Comments", "Comments", "Notes", "Remarks"], optional=True),
              'DataUsed': ColumnIdentity("DataUsed", "Datatype used to determine e.g. a tie point", ["Data"], optional=True)
}

CoreIdentityCols = [ColumnDict[col] for col in ['Site', 'Hole', 'Core', 'Tool']]
SectionIdentityCols = [ColumnDict[col] for col in ['Site', 'Hole', 'Core', 'Tool', 'Section']]

def getId(colname):
    return ColumnDict[colname]

def namesToIds(colnames):
    return [ColumnDict[colname] for colname in colnames]