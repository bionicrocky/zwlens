@echo off
rem Start SeeWave and open it in your browser. Windows.
cd /d "%~dp0"
where py >nul 2>nul && (py -m seewave %* & goto :eof)
where python >nul 2>nul && (python -m seewave %* & goto :eof)
echo Python 3.9 or newer is required: https://www.python.org/downloads/
pause
