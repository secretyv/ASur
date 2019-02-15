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
Overflow points
"""

import codecs
import datetime
import logging
import os
import pickle

try:
    from .asplume import ASPlume
except ModuleNotFoundError:
    from asplume import ASPlume

LOGGER = logging.getLogger("INRS.ASModel.station")

DTA_DELTAS = 900
DTA_DELTAT = datetime.timedelta(seconds=DTA_DELTAS)

def nint(d):
    return int(d + 0.5)

class Hit:
    def __init__(self, t0=-1.0, tc=-1.0, ix=-1, iy=-1, a=-1.0, md5='', dd=False, pnt=None):
        self.t0 = t0    # Injection time
        self.tc = tc    # Contact time
        self.ix = ix    # Normalized tide injection index
        self.iy = iy    # Normalized tide contact index
        self.a  = a     # Amplitude
        self.md5= md5   # MD5 of plume
        self.dd = dd    # Direct or inverted plume
        self.pnt= pnt
        assert pnt is None or isinstance(pnt, OverflowPointOneTide)

    def __lt__(self, other):
        """
        Opérateur de comparaison basé sur l'amplitude uniquement
        """
        return self.a < other.a

    def __eq__(self, other):
        """
        Opérateur de comparaison basé sur l'amplitude uniquement
        """
        return self.a == other.a

class OverflowPointOneTide(object):
    """
    OverflowPointOneTide
        One point
        One tide cycle
        Multiple river velocities
    All times are UTC

    tideDta: ix, iy are timedelta from tide start (HW) in 15' blocs
    """

    def __init__(self, river = None, dist = 0.0):
        self.m_river    = river
        self.m_dist2SL  = dist
        self.m_dataDir  = ''
        self.m_pathDir  = ''
        self.m_dt       = -1.0    # Tide cycle duration
        self.m_dh       =  0.0    # Tide height
        self.m_tideDta  = {}      # Dic of { ix : (iy, a) }
        self.m_pathDta  = {}      # Dic of { ix : (iy, md5, dd) }
        self.m_dilution = -1.0    # Target dilution

    def __lt__(self, other):
        """
        Comparison is based on tide attributes
        """
        return (self.m_dh < other.m_dh) or (self.m_dh == other.m_dh and self.m_dt < other.m_dt)

    def __eq__(self, other):
        """
        Comparison is based on tide attributes
        """
        return self.m_dh == other.m_dh and self.m_dt == other.m_dt

    def __repr__(self):
        return '%s: at %s' % ('OverflowPointOneTide', self.getId())

    def getTideData(self):
        return self.m_dt, self.m_dh, self.m_tideDta, self.m_pathDta, self.m_dataDir, self.m_pathDir, self.m_dilution

    def setTideData(self, dt, dh, tDta={}, pDta={}, dtaDir='', pthDir='', dil=-1.0):
        self.m_dt = dt
        self.m_dh = dh
        self.m_tideDta = tDta
        self.m_pathDta = pDta
        self.m_dataDir = dtaDir
        self.m_pathDir = pthDir
        self.m_dilution= dil

    def getId(self):
        return 'dh=%.2f, dt=%.2f' % (self.m_dh, self.m_dt/3600)

    def mergeTideData(self, other):
        """
        Merge tide data from other with self,
        if data doesnot exist in self
        or if amplitude of other is bigger
        """
        # ---  Loop on other ix's
        for ix in other.m_tideDta:
            try:
                oDta = other.m_tideDta[ix]
                sDta = self.m_tideDta[ix]   # Will raise if absent
                # ---  Loop on other iy's
                for iy, a in oDta:
                    # --- Get all indexes of iy in self data - should be at most 1
                    idxs = [i for i, (jy, a) in enumerate(sDta) if jy==iy]
                    if idxs:
                        assert len(idxs) == 1
                        idx = idxs[0]
                        # ---  Keep other value if >
                        if a > sDta[idx][1]:
                            sDta[idx] = (iy, a)
                    else:
                        sDta.append( (iy, a) )
                # ---  Keep things sorted on iy
                sDta.sort(key=lambda x: x[0])
            except KeyError:
                self.m_tideDta[ix] = other.m_tideDta[ix]

    def mergePathData(self, other):
        """
        Merge tide data from other with self,
        if data doesnot exist in self
        or if amplitude of other in bigger
        """
        # ---  Loop on other ix's
        for ix in other.m_pathDta:
            try:
                oDta = other.m_pathDta[ix]
                sDta = self.m_pathDta[ix]   # Will raise if absent
                # ---  Loop on other iy's
                for iy, md5, dd in oDta:
                    # --- Get all indexes of iy in self data - should be at most 1
                    idxs = [i for i, (jy, _1, _2) in enumerate(sDta) if jy==iy]
                    if idxs:
                        assert len(idxs) == 1
                        idx = idxs[0]
                        assert md5 == sDta[idx][1]
                    else:
                        sDta.append( (iy, md5, dd) )
                # ---  Keep things sorted on iy
                sDta.sort(key=lambda x: x[0])
            except KeyError:
                self.m_pathDta = other.m_pathDta

    def __getRiverTransitTime(self):
        return self.m_river.getTransitTimes(self.m_dist2SL) if self.m_river else [0.0]

    def __getTimeToBeach(self, ix):
        """
        For the normalized time index ix, returns a list of
        hits.
        Returns [ (iy, a), ... ] with:
            iy: arrival normalized time index (15' slot)
            a:  dilution
        If the path doesn't hit the beach, returns []
        """
        if self.m_tideDta:
            try:
                return self.m_tideDta[ix]
            except KeyError:
                return []
        else:
            return []

    def __getSingleTideData(self, ix, iy):
        """
        For the normalized time index ix, iy
        returns the associated data.
        Returns [ (iy, a), ... ] with:
            iy: arrival normalized time index (15' slot)
            a:  dilution
        """
        for dta in self.m_tideDta[ix]:
            if dta[0] == iy:
                return dta
        raise KeyError

    def __getSinglePathData(self, ix, iy):
        """
        """
        for dta in self.m_pathDta[ix]:
            if dta[0] == iy:
                return dta
        raise KeyError

    def __getHitsForOneSpill(self, t_actu, t_start, tide_tbl):
        """
        Returns a list for each river transit time:
            [ l1, ...]
        with:
        l1, list for transit time 1,
        l1[j] = d,
            j is timedelta from t_start to time to hit the beach
            j is in DTA_DELTAS slots,
            j in [0,...[
            d is dilution
        Time slots with NO hits a marked with d=-1
        """
        t2bds = []      # list of list

        # --- For each transit time in river
        for dt_rvr in self.__getRiverTransitTime():
            t2bd = [None]*(12*4)      # Hits for the transit time
            jmax = 0

            # --- Effective time
            t_rvr = t_actu + datetime.timedelta(seconds=dt_rvr)

            # --- Normalized tide time index of hits + associated dilution
            ix = tide_tbl.getNormalizedTimeIndex(t_rvr)
            hits = self.__getTimeToBeach(ix)

            # --- Get time to beach
            for iy, a in hits:
                # ---  Time of arrival (real time)
                t_hit = t_rvr + datetime.timedelta(seconds=(iy-ix)*DTA_DELTAS)
                # --- Timedelta to t_start in DTA_DELTAS slots
                j_hit = nint( (t_hit-t_start).total_seconds() / DTA_DELTAS )
                if j_hit >= len(t2bd): t2bd.extend( [None]*(j_hit-len(t2bd)+1) )
                jmax = max(j_hit, jmax)
                iy_, md5, dd = self.__getSinglePathData(ix, iy)
                t2bd[j_hit] = Hit(t_actu, t_hit, ix, iy, a, md5, dd, self)

            t2bds.append(t2bd[:jmax+1])
        return t2bds

    def __reduceHits(self, t2bdg, t2bds):
        """
        Reduce (max) t2bds in t2bdg
        """
        # LOGGER.trace('OverflowPointOneTide.__reduceHits')
        if len(t2bdg) <= 0: t2bdg = [ [] for _ in range(len(t2bds)) ]
        assert len(t2bdg) == len(t2bds)

        for ov,rv in zip(t2bds, t2bdg):
            if len(ov) > len(rv): rv.extend( [None]*(len(ov)-len(rv)) )
            for j in range(len(ov)):
                if rv[j]:
                    if ov[j]:
                        rv[j] = max(rv[j], ov[j])
                else:
                    rv[j] = ov[j]

        return t2bdg

    def getHitsForSpillWindow(self, t_start, t_end, dt, tide_tbl, merge_transit_times = False):
        """
        For t in [t_start, t_end] with step dt, compute the
        hits on the beach. Times are UTC
        Returns:
            [    # for each river transit time
                [a0, ..., ai] dilution for timedelta i, in DTA_DELTAS slots
            ]
        """
        LOGGER.trace('OverflowPointOneTide.getHitsForSpillWindow: from %s to %s', t_start, t_end)

        # ---  Effective dt
        neff = nint( (t_end-t_start).total_seconds() / dt.total_seconds() )
        neff = max(neff, 1)
        dteff = (t_end-t_start) / neff

        # ---  Loop on time steps
        t2bdg = []
        t_actu = t_start
        for it in range(neff+1):
            t2bds = self.__getHitsForOneSpill(t_actu, t_start, tide_tbl)
            if merge_transit_times:
                t2bds_tmp = []
                for t in t2bds:
                    t2bds_tmp = self.__reduceHits(t2bds_tmp, [t])
                t2bds = t2bds_tmp
            t2bdg = self.__reduceHits(t2bdg, t2bds)
            t_actu += dteff

        LOGGER.trace('OverflowPointOneTide.getHitsForSpillWindow: reduced data')
        LOGGER.trace('    %s' % [ 1 if h else 0 for h in t2bdg[0] ] if t2bdg else [])
        return t2bdg

    def getPath(self, ix, iy):
        iy, md5, dd = self.__getSinglePathData(ix, iy)
        fname = 'path-%s.pkl' % (md5)
        fname = os.path.join(self.m_pathDir, fname)
        pth = None
        if not os.path.isfile(fname):
            LOGGER.warning('Path file not found: %s', fname)
        else:
            with open(fname, 'rb') as f: pth = pickle.load(f, encoding='bytes')
        return pth

    def dump(self):
        if self.m_river:
            return '(%s, %f); (%f; %f)' % (self.m_river.name, self.m_dist2SL, self.m_dh, self.m_dt)
        else:
            return '(%f, %f)' % (self.m_dh, self.m_dt)

    def loadTide(self, dt, dh, data, dataDir, dilution):
        self.m_dt = dt
        self.m_dh = dh
        self.m_tideDta = {}
        for i, j, a, in data:
            self.m_tideDta.setdefault(i, [])
            self.m_tideDta[i].append( (j,a) )
        self.m_dataDir  = dataDir
        self.m_dilution = dilution
        LOGGER.trace('OverflowPointOneTide.loadTide: dt=%s dh=%s self=%s' % (self.m_dt, self.m_dh, self))

    def loadPath(self, dt, dh, data, pathDir, dilution):
        assert self.m_dt == dt
        assert self.m_dh == dh
        self.m_pathDta = {}
        for i, j, md5, dd in data:
            self.m_pathDta.setdefault(i, [])
            self.m_pathDta[i].append( (j,md5,dd) )
        self.m_pathDir = pathDir
        self.m_dilution = dilution
        LOGGER.trace('OverflowPointOneTide.loadPath: dt=%s dh=%s self=%s' % (self.m_dt, self.m_dh, self))

    def checkPathFiles(self):
        """
        Debug code:
        Check that all the path files exist
        """
        for ix,dta in self.m_pathDta.items():
            for iy,md5,dd in dta:
                fname = 'path-%s.pkl' % (md5)
                fname = os.path.join(self.m_pathDir, fname)
                if not os.path.isfile(fname):
                    LOGGER.warning('Path file not found: %s', fname)

    def checkInclusion(self, other):
        """
        Debug code:
        Check that other is included in self.
        """
        LOGGER.info('OverflowPointOneTide.checkInclusion: %s', (self.m_dt, self.m_dh))
        LOGGER.trace('OverflowPointOneTide.checkInclusion: %s vs %s', self, other)
        if self.m_dt != other.m_dt: raise ValueError('OverflowPointOneTide: Incoherent tide: %s vs %s' % (self.m_dh, other.m_dh))
        if self.m_dh != other.m_dh: raise ValueError('OverflowPointOneTide: Incoherent tide: %s vs %s' % (self.m_dh, other.m_dh))
        for ix, ovals in other.m_tideDta.items():
            try:
                svals = self.m_tideDta[ix]
            except KeyError:
                raise
            for oitem in ovals:
                if oitem not in svals:
                    missing = True
                    for iy, a in svals:
                        if iy == oitem[0]:
                            LOGGER.error('   Bad dilution: (%d, %d): %.2e %.2e' % (ix, iy, a, oitem[1]))
                            missing = False
                            break
                    if missing:
                        LOGGER.error('   Missing item: %d: %s' % (ix, oitem))
                    #raise ValueError('%d: %s' % (ix, oitem))

class OverflowPoint:
    """
    OverflowPoint
    Container of OverflowPointOneTide
    All times are UTC
    """

    def __init__(self, name='', river=None, dist=0.0):
        self.m_name    = name
        self.m_river   = river
        self.m_dist2SL = dist
        self.m_poly    = ()
        self.m_parent  = None
        self.m_root    = None   # The target as OPoint
        self.m_tideRsp = []

    def __str__(self):
        pstr = None
        if self.m_parent:
            if isinstance(self.m_parent, str):
                pstr = 'unlinked - %s' % self.m_parent
            else:
                pstr = self.m_parent.m_name
        return 'Point: %s; River: %s, Dist=%f, Parent point: %s' % \
            (self.m_name,
             self.m_river.name if self.m_river else None,
             self.m_dist2SL,
             pstr)

    def __getitem__(self, i):
        return self.m_tideRsp[i]

    def __iter__(self):
        return self.m_tideRsp.__iter__()

    def __reduceHits(self, t2bdg, t2bds):
        """
        Reduce (max) t2bds in t2bdg
        """
        # LOGGER.trace('OverflowPoint.__reduceHits')
        rv = t2bds[0]
        if len(t2bdg) <= 0: t2bdg = [ [] for _ in range(len(t2bds)) ]
        assert len(t2bdg) == len(t2bds)

        for ov,rv in zip(t2bds, t2bdg):
            if len(ov) > len(rv): rv.extend( [None]*(len(ov)-len(rv)) )
            for j in range(len(ov)):
                if rv[j]:
                    if ov[j]:
                        rv[j] = max(rv[j], ov[j])
                else:
                    rv[j] = ov[j]
        return t2bdg

    def getHitsForSpillWindow(self, t_start, t_end, dt, tide_tbl, tide_cycles=[], merge_transit_times=False):
        """
        For t in [t_start, t_end] with step dt, compute the hits for all required tide cycles id.
        Times are UTC
        Returns:
            [    # for each river transit time
                [   # for each exposure window part
                    [h0, ... hj] hj is Hit for time index j
                ]
            ]
        """
        LOGGER.trace('OverflowPoint.getHitsForSpillWindow')
        LOGGER.trace('   from %s', str(t_start))
        LOGGER.trace('   to   %s', str(t_end))
        if not tide_cycles:
            cycles = self.m_tideRsp
        else:
            # Cython chokes at a single expression
            # Rewrite as 2 expressions
            cycles = [ self.getTideResponse(ii) for ii in tide_cycles ]
            cycles = [ r for r in cycles if r ]
        LOGGER.trace('OverFlowPoint.getHitsForSpillWindow(): cycles[%d]', len(cycles))
        for tideRsp in cycles:
            LOGGER.trace('   %s', tideRsp)

        # ---  Loop on OverflowTideResponses - result in normalized timedelta
        t2bdg = []
        for tideRsp in cycles:
            if tideRsp:
                try:
                    t2bds = tideRsp.getHitsForSpillWindow(t_start, t_end, dt, tide_tbl, merge_transit_times)
                    t2bdg = self.__reduceHits(t2bdg, t2bds)
                except Exception as e:
                    LOGGER.exception(e)
                    LOGGER.warning('OverflowPoint.getHitsForSpillWindow: Skipping cycle %s', tideRsp)
            else:
                LOGGER.warning('OverflowPoint.getHitsForSpillWindow: Skipping cycle %s', tideRsp)
        LOGGER.trace('OverflowPoint.getHitsForSpillWindow: reduced data')
        LOGGER.trace('    %s', [ 1 if h else 0 for h in t2bdg[0] ] if t2bdg else [])

        return t2bdg

    def doPlumes(self, t_start, t_end, dt, tide_tbl, tide_cycles=[]):
        """
        For t in [t_start, t_end] with step dt, returns the particule paths
        as a list of Plume objects.
        .
        Times are UTC
        Returns:
            [
                plume1, ...
            ]
        """
        LOGGER.trace('OverflowPoint.doPlumes from %s to %s', t_start, t_end)
        hitss = self.getHitsForSpillWindow(t_start, t_end, dt, tide_tbl, tide_cycles, merge_transit_times=True)
        assert len(hitss) in [0, 1]

        # ---
        md5s = []
        res  = []
        try:
            res.append( ASPlume(name=self.m_root.m_name, poly=self.m_root.m_poly) )
        except Exception as e:
            pass
        for hits in hitss:
            for hit in hits:
                if hit and hit.md5 not in md5s:
                    md5s.append(hit.md5)
                    ptd = hit.pnt
                    ptdTideData = ptd.getTideData()
                    kwargs = {}
                    kwargs['dilution'] = ptdTideData[-1]
                    kwargs['name']   = self.m_name
                    kwargs['parent'] = self.m_parent.m_name if self.m_parent else self.m_name
                    kwargs['poly']   = self.m_parent.m_poly if self.m_parent else self.m_poly
                    kwargs['tide']   = ptdTideData[:2]
                    kwargs['t0']     = hit.t0
                    kwargs['tc']     = hit.tc
                    #kwargs['dt']   = -1.0
                    kwargs['isDirect']= hit.dd
                    kwargs['plume']   = ptd.getPath(hit.ix, hit.iy)
                    res.append( ASPlume(**kwargs) )

        LOGGER.trace('OverflowPoint.doPlumes done')
        return res

    def doOverflow(self, t_start, t_end, dt, tide_tbl, tide_cycles=[], merge_transit_times=False):
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
        LOGGER.trace('OverflowPoint.doOverflow from %s to %s', t_start, t_end)
        hitss = self.getHitsForSpillWindow(t_start, t_end, dt, tide_tbl, tide_cycles, merge_transit_times)

        # ---  Compact - back to time
        res_new = []
        for hits in hitss:
            ihit = 0
            lhits = len(hits)
            ps = []
            while ihit < lhits:
                while ihit < lhits and not hits[ihit]: ihit += 1     # get first Hit
                p = []
                while ihit < lhits and (hits[ihit] or (ihit+1 < lhits and hits[ihit+1])):    # interpolate simple hole
                    d = hits[ihit].a if hits[ihit] else (hits[ihit+1].a+hits[ihit-1].a)/2.0
                    t0 = t_start + ihit*DTA_DELTAT
                    t1 = t0 + DTA_DELTAT
                    p.append( (t0, t1, d) )
                    ihit += 1
                if p: ps.append(p)
            res_new.append(ps)

        LOGGER.trace('OverflowPoint.doOverflow done')
        return res_new

    def dump(self):
        if self.m_river:
            return '%s; %s; %f' % (self.m_name, self.m_river.name, self.m_dist2SL)
        else:
            return '%s' % (self.m_name)

    def __decodeRiver(self, data, rivers):
        #LOGGER.trace('OverflowPoint.__decodeRiver: %s (%s)' % (data, self))
        tks = data.split(';')
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

    def __decodeTide(self, data, dataDir, dilution):
        LOGGER.trace('OverflowPoint.__decodeTide: %s (%s)' % (self.m_name, self))
        self.m_tideRsp = []
        for item in data:
            tk_dt_dh, tk_tide = item.split(';')[1:3]
            dt_dh = list(eval(tk_dt_dh))
            tid   = list(eval(tk_tide))

            o = OverflowPointOneTide(self.m_river, self.m_dist2SL)
            o.loadTide(dt_dh[0], dt_dh[1], tid, dataDir, dilution)
            self.m_tideRsp.append(o)

    def __decodePath(self, data, pathDir, dilution):
        LOGGER.trace('OverflowPoint.__decodePath: %s (%s)' % (self.m_name, self))
        for item in data:
            tk_dt_dh, tk_path = item.split(';')[1:3]
            dt_dh = list(eval(tk_dt_dh))
            pth   = eval(tk_path)

            o = self.__getTideResponse(dt_dh[0], dt_dh[1])
            o.loadPath(dt_dh[0], dt_dh[1], pth, pathDir, dilution)

    def __decodePoly(self, data, pathDir, dilution):
        LOGGER.trace('OverflowPoint.__decodePoly: %s (%s)' % (self.m_name, self))
        for item in data:
            tk_poly = item.split(';')[1]
            poly = list(eval(tk_poly))
            self.m_poly = poly

    def load(self, data, rivers, dataDir, dilution, root=None):
        LOGGER.trace('OverflowPoint.load: %s' % (self))
        self.__decodeRiver(data[0], rivers)

        subDir = self.m_name
        pathDir = os.path.join(dataDir, subDir)

        if data[1]:
            self.__decodeTide(data[1], dataDir, dilution)
        if data[2]:
            self.__decodePath(data[2], pathDir, dilution)
        if data[3]:
            self.__decodePoly(data[3], pathDir, dilution)
        if root:
            self.m_root = root

    def resolveLinks(self, points):
        """
        Translate parent name to object
        Copy OverflowPointOneTide from parent
        """
        if self.m_parent:
            self.m_parent = points[self.m_parent]
            for m in self.m_parent.m_tideRsp:
                o = OverflowPointOneTide(self.m_river, self.m_dist2SL)
                o.setTideData( *m.getTideData() )
                if o in self.m_tideRsp:
                    i = self.m_tideRsp.index(o)
                    self.m_tideRsp[i].mergeTideData(o)
                    self.m_tideRsp[i].mergePathData(o)
                else:
                    self.m_tideRsp.append(o)

    def checkInclusion(self, other):
        """
        Debug Code
        Check that other is included in self.
        """
        LOGGER.info ('OverflowPoints.checkInclusion: %s', self.m_name)
        LOGGER.trace('OverflowPoints: %s vs %s', self, other)
        if self.m_name != other.m_name: raise ValueError('OverflowPoint: Incoherent name')
        if ((self.m_river is not None or other.m_river is not None) and
            (self.m_river.name != other.m_river.name)): raise ValueError('OverflowPoint: Incoherent river')
        for oitem in other.m_tideRsp:
            i = self.m_tideRsp.index(oitem)
            sitem = self.m_tideRsp[i]
            sitem.checkInclusion(oitem)

    def checkPathFiles(self):
        """
        Debug Code
        Check the presence of the path files
        """
        try:
            self.m_parent.m_name
        except AttributeError:
            for m in self.m_tideRsp:
                m.checkPathFiles()

    def __getTideResponse(self, td, th):
        """
        Returns the tide with
        tide duration td and
        tide height th
        """
        o = OverflowPointOneTide()
        o.setTideData(td, th)
        tid = o.getId()
        for m in self.m_tideRsp:
            if tid == m.getId(): return m
        return None

    def getTideResponse(self, tid):
        """
        Returns the tide with id
        """
        for m in self.m_tideRsp:
            if tid == m.getId(): return m
        return None

    def getTides(self):
        """
        Returns the list of all tides Id
        """
        return [ m.getId() for m in sorted( self.m_tideRsp ) ]

class OverflowPoints:
    """
    Container of OverflowPoint
    """

    def __init__(self):
        self.m_dataDir  = ''
        self.m_dilution = -1.0
        self.m_root = None
        self.m_pnts = {}

    def load(self, dataDir, rivers):
        """
        Load configuration from file
        """
        points = {}
        diltgt = -1.0

        # ---  Read river and link data
        fname = os.path.join(dataDir, 'overflow.river.txt')
        LOGGER.info('OverflowPoints: load river data: %s', fname)
        f = codecs.open(fname, "r", encoding="utf-8")
        for l in f.readlines():
            l = l.strip()
            if l[0] == '#': continue
            try:
                st = l.split(';')[0]
                points[st] = [l, [], [], []]    # [river, tide, path, poly]
            except ValueError as e:
                msg = ['Exception: %s' % str(e),
                       'Reading file: %s' % fname,
                       'Reading line: %s' % l]
                raise ValueError( '\n'.join(msg) )
        f.close()

        # ---  Read tide data
        fname = os.path.join(dataDir, 'overflow.tide.txt')
        LOGGER.info('OverflowPoints: load tide data: %s', fname)
        f = codecs.open(fname, "r", encoding="utf-8")
        for l in f.readlines():
            l = l.strip()
            if not l: continue
            if l[0] == '#':
                if l.find('Dilution threshold is') > 0:
                    tk_dl = l[1:].split()[-1]
                    diltgt = float(tk_dl)
            else:
                try:
                    st = l.split(';')[0]
                    points[st][1].append(l)
                except ValueError as e:
                    msg = ['Exception: %s' % str(e),
                           'Reading file: %s' % fname,
                           'Reading line: %s' % l]
                    raise ValueError( '\n'.join(msg) )
        f.close()

        # ---  Read path data
        fname = os.path.join(dataDir, 'overflow.path.txt')
        LOGGER.info('OverflowPoints: load poly data: %s', fname)
        f = codecs.open(fname, "r", encoding="utf-8")
        for l in f.readlines():
            l = l.strip()
            if not l: continue
            if l[0] == '#':
                if l.find('Dilution threshold is') > 0:
                    tk_dl = l[1:].split()[-1]
                    diltgt = float(tk_dl)
            else:
                try:
                    st = l.split(';')[0]
                    points[st][2].append(l)
                except ValueError as e:
                    msg = ['Exception: %s' % str(e),
                           'Reading file: %s' % fname,
                           'Reading line: %s' % l]
                    raise ValueError( '\n'.join(msg) )
        f.close()

        # ---  Read stations polygons
        target = ['Root', [], [], []]
        fname = os.path.join(dataDir, 'overflow.poly.txt')
        LOGGER.info('OverflowPoints: load path data: %s', fname)
        f = codecs.open(fname, "r", encoding="utf-8")
        for l in f.readlines():
            l = l.strip()
            if not l: continue
            if l[0] == '#': continue
            try:
                st = l.split(';')[0]
                points[st][3].append(l)
            except ValueError as e:
                msg = ['Exception: %s' % str(e),
                       '   Reading file: %s' % fname,
                       '   Reading line: %s' % l]
                raise ValueError( '\n'.join(msg) )
            except KeyError as e:
                if not target[3]:
                    target[3].append(l)
                else:
                    msg = ['KeyError Exception: %s' % str(e),
                           '   Reading file: %s' % fname,
                           '   Reading line: %s' % l]
                    LOGGER.warning( '\n'.join(msg) )
        f.close()

        # ---  Create root point
        root = OverflowPoint()
        root.load(target, rivers, dataDir, diltgt)

        # ---  Create points
        for k, v in points.items():
            #LOGGER.debug('OverflowPoints.load: create point %s (%s)' % (k, len(v)))
            try:
                p = OverflowPoint()
                p.load(v, rivers, dataDir, diltgt, root)
                self.m_pnts[p.m_name] = p
            except ValueError as e:
                msg = ['Exception: %s' % str(e),
                       'Decoding point: %s' % k,
                       'Data: %s' % v]
                raise ValueError( '\n'.join(msg) )

        # ---  Make the links
        for p in self.m_pnts.values():
            p.resolveLinks(self)

        # ---  Keep the data
        self.m_dataDir  = dataDir
        self.m_dilution = diltgt
        self.m_root     = root

    def checkInclusion(self, other):
        """
        Debug Code
        Check that other is included in self.
        """
        LOGGER.info('OverflowPoints.checkInclusion: Dilution %.2e', self.m_dilution)
        if self.m_dilution >=  other.m_dilution: raise ValueError('OverflowPoints: Incoherent dilution')
        for sta, oitem in other.m_pnts.items():
            sitem = self.m_pnts[sta]
            sitem.checkInclusion(oitem)

    def checkPathFiles(self):
        """
        Debug Code
        Check the presence of the path files
        """
        for p in self.m_pnts.values():
            p.checkPathFiles()

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
            if l[0] == '#' and len(l) > 1:
                info.append(l[1:])
        f.close()

        return info

    def getNames(self):
        """
        Returns the list of all overflow points
        """
        return sorted( self.m_pnts.keys() )

    def __getitem__(self, name):
        return self.m_pnts[name]


if __name__ == '__main__':
    import sys
    selfDir = os.path.dirname( os.path.abspath(__file__) )
    supPath = os.path.normpath( os.path.join(selfDir, '..') )
    if os.path.isdir(supPath) and supPath not in sys.path: sys.path.append(supPath)

    import pytz
    import addLogLevel
    addLogLevel.addLoggingLevel('TRACE', logging.DEBUG - 5)

    import ASModel.river as river
    import ASModel.tide  as tide

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

    def main():
        logHndlr = logging.StreamHandler()
        FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logHndlr.setFormatter( logging.Formatter(FORMAT) )

        LOGGER = logging.getLogger("INRS.ASModel.station")
        LOGGER.addHandler(logHndlr)
        LOGGER.setLevel(logging.TRACE)

        fpath  = r'E:\Projets_simulation\VilleDeQuebec\Beauport\BBData_v1812rc1\data.lim=1.0e-06'
        tides  = loadTides (fpath)
        rivers = loadRivers(fpath)
        points = loadPoints(fpath, rivers)
        #points.checkPathFiles()

        ##fpath   = r'E:\Projets_simulation\VilleDeQuebec\Beauport\BBData_v1812rc1\data.lim=1.0e-03'
        ##tides2  = loadTides (fpath)
        ##rivers2 = loadRivers(fpath)
        ##points2 = loadPoints(fpath, rivers2)
        ##points.checkInclusion(points2)

        t0 = datetime.datetime.now(tz=pytz.utc).replace(day=12,hour=20,minute=00,second=0,microsecond=0)
        t0 = t0 + datetime.timedelta(hours=0, minutes= 0)
        t1 = t0 + datetime.timedelta(hours=2, minutes= 0)
        dt = datetime.timedelta(seconds=30*60)
        print('t0: ', t0)
        print('t1: ', t1)

        dtmax = t0
        for p in ['BBE-STL-003']: # points.getNames():
            cycles = points[p].getTides()[-2:-1]
            print('Overflow point:', points[p])

            # dtaPt = points[p].doOverflow(t0, t1, dt, tides, tide_cycles = cycles, merge_transit_times = False)
            # for it, dtaTr in enumerate(dtaPt):
            #     for dtaXpo in dtaTr:
            #         for t0_, t1_, a in dtaXpo:
            #             print(t0_, t1_, a)
            #         print('-----')

            # ovflow = points[p].doOverflow(t0, t1, dt, tides, tide_cycles = cycles)
            plumes = points[p].doPlumes(t0, t1, dt, tides, tide_cycles = cycles)
            for plume in plumes:
                print(repr(plume))

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

    main()