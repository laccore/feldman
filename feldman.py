'''
April 14 2016
Has become a repository for all kinds of useful conversion routines that all desperately
need to be generalized and modularized in an intelligent way, but for now we're under the
gun trying to get Towuti its data...
'''

from datetime import date
import logging as log
import os.path

import numpy
import pandas

import coreIdentity as ci
import tabularImport as ti
import data.affine as aff
import data.spliceInterval as si
import data.measurement as meas
import data.sectionSummary as ss
import data.sparseSplice as ssplice
import sample

# pandas call to open Correlator's inexplicable " \t" delimited file formats 
def openCorrelatorFunkyFormatFile(filename):
    datfile = open(filename, 'rU')
    headers = ["Exp", "Site", "Hole", "Core", "CoreType", "Section", "TopOffset", "BottomOffset", "Depth", "Data", "RunNo"]
    df = pandas.read_csv(datfile, header=None, names=headers, sep=" \t", skipinitialspace=True, comment="#", engine='python')
    datfile.close()
    print df.dtypes
    # df can now be written to a normal CSV

# assumes typical CSV format (comma-delimited, no spaces)
def openSectionSummaryFile(filename):
    secsumm = ss.SectionSummary.createWithFile(filename)
    
    # force pandas.dtypes to "object" (string) for ID components
    objcols = ["Site", "Hole", "Core", "CoreType", "Section"]
    ti.forceStringDatatype(objcols, secsumm.dataframe)
    
    return secsumm
    # confirm no blank/nan cells - fail to load? ignore such rows and warn user?


def openSparseSplice(filename):
    splice = ssplice.SparseSplice.createWithFile(filename)
    
    log.debug("Sparse Splice pandas datatypes: {}".format(splice.dataframe.dtypes))
    log.debug("string columns: {}", ssplice.SparseSpliceFormat.strCols)
    
    return splice.dataframe

def openManualCorrelationFile(mcPath):
    headers = ["Site1", "Hole1", "Core1", "Tool1", "Section1", "SectionDepth1", "Site2", "Hole2", "Core2", "Tool2", "Section2", "SectionDepth2"]
    mcFile = open(mcPath, 'rU')
    mancorr = pandas.read_csv(mcFile, skiprows=1, header=None, names=headers, sep=None, engine='python', na_values="POOP")
    mcFile.close()
    
    objcols = ["Site1", "Hole1", "Core1", "Tool1", "Section1", "Site2", "Hole2", "Core2", "Section2", "Tool2"]
    
    ti.forceStringDatatype(objcols, mancorr)
    
    return ManualCorrelationTable("Jim's Manual Correlation", mancorr)
    

# get total depth of a section offset using SectionSummary data and curated lengths if available
def getOffsetDepth(secsumm, site, hole, core, section, offset, scaledDepth=False):
    secTop = secsumm.getSectionTop(site, hole, core, section) if not scaledDepth else secsumm.getScaledSectionTop(site, hole, core, section) 
    secBot = secsumm.getSectionBot(site, hole, core, section) if not scaledDepth else secsumm.getScaledSectionBot(site, hole, core, section)
    scaledTxt = "scaled " if scaledDepth else ""
    log.debug("   {}section: {}-{}{}-{}, top = {}m, bot = {}m".format(scaledTxt, site, hole, core, section, secTop, secBot))
    log.debug("   {}section offset = {}cm + {}m = {}m".format(scaledTxt, offset, secTop, secTop + offset/100.0))

    curatedLength = secsumm.getSectionLength(site, hole, core, section)
    if offset/100.0 > curatedLength:
        log.warning("   offset {}cm is beyond curated length of section {}m".format(offset, curatedLength))

    depth = secTop + (offset/100.0)
        
    # if using scaled depths, compress depth to drilled interval
    drilledLength = (secBot - secTop) * 100.0 # cm
    if scaledDepth and curatedLength > drilledLength:
        compressionFactor = drilledLength / curatedLength
        compressedDepth = secTop + (offset/100.0 * compressionFactor)
        log.warning("   curated length {}cm exceeds drilled length {}cm, compressing depth {}m to {}m".format(curatedLength, drilledLength, depth, compressedDepth))
        depth = compressedDepth
        
    return depth

    
