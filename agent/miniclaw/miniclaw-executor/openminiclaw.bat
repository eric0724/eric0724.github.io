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

echo [4/5] Checking ngrok...
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
  echo.
  echo [*] ngrok not found. Skipping ngrok setup.
  echo [*] Server will run on http://localhost:3000 (local only)
  echo.
  goto :skip_ngrok
)

echo [*] ngrok found. Checking authtoken...
ngrok config check >nul 2>&1
if %errorlevel% neq 0 (
  echo.
  echo ============================================
  echo  需要設定 ngrok authtoken 才能使用遠端連線
  echo ============================================
  echo.
  echo 正在為您開啟 ngrok authtoken 頁面...
  start /b "" cmd /c "start https://dashboard.ngrok.com/get-started/your-authtoken"
  echo 正在為您開啟更新說明記事本...
  start /b "" notepad.exe "%NGROK_GUIDE%"
  echo.
  echo 請至上方瀏覽器頁面登入後複製您的 authtoken（以 ngrok_ 開頭）
  echo.
  set /p NGROK_TOKEN="請輸入 ngrok authtoken（或直接按 Enter 跳過）: "
  if not "!NGROK_TOKEN!"=="" (
    echo [!] 正在設定 authtoken...
    ngrok config add-authtoken !NGROK_TOKEN!
    if !errorlevel! equ 0 (
      echo [OK] ngrok authtoken 設定完成！
    ) else (
      echo [X] authtoken 設定失敗，將跳過 ngrok 通道
      goto :skip_ngrok
    )
  ) else (
    echo [*] 跳過 ngrok 通道設定
    goto :skip_ngrok
  )
)

echo [OK] ngrok configured. Starting tunnel...
start /b "" ngrok http 3000 >nul 2>&1
timeout /t 3 /nobreak >nul

:skip_ngrok
echo.
echo [*] Server running on http://localhost:3000
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
  echo 3秒後自動關閉...
  timeout /t 3 /nobreak >nul
  exit /b 0
)
echo [OK] Still running. Close this window anytime.
timeout /t 3 /nobreak >nul
exit /b 0