'''
April 14 2016
Has become a repository for all kinds of useful conversion routines that all desperately
need to be generalized and modularized in an intelligent way, but for now we're under the
gun trying to get Towuti its data...
'''

from datetime import date, datetime
import logging as log
import os
import unittest

import numpy
import pandas

import coring.identity as ci
import coring.affine as aff
import coring.spliceInterval as si
import coring.measurement as meas
from coring.sectionSummary import SectionSummary
from coring.sparseSplice import SparseSplice
from coring.manualCorrelation import ManualCorrelationTable

from tabular.csvio import writeToCSV
import tabular.pandasutils as PU

FeldmanVersion = "0.0.3"

OutputVocabulary = 'IODP'

# pandas call to open Correlator's inexplicable " \t" delimited file formats 
def openCorrelatorFunkyFormatFile(filename):
    datfile = open(filename, 'rU')
    headers = ["Exp", "Site", "Hole", "Core", "CoreType", "Section", "TopOffset", "BottomOffset", "Depth", "Data", "RunNo"]
    df = pandas.read_csv(datfile, header=None, names=headers, sep=" \t", skipinitialspace=True, comment="#", engine='python')
    datfile.close()
    #print df.dtypes
    # df can now be written to a normal CSV
    

# get total depth of a section offset using SectionSummary data and curated lengths if available
def getOffsetDepth(secsumm, site, hole, core, section, offset, scaledDepth=False):
    secTop = secsumm.getSectionTop(site, hole, core, section) if not scaledDepth else secsumm.getScaledSectionTop(site, hole, core, section) 
    secBot = secsumm.getSectionBot(site, hole, core, section) if not scaledDepth else secsumm.getScaledSectionBot(site, hole, core, section)
    scaledTxt = "scaled " if scaledDepth else ""
    sectionId = "{}{}-{}-{}".format(site, hole, core, section)
    log.debug("   {}section: {}, top = {}m, bot = {}m".format(scaledTxt, sectionId, secTop, secBot))
    log.debug("   {}section offset = {}cm + {}m = {}m".format(scaledTxt, offset, secTop, secTop + offset/100.0))

    curatedLength = secsumm.getSectionLength(site, hole, core, section)
    if offset/100.0 > curatedLength:
        log.warning("   section {}: offset {}cm is beyond curated length of section {}m".format(sectionId, offset, curatedLength))

    depth = secTop + (offset/100.0) - (secsumm.getTotalGapAboveSectionDepth(site, hole, core, section, offset)/100.0)
        
    # if using scaled depths, compress depth to drilled interval
    drilledLength = (secBot - secTop) * 100.0 # cm
    if scaledDepth and curatedLength > drilledLength:
        compressionFactor = drilledLength / curatedLength
        compressedDepth = secTop + (offset/100.0 * compressionFactor)
        log.warning("   section {}: curated length {}cm exceeds drilled length {}cm, compressing depth {}m to {}m".format(sectionId, curatedLength, drilledLength, depth, compressedDepth))
        depth = compressedDepth
        
    return depth


# options: LazyAppend, UseScaledDepths, Manual Correlation File 
def convertSparseSplice(secSummPath, sparsePath, affineOutPath, sitOutPath, useScaledDepths=False, lazyAppend=False, manualCorrelationPath=None):
    log.info("--- Converting Sparse Splice to Affine and SIT ---")
    log.info("{}".format(datetime.now()))
    log.info("Using Section Summary {}".format(secSummPath))
    log.info("Using Sparse Splice {}".format(sparsePath))
    log.info("Options: Use Scaled Depths = {}, Lazy Append = {}, Manual Correlation File = {}".format(useScaledDepths, lazyAppend, manualCorrelationPath))
    
    ss = SectionSummary.createWithFile(secSummPath)
    sp = SparseSplice.createWithFile(sparsePath)

    onSpliceAffRows = sparseSpliceToSIT(sp, ss, affineOutPath, sitOutPath, useScaledDepths, lazyAppend)
    
    # load just-created SIT and find affines for off-splice cores
    sit = si.SpliceIntervalTable.createWithFile(sitOutPath)
    mancorr = ManualCorrelationTable.createWithFile(manualCorrelationPath) if manualCorrelationPath else None
    offSpliceAffRows = gatherOffSpliceAffines(sit, ss, mancorr)
    
    allAff = onSpliceAffRows + offSpliceAffRows
    allAff = fillAffineRows(allAff)
    
    arDicts = [ar.asDict() for ar in allAff]
    
    affDF = pandas.DataFrame(arDicts, columns=aff.AffineFormat.getColumnNames())
    log.info("writing affine table to {}".format(os.path.abspath(affineOutPath)))
    log.debug("affine table column types:\n{}".format(affDF.dtypes))
    prettyColumns(affDF, aff.AffineFormat)
    writeToCSV(affDF, affineOutPath)
    
    log.info("Conversion complete.")