def convertSectionSpliceToSIT(secsplice, secsumm, affineOutPath, sitOutPath):
    seenCores = [] # list of cores that have already been added to affine
    affineRows = [] # list of dicts, each representing a generated affine table row
    
    topCSFs = []
    topCCSFs = []
    botCSFs = []
    botCCSFs = []
    prevAffine = 0.0 # previous affine shift (used for APPEND shift)
    prevBotMcd = None
    prevRow = None # previous interval's row, data needed for inter-hole default APPEND gap method
    sptype = None
    gap = None
    
    # todo: create SpliceIntervalRows and return along with AffineRows
    for index, row in secsplice.iterrows():
        log.debug("Interval {}".format(index + 1))
        site = row['Site']
        hole = row['Hole']
        core = row['Core']
        top = row['Top Section']
        topOff = row['Top Offset']
        log.debug("top section = {}, top offset = {}".format(top, topOff))
        shiftTop = getOffsetDepth(secsumm, site, hole, core, top, topOff)
        
        bot = row['Bottom Section']
        botOff = row['Bottom Offset']
        log.debug("bottom section = {}, bottom offset = {}".format(bot, botOff))
        shiftBot = getOffsetDepth(secsumm, site, hole, core, bot, botOff)
        
        affine = 0.0
        if sptype is None: # first interval
            affine = 0.0
            log.debug("First interval, no splice tie type")
        elif sptype == "APPEND":
            if gap is not None: # user-specified gap
                gapEndDepth = prevBotMcd + gap 
                affine = gapEndDepth - shiftTop
                log.debug("User specified gap of {}m between previous bottom ({}m) and current top ({}m), affine = {}m".format(gap, prevBotMcd, shiftTop, affine))
            else: # default gap
                assert prevRow is not None
                if hole == prevRow['Hole']: # hole hasn't changed, use same affine shift
                    affine = prevAffine
                    log.debug("APPENDing {} at depth {} based on previous affine {}".format(shiftTop, shiftTop + affine, affine))
                else: # different hole, use scaled depths to determine gap
                    prevBotScaledDepth = getOffsetDepth(secsumm, prevRow['Site'], prevRow['Hole'], prevRow['Core'], prevRow['Bottom Section'], prevRow['Bottom Offset'], scaledDepth=True)
                    topScaledDepth = getOffsetDepth(secsumm, site, hole, core, top, topOff, scaledDepth=True)
                    scaledGap = topScaledDepth - prevBotScaledDepth
                    if scaledGap < 0.0:
                        log.warning("Bottom of previous interval is {}m *above* top of next interval in CSF-B space, is this okay?".format(scaledGap))
                    affine = (prevBotMcd - shiftTop) + scaledGap
                    log.debug("Inter-hole APPENDing {} at depth {} to preserve scaled (CSF-B) gap of {}m".format(shiftTop, shiftTop + affine, scaledGap))
        else: # TIE
            # affine = difference between prev bottom MCD and MBLF of current top
            affine = prevBotMcd - shiftTop
            log.debug("TIEing {} to previous bottom depth {}, affine shift of {}".format(shiftTop, prevBotMcd, affine))

        if prevBotMcd is not None and prevBotMcd > shiftTop + affine:
            log.warning("previous interval bottom MCD {} is below current interval top MCD {}".format(prevBotMcd, shiftTop + affine))
            # increase affine to prevent overlap in case of APPEND - this should never happen for a TIE
            if sptype == "APPEND":
                overlap = prevBotMcd - (shiftTop + affine)                
                affine += overlap 
                log.warning("interval type APPEND, adjusting affine to {}m to avoid {}m overlap".format(affine, overlap))
            
        # create data for corresponding affine
        coreid = str(site) + str(hole) + "-" + str(core)
        if coreid not in seenCores:
            seenCores.append(coreid)#str(hole) + str(core))
            affineRow = aff.AffineRow(site, hole, core, row['Core Type'], shiftTop, shiftTop + affine, affine, comment="splice") 
            affineRows.append(affineRow)
        else:
            log.error("holecore {} already seen, ignoring".format(coreid))
        
        # create new column data 
        topCSFs.append(shiftTop)
        topCCSFs.append(shiftTop + affine)
        
        botCSFs.append(shiftBot)
        botCCSFs.append(shiftBot + affine)
        log.debug("shifted top = {}m, bottom = {}m".format(shiftTop + affine, shiftBot + affine))
        
        prevBotMcd = shiftBot + affine
        prevAffine = affine
        prevRow = row
        
        # warnings
        if shiftTop >= shiftBot:
            log.warning("interval top {} at or below interval bottom {} in MBLF".format(shiftTop, shiftBot))
        
        # track splice type and (optional) gap, used to determine the next interval's depths
        sptype = row['Splice Type']
        gap = row['Gap (m)'] if not numpy.isnan(row['Gap (m)']) else None
    
    # done parsing, create final dataframe for export
    sitDF = secsplice.copy()
    sitDF.insert(6, 'Top Depth CSF-A', pandas.Series(topCSFs))
    sitDF.insert(7, 'Top Depth CCSF-A', pandas.Series(topCCSFs))
    sitDF.insert(10, 'Bottom Depth CSF-A', pandas.Series(botCSFs))
    sitDF.insert(11, 'Bottom Depth CCSF-A', pandas.Series(botCCSFs))
    
    log.info("writing splice interval table to {}".format(sitOutPath))
    log.debug("splice interval table column types:{}".format(sitDF.dtypes))
    sitDF.to_csv(sitOutPath, index=False)
    
    return affineRows
    
