rem Make-Datei 
rem
set VER=
pyuic5 -x VidArchiverUI%VER%.ui -o VidArchiverUI.py
pyuic5 -x VidArchiverRenDialogUI.ui -o VidArchiverRenDialogUI.py
pyuic5 -x VidArchiverPfaDialogUI.ui -o VidArchiverPfaDialogUI.py


if "%1%"=="simple" goto Ende
rem .
rem del /S /Y .\dist\VidArchiver
rem set LD_LIBRARY_PATH=%PYTHONPATH%\Lib
pyinstaller -w -y -i VidArchiver.ico -p %PYTHONPATH%\Lib --clean -p .\FilmDetails --hiddenimport FilmDetails\FilmDetailsUI.py -n VidArchiver VidArchiver%VER%.py

copy .\VidArchiver.ico .\dist\VidArchiver

:Ende
echo Fertig!
pause
