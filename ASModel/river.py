#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#************************************************************************
# --- Copyright (c) INRS 2016
# --- Institut National de la Recherche Scientifique (INRS)
# ---
# --- Licensed under the Apache License, Version 2.0 (the "License");
# --- you may not use this file except in compliance with the License.
# --- You may obtain a copy of the License at
# ---
# ---     http://www.apache.org/licenses/LICENSE-2.0
# ---
# --- Unless required by applicable law or agreed to in writing, software
# --- distributed under the License is distributed on an "AS IS" BASIS,
# --- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# --- See the License for the specific language governing permissions and
# --- limitations under the License.
#************************************************************************

"""
River
"""

__version__ = '1.0'

import codecs
import os
import logging

logger = logging.getLogger("INRS.ASModel.river")

class River(object):
    def __init__(self, name = u'', velocity = []):
        self.name = name
        self.vlct = velocity

    def dump(self):
        return '%s; %s' % (self.name, str(self.vlct))

    def load(self, l):
        n, v = l.split(';')
        v = v.strip()[1:-1]
        self.name = n.strip()
        self.vlct = [ float(i) for i in v.split(',') ]

    def getTransitTimes(self, d):
        return [ d/v for v in self.vlct ]

class Rivers(object):
    def __init__(self):
        self.tbl = {}

    def load(self, dataDir):
        fname = os.path.join(dataDir, 'rivers.txt')
        f = codecs.open(fname, "r", encoding="utf-8")
        for l in f.readlines():
            l = l.strip()
            if l[0] == u'#': continue
            r = River()
            r.load(l)
            self.tbl[r.name] = r

    def getNames(self):
        return sorted( self.tbl.keys() )

    def __getitem__(self, name):
        return self.tbl[name]

if __name__ == '__main__':
    def loadRivers():
        tbl = Rivers()
        tbl.load(u'data')
        return tbl

    logHndlr = logging.StreamHandler()
    FORMAT = "%(asctime)s %(levelname)s %(message)s"
    logHndlr.setFormatter( logging.Formatter(FORMAT) )

    logger = logging.getLogger("INRS.ASModel.river")
    logger.addHandler(logHndlr)
    logger.setLevel(logging.DEBUG)

    tbl = loadRivers()
    for r in tbl.tbl:
        print r.dump()

    print tbl.getNames()