# options:
# - lazyAppend - use previous core's affine shift even if it's from a different hole
# - useScaledDepths - convert section depths to total depth using ScaledTopDepth and ScaledBottomDepth
#   in SectionSummary instead of (unscaled) TopDepth and BottomDepth     
def sparseSpliceToSIT(sparse, secsumm, affineOutPath, sitOutPath, useScaledDepths=False, lazyAppend=False):
    seenCores = [] # list of cores that have already been added to affine
    affineRows = [] # list of dicts, each representing a generated affine table row
    
    topCSFs = []
    topCCSFs = []
    botCSFs = []
    botCCSFs = []
    prevAffine = 0.0 # previous affine shift (used for APPEND shift)
    prevBotCCSF = None
    prevRow = None # previous interval's row, data needed for inter-hole default APPEND gap method
    sptype = None
    gap = None
    
    # todo: create SpliceIntervalRows and return along with AffineRows
    for index, row in sparse.dataframe.iterrows():
        log.debug("Interval {}".format(index + 1))
        site = row['Site']
        hole = row['Hole']
        core = row['Core']
        top = row['TopSection']
        topOff = row['TopOffset']
        log.debug("top section = {}, top offset = {}".format(top, topOff))
        shiftTop = getOffsetDepth(secsumm, site, hole, core, top, topOff, useScaledDepths)
        
        bot = row['BottomSection']
        botOff = row['BottomOffset']
        log.debug("bottom section = {}, bottom offset = {}".format(bot, botOff))
        shiftBot = getOffsetDepth(secsumm, site, hole, core, bot, botOff, useScaledDepths)
        
        # bail on inverted or zero-length intervals
        if shiftTop >= shiftBot:
            log.error("Interval is inverted or zero-length: computed top depth {} >= computed bottom depth {}".format(shiftTop, shiftBot))
            return
        
        affine = 0.0
        if sptype is None: # first row - unconcerned about splice type now, it will affect next row of data
            affine = 0.0
            log.debug("First interval, splice type irrelevant")
        elif sptype == "APPEND":
            if gap is not None: # user-specified gap
                gapEndDepth = prevBotCCSF + gap 
                affine = gapEndDepth - shiftTop
                log.debug("User specified gap of {}m between previous bottom ({}m) and current top ({}m), affine = {}m".format(gap, prevBotCCSF, shiftTop, affine))
            else: # default gap
                assert prevRow is not None
                if hole == prevRow['Hole'] or lazyAppend: # hole hasn't changed, use same affine shift
                    affine = prevAffine
                    log.debug("APPENDing {} at depth {} based on previous affine {}".format(shiftTop, shiftTop + affine, affine))
                else: # different hole, use scaled depths to determine gap
                    prevBotScaledDepth = getOffsetDepth(secsumm, prevRow['Site'], prevRow['Hole'], prevRow['Core'],
                                                        prevRow['BottomSection'], prevRow['BottomOffset'], scaledDepth=True)
                    topScaledDepth = getOffsetDepth(secsumm, site, hole, core, top, topOff, scaledDepth=True)
                    scaledGap = topScaledDepth - prevBotScaledDepth
                    if scaledGap < 0.0:
                        log.warning("Bottom of previous interval is {}m *above* top of next interval in CSF-B space".format(scaledGap))
                    affine = (prevBotCCSF - shiftTop) + scaledGap
                    log.debug("Inter-hole APPENDing {} at depth {} to preserve scaled (CSF-B) gap of {}m".format(shiftTop, shiftTop + affine, scaledGap))
        elif sptype == "TIE":
            # affine = difference between prev bottom MCD and MBLF of current top
            affine = prevBotCCSF - shiftTop
            log.debug("TIEing {} to previous bottom depth {}, affine shift of {}".format(shiftTop, prevBotCCSF, affine))
        else:
            log.error("Encountered unknown splice type {}, bailing out!".format(sptype))
            return

        if prevBotCCSF is not None and prevBotCCSF > shiftTop + affine:
            log.warning("previous interval bottom MCD {} is below current interval top MCD {}".format(prevBotCCSF, shiftTop + affine))
            # increase affine to prevent overlap in case of APPEND - this should never happen for a TIE
            if sptype == "APPEND":
                overlap = prevBotCCSF - (shiftTop + affine)                
                affine += overlap 
                log.warning("interval type APPEND, adjusting affine to {}m to avoid {}m overlap".format(affine, overlap))

        # create data for corresponding affine - growth rate and differential offset will be filled by fillAffineRows()
        coreid = str(site) + str(hole) + "-" + str(core)
        if coreid not in seenCores:
            seenCores.append(coreid)
            coreTop = secsumm.getCoreTop(site, hole, core) # use core's top for depths in affine table, not depth of TIE in splice
            affineShiftType = _spliceShiftToAffine(sptype, gap)
            fixedCore = prevRow['Hole'] + prevRow['Core'] if sptype == "TIE" else ""
            fixedTieCsf = botCSFs[-1] if sptype == "TIE" else ""
            shiftedTieCsf = shiftTop if sptype == "TIE" else ""
            affineRow = aff.AffineRow(site, hole, core, row['Tool'], coreTop, coreTop + affine, affine, shiftType=affineShiftType,
                                      fixedCore=fixedCore, fixedTieCsf=fixedTieCsf, shiftedTieCsf=shiftedTieCsf, comment="splice") 
            affineRows.append(affineRow)
        else:
            log.error("holecore {} already seen, ignoring".format(coreid))
        
        # create new column data 
        topCSFs.append(shiftTop)
        topCCSFs.append(shiftTop + affine)
        
        botCSFs.append(shiftBot)
        botCCSFs.append(shiftBot + affine)
        log.debug("shifted top = {}m, bottom = {}m".format(shiftTop + affine, shiftBot + affine))
        
        prevBotCCSF = shiftBot + affine
        prevAffine = affine
        prevRow = row
        
        # warnings
        if shiftTop >= shiftBot:
            log.warning("{}: interval top {} at or below interval bottom {} in MBLF".format(coreid, shiftTop, shiftBot))
        
        # track splice type and (optional) gap, used to determine the next interval's depths
        sptype = row['SpliceType']
        gap = row['Gap'] if not numpy.isnan(row['Gap']) else None
    
    # done parsing, create final dataframe for export
    sitDF = sparse.dataframe.copy()
    PU.insertColumns(sitDF, 6, [(si.TopDepthCSF.name, pandas.Series(topCSFs)), (si.TopDepthCCSF.name, pandas.Series(topCCSFs))])
    PU.insertColumns(sitDF, 10, [(si.BottomDepthCSF.name, pandas.Series(botCSFs)), (si.BottomDepthCCSF.name, pandas.Series(botCCSFs))])
    
    log.info("writing splice interval table to {}".format(os.path.abspath(sitOutPath)))
    log.debug("splice interval table column types:{}".format(sitDF.dtypes))
    prettyColumns(sitDF, si.SITFormat)
    writeToCSV(sitDF, sitOutPath)
    
    return affineRows

