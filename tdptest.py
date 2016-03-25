import pandas
import tabularImport as ti

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
    forceStringDatatype(objcols, ss.dataframe)
    
    return ss
    # confirm no blank/nan cells - fail to load? ignore such rows and warn user?
    
# force pandas column dtype and convert values to object (string)
def forceStringDatatype(cols, dataframe):
    for col in cols:
        dataframe[col] = dataframe[col].astype(object)
        dataframe[col] = dataframe[col].apply(lambda x: str(x)) # todo: if x != NaN? to avoid line below?
        
        # forced string conversion forces all NaN values to the string "nan" - remove these
        dataframe[col] = dataframe[col].apply(lambda x: "" if x == "nan" else x)

def openSectionSplice(filename):
    headers = [ "Site", "Hole", "Core", "CoreType", "TopSection", "TopOffset", "BottomSection", "BottomOffset", "SpliceType", "Comment" ]
    datfile = open(filename, 'rU')
    splice = pandas.read_csv(datfile, skiprows=1, header=None, names=headers, sep=None, engine='python', na_values="POOP")
    datfile.close()
    
    objcols = ["Site", "Hole", "Core", "CoreType", "TopSection", "BottomSection", "SpliceType", "Comment"]
    
    forceStringDatatype(objcols, splice)
    
    return splice

    
def convertSectionSpliceToSIT(secsplice, secsumm, outpath):
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
        topDepth = secsumm.getSectionTop(site, hole, core, top)
        secBot = secsumm.getSectionBot(site, hole, core, top)
        print "   top section: {}-{}{}-{}, top = {}m, bot = {}m".format(site, hole, core, top, topDepth, secBot)
        print "     top offset = {}cm + {}m = {}m".format(topOff, topDepth, topDepth + topOff/100.0)

        topCuratedLength = secsumm.getSectionLength(site, hole, core, top)
        shiftTop = topDepth + topOff/100.0
        if topOff/100.0 > topCuratedLength:
            print "ERROR: top offset {}cm is beyond curated length of section {}m".format(topOff, topCuratedLength)
        
        bot = row['BottomSection']
        botOff = row['BottomOffset']
        botDepth = secsumm.getSectionTop(site, hole, core, bot)
        secBot = secsumm.getSectionBot(site, hole, core, bot)
        print "   bot section: {}-{}{}-{}, top = {}m, bot = {}m".format(site, hole, core, bot, botDepth, secBot)
        print "     bot offset = {}cm + {}m = {}m".format(botOff, botDepth, botDepth + botOff/100.0)
        
        botCuratedLength = secsumm.getSectionLength(site, hole, core, bot)
        shiftBot = botDepth + botOff/100.0 
        if botOff/100.0 > botCuratedLength:
            print "ERROR bottom offset {}cm is beyond curated length of section {}m".format(botOff, botCuratedLength)
            
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
        
    # done parsing, create final dataframe for export
    sitDF = secsplice.copy()
    sitDF.insert(6, 'Top Depth CSF-A', pandas.Series(topCSFs))
    sitDF.insert(7, 'Top Depth CCSF-A', pandas.Series(topCCSFs))
    sitDF.insert(10, 'Bottom Depth CSF-A', pandas.Series(botCSFs))
    sitDF.insert(11, 'Bottom Depth CCSF-A', pandas.Series(botCCSFs))
    sitDF.insert(13, 'Data Used', "")
    
    print sitDF.dtypes
    sitDF.to_csv("/Users/bgrivna/Desktop/SIT_test_1.csv", index=False)


if __name__ == "__main__":
    ss = openSectionSummaryFile("/Users/bgrivna/Desktop/TDPSectionSummary_B19tweak.csv")
    sp = openSectionSplice("/Users/bgrivna/Desktop/TDP_Site1_splice_test_tweak.csv")
    convertSectionSpliceToSIT(sp, ss, "/Users/bgrivna/Desktop/SIT_Site1_FOOOO.csv")
