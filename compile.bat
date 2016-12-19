::
setlocal
call setup_python27_32.bat
call setup_vc_x86_for_python.bat

:: ---  Génère ASModel
call compile_cython.bat ASModel_setup.py
call compile_cython.bat ASPlot_setup.py
call compile_cython.bat ASParam_setup.py

:: ---  Cython ASur en executable
::call compile2exe_x86_cython.bat ASur
