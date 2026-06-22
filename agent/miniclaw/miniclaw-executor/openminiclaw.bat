@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
set "ROOT=%~dp0"
set "APP_DIR=%ROOT%app"
set "STARTUP_TIPS=%ROOT%docs\startup_tips.md"
set "NGROK_GUIDE=%ROOT%docs\ngrok_update_guide.md"

cd /d "%TEMP%"

:: 在開頭即打開提示筆記本（常見問題、重新啟動指引）
start /b "" notepad.exe "%STARTUP_TIPS%"

echo [1/5] Node.js check...
where node >nul 2>&1
if %errorlevel% neq 0 (
  echo installing > "%ROOT%installing.flag"
  echo [x] Node.js not found. Installing via winget...
  winget install OpenJS.NodeJS --accept-source-agreements --accept-package-agreements
  set INSTALL_RESULT=!errorlevel!
  del "%ROOT%installing.flag" >nul 2>&1
  if !INSTALL_RESULT! neq 0 (
    echo [X] Install failed. Please visit https://nodejs.org
    pause
    exit /b 1
  )
  echo [OK] Node.js installed.
  echo Close this window and run openminiclaw.bat again.
  pause
  exit /b 0
)

echo [OK] Node.js OK

if not exist "%APP_DIR%node_modules" (
  echo [2/5] First run - installing packages...
  pushd "%APP_DIR%"
  call npm install
  popd
)

echo [OK] Packages ready

echo [3/5] Starting server (background)...
pushd "%APP_DIR%"
start /b "" node server.js >nul 2>&1
popd

timeout /t 2 /nobreak >nul

echo [OK] Server started

echo [4/5] Checking ngrok...
echo [OK] ngrok check skipped (local mode)
goto :skip_ngrok

:skip_ngrok
echo.
echo [*] Skipping ngrok tunnel. Server running on http://localhost:3000
echo     Open the web UI manually:
start /b "" cmd /c "start https://eric0724.github.io/agent/miniclaw/miniclaw-web/index.html"

:running
echo.
echo ============================================
echo  Miniclaw is running.
echo  Finish setup in the browser.
echo ============================================
echo.
echo  You can switch to the browser now. You do NOT need to type N.
echo  Type Y and press Enter only when you want to stop node and ngrok.
echo.
set /p STOP_INPUT="Stop services? (Y, or Enter to keep running): "
if /i "!STOP_INPUT!"=="Y" (
  taskkill /f /im node.exe >nul 2>&1
  taskkill /f /im ngrok.exe >nul 2>&1
  echo [OK] All services stopped.
  pause
  exit /b 0
)
echo [OK] Still running. Close this window anytime, or press a key below.
pause
exit /b 0