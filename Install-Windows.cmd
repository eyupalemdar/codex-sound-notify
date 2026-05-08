@echo off
setlocal
title Codex Notify Music Installer
cd /d "%~dp0"
set "PYTHON_INSTALL_TRIED=0"
set "INSTALL_LANG=en"

if defined CODEX_NOTIFY_LANG (
  set "INSTALL_LANG=%CODEX_NOTIFY_LANG%"
) else (
  for /f %%L in ('powershell -NoProfile -Command "[System.Globalization.CultureInfo]::CurrentUICulture.TwoLetterISOLanguageName" 2^>nul') do set "INSTALL_LANG=%%L"
)
if /i "%INSTALL_LANG:~0,2%"=="tr" (
  set "INSTALL_LANG=tr"
) else if /i "%INSTALL_LANG:~0,7%"=="turkish" (
  set "INSTALL_LANG=tr"
) else (
  set "INSTALL_LANG=en"
)

if /i "%INSTALL_LANG%"=="tr" (
  set "MSG_NO_PYTHON=Python bulunamadi."
  set "MSG_PYTHON_OLD=Python bulundu ama surumu eski."
  set "MSG_PYTHON_REQUIRED=Bu kurulum icin Python 3.10 veya daha yeni bir surum gerekir."
  set "PROMPT_INSTALL_PYTHON=Python'u winget ile otomatik kurmak ister misiniz? [E/H]: "
  set "MSG_INSTALLING_PYTHON=Python kuruluyor..."
  set "MSG_INSTALL_FAILED=Python otomatik kurulumu basarisiz oldu."
  set "MSG_INSTALL_DONE=Python kurulumu tamamlandi. Kontrol tekrar yapiliyor..."
  set "MSG_NO_WINGET=winget bulunamadi; otomatik kurulum yapilamiyor."
  set "MSG_INSTALL_MANUAL=Python 3 kurun: https://www.python.org/downloads/"
  set "MSG_RERUN=Kurulumdan sonra bu dosyayi tekrar calistirin."
  set "MSG_FAILED=Kurulum tamamlanamadi. Yukaridaki mesaji kontrol edin."
) else (
  set "MSG_NO_PYTHON=Python was not found."
  set "MSG_PYTHON_OLD=Python was found, but its version is too old."
  set "MSG_PYTHON_REQUIRED=This installer requires Python 3.10 or newer."
  set "PROMPT_INSTALL_PYTHON=Install Python automatically with winget? [Y/N]: "
  set "MSG_INSTALLING_PYTHON=Installing Python..."
  set "MSG_INSTALL_FAILED=Automatic Python installation failed."
  set "MSG_INSTALL_DONE=Python installation completed. Checking again..."
  set "MSG_NO_WINGET=winget was not found; automatic installation is unavailable."
  set "MSG_INSTALL_MANUAL=Install Python 3: https://www.python.org/downloads/"
  set "MSG_RERUN=Run this file again after installation."
  set "MSG_FAILED=Installation did not complete. Check the message above."
)

echo Codex Notify Music - Windows Installer
echo.

:find_python
where py >nul 2>nul
if errorlevel 1 goto try_python
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 goto python_too_old
py -3 app\install.py --interactive --language "%INSTALL_LANG%"
set "RESULT=%ERRORLEVEL%"
goto finish

:try_python
where python >nul 2>nul
if errorlevel 1 goto no_python
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 goto python_too_old
python app\install.py --interactive --language "%INSTALL_LANG%"
set "RESULT=%ERRORLEVEL%"
goto finish

:no_python
echo %MSG_NO_PYTHON%
goto offer_python_install

:python_too_old
echo %MSG_PYTHON_OLD%

:offer_python_install
echo %MSG_PYTHON_REQUIRED%
echo.

where winget >nul 2>nul
if errorlevel 1 goto no_winget
if "%PYTHON_INSTALL_TRIED%"=="1" goto manual_python

set /p INSTALL_PYTHON="%PROMPT_INSTALL_PYTHON%"
if /i "%INSTALL_PYTHON%"=="E" goto install_python_winget
if /i "%INSTALL_PYTHON%"=="EVET" goto install_python_winget
if /i "%INSTALL_PYTHON%"=="Y" goto install_python_winget
if /i "%INSTALL_PYTHON%"=="YES" goto install_python_winget
goto manual_python

:install_python_winget
echo.
echo %MSG_INSTALLING_PYTHON%
set "PYTHON_INSTALL_TRIED=1"
winget install --id Python.Python.3 --source winget --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
  echo %MSG_INSTALL_FAILED%
  goto manual_python
)
echo.
echo %MSG_INSTALL_DONE%
goto find_python

:no_winget
echo %MSG_NO_WINGET%

:manual_python
echo %MSG_INSTALL_MANUAL%
echo %MSG_RERUN%
set "RESULT=1"

:finish

echo.
if not "%RESULT%"=="0" (
  echo %MSG_FAILED%
)
pause
exit /b %RESULT%