# todo: basically a dup of exportMeasurementData with some extra reporting
def exportSampleData(sitPath, sdPath, exportPath): #Template, holes, exportPath):
    log.info("--- Exporting Sample Data --- ")
    # load SIT
    sit = si.SpliceIntervalTable.createWithFile(sitPath)

    # load sample data
    sd = sample.SampleData.createWithFile("Many Holes", sdPath)
#     log.info("{} sample data rows loaded from {} files".format(totalSampleRows, len(holes)))
    log.info("Applying SIT to Sample Data...")

    sprows = [] # rows comprising spliced dataset
    rowcount = 0
    for index, sirow in enumerate(sit.getIntervals()):
        log.debug("Interval {}: {}".format(index, sirow))
        
        sections = [sirow.topSection]
        if sirow.topSection != sirow.botSection:
            intTop = int(sirow.topSection)
            intBot = int(sirow.botSection)
            sections = [str(x + intTop) for x in range(1 + intBot - intTop)]
        log.debug("   Searching section(s) {}...".format(sections))
        
        sdrows = sd.getByRangeFullID(sirow.topMBSF, sirow.botMBSF, sirow.site, sirow.hole, sirow.core, sections)        
        log.debug("   found {} rows".format(len(sdrows)))
        if len(sdrows) > 0:
            log.debug("...top depth = {}, bottom depth = {}".format(sdrows.iloc[0]['Depth'], sdrows.iloc[-1]['Depth']))
            log.debug(str(sdrows))
        else:
            log.error("Zero matching rows found in sample data")
        
        affineOffset = sirow.topMCD - sirow.topMBSF
        
        # adjust depth column
        sdrows.rename(columns={'Depth':'RawDepth'}, inplace=True)
        
        # round here until we can upgrade to pandas 0.17.0 (see below)
        sdrows.insert(8, 'Depth', pandas.Series(sdrows['RawDepth'] + affineOffset).round(3))
        sdrows.insert(9, 'Offset', round(affineOffset, 3))
        sdrows = sdrows[ti.SampleExportFormat.req] # reorder to reflect export format
        
        sprows.append(sdrows)
        
        rowcount += len(sdrows)
                
    log.info("Total sample rows exported: {}".format(rowcount))
    
    exportdf = pandas.concat(sprows)

    # Argh. Introduced in pandas 0.17.0, we're stuck on 0.16.0 for now...
    # print "Rounding..."
    #exportdf = exportdf.round({'Depth': 3, 'Offset': 3})
    
    ti.writeToFile(exportdf, exportPath)


