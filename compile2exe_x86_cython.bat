:: Compile to pxd
setlocal
cython %*.py --embed

@set PPATH="%PYTHON_ROOT%"

@set INC=
@set INC=%INC% -I%PPATH%\include 
::@set INC=%INC% -I%PPATH%\PC
@set CFLAG=
::@set CFLAG=%CFLAG% /nologo /Od /Ob0 /MD /W3 /GS- /Zi /RTCsu /DEBUG
@set CFLAG=%CFLAG% /nologo /Ox /MD /W3 /GS- /DNDEBUG
@set LFLAG=
@set LFLAG=%LFLAG% /link /SUBSYSTEM:CONSOLE /MACHINE:X86
@set LIBS=
@set LIBS=%LIBS% /LIBPATH:%PPATH%\libs python27.lib
::@set LIBS=%LIBS% /LIBPATH:%PPATH%\PCbuild

cl.exe %CFLAG% %INC% /Tc %*.c %LFLAG% %LIBS% /OUT:"%*.exe"
