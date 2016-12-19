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
Tide table 
A tide table is made of tide records, LW or HW.
Utilitaries allow to download the data from MPO site
"""

from __future__ import print_function

__version__ = '1.0'

import bisect
import codecs
import datetime
import logging
import os
import time
import warnings
import mechanize
import pytz
import dateutil.parser

# Obscur bug in dateutil.parser
# http://stackoverflow.com/questions/21296475/python-dateutil-unicode-warning
warnings.filterwarnings("ignore", category=UnicodeWarning)

logger = logging.getLogger("INRS.ASModel.tide")

def nint(d):
    return int(d + 0.5)

class FixedOffset(datetime.tzinfo):
    """Fixed offset in minutes east from UTC."""

    def __init__(self, offset, name):
        self.__offset = datetime.timedelta(minutes = offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return 0


class DataReaderMPO(object):
    """
    DAta reader for MPO tide tables
    """
    def __init__(self, station = -1, year = datetime.date.today().year):
        self.station = station
        self.year    = year
        self.tzinfo  = FixedOffset(-5*60, 'HNE')

    def __buildURL(self):
        y = self.year
        i = self.station
        url = u'http://www.tides.gc.ca/fra/donnees/tableau/%i/wlev_sec/%i' % (y, i)
        return url

    def __skipToLine(self, f, tgt):
        l = u''
        while True:
            l = f.readline()
            if not l: break
            if l.strip() == tgt: break

    def __decodeRecord(self, m, l1, l2, l3):
        d = l1.split(u'>')[1].split(u'<')[0]
        t = l2.split(u'>')[1].split(u'<')[0]
        h = l3.split(u'>')[1].split(u'<')[0]

        yy = self.year
        dd = int(d)
        hh = [ int(tt) for tt in t.split(u':') ]
        wl = float(h)
        lcl_dt = datetime.datetime(yy, m, dd, hh[0], hh[1], tzinfo=self.tzinfo)
        utc_dt = lcl_dt.astimezone(pytz.utc)
        return TideRecord(utc_dt, wl)

    def __readData(self, f):
        records = []
        m = 0
        while True:
            self.__skipToLine(f, u'<table class="width-100">')

            l = f.readline()
            if not l: break
            l = l.strip()
            assert l[:9] == u'<caption>'
            m += 1
            self.__skipToLine(f, u'<tbody>')

            self.__skipToLine(f, u'<tr>')
            eob = False
            while not eob:
                l1 = f.readline().strip()
                l2 = f.readline().strip()
                l3 = f.readline().strip()
                r = self.__decodeRecord(m, l1, l2, l3)
                records.append(r)

                l = f.readline().strip()
                assert l[:9] == u'</tr>'
                l = f.readline().strip()
                if l == u'</tbody>': eob = True

        return records

    def __open(self, url):
        br = mechanize.Browser()
        br.set_handle_refresh(False)
        r = br.open(url)
        return br

    def read(self):
        url = self.__buildURL()
        try:
            br = self.__open(url)
        except:
            print(u'Connection failure')
            time.sleep(5) # (900)
            br = self.__open(url)
            #raise RuntimeError('')

        p = br.response()
        if (p.code != 200):
            raise ValueError(u'Connection error')

        return self.__readData(p)

class TideRecord(object):
    """
    A TideRecord is either a HW or LW time stamp.
    """
    def __init__(self, dt = datetime.datetime(datetime.MINYEAR, 1, 1), wl = 0.0):
        self.dt = dt
        self.wl = wl

    #def __lt__(self, other):
    #    return str(self.dt) < str(other.dt)

    #def __eq__(self, other):
    #    return self.dt == other.dt and self.wl == other.wl

    #def __ne__(self, other):
    #    return self.dt != other.dt or self.wl != other.wl

    def __richcmp__(self, other, op):
        """
        cython code
        op: < 0; <= 1; == 2; != 3; > 4; >= 5        
        """
        if op == 0: 
            return str(self.dt) <  str(other.dt)
        if op == 1: 
            return self.dt <= other.dt
        if op == 2: 
            return self.dt == other.dt and self.wl == other.wl
        if op == 3: 
            return self.dt != other.dt or self.wl != other.wl
        if op == 4: 
            return self.dt >  other.dt
        if op == 5: 
            return self.dt >= other.dt
        assert False
            
    def __str__(self):
        return '%s %f' % (self.dt.isoformat(), self.wl)

    def dump(self):
        return '%s; %f' % (self.dt.isoformat(), self.wl)

    def load(self, l):
        dt, wl = l.split(';')
        self.dt = dateutil.parser.parse(dt)
        self.wl = float(wl)

class TideTable(object):
    """
    A TideTable is a sequence of TideRecords
    """

    NPNTS_HW_LW = 31
    NPNTS_LW_HW = 19
    DELTA_NRMTD = 900.0     # delta t for normalized tiide

    def __init__(self):
        self.tbl = []

    def dump(self, dataDir):
        fname = os.path.join(dataDir, 'tide_3248.txt')
        f = codecs.open(fname, "w", encoding="utf-8")
        for r in self.tbl:
            f.write('%s\n' % r.dump())

    def load(self, dataDir):
        fname = os.path.join(dataDir, 'tide_3248.txt')
        f = codecs.open(fname, "r", encoding="utf-8")
        for l in f.readlines():
            l = l.strip()
            if l[0] == u'#': continue
            r = TideRecord()
            r.load(l)
            self.tbl.append(r)
        logger.debug('Tide table loaded, size = %i' % len(self.tbl))

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
        doDebug = (logger.getEffectiveLevel() == logging.DEBUG)
        hw0 = self.getPreviousHW(dt)
        lw  = self.getNextLW(hw0.dt)
        hw1 = self.getNextHW(hw0.dt)
        if doDebug:
            logger.debug('HW0: %s' % str(hw0))
            logger.debug('LW:  %s' % str(lw))
            logger.debug('HW1: %s' % str(hw1))
        assert hw0.dt <= dt <= hw1.dt
        if dt <= lw.dt:
            dt2hw = (   dt - hw0.dt).total_seconds()    # delta from item to previous HW
            lw2hw = (lw.dt - hw0.dt).total_seconds()    # delta from LW to previous HW
            stp_hw2lw  = lw2hw / TideTable.NPNTS_HW_LW
            nstp_dt2lw = nint(dt2hw/stp_hw2lw)
            inrm_tim = nstp_dt2lw
            if doDebug:
                logger.debug('dt < lw.dt')
                logger.debug('   Delta HW-T : %6.3fh %9.1fs' % (dt2hw/3600.0, dt2hw))
                logger.debug('   Delta HW-LW: %6.3fh %9.1fs' % (lw2hw/3600.0, lw2hw))
                logger.debug('   Step  HW-LW: %9.1fs' % stp_hw2lw)
                logger.debug('   nsteps: %i' % nstp_dt2lw)
                logger.debug('   normalized time: %f %f' % (inrm_tim*TideTable.DELTA_NRMTD, dt2hw))
        else:
            dt2lw = (    dt -  lw.dt).total_seconds()    # delta from item to LW
            dt2hw = (    dt - hw0.dt).total_seconds()    # delta from item to previous HW
            hw2lw = (hw1.dt -  lw.dt).total_seconds()    # delta from next HW to LW
            lw2hw = ( lw.dt - hw0.dt).total_seconds()    # delta from LW to previous HW
            stp_lw2hw  = hw2lw / TideTable.NPNTS_LW_HW
            stp_hw2lw  = lw2hw / TideTable.NPNTS_HW_LW
            nstp_dt2lw = nint(dt2lw/stp_lw2hw)
            nstp_hw2lw = nint(lw2hw/stp_lw2hw)
            inrm_tim = (nstp_hw2lw + nstp_dt2lw)
            if doDebug:
                logger.debug('dt > lw.dt')
                logger.debug('   Delta LW-T : %6.3fh %9.1fs' % (dt2lw/3600.0, dt2lw))
                logger.debug('   Delta HW-T : %6.3fh %9.1fs' % (dt2hw/3600.0, dt2hw))
                logger.debug('   Delta HW-LW: %6.3fh %9.1fs' % (lw2hw/3600.0, lw2hw))
                logger.debug('   Delta LW-HW: %6.3fh %9.1fs' % (hw2lw/3600.0, hw2lw))
                logger.debug('   step HW-LW: %9.1fs' % stp_hw2lw)
                logger.debug('   step LW-HW: %9.1fs' % stp_lw2hw)
                logger.debug('   nsteps HW-LW: %i' % nstp_hw2lw)
                logger.debug('   nsteps LW-T : %i' % nstp_dt2lw)
                logger.debug('   normalized time: %f %f' % (inrm_tim*TideTable.DELTA_NRMTD, dt2hw))
        return inrm_tim


if __name__ == '__main__':
    def downloadTables():
        tide_tbl = TideTable()
        # ---  Download from internet
        for y in [2012, 2013, 2014, 2015, 2016]:
            r = DataReaderMPO(3248, y)
            tide_tbl.extend( r.read() )
        # ---  Check sorted
        for r0, r1 in zip(tide_tbl.tbl, tide_tbl.tbl[1:]):
            if not r0 < r1:
                print('Table not sorted: r0=%s r1=%s' %(str(r0), str(r1)))
        #tide_tbl.sort()
        tide_tbl.dump(u'.')
        return tide_tbl

    def loadTable():
        tide_tbl = TideTable()
        tide_tbl.load(u'.')
        return tide_tbl

    logHndlr = logging.StreamHandler()
    FORMAT = "%(asctime)s %(levelname)s %(message)s"
    logHndlr.setFormatter( logging.Formatter(FORMAT) )

    logger = logging.getLogger("INRS.ASModel.tide")
    logger.addHandler(logHndlr)
    logger.setLevel(logging.DEBUG)

    #tbl = loadTable()

    tbl1 = downloadTables()
    #tbl2 = loadTable()
    #for r1, r2 in zip(tbl1.tbl, tbl2.tbl):
    #    if r1 != r2:
    #        print r1, r2
    #        break
    #readTimes('tide_times.pkl')

    #dt = datetime.datetime.now(tz=pytz.utc)
    #print 'now: ', dt.isoformat()
    #print tbl.getNextHW(dt).dt-tbl.getPreviousHW(dt).dt
    #tbl.getNormalizedTime(dt)
    #dt = dt - datetime.timedelta(hours=6)
    #print 'now-6h: ', dt.isoformat()
    #print tbl.getNextHW(dt).dt-tbl.getPreviousHW(dt).dt
    #tbl.getNormalizedTime(dt)

    #dt0 = datetime.datetime.now(tz=pytz.utc)
    #dt1 = dt0 + datetime.timedelta(hours=24)
    #res = tbl.getTideSignal(dt0, dt1, datetime.timedelta(seconds=900))
    #for tr0, tr1 in zip(res[0:-1], res[1:]):
    #    print (tr1.dt-tr0.dt, tr1.wl-tr0.wl)

