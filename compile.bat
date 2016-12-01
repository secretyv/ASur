::
setlocal
call setup_python27_32.bat
call setup_vc_x86_for_python.bat

:: ---  Génère BBModel dans BBModel_c
call compile_cython.bat BBModel_setup.py
call compile_cython.bat PaPlot_setup.py
call compile_cython.bat PaParam_setup.py

:: ---  Cython PaBeau en executable
::call compile2exe_x86_cython.bat PaBeau