# attempt to map the shift type from the sparse splice to a valid affine shift type
def _spliceShiftToAffine(spliceShift, gap):
    affineShiftType = 'REL'
    if spliceShift == 'TIE': # sparse splice TIEs naturally become affine TIEs
        affineShiftType = "TIE"
    elif spliceShift == 'APPEND' and gap is not None:
        # if user defined a gap, use SET since they actively chose to position the core
        affineShiftType = "SET"
    return affineShiftType


# todo: MeasDataDB class that hides multi-file (broken into holes) vs single-file data
# - includeOffSplice: if True, all off-splice rows in mdPath will be included in export with 'On-Splice' value = FALSE 
# - wholeSpliceSection: if True, all rows in all sections included in a splice interval will be exported as 'On-Splice' 
def exportMeasurementData(affinePath, sitPath, mdPath, exportPath, includeOffSplice=True, wholeSpliceSection=False, depthColumn='Depth'):
    log.info("--- Splicing Measurement Data ---")
    log.info("{}".format(datetime.now()))
    log.info("Using Affine Table {}".format(affinePath))
    log.info("Using Splice Interval Table {}".format(sitPath))
    log.info("Splicing {}".format(mdPath))
    log.info("Using '{}' as depth column".format(depthColumn))
    log.info("Options: includeOffSplice = {}, wholeSpliceSection = {}".format(includeOffSplice, wholeSpliceSection))
    
    affine = aff.AffineTable.createWithFile(affinePath)
    sit = si.SpliceIntervalTable.createWithFile(sitPath)
    md = meas.MeasurementData.createWithFile(mdPath)
    PU.renameColumns(md.df, {depthColumn:'Depth'})
    log.info("Loaded {} rows of data from {}".format(len(md.df.index), mdPath))
    log.debug(md.df.dtypes)

    onSpliceRows = []
    for index, sirow in enumerate(sit.getIntervals()):
        log.debug("Interval {}: {}".format(index, sirow))
        
        sections = [sirow.topSection]
        if sirow.topSection != sirow.botSection:
            intTop = int(sirow.topSection)
            intBot = int(sirow.botSection)
            sections = [str(x + intTop) for x in range(1 + intBot - intTop)]
        log.debug("   Searching section(s) {}...".format(sections))
        
        if wholeSpliceSection:
            mdrows = md.getByFullID(sirow.site, sirow.hole, sirow.core, sections)
        else:
            mdrows = md.getByRangeFullID(sirow.topCSF, sirow.botCSF, sirow.site, sirow.hole, sirow.core, sections)
        #print mdrows
        #print "   found {} rows, top depth = {}, bottom depth = {}".format(len(mdrows), mdrows.iloc[0]['Depth'], mdrows.iloc[-1]['Depth'])
        
        if len(mdrows) > 0:
            affineOffset = sirow.topCCSF - sirow.topCSF
            _prepSplicedRowsForExport(md.df, mdrows, depthColumn, affineOffset, onSplice=True) 
            onSpliceRows.append(mdrows)
        
    onSpliceDF = pandas.concat(onSpliceRows)
    log.info("Total spliced rows: {}".format(len(onSpliceDF)))

    if includeOffSplice:    
        offSpliceDF = md.df[~(md.df.index.isin(onSpliceDF.index))] # off-splice rows
        totalOffSplice = len(offSpliceDF)
        log.info("Total off-splice rows: {}".format(totalOffSplice))
        #print affine.dataframe.dtypes
        #print offSpliceDF.dtypes
        
        # I think iterating over all rows in the affine table, finding
        # matching rows, and setting their offsets should be faster than iterating
        # over all rows in offSpliceRows and finding/setting the affine of each?
        offSpliceRows = []
        totalOffSpliceWritten = 0
        for ar in affine.allRows():
            shiftedRows = offSpliceDF[(offSpliceDF.Site == ar.site) & (offSpliceDF.Hole == ar.hole) & (offSpliceDF.Core == ar.core)]
            log.debug("   found {} off-splice rows for affine row {}".format(len(shiftedRows.index), ar))
            
            _prepSplicedRowsForExport(md.df, shiftedRows, depthColumn, ar.cumOffset, onSplice=False)
            onSpliceRows.append(shiftedRows)
            offSpliceRows.append(shiftedRows)
            
            totalOffSpliceWritten += len(shiftedRows)
            
        log.info("Total off-splice rows included in export: {}".format(totalOffSpliceWritten))
        
        unwritten = offSpliceDF[~(offSpliceDF.index.isin(pandas.concat(offSpliceRows).index))].copy() # rows that still haven't been written!
        if len(unwritten.index) > 0:
            log.warn("Of {} off-splice rows, {} were not included in the export.".format(totalOffSplice, len(unwritten)))
            unwrittenPath = os.path.splitext(mdPath)[0] + "-unwritten.csv"
            log.warn("Those rows will be saved to {}".format(unwrittenPath))
            prettyColumns(unwritten, meas.MeasurementFormat)
            writeToCSV(unwritten, unwrittenPath)
    
    exportdf = pandas.concat(onSpliceRows)

    prettyColumns(exportdf, meas.MeasurementFormat)
    writeToCSV(exportdf, exportPath)
    log.info("Wrote spliced data to {}".format(exportPath))

