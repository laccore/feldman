'''
April 14 2016
Has become a repository for all kinds of useful conversion routines that all desperately
need to be generalized and modularized in an intelligent way, but for now we're under the
gun trying to get Towuti its data...
'''

import logging as log

import pandas

import coreIdentity as ci
import tabularImport as ti
import data.spliceInterval as si
import data.measurement as meas
import data.sectionSummary as ss
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
    objcols = ["Exp", "Site", "Hole", "Core", "CoreType", "Section"]
    ti.forceStringDatatype(objcols, secsumm.dataframe)
    
    return secsumm
    # confirm no blank/nan cells - fail to load? ignore such rows and warn user?


def openSectionSplice(filename):
    headers = ["Site", "Hole", "Core", "CoreType", "TopSection", "TopOffset", "BottomSection", "BottomOffset", "SpliceType", "Comment"]
    datfile = open(filename, 'rU')
    splice = pandas.read_csv(datfile, skiprows=1, header=None, names=headers, sep=None, engine='python', na_values="POOP")
    datfile.close()
    
    objcols = ["Site", "Hole", "Core", "CoreType", "TopSection", "BottomSection", "SpliceType", "Comment"]
    
    ti.forceStringDatatype(objcols, splice)
    
    return splice

def openManualCorrelationFile(mcPath):
    headers = ["Site1", "Hole1", "Core1", "Tool1", "Section1", "SectionDepth1", "Site2", "Hole2", "Core2", "Tool2", "Section2", "SectionDepth2"]
    mcFile = open(mcPath, 'rU')
    mancorr = pandas.read_csv(mcFile, skiprows=1, header=None, names=headers, sep=None, engine='python', na_values="POOP")
    mcFile.close()
    
    objcols = ["Site1", "Hole1", "Core1", "Tool1", "Section1", "Site2", "Hole2", "Core2", "Section2", "Tool2"]
    
    ti.forceStringDatatype(objcols, mancorr)
    
    return ManualCorrelationTable("Jim's Manual Correlation", mancorr)
    

# get total depth of a section offset using SectionSummary data and curated lengths if available
def getOffsetDepth(secsumm, site, hole, core, section, offset, compress=True):
    secTop = secsumm.getSectionTop(site, hole, core, section)
    secBot = secsumm.getSectionBot(site, hole, core, section)
    log.debug("   section: {}-{}{}-{}, top = {}m, bot = {}m".format(site, hole, core, section, secTop, secBot))
    log.debug("   section offset = {}cm + {}m = {}m".format(offset, secTop, secBot + offset/100.0))

    curatedLength = secsumm.getSectionLength(site, hole, core, section)
    if offset/100.0 > curatedLength:
        log.warning("top offset {}cm is beyond curated length of section {}m".format(offset, curatedLength))
        
    # if compress=True, compress depth to drilled interval
    drilledLength = secBot - secTop
    compFactor = 1.0
    if compress and curatedLength > drilledLength:
        compFactor = drilledLength / curatedLength
        
    return secTop + (offset/100.0 * compFactor)

    
