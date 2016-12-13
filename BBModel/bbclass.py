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
Modèle de calcul des temps d'arrivée d'une surverse
"""

__version__ = '1.0'

import datetime
import logging

from river   import Rivers
from station import OverflowPoints
from tide    import TideTable

logger = logging.getLogger("INRS.BBModel.BBModel")

class BBModel:
    def __init__(self, dataDir):
        """
        La fonction __init__() construit un objet BBModel. Elle configure le système.
        """
        self.m_rivers = Rivers()
        self.m_rivers.load(dataDir)

        self.m_points = OverflowPoints()
        self.m_points.load(dataDir, self.m_rivers)

        self.m_tide = TideTable()
        self.m_tide.load(dataDir)

        self.m_dataDir = dataDir

    def getDataDir(self):
        """
        La fonction getDataDir() retourne le répertoire des données
        """
        return self.m_dataDir

    def getInfo(self):
        """
        La fonction getInfo() retourne l'information sur les données.
        """
        return self.m_points.getInfo()

    def getPointNames(self):
        """
        La fonction getPointNames() retourne la liste des noms
        des points de surverse.
        """
        return self.m_points.getNames()

    def getPointTideNames(self, name):
        """
        La fonction getPointTideNames() retourne la liste des noms
        des cycles de marée pour le point de surverse de nom 'name'.
        """
        return self.m_points[name].getTides()


    def getTideSignal(self, t_start, t_end, dt):
        """
        La fonction getTideSignal() retourne le signal de marée
        entre t_start et t_end, avec un pas de temps de dt.
        La fonction retourne l'information comme liste de tuples
        (temps, niveau d'eau).
        Tous les temps sont UTC.
        """
        assert isinstance(t_start, datetime.datetime)
        assert isinstance(t_end,   datetime.datetime)
        assert isinstance(dt,      datetime.timedelta)

        sgnl = self.m_tide.getTideSignal(t_start, t_end, dt)
        return [ (tr.dt, tr.wl) for tr in sgnl ]

    def xeq(self, t_start, t_end, dt, pts, do_merge):
        """
        La fonction xeq(..) calule les temps d'arrivée pour une surverse. L'interval de surverse
        est donné par [t_start, t_end], le pas de calul est dt. Le calcul est effectué pour
        chacun des points de surverse. La liste pts ccomprend, pour chaque point de surverse,
        son nom et la liste des cycles de marée. Une liste de marée vide implique tous les cycles.
        Par exemple: [ [p1, [c1, c2, c5]], [p2, []] ...].
        La valeur booléenne do_merge contrôle si les différents temps de transit sont agglomérés ou 
        gardés séparés.

        La fonction retourne l'information suivante:
        [
            (pnt_de_surverse, [ (t_min, t_max) arrival for each transit time in river] ),
            ...
        ]
        Tous les temps sont UTC.
        """
        assert isinstance(t_start, datetime.datetime)
        assert isinstance(t_end,   datetime.datetime)
        assert isinstance(dt,      datetime.timedelta)
        assert isinstance(pts,    (list, tuple))
        assert isinstance(pts[0], (list))

        res = []
        for pt, cycls in pts:
            try:
                r = self.m_points[pt].doOverflow(t_start, t_end, dt, self.m_tide, tide_cycles=cycls, merge_transit_times = do_merge)
                res.append( (pt, r) )
            except KeyError as e:
                logger.debug('BBModel.xeq: Skipping point %s' % pt)
        return res

if __name__ == '__main__':
    import pytz
    logHndlr = logging.StreamHandler()
    FORMAT = "%(asctime)s %(levelname)s %(message)s"
    logHndlr.setFormatter( logging.Formatter(FORMAT) )

    logger.addHandler(logHndlr)
    logger.setLevel(logging.DEBUG)

    t0 = datetime.datetime.now(tz=pytz.utc)
    t1 = t0 + datetime.timedelta(hours=1)
    dt = datetime.timedelta(seconds=900)
    bb = BBModel()
    #xeq(t0, t1, dt, ['AFO-STL-002'])
    bb.getTideSignal(t0, t1, dt)