# rename and add columns in spliced measurement data per LacCore requirements
def _prepSplicedRowsForExport(dataframe, rows, depthColumn, offset, onSplice):
    PU.renameColumns(rows, {'Depth':depthColumn})
    idIndex = PU.getColumnIndex(dataframe, 'SectionID')
    if not idIndex: # if SectionID is missing, insert at the beginning
        idIndex = 0
    nameValuesList = [('Splice Depth', pandas.Series(rows[depthColumn] + offset)), ('Offset', offset), ('On-Splice', str(onSplice).upper())]
    PU.insertColumns(rows, idIndex + 1, nameValuesList) 
    

class OffSpliceCore:
    def __init__(self, row):
        self.osc = row
        
    def __repr__(self):
        return "{}{}-{}".format(self.osc.Site, self.osc.Hole, self.osc.Core)


def gatherOffSpliceAffines(sit, secsumm, mancorr):
    # find all off-splice cores: those in section summary that are *not* in SIT
    skippedCoreCount = 0
    offSpliceCores = []
    onSpliceCores = []
    ssCores = secsumm.getCores()
    for _, row in ssCores.iterrows():
        if row.Site not in secsumm.getSites(): # skip section summary rows from non-site cores
            skippedCoreCount += 1
            continue
        if not sit.containsCore(row.Site, row.Hole, row.Core):
            offSpliceCores.append(row)
        else:
            onSpliceCores.append(row)
            
    log.info("Found {} off-splice cores in {} section summary cores for sites {} - skipped {} non-site cores".format(len(offSpliceCores), len(ssCores), secsumm.getSites(), skippedCoreCount))

    osAffineShifts = {}
    affineRows = []
    
    # for each of the off-splice cores:
    for osc in offSpliceCores:
        oscid = ci.CoreIdentity("[Project Name]", osc.Site, osc.Hole, osc.Core, osc.Tool)
        
        mcc = None
        if mancorr is not None:
            mcc = mancorr.findByOffSpliceCore(osc.Site, osc.Hole, osc.Core)
            if mcc is not None:
                log.debug("Found manual correlation for {}".format(OffSpliceCore(osc)))
            else:
                log.debug("no manual correlation for {}".format(OffSpliceCore(osc)))
            
        offSpliceMbsf = 0.0
        offset = 0.0
        # is that core manually correlated?
        if mcc is not None:
            # if the on-splice "correlation core" is actually on-splice:
            if sit.containsCore(mcc.Site2, mcc.Hole2, mcc.Core2):
                log.debug("SIT contains on-splice core")

                # use sparse splice to SIT logic to determine affine for off-splice core based on alignment of section depths
                offSpliceMbsf = getOffsetDepth(secsumm, mcc.Site1, mcc.Hole1, mcc.Core1, mcc.Section1, mcc.SectionDepth1) # TODO: UPDATE
                log.debug("off-splice: {}@{} = {} MBSF".format(oscid, mcc.SectionDepth1, offSpliceMbsf))
                onSpliceMbsf = getOffsetDepth(secsumm, mcc.Site2, mcc.Hole2, mcc.Core2, mcc.Section2, mcc.SectionDepth2)
                log.debug("on-splice: {}{}-{}@{} = {} MBSF".format(mcc.Site2, mcc.Hole2, mcc.Core2, mcc.SectionDepth2, onSpliceMbsf))
                sitOffset = sit.getCoreOffset(mcc.Site2, mcc.Hole2, mcc.Core2)
                onSpliceMcd = onSpliceMbsf + sitOffset
                offset = onSpliceMcd - offSpliceMbsf
                log.debug("   + SIT offset of {} = {} MCD".format(sitOffset, onSpliceMcd))
                log.debug("   off-splice MBSF {} + {} offset = {} on-splice MCD".format(offSpliceMbsf, offset, onSpliceMcd))
                
                # track affine for off-splice core - additional correlations for that core will be ignored if present
                if oscid not in osAffineShifts:
                    osAffineShifts[oscid] = offset
                else:
                    log.warning("Found additional offset for {}: {} (new) vs. {} (existing) - ignoring new!".format(oscid, offset, osAffineShifts[oscid]))
            else:
                # warn that "correlation core" is NOT on-splice and fall back on default top MBSF approach
                log.warning("Alleged correlation core {}{}-{} is NOT on-splice".format(mcc.Site2, mcc.Hole2, mcc.Core2))
                
        if oscid not in osAffineShifts:
            # find on-splice core with top MBSF closest to that of the current core and use its affine shift
            log.debug("No manual shift for {}, seeking closest top...".format(oscid))
            closestCore = secsumm.getCoreWithClosestTop(osc.Site, osc.Hole, osc.Core, onSpliceCores)
            offset = sit.getCoreOffset(closestCore.Site, closestCore.Hole, closestCore.Core)
            osAffineShifts[oscid] = offset

        coreTop = secsumm.getCoreTop(osc.Site, osc.Hole, osc.Core)  # use core's top for depths in affine table, not depth of TIE in splice
        affineRow = aff.AffineRow(osc.Site, osc.Hole, osc.Core, osc.Tool, coreTop, coreTop + offset, offset, shiftType="REL", comment="off-splice")
        affineRows.append(affineRow)
        
    return affineRows

