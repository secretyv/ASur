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
Overflow points
"""

__version__ = u'1.0'

import codecs
import datetime
import logging
import os

logger = logging.getLogger("INRS.ASModel.station")

DTA_DELTAS = 900
DTA_DELTAT = datetime.timedelta(seconds=DTA_DELTAS)

def nint(d):
    return int(d + 0.5)

class OverflowTideResponse(object):
    """
    OverflowTideResponse for one tide cycle
    All times are UTC
    """

    def __init__(self, river = None, dist = 0.0):
        self.m_river    = river
        self.m_dist2SL  = dist
        self.m_dt       = -1.0    # Durée du cycle
        self.m_dh       =  0.0    # marnage
        self.m_tideDta  = {}

    #def __lt__(self, other):
    #    return (self.m_dh < other.m_dh) or (self.m_dh == other.m_dh and self.m_dt < other.m_dt)

    #def __eq__(self, other):
    #    return self.m_dh == other.m_dh and self.m_dt == other.m_dt

    def __richcmp__(self, other, op):
        """
        cython code
        op: < 0; <= 1; == 2; != 3; > 4; >= 5        
        """
        if op == 0: 
            return (self.m_dh < other.m_dh) or (self.m_dh == other.m_dh and self.m_dt < other.m_dt)
        #if op == 1: 
        #    return self.dt <= other.dt
        if op == 2: 
            return self.m_dh == other.m_dh and self.m_dt == other.m_dt
        if op == 3: 
            return self.m_dh != other.m_dh or self.m_dt != other.m_dt
        #if op == 4: 
        #    return self.dt >  other.dt
        #if op == 5: 
        #    return self.dt >= other.dt
        assert False

    def getTideData(self):
        return self.m_dt, self.m_dh, self.m_tideDta

    def setTideData(self, dt, dh, tDta):
        self.m_dt = dt
        self.m_dh = dh
        self.m_tideDta = tDta

    def getId(self):
        return u'dh=%.2f, dt=%.2f' % (self.m_dh, self.m_dt/3600)

    def __getTimeToBeach(self, inrmTime):
        """
        For the normalized tide time index inrmTime, returns a list of
        hits.
        Returns [ (j, dil), ... ] with:
            j timedelta index (15' slot)
            dil dilution
        If the path doesn't hit the beach, returns [ (0,-1.0) ]
        """
        if self.m_tideDta:
            try:
                return self.m_tideDta[inrmTime]
            except KeyError:
                return [(0, -1.0)]
        else:
            return [(0, -1.0)]

    def __getTransitTime(self):
        return self.m_river.getTransitTimes(self.m_dist2SL) if self.m_river else [0.0]
 
    def __doOneOverflow(self, t_actu, t_start, tide_tbl):
        """
        Returns a list for each river transit time:
            [ l1, ...]
        with:
        l1, list for transit time 1,
        l1[j] = d, j is timedelta index of times to reach the beach, and d is dilution,
        """
        t2bds = []      # list of time to beach + dilution
        # --- For each transit time in river
        for dt_rvr in self.__getTransitTime():
            t2bd = [-1.0]*(12*4)      # Time to beach + dilution

            t_rvr = t_actu + datetime.timedelta(seconds=dt_rvr)

            # --- Index of times to hit the beach + associated dilution
            inrm_time = tide_tbl.getNormalizedTimeIndex(t_rvr)
            hits = self.__getTimeToBeach(inrm_time)
            #print u'%7.1f  %s %3i' % (dt_rvr, t_rvr, inrm_time), hits

            # --- Get time to beach
            for j,d in hits:
                t_tot = t_rvr + datetime.timedelta(seconds=j*DTA_DELTAS)
                # --- Time index DTA_DELTAS slots
                j_tot = nint( (t_tot-t_start).total_seconds() / DTA_DELTAS )
                if j_tot >= len(t2bd): t2bd.extend( [-1.0]*(j_tot-len(t2bd)+1) )
                t2bd[j_tot] = d

            t2bds.append(t2bd)
        return t2bds

    def __doOverflowReduction(self, t2bdg, t2bds, t_actu):
        """
        Reduce (max) t2bds in t2bdg
        """
        #print u'OverflowTideResponse.__doOverflowReduction', t_actu
        if len(t2bdg) <= 0: t2bdg = [ [] for _ in xrange(len(t2bds)) ]
        assert len(t2bdg) == len(t2bds)

        for ov,rv in zip(t2bds, t2bdg):
            if len(ov) > len(rv): rv.extend( [-1]*(len(ov)-len(rv)) )
            for j in xrange(len(ov)):
                rv[j] = max(rv[j], ov[j])

        return t2bdg

    def doOverflow(self, t_start, t_end, dt, tide_tbl, merge_transit_times = False):
        """
        For t in [t_start, t_end] with step dt, compute the
        exposure time window to overflow. Times are UTC
        Returns:
            [    # for each river transit time
                [dil, ...] dilution for time index
            ]
        """
        # ---  Effective dt
        neff = nint( (t_end-t_start).total_seconds() / dt.total_seconds() )
        neff = max(neff, 1)
        dteff = (t_end-t_start) / neff

        # ---  Loop on time steps
        res = []
        t_actu = t_start
        for it in xrange(neff+1):
            t2bds = self.__doOneOverflow(t_actu, t_start, tide_tbl)
            if merge_transit_times:
                t2bds_tmp = []
                for t in t2bds:
                    t2bds_tmp = self.__doOverflowReduction(t2bds_tmp, [t], t_actu)
                t2bds = t2bds_tmp
            res = self.__doOverflowReduction(res, t2bds, t_actu)
            t_actu += dteff

        #logger.debug(u'OverflowTideResponse.doOverflow: reduced data')
        #logger.debug(u'    %s' % [ 1 if r > 0 else 0 for r in res[0] ] if res else [])
        return res

    def dump(self):
        if self.m_river:
            return u'(%s, %f); (%f; %f)' % (self.m_river.name, self.m_dist2SL, self.m_dh, self.m_dt)
        else:
            return u'(%f, %f)' % (self.m_dh, self.m_dt)

    def load(self, dt, dh, data):
        self.m_dt = dt
        self.m_dh = dh
        self.m_tideDta = {}
        for i, j, a, in data:
            self.m_tideDta.setdefault(i, [])
            self.m_tideDta[i].append( (j,a) )
        #logger.debug(u'OverflowTideResponse.load: dt=%s dh=%s self=%s' % (self.m_dt, self.m_dh, self))

class OverflowPoint(object):
    """
    OverflowPoint
    Container of OverflowTideResponse
    All times are UTC
    """

    def __init__(self, name = u'', river = None, dist = 0.0):
        self.m_name    = name
        self.m_river   = river
        self.m_dist2SL = dist
        self.m_parent  = None
        self.m_tideRsp = []

    def __str__(self):
        pstr = None
        if self.m_parent:
            if isinstance(self.m_parent, basestring):
                pstr = u'unlinked - %s' % self.m_parent
            else:
                pstr = self.m_parent.m_name
        return u'Point: %s; River: %s, Dist=%f, Parent point: %s' % \
            (self.m_name, 
             self.m_river.name if self.m_river else None,
             self.m_dist2SL, 
             pstr)
        
    def __getitem__(self, i):
        return self.m_tideRsp[i]

    def __iter__(self):
        return self.m_tideRsp.__iter__()

    def __doOverflowReduction(self, t2bdg, t2bds):
        """
        Reduce (max) t2bds in t2bdg
        """
        #print u'OverflowPoint.__doOverflowReduction'
        rv = t2bds[0]
        d = [ 0 if rv[i] < 0 else 1 for i in xrange(len(rv))]
        if len(t2bdg) <= 0: t2bdg = [ [] for _ in xrange(len(t2bds)) ]
        assert len(t2bdg) == len(t2bds)

        for ov,rv in zip(t2bds, t2bdg):
            if len(ov) > len(rv): rv.extend( [-1]*(len(ov)-len(rv)) )
            for i in xrange(len(ov)):
                rv[i] = max(rv[i], ov[i])
            d = [ 0 if rv[i] < 0 else 1 for i in xrange(len(rv))]
        return t2bdg

    def doOverflow(self, t_start, t_end, dt, tide_tbl, tide_cycles = [], merge_transit_times = False):
        """
        For t in [t_start, t_end] with step dt, compute the
        exposure time window to overflow for all required tide cycles id.
        Times are UTC
        Returns:
            [    # for each river transit time
                [   # for each exposure window part
                    [(t0, t1, dil), ...] time_start, time_end, dilution
                ]
            ]
        """
        logger.debug(u'OverflowPoint.doOverflow: %s %s' % (str(t_start), str(t_end)))
        if not tide_cycles: 
            cycles = self.m_tideRsp
        else:
            cycles = [ self.getTideResponse(id) for id in tide_cycles]

        res = []
        for i, tideRsp in enumerate(cycles):
            if tideRsp:
                try:
                    t2bds = tideRsp.doOverflow(t_start, t_end, dt, tide_tbl, merge_transit_times)
                    res = self.__doOverflowReduction(res, t2bds)
                except Exception as e:
                    # if tide_cycles is empty, logging will throw an exception
                    # but if tide_cycles is empty, we should never arrive here
                    logger.debug(u'OverflowPoint.doOverflow: Skipping cycle %s' % tide_cycles[i])
            else:
                logger.debug(u'OverflowPoint.doOverflow: Skipping cycle %s' % tide_cycles[i])
        logger.debug(u'OverflowPoint.doOverflow: reduced data')
        logger.debug(u'    %s' % [ 1 if d > 0 else 0 for d in res[0] ] if res else [])

        res_new = []
        for r in res:
            i = 0
            lr = len(r)
            ps = []
            while i < lr:
                while i < lr and r[i] <= 0: i +=1     # first non negativ dilution
                p = []
                while i < lr and (r[i] >  0 or (i+1 < lr and r[i+1] > 0)):  # interpolate simple hole
                    d = r[i] if r[i] > 0 else (r[i+1]+r[i-1])/2.0
                    t0 = t_start + i*DTA_DELTAT
                    t1 = t0 + DTA_DELTAT
                    p.append( (t0, t1, d) )
                    i += 1
                if p: ps.append(p)
            res_new.append(ps)

        #for r in res_new[0]: print u'%3i' % len(r), r[0], r[-1]
        return res_new

    def dump(self):
        if self.m_river:
            return u'%s; %s; %f' % (self.m_name, self.m_river.name, self.m_dist2SL)
        else:
            return u'%s' % (self.m_name)

    def __decodeRiver(self, data, rivers):
        #logger.debug(u'OverflowPoint.__decodeRiver: %s (%s)' % (data, self))
        tks = data.split(u';')
        if len(tks) == 1:
            self.m_name  = tks[0].strip()
            self.m_river = None
            self.m_dist2SL = 0.0
        elif len(tks) == 3:
            self.m_name  = tks[0].strip()
            self.m_river = rivers[ tks[1].strip() ]
            self.m_dist2SL = float( tks[2] )
        elif len(tks) == 4:
            self.m_name  = tks[0].strip()
            self.m_river = rivers[ tks[1].strip() ]
            self.m_dist2SL = float( tks[2] )
            self.m_parent  = tks[3].strip()
        else:
            raise ValueError

    def __decodeTide(self, datas):
        #logger.debug(u'OverflowPoint.__decodeTide: %s (%s)' % (self.m_name, self))
        self.m_tideRsp = []
        for data in datas:
            tk_dt_dh, tk_tide = data.split(';')[1:3]
            dt_dh = eval(tk_dt_dh)
            tide  = eval(tk_tide)
            
            o = OverflowTideResponse(self.m_river, self.m_dist2SL)
            o.load(dt_dh[0], dt_dh[1], tide)
            self.m_tideRsp.append(o)

    def load(self, data, rivers):
        #logger.debug(u'OverflowPoint.load: %s' % (self))
        self.__decodeRiver(data[0], rivers)
        if len(data) > 1:
            self.__decodeTide(data[1:])

    def resolveLinks(self, points):
        """
        Translate parent name to object
        Copy OverflowTideResponse from parent
        """
        if self.m_parent:
            self.m_parent = points[self.m_parent]
            for m in self.m_parent.m_tideRsp:
                o = OverflowTideResponse(self.m_river, self.m_dist2SL)
                o.setTideData( *m.getTideData() )
                self.m_tideRsp.append(o)

    def getTideResponse(self, id):
        """
        Returns the tide with id
        """
        for m in self.m_tideRsp:
            if id == m.getId(): return m
        return None
        
    def getTides(self):
        """
        Returns the list of all tides Id
        """
        return [ m.getId() for m in sorted( self.m_tideRsp ) ]

class OverflowPoints(object):
    """
    Container of OverflowPoint
    """

    def __init__(self):
        self.m_dataDir = u''
        self.m_pnts = {}

    def load(self, dataDir, rivers):
        """
        Load configuration from file
        """
        points = {}

        # ---  Read river and link data
        fname = os.path.join(dataDir, 'overflow.river.txt')
        f = codecs.open(fname, "r", encoding="utf-8")
        for l in f.readlines():
            l = l.strip()
            if l[0] == u'#': continue
            try:
                st = l.split(u';')[0]
                points[st] = [l]
            except ValueError as e:
                msg = [u'Exception: %s' % str(e),
                       u'Reading file: %s' % fname,
                       u'Reading line: %s' % l]
                raise ValueError( u'\n'.join(msg) )
        f.close

        # ---  Read tide data
        fname = os.path.join(dataDir, 'overflow.tide.txt')
        f = codecs.open(fname, "r", encoding="utf-8")
        for l in f.readlines():
            l = l.strip()
            if not l: continue
            if l[0] == u'#': continue
            try:
                st = l.split(';')[0]
                points[st].append(l)
            except ValueError as e:
                msg = [u'Exception: %s' % str(e),
                       u'Reading file: %s' % fname,
                       u'Reading line: %s' % l]
                raise ValueError( u'\n'.join(msg) )
        f.close

        # ---  Create points
        for k, v in points.iteritems():
            #logger.debug(u'OverflowPoints.load: create point %s (%s)' % (k, len(v)))
            try:
                p = OverflowPoint()
                p.load(v, rivers)
                self.m_pnts[p.m_name] = p
            except ValueError as e:
                msg = [u'Exception: %s' % str(e),
                       u'Decoding point: %s' % k,
                       u'Data: %s' % v]
                raise ValueError( u'\n'.join(msg) )

        # ---  Make the links
        for p in self.m_pnts.itervalues():
            p.resolveLinks(self)

        # ---  Keep the data directory
        self.m_dataDir = dataDir
            
    def getInfo(self):
        """
        Returns the data info.
        """
        info = []

        # ---  Read tide data info
        fname = os.path.join(self.m_dataDir, 'overflow.tide.txt')
        f = codecs.open(fname, "r", encoding="utf-8")
        for l in f.readlines():
            l = l.strip()
            if l[0] == u'#' and len(l) > 1:
                info.append(l[1:])
        f.close

        return info
            
    def getNames(self):
        """
        Returns the list of all overflow points
        """
        return sorted( self.m_pnts.keys() )

    def __getitem__(self, name):
        return self.m_pnts[name]


if __name__ == '__main__':
    import pytz
    import river
    import tide
    def loadTides(path):
        tbl = tide.TideTable()
        tbl.load(path)
        return tbl
    def loadRivers(path):
        tbl = river.Rivers()
        tbl.load(path)
        return tbl
    def loadPoints(path, rivers):
        tbl = OverflowPoints()
        tbl.load(path, rivers)
        return tbl

    logHndlr = logging.StreamHandler()
    FORMAT = "%(asctime)s %(levelname)s %(message)s"
    logHndlr.setFormatter( logging.Formatter(FORMAT) )

    logger = logging.getLogger("INRS.ASModel.station")
    logger.addHandler(logHndlr)
    logger.setLevel(logging.DEBUG)

    #tbl1 = downloadTables()
    #tbl2 = loadStations()
    #for r1, r2 in zip(tbl1.tbl, tbl2.tbl):
    #    if r1 != r2:
    #        print r1, r2
    #        break
    #readTimes('tide_times.pkl')

    path = u'../../BBData_v3.1/data.lim=1e-4'
    tides  = loadTides (path)
    rivers = loadRivers(path)
    points = loadPoints(path, rivers)

    #for p in points.getNames():
    #    pp = points[p]
    #    print pp.name
    #    print '   ', pp.river
    #    print '   ', pp.dist2SL
    #    print '   ', pp.parent.name if pp.parent else pp.parent
    #    print '   ', pp.tideDta

    t0 = datetime.datetime.now(tz=pytz.utc).replace(hour=5,minute=0,second=0,microsecond=0)
    t0 = t0 + datetime.timedelta(hours=0, minutes= 0)
    t1 = t0 + datetime.timedelta(hours=2, minutes= 0)
    dt = datetime.timedelta(seconds=5*60)
    print 't0: ', t0.isoformat()
    print 't1: ', t1.isoformat()

    dtmax = t0
    for p in [u'BBE-MOU-003']: # points.getNames():
        cycles = points[p].getTides()[3:4]
        print 'Overflow point:', points[p], cycles

        dtaPt = points[p].doOverflow(t0, t1, dt, tides, tide_cycles = cycles, merge_transit_times = False)
        for it, dtaTr in enumerate(dtaPt):
            for dtaXpo in dtaTr:
                for t0_, t1_, a in dtaXpo:
                    print t0_, t1_, a
                print '-----'

        #for c in cycles:
        #    print c
        #    dtaPt = points[p].doOverflow(t0, t1, dt, tides, tide_cycles = [c])
        #    for it, dtaTr in enumerate(dtaPt):
        #        print '   ', it, dtaTr
        #        for dtaXpo in dtaTr:
        #            print dtaXpo
        #            if not dtaXpo: continue
        #            dtmin_arr = dtaXpo[ 0][0]
        #            dtmax_arr = dtaXpo[-1][0]
        #            if dtmax_arr: dtmax = max(dtmax, dtmax_arr)
        #            print '      ', dtmin_arr, dtmax_arr
    #print dtmax