def convertSectionSpliceToSIT(secsplice, secsumm, affineOutPath, sitOutPath):
    seenCores = [] # list of cores that have already been added to affine
    affineRows = [] # list of dicts, each representing a generated affine table row
    
    topCSFs = []
    topCCSFs = []
    botCSFs = []
    botCCSFs = []
    prevAffine = 0.0 # previous affine shift (used for APPEND shift)
    prevBotMcd = None
    sptype = None
    for index, row in secsplice.iterrows():
        log.debug("Interval {}".format(index + 1))
        site = row['Site']
        hole = row['Hole']
        core = row['Core']
        top = row['TopSection']
        topOff = row['TopOffset']
        shiftTop = getOffsetDepth(secsumm, site, hole, core, top, topOff, compress=True)
        
        bot = row['BottomSection']
        botOff = row['BottomOffset']
        shiftBot = getOffsetDepth(secsumm, site, hole, core, bot, botOff, compress=True)
        
        affine = 0.0
        if sptype is None: # first interval
            affine = 0.0
            log.debug("First interval, no splice tie type")
        elif sptype == "APPEND":
            # affine = distance between bottom of previous interval and top of current in MBLF space
            affine = prevAffine
            log.debug("APPENDing {} at depth {} based on previous affine {}".format(shiftTop, shiftTop + affine, affine))
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
        holecore = str(hole) + str(core)
        if holecore not in seenCores:
            seenCores.append(str(hole) + str(core))
            affineRow = {'Site':site, 'Hole':hole, 'Core':core, 'Core Type':row['CoreType'], 'Depth CSF (m)':shiftTop,
                         'Depth CCSF (m)':shiftTop + affine, 'Cumulative Offset (m)': affine, 'Differential Offset (m)': 0.0,
                         'Growth Rate':'', 'Shift Type':'TIE', 'Data Used':'', 'Quality Comment':''}
            affineRows.append(affineRow)
        else:
            log.error("holecore {} already seen, ignoring".format(holecore))
        
        # create new column data 
        topCSFs.append(shiftTop)
        topCCSFs.append(shiftTop + affine)
        
        botCSFs.append(shiftBot)
        botCCSFs.append(shiftBot + affine)
        
        prevBotMcd = shiftBot + affine
        prevAffine = affine
        
        # warnings
        if shiftTop >= shiftBot:
            log.warning("interval top {} at or below interval bottom {} in MBLF".format(shiftTop, shiftBot))
        
        sptype = row['SpliceType']

    # done parsing, create affine table
    affDF = pandas.DataFrame(affineRows, columns=ti.AffineFormat.req)
    log.info("writing affine table to {}".format(affineOutPath))
    log.debug("affine table column types:\n{}".format(affDF.dtypes))
    affDF.to_csv(affineOutPath, index=False)
    
    # done parsing, create final dataframe for export
    sitDF = secsplice.copy()
    sitDF.insert(6, 'Top Depth CSF-A', pandas.Series(topCSFs))
    sitDF.insert(7, 'Top Depth CCSF-A', pandas.Series(topCCSFs))
    sitDF.insert(10, 'Bottom Depth CSF-A', pandas.Series(botCSFs))
    sitDF.insert(11, 'Bottom Depth CCSF-A', pandas.Series(botCCSFs))
    sitDF.insert(13, 'Data Used', "")
    
    log.info("writing splice interval table to {}".format(sitOutPath))
    log.debug("splice interval table column types:{}".format(sitDF.dtypes))
    sitDF.to_csv(sitOutPath, index=False)
    
def exportSampleData(sitPath, sdPathTemplate, holes, exportPath):
    log.info("--- Exporting Sample Data --- ")
    # load SIT
    sit = si.SpliceIntervalTable.createWithFile(sitPath)

    # load sample data from each hole in site 1
    sampleFiles = {}
    totalSampleRows = 0
    for hole in holes:
        path = sdPathTemplate.format(hole)
        
        # TODO: NEED WAY TO DETECT AND COPE WITH BAD DATA ROWS, THEY FUCK EVERYTHING UP
        sd = sample.SampleData.createWithFile(hole, path)

        log.info("Loading sample data file {}...loaded {} rows".format(path), sd.rowCount()),
        totalSampleRows += sd.rowCount()
        sampleFiles[hole] = sd

    log.info("{} sample data rows loaded from {} files".format(totalSampleRows, len(holes)))
    log.info("Applying SIT to Sample Data...")

    # TODO: one-liner to create map keyed on hole with empty lists for values?
    expVals = {} # track exported rows from each hole for reporting purposes
    for h in holes:
        expVals[h] = []
    
    sprows = [] # rows comprising spliced dataset
    rowcount = 0
    for index, sirow in enumerate(sit.getIntervals()):
        log.debug("Interval {}: {}".format(index, sirow))
        sd = sampleFiles[sirow.hole]
        sdrows = sd.getByRangeAndCore(sirow.topMBSF, sirow.botMBSF, sirow.core)
        log.debug("   found {} rows".format(len(sdrows)))
        if len(sdrows) > 0:
            log.debug("...top depth = {}, bottom depth = {}".format(sdrows.iloc[0]['Depth'], sdrows.iloc[-1]['Depth']))
            log.debug(str(sdrows))
        else:
            log.error("Zero matching rows found in sample data")
        
        # track Data values for rows we're exporting in attempt to figure out what's missing
        for t in sdrows.itertuples():
            expVals[sirow.hole].append(t[9])
        
        affineOffset = sirow.topMCD - sirow.topMBSF
        
        # adjust depth column
        sdrows.rename(columns={'Depth':'RawDepth'}, inplace=True)
        
        # round here until we can upgrade to pandas 0.17.0 (see below)
        sdrows.insert(8, 'Depth', pandas.Series(sdrows['RawDepth'] + affineOffset).round(3))
        sdrows.insert(9, 'Offset', round(affineOffset, 3))
        sdrows = sdrows[ti.SampleExportFormat.req] # reorder to reflect export format
        
        sprows.append(sdrows)
        
        rowcount += len(sdrows)
        
    for key, dlist in expVals.items():
        fileTotal = sampleFiles[key].rowCount()
        uniqueTotal = len(set(dlist))
        expTotal = len(dlist)
        log.info("Hole {}: {} ({} unique) of {} rows exported ({} not exported)".format(key, expTotal, uniqueTotal, fileTotal, fileTotal - expTotal))
        
    log.info("Total sample rows exported: {}".format(rowcount))
    
    exportdf = pandas.concat(sprows)

    # Argh. Introduced in pandas 0.17.0, we're stuck on 0.16.0 for now...
    # print "Rounding..."
    #exportdf = exportdf.round({'Depth': 3, 'Offset': 3})
    
    ti.writeToFile(exportdf, exportPath)


