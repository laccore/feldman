import pandas
import tabularImport as ti
import spliceInterval as si
import measurement as meas
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
    ss = ti.SectionSummary.createWithFile(filename)
    
    # force pandas.dtypes to "object" (string) for ID components
    objcols = ["Exp", "Site", "Hole", "Core", "CoreType", "Section"]
    ti.forceStringDatatype(objcols, ss.dataframe)
    
    return ss
    # confirm no blank/nan cells - fail to load? ignore such rows and warn user?


def openSectionSplice(filename):
    headers = [ "Site", "Hole", "Core", "CoreType", "TopSection", "TopOffset", "BottomSection", "BottomOffset", "SpliceType", "Comment" ]
    datfile = open(filename, 'rU')
    splice = pandas.read_csv(datfile, skiprows=1, header=None, names=headers, sep=None, engine='python', na_values="POOP")
    datfile.close()
    
    objcols = ["Site", "Hole", "Core", "CoreType", "TopSection", "BottomSection", "SpliceType", "Comment"]
    
    ti.forceStringDatatype(objcols, splice)
    
    return splice

# get total depth of a section offset using SectionSummary data and curated lengths if available
def getOffsetDepth(secsumm, site, hole, core, section, offset, compress=True):
    secTop = secsumm.getSectionTop(site, hole, core, section)
    secBot = secsumm.getSectionBot(site, hole, core, section)
    print "   section: {}-{}{}-{}, top = {}m, bot = {}m".format(site, hole, core, section, secTop, secBot)
    print "   section offset = {}cm + {}m = {}m".format(offset, secTop, secBot + offset/100.0)

    curatedLength = secsumm.getSectionLength(site, hole, core, section)
    if offset/100.0 > curatedLength:
        print "ERROR: top offset {}cm is beyond curated length of section {}m".format(offset, curatedLength)
        
    # if compress=True, compress depth to drilled interval
    drilledLength = secBot - secTop
    compFactor = 1.0
    if compress and curatedLength > drilledLength:
        compFactor = drilledLength / curatedLength
        
    return secTop + (offset/100.0 * compFactor)

    
def convertSectionSpliceToSIT(secsplice, secsumm, outpath):
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
        print "Interval {}".format(index + 1)
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
            print "   First interval, no splice tie type"
        elif sptype == "APPEND":
            # affine = distance between bottom of previous interval and top of current in MBLF space
            affine = prevAffine
            print "   APPENDing {} at depth {} based on previous affine {}".format(shiftTop, shiftTop + affine, affine)
        else: # TIE
            # affine = difference between prev bottom MCD and MBLF of current top
            affine = prevBotMcd - shiftTop
            print "   TIEing {} to previous bottom depth {}, affine shift of {}".format(shiftTop, prevBotMcd, affine)

        if prevBotMcd is not None and prevBotMcd > shiftTop + affine:
            print "   ERROR: previous interval bottom MCD {} is below current interval top MCD {}".format(prevBotMcd, shiftTop + affine)
            # increase affine to prevent overlap in case of APPEND - this should never happen for a TIE
            if sptype == "APPEND":
                overlap = prevBotMcd - (shiftTop + affine)                
                affine += overlap 
                print "   interval type APPEND, adjusting affine to {}m to avoid {}m overlap".format(affine, overlap)
            
        # create data for corresponding affine
        holecore = str(hole) + str(core)
        if holecore not in seenCores:
            seenCores.append(str(hole) + str(core))
            affineRow = {'Site':site, 'Hole':hole, 'Core':core, 'Core Type':row['CoreType'], 'Depth CSF (m)':shiftTop,
                         'Depth CCSF (m)':shiftTop + affine, 'Cumulative Offset (m)': affine, 'Differential Offset (m)': 0.0,
                         'Growth Rate':'', 'Shift Type':'TIE', 'Data Used':'', 'Quality Comment':''}
            affineRows.append(affineRow)
        else:
            print "ERROR: holecore {} already seen".format(holecore)
        
        # create new column data 
        topCSFs.append(shiftTop)
        topCCSFs.append(shiftTop + affine)
        
        botCSFs.append(shiftBot)
        botCCSFs.append(shiftBot + affine)
        
        prevBotMcd = shiftBot + affine
        prevAffine = affine
        
        # warnings
        if shiftTop >= shiftBot:
            print "    ERROR: interval top {} at or below interval bottom {} in MBLF".format(shiftTop, shiftBot)
        
        sptype = row['SpliceType']

    # done parsing, create affine table
    affDF = pandas.DataFrame(affineRows, columns=ti.AffineFormat.req)
    print "creating affine table, types:"
    print affDF.dtypes
    affDF.to_csv("/Users/bgrivna/Desktop/Affine_test_1.csv", index=False)
    
    # done parsing, create final dataframe for export
    sitDF = secsplice.copy()
    sitDF.insert(6, 'Top Depth CSF-A', pandas.Series(topCSFs))
    sitDF.insert(7, 'Top Depth CCSF-A', pandas.Series(topCCSFs))
    sitDF.insert(10, 'Bottom Depth CSF-A', pandas.Series(botCSFs))
    sitDF.insert(11, 'Bottom Depth CCSF-A', pandas.Series(botCCSFs))
    sitDF.insert(13, 'Data Used', "")
    
    print sitDF.dtypes
    sitDF.to_csv("/Users/bgrivna/Desktop/SIT_test_1.csv", index=False)
    
