:: ---  Clean
call clean.bat

:: ---  Génère help
pushd help
call all.bat
popd

:: ---  Génère ASModel
call compile.bat

:: ---  Installe
call install-ASur.bat
pause