# todo: MeasDataDB class that hides multi-file (broken into holes) vs single-file data
# - includeOffSplice: if True, all off-splice rows in mdPath will be included in export with 'On-Splice' value = FALSE 
# - wholeSpliceSection: if True, all rows in all sections included in a splice interval will be exported as 'On-Splice' 
def exportMeasurementData(affinePath, sitPath, mdPath, exportPath, includeOffSplice=True, wholeSpliceSection=False):
    log.info("--- Exporting Measurement Data ---")
    
    affine = aff.AffineTable.createWithFile(affinePath)
    sit = si.SpliceIntervalTable.createWithFile(sitPath)
    md = meas.MeasurementData.createWithFile("Multi-hole", "Gamma Density", mdPath)
    log.info("Loaded {} rows of data from {}".format(len(md.df.index), mdPath))
    log.debug(md.df.dtypes)

    sprows = [] # rows comprising spliced dataset
    rowcount = 0
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
            mdrows = md.getByRangeFullID(sirow.topMBSF, sirow.botMBSF, sirow.site, sirow.hole, sirow.core, sections)
        #print mdrows
        #print "   found {} rows, top depth = {}, bottom depth = {}".format(len(mdrows), mdrows.iloc[0]['Depth'], mdrows.iloc[-1]['Depth'])
        
        if len(mdrows) > 0:
            affineOffset = sirow.topMCD - sirow.topMBSF
            
            # adjust depth column
            mdrows.rename(columns={'Depth':'RawDepth'}, inplace=True)
            mdrows.insert(8, 'Depth', pandas.Series(mdrows['RawDepth'] + affineOffset))
            mdrows.insert(9, 'Offset', affineOffset)
            mdrows.insert(10, 'On-Splice', 'TRUE')
            
            sprows.append(mdrows)
            
            rowcount += len(mdrows)
        
    onSpliceDF = pandas.concat(sprows)
    
    log.info("Total spliced rows: {}".format(rowcount))

    totalOffSplice = 0
    nonsprows = []
    if includeOffSplice:    
        osr = md.df[~(md.df.index.isin(onSpliceDF.index))] # off-splice rows
        log.info("Total off-splice rows: {}".format(len(osr.index)))
        print affine.dataframe.dtypes
        print osr.dtypes
        
        # I think iterating over all rows in the affine table, finding
        # matching rows, and setting their offsets should be faster than iterating
        # over all rows in offSpliceRows and finding/setting the affine of each?
        for ar in affine.allRows():
            shiftedRows = osr[(osr.Site == ar.site) & (osr.Hole == ar.hole) & (osr.Core == ar.core)]# & (osr.CoreType == ar.coreType)]
            log.info("   found {} off-splice rows for affine row {}".format(len(shiftedRows.index), ar))
            
            shiftedRows.rename(columns={'Depth':'RawDepth'}, inplace=True)
            shiftedRows.insert(8, 'Depth', pandas.Series(shiftedRows['RawDepth'] + ar.cumOffset))
            shiftedRows.insert(9, 'Offset', ar.cumOffset)
            shiftedRows.insert(10, 'On-Splice', 'FALSE')
            
            sprows.append(shiftedRows)
            nonsprows.append(shiftedRows)
            
            totalOffSplice += len(shiftedRows)
            
        log.info("Total off-splice rows to be written: {}".format(totalOffSplice))
        
        unwritten = osr[~(osr.index.isin(pandas.concat(nonsprows).index))] # rows that still haven't been written!
        log.info("Rows remaining unwritten: {}".format(len(unwritten.index)))
        print unwritten
    
    exportdf = pandas.concat(sprows)
   
    ti.writeToFile(exportdf, exportPath)

class ManualCorrelationTable:
    def __init__(self, name, dataframe):
        self.name = name
        self.df = dataframe
        
    def getOffSpliceCore(self, site, hole, core):
        # must return a pandas.Series, not a pandas.DataFrame or there will be issues comparing to e.g. SIT rows!
        # specifically, a "Series lengths must match to compare" error
        mc = self.df[(self.df.Site1 == site) & (self.df.Hole1 == hole) & (self.df.Core1 == core)]
        if len(mc) > 0:
            return mc.iloc[0] # force to Series
        return None
    
    def getOnSpliceCore(self, site, hole, core):
        return self.df[(self.df.Site2 == site) & (self.df.Hole2 == hole) & (self.df.Core2 == core)]
    

