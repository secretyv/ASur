# -*- mode: python -*-

import glob
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

ROOTDIR = r'E:\Projets_simulation\VilleDeQuebec\Beauport\PaBeau'

ASCmp = ['tide', 'river', 'station', 'asclass', 'asapi', '__init__']
ASModel_hiddenimports = [ 'ASModel.'+c for c in ASCmp[0:5] ]
#ASModel_data          = [ (r'ASModel\BBData', 'BBData'), (r'LICENSE', '.') ]
ASModel_data          = [ (r'LICENSE', '.') ]

python_hiddenimports = [ 'tzlocal', 'numpy', 'matplotlib', 'FileDialog', 'mpldatacursor', 'wxmpl', 'mechanize', 'appdirs', 'packaging' ]
python_hiddenimports += collect_submodules('pkg_resources._vendor')

pb2_a = Analysis(['ASur.py'],
             pathex  = [os.path.join(ROOTDIR, 'ASModel')],
             binaries       = [],
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
