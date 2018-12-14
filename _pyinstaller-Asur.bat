
:: LD_LIBRARY_PATH=/opt/anaconda3/lib:$LD_LIBRARY_PATH
pyinstaller --noconfirm ASur.spec
cp dist/ASur/osgeo._gdal.pyd dist/ASur/_gdal.pyd