class OffSpliceCore:
    def __init__(self, row):
        self.osc = row
        
    def __repr__(self):
        return "{}{}-{}".format(self.osc.Site, self.osc.Hole, self.osc.Core)


def gatherOffSpliceAffines(sit, secsumm, mancorr, sites):
    # find all off-splice cores: those in section summary that are *not* in SIT
    skippedCoreCount = 0
    offSpliceCores = []
    onSpliceCores = []
    ssCores = secsumm.getCores()
    for index, row in ssCores.iterrows():
        if row.Site not in sites: # skip section summary rows from non-site cores
            skippedCoreCount += 1
            continue
        if not sit.containsCore(row.Site, row.Hole, row.Core):
            offSpliceCores.append(row)
        else:
            onSpliceCores.append(row)
            
    log.info("Found {} off-splice cores in {} section summary cores for sites {} - skipped {} non-site cores".format(len(offSpliceCores), len(ssCores), sites, skippedCoreCount))

    osAffineShifts = {}
    affineRows = []
    
    # for each of the off-splice cores:
    for osc in offSpliceCores:
        oscid = ci.CoreIdentity("TDP-TOW15", osc.Site, osc.Hole, osc.Core, osc.CoreType)
        
        mcc = None
        if mancorr is not None:
            mcc = mancorr.getOffSpliceCore(osc.Site, osc.Hole, osc.Core)
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

                # use sparse splice to SIT logic to determine affine for that core based on alignment of section depths
                offSpliceMbsf = getOffsetDepth(secsumm, mcc.Site1, mcc.Hole1, mcc.Core1, mcc.Section1, mcc.SectionDepth1)
                log.debug("off-splice: {}@{} = {} MBSF".format(oscid, mcc.SectionDepth1, offSpliceMbsf))
                onSpliceMbsf = getOffsetDepth(secsumm, mcc.Site2, mcc.Hole2, mcc.Core2, mcc.Section2, mcc.SectionDepth2)
                log.debug("on-splice: {}{}-{}@{} = {} MBSF".format(mcc.Site2, mcc.Hole2, mcc.Core2, mcc.SectionDepth2, onSpliceMbsf))
                sitOffset = sit.getCoreOffset(mcc.Site2, mcc.Hole2, mcc.Core2)
                onSpliceMcd = onSpliceMbsf + sitOffset
                offset = onSpliceMcd - offSpliceMbsf
                log.debug("   + SIT offset of {} = {} MCD".format(sitOffset, onSpliceMcd))
                log.debug("   off-splice MBSF {} + {} offset = {} on-splice MCD".format(offSpliceMbsf, offset, onSpliceMcd))
                
                # Track affine for that core and confirm that other correlations result in the same affine shift - if not, use original shift and WARN
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
            offSpliceMbsf = secsumm.getCoreTop(osc.Site, osc.Hole, osc.Core)
            osAffineShifts[oscid] = offset
            
        affineRow = aff.AffineRow(osc.Site, osc.Hole, osc.Core, osc.CoreType, offSpliceMbsf, offSpliceMbsf + offset, offset, comment="off-splice")
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
    
    
def doMeasurementExport():
    affinePath = "/Users/bgrivna/Desktop/LacCore/TDP Towuti/TDP_Site1_AffineFromSparse_20161130.csv"
    sitPath = "/Users/bgrivna/Desktop/LacCore/TDP Towuti/TDP_Site1_SITFromSparse_20161130.csv"#,
        
    mdFilePaths = ["/Users/bgrivna/Desktop/LacCore/TDP Towuti/TDP_RGB.csv"]
#                   "/Users/bgrivna/Desktop/CHB May 2017/CHB_XYZ_20170518.csv",
#                   "/Users/bgrivna/Desktop/CHB May 2017/CHB_XRF_20170518.csv"]#,
#                   "/Users/bgrivna/Desktop/LacCore/DCH/DCH_MSCL_MBLF.csv"]
        