# sort affine rows, compute Differential Offset and Growth Rate column values
def fillAffineRows(affineRows):
    sortedRows = sorted(affineRows, key = lambda ar: (ar.site, ar.hole, int(ar.core)))
    
    holes = set([r.hole for r in sortedRows])
    for h in holes:
        rows = [r for r in sortedRows if r.hole == h]
        mbsfVals = []
        mcdVals = []
        prevOffset = None
        for row in rows:
            if prevOffset is None: # first row
                row.diffOffset = row.cumOffset
            else:
                row.diffOffset = row.cumOffset - prevOffset
            prevOffset = row.cumOffset
            
            mbsfVals.append(row.csf)
            mcdVals.append(row.ccsf)
            if len(mbsfVals) > 1:
                row.growthRate = round(numpy.polyfit(mbsfVals, mcdVals, 1)[0], 3)
            else:
                row.growthRate = 0.0
    
    return sortedRows

# Rename columns in dataframe from their format's internal name to their
# pretty name if the internal name is in the dataframe.
def prettyColumns(dataframe, fmt):
    colmap = {c.name: c.prettyName(OutputVocabulary) for c in fmt.cols if c.name in dataframe}
    PU.renameColumns(dataframe, colmap)
    
def appendDate(text):
    return text + "_{}".format(date.today().isoformat())



