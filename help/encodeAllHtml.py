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
Encodes all the help file, i.e. transforms all the diacritical marks to
their html form.
Read  in   *.utf8.htm file
write out  *.htm file
"""


import glob
import html
import os

for fInp in glob.glob('*.utf8.htm*'):
    root = fInp
    root = os.path.splitext(root)[0]
    root = os.path.splitext(root)[0]

    fOut = root + '.htm'
    print('Encoding "%s" to "%s"' % (fInp, fOut))
    with open(fInp, "rt", encoding="utf-8") as ifs,\
         open(fOut, "wt", encoding="ascii") as ofs:
        for l_i in ifs.readlines():
            l_o = l_i.encode('ascii', 'xmlcharrefreplace')
            l_o = l_o.decode('ascii')
            ofs.write("%s" % l_o)
