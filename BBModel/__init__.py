#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#************************************************************************
# --- Copyright (c) INRS 2016
# --- Institut National de la Recherche Scientifique (INRS)
# ---
# --- Distributed under the GNU Lesser General Public License, Version 3.0.
# --- See accompanying file LICENSE.txt.
#************************************************************************

"""
Modèle de temps d'arrivée
de surverses à la Baie de Beauport
"""

__version__ = '1.0.rc2'

from station import DTA_DELTAS
from station import DTA_DELTAT

# ---  BBModel class
from bbclass import BBModel

# ---  Static API
from bbapi import init
from bbapi import getPointNames
from bbapi import getTideSignal
from bbapi import xeq
