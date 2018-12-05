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
Information pour une surverse
"""

import logging

LOGGER = logging.getLogger("INRS.ASModel.overflow")

"https://stackoverflow.com/questions/1835018/how-to-check-if-an-object-is-a-list-or-tuple-but-not-string"
def is_sequence(arg):
    """
    Return True if arg is a sequence (list, tuple, ...) but not a str
    """
    if isinstance(arg, str): return False
    if hasattr(arg, 'strip'): return False
    return hasattr(arg, '__getitem__') or hasattr(arg, '__iter__')

class Overflow:
    """
    Structure to hold informations pertaining to an overflow
    """
    def __init__(self, name, start, stop, tides):
        self.name  = name       # overflow station name
        self.tini  = start      # overflow start
        self.tend  = stop       # overflow end
        self.tides = tides      # overflow tide cycles

    def __str__(self):
        return '%s from %s to %s with %d tide cycles' % (self.name, self.tini, self.tend, len(self.tides))

    def isValid(self):
        errMsg = ''
        errLst = []
        if not self.name:
            errLst.append('Nom vide')
        if self.tini >= self.tend:
            errLst.append('Temps invalides: Le temps initial doit être inférieur au temps final')
        if not is_sequence(self.tides):
            errLst.append('Marées invalides: Doit être une séquence, possiblement vide')
        if errLst:
            errLst.append(str(self))
            errMsg = '\n'.join(errLst)
        return errMsg

if __name__ == "__main__":
    from datetime import datetime, timedelta
    import pytz
    def main():
        dt = datetime.now(tz=pytz.utc)
        item = Overflow('', dt, dt, 'aa')
        print(item.isValid())
        item = Overflow('a', dt, dt+timedelta(1), ['a'])
        print(item.isValid())

    main()