#     mdFilePaths = ["/Users/bgrivna/Desktop/CHB/HSPDP-CHB14_MSCL_MBS.csv",
#                    "/Users/bgrivna/Desktop/CHB/HSPDP-CHB14_XRF_MBS.csv",
#                     "/Users/bgrivna/Desktop/CHB/HSPDP-CHB14_XYZ_MBS.csv",
#                     "/Users/bgrivna/Desktop/CHB/HSPDP-CHB14_Subsamples_MBS.csv"]
    for mdPath in mdFilePaths:
        path, ext = os.path.splitext(mdPath)
        exportPath = path + "_spliced" + ext
        exportMeasurementData(affinePath, sitPath, mdPath, exportPath, wholeSpliceSection=True)

def doSampleExport():
    sitPath = "/Users/bgrivna/Desktop/PLJ Lago Junin/Site 1/PLJ_Site1_SITfromSparse.csv"
    #sampleDataTemplate = "/Users/bgrivna/Desktop/TDP Towuti/TDP_Samples/TDP-5055-3{}-samples.csv"
    #holes = ["A"]
    sdPath = "/Users/bgrivna/Desktop/PLJ Lago Junin/PLJsubsamples.csv"
    sampleExportPath = "/Users/bgrivna/Desktop/PLJ_Site1_Spliced_Samples.csv"
    exportSampleData(sitPath, sdPath, sampleExportPath)#, holes, sampleExportPath)
    
def doOffSpliceAffineExport():
    sit = si.SpliceIntervalTable.createWithFile("/Users/bgrivna/Desktop/TDP Towuti/Site 2 Exportage/TDP_Site2_SITfromSparse.csv")
    secsumm = openSectionSummaryFile("/Users/bgrivna/Desktop/TDP section summary.csv")
    mancorr = None #openManualCorrelationFile("/Users/bgrivna/Desktop/JimOffSpliceCorrelations.csv")
    exportPath = "/Users/bgrivna/Desktop/TDP_Site2_offSpliceAffine.csv"
    affineRows = gatherOffSpliceAffines(sit, secsumm, mancorr, exportPath, site="2")
    # write affineRows to file...

def appendDate(text):
    return text + "_{}".format(date.today().isoformat())

def doSparseSpliceToSITExport():
    log.info("--- Converting Sparse Splice to SIT ---")
    #ss = openSectionSummaryFile("/Users/bgrivna/Desktop/LacCore/DCH Challa/DCH_SectionSummary.csv")
    #sp = openSectionSplice("/Users/bgrivna/Desktop/LacCore/DCH Challa/DCH_SparseSplice.csv")
    #ss = openSectionSummaryFile("/Users/bgrivna/Desktop/LacCore/CHB/HSPDP-CHB section summary.csv")
    #sp = openSectionSplice("/Users/bgrivna/Desktop/LacCore/CHB/CHB_SpliceTable_23Dec_2016.csv")
    ss = openSectionSummaryFile("/Users/bgrivna/Desktop/DCSI/DCSI_SectionSummary.csv")
    sp = openSparseSplice("/Users/bgrivna/Desktop/DCSI/DCSI Sparse Splice Demo.csv")
    basepath = "/Users/bgrivna/Desktop/"
    affPath = basepath + appendDate("DCSI_AffineFromSparse") + ".csv"
    sitPath = basepath + appendDate("DCSI_SITFromSparse") + ".csv"
    onSpliceAffRows = convertSectionSpliceToSIT(sp, ss, affPath, sitPath)
    
    # load just-created SIT and find affines for off-splice cores
    sit = si.SpliceIntervalTable.createWithFile(sitPath)
    mancorr = None #openManualCorrelationFile("/Users/bgrivna/Desktop/TDP Towuti/Site 1/JimOffSpliceCorrelations.csv")
    offSpliceAffRows = gatherOffSpliceAffines(sit, ss, mancorr, sit.getSites())
    
    allAff = onSpliceAffRows + offSpliceAffRows
    allAff = fillAffineRows(allAff)
    
    arDicts = [ar.asDict() for ar in allAff]
    
    affDF = pandas.DataFrame(arDicts, columns=aff.AffineFormat.req)
    log.info("writing affine table to {}".format(affPath))
    log.debug("affine table column types:\n{}".format(affDF.dtypes))
    affDF.to_csv(affPath, index=False)

if __name__ == "__main__":
    log.basicConfig(level=log.DEBUG)
    
    #doSparseSpliceToSITExport()
    #doOffSpliceAffineExport()
    doMeasurementExport()
    #doSampleExport()
