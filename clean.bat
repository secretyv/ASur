:: ---  Clean
rm -rf build
rm -rf dist
rm -rf BBModel_c
del /s *.c
del /s *.lib
del /s *.obj
del /s *.exp
del /s *.exe
del /s *.exe.*
del /s *.pyc
del /s *.pyd

rm -rf %APPDATA%\pyinstaller\*
