'''
Created on Apr 5, 2016

@author: bgrivna

Parsing of core naming formats e.g. LacCore, IODP
'''

import re

# Only attempting LacCore format for now:
# ex. GLAD7-MAL05-1B-32E-4-A
# Expedition = GLAD7
# Lake = MAL
# Year = 05
# Site = 1
# Hole = B
# Core = 32
# Core Type = E
# Section = 4
# Half (optional) = A

# IODP format is very similar, main difference is absence of lake/year token and longer site (U + #)
# ex. 327-U1363B-2H-5-A
# Expedition = 327
# Site = U1363
# Hole = B
# Core = 2
# Core Type = H
# Section = 5
# Half (optional) = A


# This isn't general enough to work for both LacCore and IODP due to LC's additional Lake/Year field.
# However, Exp + optional Lake/Year field could be regarded as "top-level" identity, essentially a name
# for the meaningful drilling information that follows. Can parse out details of these identities on a
# group-specific basis if needed.
class CoreIdentity:
    name = None
    site = None
    hole = None
    core = None
    tool = None
    section = None
    half = None
    
    # default to empty section and half - in many cases we only need core-level identity (e.g. affines)
    def __init__(self, name, site, hole, core, tool, section=None, half=None):
        self.name = name
        self.site = site
        self.hole = hole
        self.core = core
        self.tool = tool
        self.section = section
        self.half = half
        
    def __repr__(self):
        rep = ""
        if self.name is not None:
            rep += self.name + "-"
        rep += "{}{}-{}{}".format(self.site, self.hole, self.core, self.tool)
        if self.section is not None:
            rep += "-{}".format(self.section)
        if self.half is not None:
            rep += "-{}".format(self.half)
        return rep
        
#     def __repr__(self):
#         rep = "Name: {}\nSite: {}\nHole: {}\nCore: {}\nCoreType: {}\nSection: {}".format(self.name, self.site, self.hole, self.core, self.tool, self.section)
#         if self.half is not None:
#             rep += "\nHalf: {}".format(self.half)
#         return rep
    
def parseIdentity(idstr):
    tokens = idstr.split('-')
    if len(tokens) == 5 or len(tokens) == 6:
        exp = tokens[0]
        ly = tokens[1]
        sh = tokens[2]
        cct = tokens[3]
        sec = tokens[4]
        half = None
        if len(tokens) == 6: # half: A (archive), W (working) or WR (whole-round)
            halfToken = tokens[5]
            if halfToken == 'A' or halfToken == 'W' or halfToken == 'WR':
                half = halfToken
            else:
                print "Invalid half {}, expected A, W or WR".format(halfToken)
        
        charNumPattern = "([0-9]+)([A-Z]+)"
        sh_items = re.match(charNumPattern, sh)
        if sh_items:
            site = sh_items.groups()[0]
            hole = sh_items.groups()[1]
        
        cct_items = re.match(charNumPattern, cct)
        if cct_items:
            core = cct_items.groups()[0]
            tool = cct_items.groups()[1]
        
        name = exp + "-" + ly
        ci = CoreIdentity(name, site, hole, core, tool, sec, half)
        return ci

if __name__ == "__main__":
    parseIdentity("TDP-TOW15-1B-23H-2")
    parseIdentity("GLAD07-MAL05-12A-1X-5")
    parseIdentity("FOO-BAR69-6Z-3A-4-A")
    parseIdentity("FOO-BAR69-6Z-3A-4-J")