def sparseToSIT():
    ss = openSectionSummaryFile("/Users/bgrivna/Desktop/TDPSecSumm_AJN_03282016.csv")
    sp = openSectionSplice("/Users/bgrivna/Desktop/TDP_Site1_splice_test_tweak.csv")
    convertSectionSpliceToSIT(sp, ss, "/Users/bgrivna/Desktop/SIT_Site1_FOOOO.csv")

def exportSampleData():
    # load SIT
    sitPath = "/Users/bgrivna/Desktop/TDP Towuti/Site 1 Splice Export/TDP_Site1_SIT_cols.csv"
    sit = si.SpliceIntervalTable.createWithFile(sitPath)

    # load sample data from each hole in site 1
    holes = ["A", "B", "D", "E", "F"]
    sampleFiles = {}
    totalSampleRows = 0
    for hole in holes:
        path = "/Users/bgrivna/Desktop/TDP Towuti/TDP_Samples/TDP-5055-1{}-samples.csv".format(hole)
        sd = sample.SampleData.createWithFile(hole, path)

        print "Loading sample data file {}...".format(path),
        print "loaded {} rows".format(sd.rowCount())
        totalSampleRows += sd.rowCount()
        sampleFiles[hole] = sd

    print "{} sample data rows loaded from {} files".format(totalSampleRows, len(holes))
    
    print "\nApplying SIT to Sample Data..."

    expVals = {'A':[], 'B':[], 'D':[], 'E':[], 'F':[]}
    
    sprows = [] # rows comprising spliced dataset
    rowcount = 0
    for index, sirow in enumerate(sit.getIntervals()):
        print "Interval {}: {}".format(index, sirow)
        sd = sampleFiles[sirow.hole]
        sdrows = sd.getByRange(sirow.topMBSF, sirow.botMBSF)
        print "   found {} rows".format(len(sdrows)),
        if len(sdrows) > 0:
            print "...top depth = {}, bottom depth = {}".format(sdrows.iloc[0]['Depth'], sdrows.iloc[-1]['Depth'])
            print sdrows
        else:
            print "  ### WARNING: Zero matching rows found in sample data"
        
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
        print "Hole {}: {} ({} unique) of {} rows exported ({} not exported)".format(key, expTotal, uniqueTotal, fileTotal, fileTotal - expTotal)
        
    print "Total sample rows exported: {}".format(rowcount)
    
    exportdf = pandas.concat(sprows)

    # Argh. Introduced in pandas 0.17.0, we're stuck on 0.16.0 for now...
    # print "Rounding..."
    #exportdf = exportdf.round({'Depth': 3, 'Offset': 3})
    
    ti.writeToFile(exportdf, "/Users/bgrivna/Desktop/TDP_Site1_Samples_export_v2_E_fix.csv")


def exportMeasurementData():
    sitPath = "/Users/bgrivna/Desktop/TDP_Site1_SIT_cols.csv"
    sit = si.SpliceIntervalTable.createWithFile(sitPath)

    # load measurement data from each hole in site 1
    mdHoles = ["A", "B", "D", "E", "F"]
    mdFiles = {}
    for hole in mdHoles:
        #mdpath = "testdata/TDP-5055-1{}-gamma.csv".format(hole)
        #md = meas.MeasurementData.createWithFile(hole, "Natural Gamma", mdpath)
        mdpath = "/Users/bgrivna/Desktop/TDP Towuti/TDP_MS/TDP-5055-1{}-MS.csv".format(hole)
        md = meas.MeasurementData.createWithFile(hole, "Magnetic Susceptibility", mdpath)

        print "Loading measurement data file {}".format(mdpath)
        mdFiles[hole] = md
        
    sprows = [] # rows comprising spliced dataset
    rowcount = 0
    for index, sirow in enumerate(sit.getIntervals()):
        print "Interval {}: {}".format(index, sirow)
        md = mdFiles[sirow.hole]
        mdrows = md.getByRange(sirow.topMBSF, sirow.botMBSF)
        #print "   found {} rows, top depth = {}, bottom depth = {}".format(len(mdRows), mdRows.iloc[0]['Depth'], mdRows.iloc[-1]['Depth'])
        
        affineOffset = sirow.topMCD - sirow.topMBSF
        
        # adjust depth column
        mdrows.rename(columns={'Depth':'RawDepth'}, inplace=True)
        mdrows.insert(8, 'Depth', pandas.Series(mdrows['RawDepth'] + affineOffset))
        mdrows.insert(9, 'Offset', affineOffset)
        mdrows = mdrows[ti.MeasurementExportFormat.req] # reorder to reflect export format
        
        sprows.append(mdrows)
        
        rowcount += len(mdrows)
        
    print "Total rows: {}".format(rowcount)
    
    exportdf = pandas.concat(sprows)
    ti.writeToFile(exportdf, "TDP_Site1_MS_export.csv")


if __name__ == "__main__":
    exportSampleData()
    #exportMeasurementData()
