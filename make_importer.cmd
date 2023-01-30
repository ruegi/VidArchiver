@echo off
rem Make-Datei 
rem -------------------------------------
set NAME=Importer
pyuic6 -x frm_%NAME%.ui -o frm_%NAME%UI.py

if "%1%"=="simple" goto Ende
rem .
del /S /Y .\dist\%NAME%
rem set LD_LIBRARY_PATH=%PYTHONPATH%\Lib
pyinstaller -w -y -i %NAME%.ico -p %PYTHONPATH%\Lib --clean -n %NAME% %NAME%.py

copy .\%NAME%.ico .\dist\%NAME%

:Ende
echo Fertig!

