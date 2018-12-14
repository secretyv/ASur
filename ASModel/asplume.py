#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#************************************************************************
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
"""

from datetime import datetime 
import logging

LOGGER = logging.getLogger("INRS.ASModel.plume")

class ASPlume:
    """
    Structure to hold all information pertaining to a
    particle path (plume)
    """
    def __init__(self, 
                 dilution=-1.0, 
                 name='', 
                 poly=[], 
                 tide=(-1,-1), 
                 t0=datetime.now(),
                 tc=datetime.now(), 
                 isDirect=False, 
                 plume=None):
        self.dilution       = dilution  # 
        self.stationName    = name      # string
        self.stationPolygon = poly      # sequence of (x, y) 
        self.tide           = tide      # (tide duration [s], tide amplitude [m])
        self.injectionTime  = t0        # datetime
        self.contactTime    = tc        # datetime
        self.isPlumeDirect  = isDirect  # Bool
        self.plume          = plume

    def __str__(self):
        return 'Station: %s; tide: %s; t0: %s' % (self.stationName, self.tide, self.injectionTime)
        
    def __repr__(self):
        s = []
        s.append('%.2e' % self.dilution)
        s.append('%s' % self.stationName)
        s.append('%s' % (self.tide,))
        s.append(':')
        s.append('t_inj=%s' % self.injectionTime)
        s.append('t_hit=%s' % self.contactTime)
        s.append('direct=%s' % self.isPlumeDirect)
        s.append('plume=%d' % len(self.plume))
        return ' '.join(s)
