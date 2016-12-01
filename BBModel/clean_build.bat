rm -rf build
del *.c
del *.pyd

call ..\compile_cython.bat tide_setup.py
call ..\compile_cython.bat river_setup.py
call ..\compile_cython.bat station_setup.py
call ..\compile_cython.bat bbclass_setup.py
call ..\compile_cython.bat bbapi_setup.py
call ..\compile_cython.bat __init_setup.py

pause