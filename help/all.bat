:: Must be run from the local directory
@echo off

:: Generate .htm files
python encodeAllHtml.py

:: Compile Window help (not really necessary)
set HHC_PATH=%ProgramFiles(x86)%\HTML Help Workshop
"%HHC_PATH%\hhc.exe" ASur.hhp