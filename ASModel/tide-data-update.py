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
Utilitaries allow to download the data from MPO site
"""

import codecs
import contextlib
import datetime
import dateutil
import glob
import logging
import traceback
import os
import time
import warnings
import requests
import pytz
import dateutil.parser

from tide import TideRecord

# Obscur bug in dateutil.parser
# http://stackoverflow.com/questions/21296475/python-dateutil-str-warning
warnings.filterwarnings("ignore", category=UnicodeWarning)

LOGGER = logging.getLogger("INRS.ASModel.tide")

def nint(d):
    return int(d + 0.5)

class DataReaderMPO:
    """
    Data reader for MPO tide tables
    """
    def __init__(self, station = -1, year = datetime.date.today().year):
        self.station = station
        self.year    = year
        self.tzinfo  = dateutil.tz.tzoffset('HNE', datetime.timedelta(hours=-5))

    def __buildURL(self):
        y = self.year
        i = self.station
        url = 'http://www.waterlevels.gc.ca/fra/donnees/tableau/%i/wlev_sec/%i' % (y, i)
        return url

    def __decodeRecord(self, m, l1, l2, l3):
        d = l1.split('>')[1].split('<')[0]
        t = l2.split('>')[1].split('<')[0]
        h = l3.split('>')[1].split('<')[0]

        yy = self.year
        dd = int(d)
        hh = [ int(tt) for tt in t.split(':') ]
        wl = float(h)
        lcl_dt = datetime.datetime(yy, m, dd, hh[0], hh[1], tzinfo=self.tzinfo)
        utc_dt = lcl_dt.astimezone(pytz.utc)
        return TideRecord(utc_dt, wl)

    def __skipToLine(self, lines, tgt):
        while True:
            l = self.__readLine(lines)
            if l == tgt: 
                LOGGER.debug('DataReaderMPO.__skipToLine found %s', tgt)
                break

    def __readLine(self, lines):
        l = ''
        while not l:
            l = next(lines).strip()
        return l

    def __readData(self, lines):
        """
        Return a list of TideRecord(s)
        lines is an iterator on the content
        """
        records = []
        m = 0
        while True:
            try:
                self.__skipToLine(lines, '<table class="width-100">')
            except StopIteration:
                break

            l = self.__readLine(lines)
            if not l: break
            l = l.strip()
            assert l[:9] == '<caption>'
            m += 1
            self.__skipToLine(lines, '<tbody>')

            self.__skipToLine(lines, '<tr>')
            eob = False
            while not eob:
                l1 = self.__readLine(lines)
                l2 = self.__readLine(lines)
                l3 = self.__readLine(lines)
                r = self.__decodeRecord(m, l1, l2, l3)
                records.append(r)

                l = self.__readLine(lines)
                assert l[:9] == '</tr>'
                l = self.__readLine(lines)
                if l == '</tbody>': 
                    eob = True
                else:
                    assert l[:8] == '<tr>'

        return records

    def read(self):
        MAX_RETRY = 3
        url = self.__buildURL()
        LOGGER.info('Connecting to : %s', url)
        for itry in range(MAX_RETRY):
            try:
                r = requests.get(url, stream=True)
            except requests.RequestException as e:
                LOGGER.error('Connection failure: %s', str(e))
                LOGGER.error('   Retrying %i/%i', itry+1, MAX_RETRY)
                time.sleep(5) # (900)

        if (r.status_code != 200):
            raise ValueError('\n'.join((
                        'Connection error:',
                        '   HTTP Status: %i' % r.status_code,
                        '   Reason: %s' % r.reason)))

        records = []
        with contextlib.closing(r) as r_:
            records = self.__readData( r_.iter_lines(decode_unicode=True) )

        return records

class TideTable:
    """
    A TideTable is a sequence of TideRecords
    """

    def __init__(self):
        self.tbl = []

    def dump(self, fname):
        LOGGER.info('Write file %s', fname)
        f = codecs.open(fname, "w", encoding="utf-8")
        for r in self.tbl:
            f.write('%s%s' % (r.dump(), os.linesep))

    def append(self, r):
        self.tbl.append(r)

    def extend(self, t):
        self.tbl.extend(t)

    def sort(self):
        self.tbl.sort()

if __name__ == '__main__':
    def downloadTables():
        for y in [2017, 2018, 2019, 2020]:
            try:
                tide_tbl = TideTable()
                # ---  Download from internet
                LOGGER.info('Reading tide table for year %i', y)
                r = DataReaderMPO(3248, y)
                tide_tbl.extend( r.read() )

                # ---  Sort
                tide_tbl.sort()

                # ---  Check sorted
                for r0, r1 in zip(tide_tbl.tbl, tide_tbl.tbl[1:]):
                    if not r0 < r1:
                        LOGGER.warning('Table not sorted: r0=%s r1=%s' %(str(r0), str(r1)))

                # ---  Dump
                fname = os.path.join('.', 'tide_3248-%i.txt' % y)
                tide_tbl.dump(fname)
            except Exception as e:
                LOGGER.error('%s', str(e))
                LOGGER.debug('%s', traceback.format_exc())
        return tide_tbl

    logHndlr = logging.StreamHandler()
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logHndlr.setFormatter( logging.Formatter(FORMAT) )

    #LOGGER = logging.getLogger("INRS.ASModel.tide")
    LOGGER.addHandler(logHndlr)
    LOGGER.setLevel(logging.INFO)

    tbl1 = downloadTables()
