setlocal

call setup_python27_32.bat
call setup_vc_x86_for_python.bat

:: ---  Pyinstaller 3.1 (3.2 est buggé)
pyinstaller --version-file=Pa2Beau_version.txt Pa2Beau.spec

:eoj
