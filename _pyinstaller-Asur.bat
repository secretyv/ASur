
:: LD_LIBRARY_PATH=/opt/anaconda3/lib:$LD_LIBRARY_PATH
pyinstaller --noconfirm ASur.spec

:: Fix osgeo
cp dist/ASur/osgeo._gdal.pyd dist/ASur/_gdal.pyd
cp dist/ASur/_gdal_array.pyd dist/ASur/osgeo._gdal_array.pyd
