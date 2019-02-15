# -*- coding: utf-8 -*-
#************************************************************************
# --- Copyright (c) INRS 2018
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
Events
"""

import wx.lib.newevent

ASEventMessage,ASEVT_MESSAGE= wx.lib.newevent.NewCommandEvent()
ASEventMotion, ASEVT_MOTION = wx.lib.newevent.NewCommandEvent()
ASEventDClick, ASEVT_DCLICK = wx.lib.newevent.NewCommandEvent()

ASEventButton, ASEVT_BUTTON = wx.lib.newevent.NewCommandEvent()

