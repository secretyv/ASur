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
Translator, providing two ways mapping between strings.

The variable translator is a "singleton", accessible by import of the module
"""

import codecs
import logging
import traceback

try:
    import addLogLevel
    addLogLevel.addLoggingLevel('TRACE', logging.DEBUG - 5)
except AttributeError:
    pass
LOGGER = logging.getLogger("INRS.ASur.translator")

class ASTranslator:
    """
    Translator class based on a simple dictionnary.
    Provides direct and reversed translation.
    """
    def __init__(self, fname = ''):
        self.dicoDir = {}
        self.dicoRev = {}
        if fname:
            self.loadFromFile(fname)

    def loadFromFile(self, fname):
        """
        Load 
            key=value or 
            key=(value, help) 
        lines from file fname.
        """
        with codecs.open(fname, "r", encoding="utf-8") as ifs:
            for l in ifs.readlines():
                l = l.strip()
                if not l: continue
                if l[0] == '#': continue
                try:
                    k, v = l.split('=', 1)
                    k = k.strip()
                    v = v.strip()
                    try:
                        v, h = eval(v, {}, {})
                    except (NameError, SyntaxError):
                        h = ''
                        pass
                    v = v.strip()
                    h = h.strip()
                    self.dicoDir[k] = (v, h)
                    self.dicoRev[v] = k
                except Exception as e:
                    LOGGER.warning('Invalid entry: %s', l)
                    LOGGER.error('Exception: %s', str(e))

    def __getitem__(self, k):
        """
        Syntactic suggar for translateDirect
        """
        return self.dicoDir.get(k, (k, '') )
            
    def translateDirect(self, k):
        """
        Direct translation, return value associated with key k
        """
        return self.dicoDir.get(k, (k, '') )

    def translateInverse(self, v):
        """
        Inverse translation, return key associated with value v
        """
        return self.dicoRev.get(v, v)
        
# ---  Module instance as a global singleton
translator = ASTranslator()

if __name__ == "__main__":
    def main():
        logHndlr = logging.StreamHandler()
        FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logHndlr.setFormatter( logging.Formatter(FORMAT) )

        LOGGER.addHandler(logHndlr)
        LOGGER.setLevel(logging.TRACE)

        #fname = r'E:\Projets_simulation\VilleDeQuebec\Beauport\BBData_v3.2\overflow-tbl.txt'
        fname = r'E:\Projets_simulation\VilleDeQuebec\Beauport\ASur\Exutoire_à_Corpo.atf'
        tr = ASTranslator(fname)
        print(tr['BBE-MOU-003'])

    main()
