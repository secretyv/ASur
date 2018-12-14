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
Constantes
"""

import datetime
import pytz
import tzlocal

LOCAL_TZ = tzlocal.get_localzone()

DATE_MAX = datetime.datetime(datetime.MAXYEAR-1, 12, 31)
DATE_MAX = LOCAL_TZ.localize(DATE_MAX)
DATE_MAX = DATE_MAX.astimezone(pytz.utc)

DATE_MIN = datetime.datetime(datetime.MINYEAR+1,  1,  1)
DATE_MIN = LOCAL_TZ.localize(DATE_MIN)
DATE_MIN = DATE_MIN.astimezone(pytz.utc)


