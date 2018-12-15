# -*- mode: python -*-

import glob
import os
from PyInstaller.utils.hooks import collect_submodules

def findFileInPath(f):
    paths = os.environ['PATH'].split(os.pathsep)
    for p in paths:
        fp = os.path.join(p, f)
        if os.path.isfile(fp):
            return p
    return '' 

block_cipher = None

ROOTDIR = r'E:\Projets_simulation\VilleDeQuebec\Beauport\ASur'

ASCmp = ['tide', 'river', 'station', 'overflow', 'asplume', 'asclass', 'asapi', '__init__']
ASModel_hiddenimports = [
    'ASModel.'+c for c in ASCmp[:-1] 
    ]
ASModel_binaries = [ 
    ]
ASModel_data = [ 
    ('LICENSE',             '.'),
    ('bitmaps/*.png',       'bitmaps'),
    ('bitmaps/LICENSE.TXT', 'bitmaps'),
    ('background',          'background'),
    ('traduction',          'traduction'),
    (findFileInPath('gdalsrsinfo.exe'), '.'),
    (findFileInPath('gdalwarp.exe'),    '.'),
    ]

    
python_hiddenimports = [
    'gdal',
    # 'gdalarray',
    'pytimeparse',
    ]

pb2_a = Analysis(['ASur.py'],
                 pathex  = [os.path.join(ROOTDIR, 'ASModel')],
                 binaries       = ASModel_binaries,
                 datas          = ASModel_data,
                 hiddenimports  = ASModel_hiddenimports + python_hiddenimports,
                 hookspath      = [],
                 runtime_hooks  = [],
                 excludes       = [],
                 win_no_prefer_redirects=False,
                 win_private_assemblies =False,
                 cipher=block_cipher)

pb2_pyz = PYZ(pb2_a.pure,
              pb2_a.zipped_data,
              cipher=block_cipher)

pb2_exe = EXE(pb2_pyz,
              pb2_a.scripts,
              exclude_binaries=True,
              name='ASur',
              debug=False,
              strip=False,
              upx=True,
              console=True )

pb2_coll = COLLECT(pb2_exe,
              pb2_a.binaries,
              pb2_a.zipfiles,
              pb2_a.datas,
              strip=False,
              upx=True,
              name='ASur')
