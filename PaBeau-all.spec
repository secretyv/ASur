# -*- mode: python -*-

import glob
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

ROOTDIR = r'E:\Projets_simulation\VilleDeQuebec\Beauport\PaBeau'

BBCmp = ['tide', 'river', 'station', 'bbclass', 'bbapi', '__init__']
BBModel_hiddenimports = [ 'BBModel.'+c for c in BBCmp[0:5] ]
#BBModel_data          = [ (r'BBModel\BBData', 'BBData'), (r'lgpl-3.0.txt', '.') ]
BBModel_data          = [ (r'lgpl-3.0.txt', '.') ]

python_hiddenimports = [ 'tzlocal', 'numpy', 'matplotlib', 'FileDialog', 'mpldatacursor', 'wxmpl', 'mechanize', 'appdirs', 'packaging' ]
python_hiddenimports += collect_submodules('pkg_resources._vendor')

pb1_a = Analysis(['PaBeau.py'],
             pathex  = [os.path.join(ROOTDIR, 'BBModel')],
             binaries       = [],
             datas          = BBModel_data,
             hiddenimports  = BBModel_hiddenimports + python_hiddenimports,
             hookspath      = [],
             runtime_hooks  = [],
             excludes       = [],
             win_no_prefer_redirects=False,
             win_private_assemblies =False,
             cipher=block_cipher)

pb2_a = Analysis(['Pa2Beau.py'],
             pathex  = [os.path.join(ROOTDIR, 'BBModel')],
             binaries       = [],
             datas          = BBModel_data,
             hiddenimports  = BBModel_hiddenimports + python_hiddenimports,
             hookspath      = [],
             runtime_hooks  = [],
             excludes       = [],
             win_no_prefer_redirects=False,
             win_private_assemblies =False,
             cipher=block_cipher)

MERGE( (pb1_a, 'PaBeau', 'PaBeau'), (pb2_a, 'Pa2Beau', 'Pa2Beau') )

pb1_pyz = PYZ(pb1_a.pure,
          pb1_a.zipped_data,
          cipher=block_cipher)

pb2_pyz = PYZ(pb2_a.pure,
              pb2_a.zipped_data,
              cipher=block_cipher)

pb1_exe = EXE(pb1_pyz,
          pb1_a.scripts,
          exclude_binaries=True,
          name='PaBeau',
          debug=False,
          strip=False,
          upx=True,
          console=True )

pb2_exe = EXE(pb2_pyz,
              pb2_a.scripts,
              exclude_binaries=True,
              name='Pa2Beau',
              debug=False,
              strip=False,
              upx=True,
              console=True )

pb1_coll = COLLECT(pb1_exe,
              pb1_a.binaries,
              pb1_a.zipfiles,
              pb1_a.datas,
              strip=False,
              upx=True,
              name='PaBeau')

pb2_coll = COLLECT(pb2_exe,
              pb2_a.binaries,
              pb2_a.zipfiles,
              pb2_a.datas,
              strip=False,
              upx=True,
              name='Pa2Beau')

