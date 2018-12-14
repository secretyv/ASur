@echo off
setlocal

set BIN_DIR=%~dp0
set BIN_DIR=%BIN_DIR:~0,-1%

set INRS_BBM_ROOT=%BIN_DIR%
set INRS_H2D2_TOOLS=%INRS_DEV%/H2D2-tools/script
:: call C:\ProgramData\Anaconda3\Scripts\activate.bat ASur
python Asur.py %*

