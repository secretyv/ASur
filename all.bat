:: ---  Clean
call clean.bat

:: ---  Génère BBModel dans BBModel_c
call compile.bat

:: ---  Installe
call install-all.bat
copy dist\Pa2Beau\*.* dist\PaBeau
pause
