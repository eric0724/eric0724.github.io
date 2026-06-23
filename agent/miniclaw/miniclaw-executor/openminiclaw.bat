@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
set "ROOT=%~dp0"
set "APP_DIR=%ROOT%app"
set "STARTUP_TIPS=%ROOT%docs\startup_tips.md"

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
  echo 3秒後自動關閉，請重新執行 openminiclaw.bat...
  timeout /t 3 /nobreak >nul
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

:: ngrok 和 API key 設定由 setup_ngrok.bat 處理
echo [*] ngrok and API setup will be handled by setup_ngrok.bat
echo.
echo [*] openminiclaw.bat done. Server running on http://localhost:3000
echo.
exit /b 0