class Test(unittest.TestCase):
    def test_sparse_to_sit(self):
        # TODO: replace with testdata GLAD9 or contrived files
        sparsePath = "/Users/bgrivna/Desktop/LacCore/TDP Towuti/TDP_Site1_SparseSpliceTable_20161117.csv"
        secsummPath = "/Users/bgrivna/Desktop/LacCore/TDP Towuti/TDP Section Summary 20161117.csv"
        affinePath = "/Users/bgrivna/Desktop/LacCore/TDP Towuti/TDP_Site1_TestAffine.csv"
        splicePath = "/Users/bgrivna/Desktop/LacCore/TDP Towuti/TDP_Site1_TestSplice.csv"
        convertSparseSplice(secsummPath, sparsePath, affinePath, splicePath)
        affine = aff.AffineTable.createWithFile(affinePath)
        sit = si.SpliceIntervalTable.createWithFile(splicePath)
        self.assertTrue(len(affine.getSites()) == 3)
        self.assertTrue(len(sit.df) == 105)
    
    def test_splice_measurement(self):
        affinePath = "/Users/bgrivna/Desktop/LacCore/TDP Towuti/TDP_Site1_TestAffine.csv"
        splicePath = "/Users/bgrivna/Desktop/LacCore/TDP Towuti/TDP_Site1_TestSplice.csv"
        measPath = "/Users/bgrivna/Desktop/LacCore/TDP Towuti/TDP_subsamples_20161120_utf8err.csv"
        splicedMeasPath = "/Users/bgrivna/Desktop/LacCore/TDP Towuti/TDP_subsamples_TestSpliced.csv"
        exportMeasurementData(affinePath, splicePath, measPath, splicedMeasPath, depthColumn='Top Depth (MBLF, unscaled)') # include off-splice

if __name__ == "__main__":
    log.basicConfig(level=log.INFO)
    unittest.main()

    # convert sparse splice to SIT
#     ssPath = "[section summary path]"
#     sparsePath = "[sparse splice path]"
#     basepath = "[root export path and filename prefix]"
#     affPath = basepath + appendDate("_AffineFromSparse") + ".csv"
#     sitPath = basepath + appendDate("_SITFromSparse") + ".csv"
#     convertSparseSpliceToSIT(ssPath, sparsePath, affPath, sitPath)

    # splice measurement data    
#     for mdPath in mdFilePaths:
#         path, ext = os.path.splitext(mdPath)
#         exportPath = path + "_spliced" + ext
#         exportMeasurementData(affinePath, sitPath, mdPath, exportPath, wholeSpliceSection=False)
