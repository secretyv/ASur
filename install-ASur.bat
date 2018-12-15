setlocal

:: ---  Pyinstaller 3.1 (3.2 est buggé)
pyinstaller --noconfirm --version-file=ASur_version.txt ASur.spec

:: Fix osgeo
cp dist/ASur/osgeo._gdal.pyd dist/ASur/_gdal.pyd
cp dist/ASur/_gdal_array.pyd dist/ASur/osgeo._gdal_array.pyd

:eoj
