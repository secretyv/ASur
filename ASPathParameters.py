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
Particle path parameters
"""

import enum

try:
    from ASPathParametersEnum    import COLOR_SOURCE as CLR_SRC
except ImportError:
    from ASPathParametersEnum_pp import COLOR_SOURCE as CLR_SRC
try:
    from ASPathParametersEnum    import ELLIPSE_STYLE as ELL_STL
except ImportError:
    from ASPathParametersEnum_pp import ELLIPSE_STYLE as ELL_STL

class ASPathParameters:
    def __init__(self, **kwargs):
        self.doDrawBGMap     = kwargs.pop('doDrawBGMap',     True)
        self.doDrawShoreline = kwargs.pop('doDrawShoreline', False)
        self.doDrawPolygon   = kwargs.pop('doDrawPolygon',   True)
        self.shorelineColor  = kwargs.pop('shorelineColor',  "#000080") # HTML Navy
        self.polygonColor    = kwargs.pop('polygonColor',    "#D3D3D3") # HTML LightGray

        self.doDrawPath      = kwargs.pop('doDrawPath',      True)
        self.doClipPath      = kwargs.pop('doClipPath',      True)
        self.doPathCursor    = kwargs.pop('doPathCursor',    True)
        self.doDrawColorbar  = kwargs.pop('doDrawColorbar',  True)
        self.pathColorSource = kwargs.pop('pathColorSource', CLR_SRC.TIME)

        self.doDrawEllipse   = kwargs.pop('doDrawEllipse',   True)
        self.doEllipseCursor = kwargs.pop('doEllipseCursor', True)
        self.ellipseStyle    = kwargs.pop('ellipseStyle',    ELL_STL.ELLIPSE)
        self.ellipseFrequency= kwargs.pop('ellipseFrequency', 8)
        self.ellipseColor    = kwargs.pop('ellipseColor',    "#4682B4") # HTML SteelBlue
        self.ellipseAlpha    = kwargs.pop('ellipseAlfa',     0.4)

    def __iter__(self):
        for name in dir(self):
            if not name.startswith('__') and not callable(getattr(self, name)):
                yield getattr(self, name)
                
    def iterOnAttributeNames(self):
        for name in dir(self):
            if not name.startswith('__') and not callable(getattr(self, name)):
                yield name
