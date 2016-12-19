rm -rf build
del *.c
del *.pyd

call ..\compile_cython.bat tide_setup.py
call ..\compile_cython.bat river_setup.py
call ..\compile_cython.bat station_setup.py
call ..\compile_cython.bat asclass_setup.py
call ..\compile_cython.bat asapi_setup.py
call ..\compile_cython.bat __init_setup.py

pause