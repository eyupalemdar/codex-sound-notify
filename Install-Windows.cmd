@echo off
setlocal
title Codex Notify Music Installer
cd /d "%~dp0"
set "PYTHON_INSTALL_TRIED=0"

echo Codex Notify Music - Windows Installer
echo.

:find_python
where py >nul 2>nul
if errorlevel 1 goto try_python
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 goto python_too_old
py -3 app\install.py --interactive
set "RESULT=%ERRORLEVEL%"
goto finish

:try_python
where python >nul 2>nul
if errorlevel 1 goto no_python
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 goto python_too_old
python app\install.py --interactive
set "RESULT=%ERRORLEVEL%"
goto finish

:no_python
echo Python bulunamadi.
goto offer_python_install

:python_too_old
echo Python bulundu ama surumu eski.

:offer_python_install
echo Bu kurulum icin Python 3.10 veya daha yeni bir surum gerekir.
echo.

where winget >nul 2>nul
if errorlevel 1 goto no_winget
if "%PYTHON_INSTALL_TRIED%"=="1" goto manual_python

set /p INSTALL_PYTHON="Python'u winget ile otomatik kurmak ister misiniz? [E/H]: "
if /i "%INSTALL_PYTHON%"=="E" goto install_python_winget
if /i "%INSTALL_PYTHON%"=="EVET" goto install_python_winget
goto manual_python

:install_python_winget
echo.
echo Python kuruluyor...
set "PYTHON_INSTALL_TRIED=1"
winget install --id Python.Python.3 --source winget --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
  echo Python otomatik kurulumu basarisiz oldu.
  goto manual_python
)
echo.
echo Python kurulumu tamamlandi. Kontrol tekrar yapiliyor...
goto find_python

:no_winget
echo winget bulunamadi; otomatik kurulum yapilamiyor.

:manual_python
echo Python 3 kurun: https://www.python.org/downloads/
echo Kurulumdan sonra bu dosyayi tekrar calistirin.
set "RESULT=1"

:finish

echo.
if not "%RESULT%"=="0" (
  echo Kurulum tamamlanamadi. Yukaridaki mesaji kontrol edin.
)
pause
exit /b %RESULT%