# todo: MeasDataDB class that hides multi-file (broken into holes) vs single-file data
def exportMeasurementData(sitPath, measDataTemplate, holes, exportPath):
    log.info("--- Exporting Measurement Data ---")
    
    #sitPath = "/Users/bgrivna/Desktop/TDP Towuti/Site 1 Splice Export/TDP_Site1_SIT_cols.csv"
    sit = si.SpliceIntervalTable.createWithFile(sitPath)

    # load measurement data from each hole in site 1
    mdHoles = holes #["A", "B", "D", "E", "F"]
    mdFiles = {}
    for hole in mdHoles:
        #mdpath = "testdata/TDP-5055-1{}-gamma.csv".format(hole)
        #md = meas.MeasurementData.createWithFile(hole, "Natural Gamma", mdpath)
#         mdpath = "/Users/bgrivna/Desktop/TDP Towuti/TDP_MS/TDP-5055-1{}-MS.csv".format(hole)
#         md = meas.MeasurementData.createWithFile(hole, "Magnetic Susceptibility", mdpath)
        #mdpath = "/Users/bgrivna/Desktop/TDP Towuti/TDP_Gamma/TDP-5055-1{}-gamma.csv".format(hole)
        mdpath = measDataTemplate.format(hole)
        md = meas.MeasurementData.createWithFile(hole, "Gamma Density", mdpath)

        log.info("Loading measurement data file {}".format(mdpath))
        mdFiles[hole] = md
        
    sprows = [] # rows comprising spliced dataset
    rowcount = 0
    for index, sirow in enumerate(sit.getIntervals()):
        log.debug("Interval {}: {}".format(index, sirow))
        md = mdFiles[sirow.hole]
        mdrows = md.getByRangeAndCore(sirow.topMBSF, sirow.botMBSF, sirow.core)
        #print "   found {} rows, top depth = {}, bottom depth = {}".format(len(mdRows), mdRows.iloc[0]['Depth'], mdRows.iloc[-1]['Depth'])
        
        affineOffset = sirow.topMCD - sirow.topMBSF
        
        # adjust depth column
        mdrows.rename(columns={'Depth':'RawDepth'}, inplace=True)
        mdrows.insert(8, 'Depth', pandas.Series(mdrows['RawDepth'] + affineOffset))
        mdrows.insert(9, 'Offset', affineOffset)
        mdrows = mdrows[meas.MeasurementExportFormat.req] # reorder to reflect export format
        
        sprows.append(mdrows)
        
        rowcount += len(mdrows)
        
    log.info("Total rows: {}".format(rowcount))
    
    exportdf = pandas.concat(sprows)
    #ti.writeToFile(exportdf, "TDP_Site1_Gamma_export_CoreCheck_04132016.csv")
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



def exportOffSpliceAffines(sit, secsumm, mancorr, exportPath, site):
    # find all off-splice cores: those in section summary that are *not* in SIT
    skippedCoreCount = 0
    offSpliceCores = []
    onSpliceCores = []
    ssCores = secsumm.getCores()
    for index, row in ssCores.iterrows():
        if row.Site != site: # skip section summary rows from non-site cores
            skippedCoreCount += 1
            continue
        if not sit.containsCore(row.Site, row.Hole, row.Core):
            offSpliceCores.append(row)
        else:
            onSpliceCores.append(row)
            
    log.info("Found {} off-splice cores in {} section summary cores for site {} - skipped {} non-site cores".format(len(offSpliceCores), len(ssCores), site, skippedCoreCount))

    osAffineShifts = {}
    
    # for each of the off-splice cores:
    for osc in offSpliceCores:
        oscid = "{}{}-{}{}".format(osc.Site, osc.Hole, osc.Core, osc.CoreType)
        #oscid = ci.CoreIdentity(osc.Site, osc.Hole, osc.Core, osc.CoreType)
        
        mcc = None
        if mancorr is not None:
            mcc = mancorr.getOffSpliceCore(osc.Site, osc.Hole, osc.Core)
            if mcc is not None:
                log.debug("Found manual correlation for {}".format(OffSpliceCore(osc)))
            else:
                log.debug("no manual correlation for {}".format(OffSpliceCore(osc)))
            
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
                offSpliceOffset = onSpliceMcd - offSpliceMbsf
                log.debug("   + SIT offset of {} = {} MCD".format(sitOffset, onSpliceMcd))
                log.debug("   off-splice MBSF {} + {} offset = {} on-splice MCD".format(offSpliceMbsf, offSpliceOffset, onSpliceMcd))
                
                # Track affine for that core and confirm that other correlations result in the same affine shift - if not, use original shift and WARN
                if oscid not in osAffineShifts:
                    osAffineShifts[oscid] = offSpliceOffset
                else:
                    log.warning("Found additional offset for {}: {} (new) vs. {} (existing) - ignoring new!".format(oscid, offSpliceOffset, osAffineShifts[oscid]))
            else:
                # warn that "correlation core" is NOT on-splice and fall back on default top MBSF approach
                log.warning("Alleged correlation core {}{}-{} is NOT on-splice".format(mcc.Site2, mcc.Hole2, mcc.Core2))
                
        if oscid not in osAffineShifts:
            # find on-splice core with top MBSF closest to that of the current core and use its affine shift
            log.debug("No manual shift for {}, seeking closest top...".format(oscid))
            closestCore = secsumm.getCoreWithClosestTop(osc.Site, osc.Hole, osc.Core, onSpliceCores)
            closestCoreOffset = sit.getCoreOffset(closestCore.Site, closestCore.Hole, closestCore.Core)
            osAffineShifts[oscid] = closestCoreOffset
            
    # generate affine rows for each affine and export as CSV - can be combined with existing (on-splice) affine table to create complete table
    affineRows = []
    #sortedCoreKeys = sorted(osAffineShifts.keys())
    for key, offset in osAffineShifts.items():
        affineRows.append({'Core ID': key, 'Offset': offset})
