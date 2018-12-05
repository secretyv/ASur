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

import codecs
import os
import logging

LOGGER = logging.getLogger('INRS.ASModel.river')

class River:
    """
    Class River represent a river in ASModel. A River has a name
    and flow velocities.
    """
    def __init__(self, name='', velocity=()):
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

class Rivers:
    """
    Container of River
    """
    def __init__(self):
        self.tbl = {}

    def load(self, dataDir):
        """
        Load the rivers from file
        """
        fname = os.path.join(dataDir, 'rivers.txt')
        LOGGER.info('Reading %s', fname)
        f = codecs.open(fname, 'r', encoding='utf-8')
        for line in f.readlines():
            line = line.strip()
            if not line: continue
            if line[0] == '#': continue
            rvr = River()
            rvr.load(line)
            self.tbl[rvr.name] = rvr

    def getNames(self):
        """
        Return the list of all river names
        """
        return sorted( self.tbl.keys() )

    def __getitem__(self, name):
        return self.tbl[name]

if __name__ == '__main__':
    def loadRivers(path):
        tbl = Rivers()
        tbl.load(path)
        return tbl

    def main():
        logHndlr  = logging.StreamHandler()
        logFormat = '%(asctime)s %(levelname)s %(message)s'
        logHndlr.setFormatter( logging.Formatter(logFormat) )

        logger = logging.getLogger('INRS.ASModel.river')
        logger.addHandler(logHndlr)
        logger.setLevel(logging.DEBUG)

        path = '../BBData_v3.2/data.lim=1e-4'
        tbl = loadRivers(path)
        for rvr in tbl.tbl:
            print(rvr)

        print(tbl.getNames())

    main()
