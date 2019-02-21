#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#************************************************************************
# --- Copyright (c) INRS 2016
# --- Institut National de la Recherche Scientifique (INRS)
# --- Copyright (c) Yves Secretan 2018
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
Tide table
A tide table is made of tide records, LW or HW.
"""

import bisect
import codecs
import contextlib
import datetime
import dateutil
import glob
import logging
import os
import time
import warnings
import requests
import pytz
import dateutil.parser

# Obscur bug in dateutil.parser
# http://stackoverflow.com/questions/21296475/python-dateutil-str-warning
warnings.filterwarnings("ignore", category=UnicodeWarning)

LOGGER = logging.getLogger("INRS.ASModel.tide")

def nint(d):
    return int(d + 0.5)

class TideRecord:
    """
    A TideRecord is either a HW or LW time stamp.
    """
    def __init__(self, dt = datetime.datetime(datetime.MINYEAR, 1, 1), wl = 0.0):
        self.dt = dt
        self.wl = wl

    def __hash__(self):
        return hash((self.dt, self.wl))
    
    def __lt__(self, other):
        # La version complète n'est pas compatible avec par exemple getNextHW.
        # Il ne trouve plus la HW suivante mais retourne l'identique.
        # return (self.dt < other.dt) or (self.dt == other.dt and self.wl < other.wl)
        return (self.dt < other.dt)

    def __eq__(self, other):
        return self.dt == other.dt and self.wl == other.wl

    def __ne__(self, other):
        return self.dt != other.dt or self.wl != other.wl

    def __str__(self):
        return '%s %f' % (self.dt.isoformat(), self.wl)

    def dump(self):
        return '%s; %f' % (self.dt.isoformat(), self.wl)

    def load(self, l):
        dt, wl = l.split(';')
        self.dt = dateutil.parser.parse(dt)
        self.wl = float(wl)

class TideTable:
    """
    A TideTable is a sequence of TideRecords
    """

    NPNTS_HW_LW = 31
    NPNTS_LW_HW = 19
    DELTA_NRMTD = 900.0     # delta t for normalized tide

    def __init__(self):
        self.tbl = []

    def dump(self, fname):
        f = codecs.open(fname, "w", encoding="utf-8")
        for r in self.tbl:
            f.write('%s\n' % r.dump())

    def load(self, dataDir):
        uniquer = set()
        ptrn = os.path.join(dataDir, 'tide_3248*.txt')
        for fname in glob.glob(ptrn):
            LOGGER.debug('Read tide file %s', fname)
            f = codecs.open(fname, "r", encoding="utf-8")
            for l in f.readlines():
                l = l.strip()
                if l[0] == '#': continue
                r = TideRecord()
                r.load(l)
                uniquer.add(r)
        self.tbl.extend( sorted(uniquer) )
        LOGGER.debug('Tide table loaded, size = %i', len(self.tbl))

    def append(self, r):
        self.tbl.append(r)

    def extend(self, t):
        self.tbl.extend(t)

    def sort(self):
        self.tbl.sort()

    def getTideSignal(self, t_start, t_end, dt):
        """
        Tide WL between t_start and t_end
        """
        res = []
        t_actu = t_start
        while t_actu < t_end:
            res.append( self.getWL(t_actu) )
            t_actu += dt
        t_actu = t_end
        res.append( self.getWL(t_actu) )
        return res

    def getWL(self, dt):
        """
        Linear interpolation of water level at datetime dt
        """
        i = bisect.bisect_left(self.tbl, TideRecord(dt))
        r0 = self.tbl[i-1]
        r1 = self.tbl[i]
        assert r0.dt <= dt <= r1.dt
        a = (dt-r0.dt).total_seconds() / (r1.dt-r0.dt).total_seconds()
        assert 0.0 <= a <= 1.0
        h = r0.wl + a*(r1.wl-r0.wl)
        return TideRecord(dt, h)

    def getPreviousHW(self, dt):
        """
        Return the High Water before datetime dt
        """
        i = bisect.bisect_left(self.tbl, TideRecord(dt))
        if self.tbl[i-1].wl > self.tbl[i-2].wl:
            return self.tbl[i-1]
        else:
            return self.tbl[i-2]

    def getPreviousLW(self, dt):
        """
        Return the Low Water before datetime dt
        """
        i = bisect.bisect_left(self.tbl, TideRecord(dt))
        if self.tbl[i-1].wl < self.tbl[i-2].wl:
            return self.tbl[i-1]
        else:
            return self.tbl[i-2]

    def getNextHW(self, dt):
        """
        Return the High Water after datetime dt
        """
        i = bisect.bisect_right(self.tbl, TideRecord(dt))
        if self.tbl[i].wl > self.tbl[i+1].wl:
            return self.tbl[i]
        else:
            return self.tbl[i+1]

    def getNextLW(self, dt):
        """
        Return the Low Water after datetime dt
        """
        i = bisect.bisect_right(self.tbl, TideRecord(dt))
        if self.tbl[i].wl < self.tbl[i+1].wl:
            return self.tbl[i]
        else:
            return self.tbl[i+1]

    def getNormalizedTime(self, dt):
        return self.getNormalizedTimeIndex(dt) * TideTable.DELTA_NRMTD

    def getNormalizedTimeIndex(self, dt):
        """
        Return the normalized time span from previous HW

        Real HW to LW is divided in 31 intervals of ~ 900s
        Real LW to HW is divided in 19 intervals of ~ 900s
        The normalized time is based on intervals of exactly 900s
        from the previous HW
        """
        doDebug = (LOGGER.getEffectiveLevel() == logging.DEBUG)
        hw0 = self.getPreviousHW(dt)
        lw  = self.getNextLW(hw0.dt)
        hw1 = self.getNextHW(hw0.dt)
        if doDebug:
            LOGGER.debug('HW0: %s', str(hw0))
            LOGGER.debug('LW:  %s', str(lw))
            LOGGER.debug('HW1: %s', str(hw1))
        assert hw0.dt <= dt <= hw1.dt
        if dt <= lw.dt:
            dt2hw = (   dt - hw0.dt).total_seconds()    # delta from item to previous HW
            lw2hw = (lw.dt - hw0.dt).total_seconds()    # delta from LW to previous HW
            stp_hw2lw  = lw2hw / TideTable.NPNTS_HW_LW
            nstp_dt2lw = nint(dt2hw/stp_hw2lw)
            inrm_tim = nstp_dt2lw
            if doDebug:
                LOGGER.debug('dt < lw.dt')
                LOGGER.debug('   Delta HW-T : %6.3fh %9.1fs', dt2hw/3600.0, dt2hw)
                LOGGER.debug('   Delta HW-LW: %6.3fh %9.1fs', lw2hw/3600.0, lw2hw)
                LOGGER.debug('   Step  HW-LW: %9.1fs', stp_hw2lw)
                LOGGER.debug('   nsteps: %i', nstp_dt2lw)
                LOGGER.debug('   normalized time: %f %f', inrm_tim*TideTable.DELTA_NRMTD, dt2hw)
        else:
            dt2lw = (    dt -  lw.dt).total_seconds()    # delta from item to LW
            dt2hw = (    dt - hw0.dt).total_seconds()    # delta from item to previous HW
            hw2lw = (hw1.dt -  lw.dt).total_seconds()    # delta from next HW to LW
            lw2hw = ( lw.dt - hw0.dt).total_seconds()    # delta from LW to previous HW
            stp_lw2hw  = hw2lw / TideTable.NPNTS_LW_HW
            stp_hw2lw  = lw2hw / TideTable.NPNTS_HW_LW
            nstp_dt2lw = nint(dt2lw/stp_lw2hw)
            nstp_hw2lw = nint(lw2hw/stp_hw2lw)
            inrm_tim = (nstp_hw2lw + nstp_dt2lw)
            assert nstp_hw2lw == TideTable.NPNTS_HW_LW
            if doDebug:
                LOGGER.debug('dt > lw.dt')
                LOGGER.debug('   Delta LW-T : %6.3fh %9.1fs', dt2lw/3600.0, dt2lw)
                LOGGER.debug('   Delta HW-T : %6.3fh %9.1fs', dt2hw/3600.0, dt2hw)
                LOGGER.debug('   Delta HW-LW: %6.3fh %9.1fs', lw2hw/3600.0, lw2hw)
                LOGGER.debug('   Delta LW-HW: %6.3fh %9.1fs', hw2lw/3600.0, hw2lw)
                LOGGER.debug('   step HW-LW: %9.1fs', stp_hw2lw)
                LOGGER.debug('   step LW-HW: %9.1fs', stp_lw2hw)
                LOGGER.debug('   nsteps HW-LW: %i', nstp_hw2lw)
                LOGGER.debug('   nsteps LW-T : %i', nstp_dt2lw)
                LOGGER.debug('   normalized time: %f %f', inrm_tim*TideTable.DELTA_NRMTD, dt2hw)
        return inrm_tim


if __name__ == '__main__':
    logHndlr = logging.StreamHandler()
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logHndlr.setFormatter( logging.Formatter(FORMAT) )

    #LOGGER = logging.getLogger("INRS.ASModel.tide")
    LOGGER.addHandler(logHndlr)
    LOGGER.setLevel(logging.DEBUG)

    dirname = r'E:\Projets_simulation\VilleDeQuebec\Beauport\Simulation\PIO\BBData_v1812\data.lim=1.0e-03'
    tbl = TideTable()
    tbl1 = tbl.load(dirname)