#     for oas in osAffineShifts:
#         affineRow = {'Site':oas.Site, 'Hole':oas.Hole, 'Core':oas.Core, 'CoreType':oas.CoreType, 'Cumulative Offset (m)':osAffineShifts[oas]}
#         affineRows.append(affineRow)
        
    # create affine file!
    affDF = pandas.DataFrame(affineRows, columns=["Core ID", "Offset"])
    log.info("writing off-splice affine table to {}".format(exportPath))
    affDF.to_csv(exportPath, index=False)
    
def doMeasurementExport():
    sitPath = "/Users/bgrivna/Desktop/TDP Towuti/Site 1 Splice Export/TDP_Site1_SIT_cols.csv"
    measDataTemplate = "/Users/bgrivna/Desktop/TDP Towuti/TDP_Samples/TDP-5055-1{}-samples.csv"
    measDataHoles = ["A", "B", "D", "E", "F"]
    exportPath = "/Users/bgrivna/TDP_Site2_MeasurementData.csv"
    exportMeasurementData(sitPath, measDataTemplate, measDataHoles, exportPath)

def doSampleExport():
    sitPath = "/Users/bgrivna/Desktop/TDP Towuti/Site 1 Splice Export/TDP_Site1_SIT_cols.csv"
    sampleDataTemplate = "/Users/bgrivna/Desktop/TDP Towuti/TDP_Samples/TDP-5055-1{}-samples.csv"
    holes = ["A", "B", "D", "E", "F"]
    sampleExportPath = "/Users/bgrivna/Desktop/TDP_Site1_Samples_04142016_export.csv"
    exportSampleData(sitPath, sampleDataTemplate, holes, sampleExportPath)
    
def doOffSpliceAffineExport():
    sit = si.SpliceIntervalTable.createWithFile("/Users/bgrivna/Desktop/TDP Towuti/Site 2 Exportage/TDP_Site2_SITfromSparse.csv")
    secsumm = openSectionSummaryFile("/Users/bgrivna/Desktop/TDP section summary.csv")
    mancorr = None #openManualCorrelationFile("/Users/bgrivna/Desktop/JimOffSpliceCorrelations.csv")
    exportPath = "/Users/bgrivna/Desktop/TDP_Site2_offSpliceAffine.csv"
    exportOffSpliceAffines(sit, secsumm, mancorr, exportPath, site="2")
    
def doSparseSpliceToSITExport():
    log.info("--- Converting Sparse Splice to SIT ---")
    ss = openSectionSummaryFile("/Users/bgrivna/Desktop/TDP section summary.csv")
    sp = openSectionSplice("/Users/bgrivna/Desktop/TDP Towuti/Site 2 Exportage/TDP_Site2_SparseSplice.csv")
    basepath = "/Users/bgrivna/Desktop/"
    convertSectionSpliceToSIT(sp, ss, basepath + "TDP_Site2_AffineFromSparse.csv", basepath + "TDP_Site2_SITfromSparse.csv")


if __name__ == "__main__":
    log.basicConfig(level=log.DEBUG)
    
    #doSparseSpliceToSITExport()
    doOffSpliceAffineExport()
    #exportMeasurementData()
