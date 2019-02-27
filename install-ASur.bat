setlocal

:: ---  Pyinstaller
pyinstaller --noconfirm --version-file=ASur_version.txt ASur.spec

:: ---  Fix osgeo (gdal 2.3.3 semble OK)
:: cp dist/ASur/osgeo._gdal.pyd dist/ASur/_gdal.pyd
:: cp dist/ASur/_gdal_array.pyd dist/ASur/osgeo._gdal_array.pyd

:eoj
