::
setlocal

set CC=%INRS_BLD%\compile_cython

:: ---  Génère ASModel
call %CC%.bat ASModel.pxd

:: ---  Génère ASur
:: call %CC%.bat ASConst.pxd
:: call %CC%.bat ASGlobalParameters.pxd
:: call %CC%.bat ASModel.pxd
:: call %CC%.bat ASPathParameters.pxd
:: call %CC%.bat ASPathParametersEnum.pxd
:: call %CC%.bat ASTranslator.pxd
:: call %CC%.bat ASur.pxd

:: ---  Cython ASur en executable
::call compile2exe_x86_cython.bat ASur
