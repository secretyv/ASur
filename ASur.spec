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

ROOTDIR = SPECPATH

ASModel_path = [
   os.path.join(ROOTDIR, 'ASModel'),
   os.path.join(os.environ['INRS_DEV'], 'H2D2-tools', 'script'),
   ]
ASCmp = ('tide', 'river', 'station', 'overflow', 'asplume', 'asclass', 'asapi', '__init__')
ASModel_hiddenimports = ['ASModel.'+c for c in ASCmp[:-1] ]
ASModel_binaries = [
    ]
ASModel_data = [
    ('LICENSE',             '.'),
    ('background',          'background'),
    ('bitmaps/*.png',       'bitmaps'),
    ('bitmaps/LICENSE.TXT', 'bitmaps'),
    ('help/Asur.*',         'help'),
    ('help/*.htm*',         'help'),
    ('help/images',         'help/images'),
    ('traduction',          'traduction'),
    (findFileInPath('gdalsrsinfo.exe'), '.'),
    (findFileInPath('gdalwarp.exe'),    '.'),
    ]


python_hiddenimports = [
    'gdal',
    # 'gdalarray',
    'pytimeparse',
    ]
python_excludes = [
    'PyQt4',
    'PyQt5',
    'FixTk',
    'tkinter',
    ]

pb2_a = Analysis(['ASur.py'],
                 pathex         = ASModel_path,
                 binaries       = ASModel_binaries,
                 datas          = ASModel_data,
                 hiddenimports  = ASModel_hiddenimports + python_hiddenimports,
                 hookspath      = [],
                 runtime_hooks  = [],
                 excludes       = python_excludes,
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
