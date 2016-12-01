:: Compile to pxd
setlocal
cython %*.py --embed

set PPATH="%PYTHON_ROOT%"
set VCBIN="C:\Users\secretyv\AppData\Local\Programs\Common\Microsoft\Visual C++ for Python\9.0\VC\bin"

set INC=
set INC=%INC% -I%PPATH%\include 
set INC=%INC% -I%PPATH%\PC
set CFLAG=
set CFLAG=%CFLAG% /nologo /Ox /MD /W3 /GS- /DNDEBUG
set LFLAG=
set LFLAG=%LFLAG% /link /SUBSYSTEM:CONSOLE /MACHINE:X64
set LIBS=
set LIBS=%LIBS% /LIBPATH:%PPATH%\libs
set LIBS=%LIBS% /LIBPATH:%PPATH%\PCbuild

%VCBIN%\cl.exe %CFLAG% %INC% /Tc%*.c %LFLAG% %LIBS% /OUT:"%*.exe"
