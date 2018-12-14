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
La génération de ASModel directement dans le répertoire du module cause des 
interférences avec pyinstaller qui ne parvient pas à décoder le __init__.pyd.

Le module est ici généré dans le répertoire ASModel_c à partir du source qui
est dans ASModel.
"""

try:
    from setuptools import setup
    from setuptools import Extension
except ImportError:
    from distutils.core import setup
    from distutils.extension import Extension
from Cython.Build import cythonize

cython_include = []

extensions = [
    Extension('ASModel.tide',
        ['ASModel/tide.py'],
        include_dirs = cython_include,
        #extra_compile_args=["-Zi", "/Od"],
        #extra_link_args=["-debug"],        
        ),
    Extension('ASModel.river',
        ['ASModel/river.py'],
        include_dirs = cython_include,
        #extra_compile_args=["-Zi", "/Od"],
        #extra_link_args=["-debug"],        
        ),
    Extension('ASModel.overflow',
        ['ASModel/overflow.py'],
        include_dirs = cython_include,
        #extra_compile_args=["-Zi", "/Od"],
        #extra_link_args=["-debug"],        
        ),
    Extension('ASModel.station',
        ['ASModel/station.py'],
        include_dirs = cython_include,
        #extra_compile_args=["-Zi", "/Od"],
        #extra_link_args=["-debug"],        
        ),
    Extension('ASModel.asplume',
        ['ASModel/asplume.py'],
        include_dirs = cython_include,
        #extra_compile_args=["-Zi", "/Od"],
        #extra_link_args=["-debug"],        
        ),
    Extension('ASModel.asclass',
        ['ASModel/asclass.py'],
        include_dirs = cython_include,
        #extra_compile_args=["-Zi", "/Od"],
        #extra_link_args=["-debug"],        
        ),
    Extension('ASModel.asapi',
        ['ASModel/asapi.py'],
        include_dirs = cython_include,
        #extra_compile_args=["-Zi", "/Od"],
        #extra_link_args=["-debug"],        
        ),
]

setup(
    name = 'ASModel',
    ext_modules = cythonize(extensions),
)
