'''
Created on Jan 24, 2018

@author: bgrivna
'''

from tabular.columns import TabularDatatype, ColumnIdentity

# core identity elements
# TODO? define in external resource file instead of hard-coding here?
ColumnDict = {
    'Project': ColumnIdentity("Project", ["Exp", "Name", "Expedition", "Proj", "Cruise"], desc="Project, expedition, cruise or another high-level identifier"),
    'Site': ColumnIdentity("Site", ["Location"], desc="Location of core collection"),
    'Hole': ColumnIdentity("Hole", ["Track"], desc="Penetration from which one or more cores are collected"),
    'Core': ColumnIdentity("Core", ["Drive"], desc="Material collected in a single drive"),
    'Tool': ColumnIdentity("Tool", ["Core Type", "Type"], orgNames={'IODP':"Core type", 'LacCore':"Tool"}, desc="Identifier of tool used to collect a core"),
    'Section': ColumnIdentity("Section", desc="Subdivision of core performed post-extraction"),
    'TopSection': ColumnIdentity("TopSection", desc="Top section of an interval"),
    'BottomSection': ColumnIdentity("BottomSection", desc="Bottom section of an interval"),
    'TopOffset': ColumnIdentity("TopOffset", desc="Section depth at the top of an interval", datatype=TabularDatatype.NUMERIC, unit='cm'),
    'BottomOffset': ColumnIdentity("BottomOffset", desc="Section depth at the top of an interval", datatype=TabularDatatype.NUMERIC, unit='cm'),
    'Comment': ColumnIdentity("Comment", ["Quality Comment", "Quality Comments", "Comments", "Notes", "Remarks"], orgNames={'IODP':"Quality comment"}, desc="Comments", optional=True),
    'DataUsed': ColumnIdentity("DataUsed", ["Data"], orgNames={'IODP':"Data used"}, desc="Datatype used to determine e.g. a tie point", optional=True)
}

CoreIdentityCols = [ColumnDict[col] for col in ['Site', 'Hole', 'Core', 'Tool']]
SectionIdentityCols = [ColumnDict[col] for col in ['Site', 'Hole', 'Core', 'Tool', 'Section']]

def getId(colname):
    return ColumnDict[colname]

def namesToIds(colnames):
    return [ColumnDict[colname] for colname in colnames]