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
if errorlevel 1 (
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
set NGROK_EXE=ngrok
where ngrok >nul 2>&1
if errorlevel 1 (
  if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" (
    set "NGROK_EXE=%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"
    goto :ngrok_found
  )
  if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\ngrok.ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" (
    set "NGROK_EXE=%LOCALAPPDATA%\Microsoft\WinGet\Packages\ngrok.ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"
    goto :ngrok_found
  )
  echo [!] ngrok not found. Skipping auto-install to prevent hang.
  echo     Watchdog will continue. Please install ngrok manually:
  echo     - Run: winget install ngrok.ngrok --accept-source-agreements --accept-package-agreements
  echo     - Or download from: https://ngrok.com/download
  echo     Then re-run openminiclaw.bat.
  echo.
  echo     For now, the server is running on http://localhost:3000
  echo     You can still use the web UI without ngrok (local only).
  goto :skip_ngrok
)

:ngrok_found
echo [OK] ngrok ready: %NGROK_EXE%

echo [4.4] Skipping ngrok version check to prevent hang...

echo [4.5] Resetting ngrok authtoken...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$paths=@($env:LOCALAPPDATA+'\ngrok\ngrok.yml',$env:APPDATA+'\ngrok\ngrok.yml',$env:USERPROFILE+'\.ngrok2\ngrok.yml'); foreach($p in $paths){ Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo [4.6] Checking ngrok authtoken...
call :check_authtoken
if "!HAS_AUTHTOKEN!"=="0" (
  echo [!] ngrok authtoken not set.
  echo     Skipping interactive setup to prevent watchdog hang.
  echo     The browser will open the ngrok token page for manual setup.
  echo     To set it manually later, run in CMD:
  echo       ngrok config add-authtoken YOUR_TOKEN
  echo.
  start /b "" cmd /c "start https://dashboard.ngrok.com/get-started/your-authtoken"
  echo     Continuing without ngrok tunnel...
  goto :skip_ngrok
)

:authtoken_ok
echo [OK] ngrok authtoken OK

echo.
echo [Tip] If ngrok shows an error, the version may be too old.
echo       Press Win+R, type cmd, then run:
echo       ngrok update
echo       Then run openminiclaw.bat again.
echo       If antivirus blocks it, download a newer version from https://ngrok.com/download.
echo.

echo [5/5] Starting ngrok tunnel (new window)...
start "" cmd /c ""%NGROK_EXE%" http 3000"

echo Waiting for ngrok start (8 sec)...
timeout /t 8 /nobreak >nul

echo Getting ngrok URL...
powershell -NoProfile -Command "try { $r = Invoke-RestMethod 'http://127.0.0.1:4040/api/tunnels'; $t = $r.tunnels | Where-Object { $_.proto -eq 'https' } | Select-Object -First 1; if ($t) { $t.public_url } else { '' } } catch { '' }" > "%TEMP%\ngrok_url.txt" 2>nul
set /p NGROK_URL=<"%TEMP%\ngrok_url.txt"
del "%TEMP%\ngrok_url.txt" >nul 2>&1

set NGROK_URL_EMPTY=1
if not "!NGROK_URL!"=="" set NGROK_URL_EMPTY=0

if !NGROK_URL_EMPTY!==1 (
  echo [x] Could not read ngrok URL.
  echo   Check the ngrok window and paste the https URL in Step 2.
  start /b "" cmd /c "start https://eric0724.github.io/agent/miniclaw/miniclaw-web/index.html"
) else (
  echo [OK] ngrok URL: !NGROK_URL!
  start /b "" cmd /c "start https://eric0724.github.io/agent/miniclaw/miniclaw-web/index.html?ngrok=!NGROK_URL!"
)
goto :running

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
echo  [Tip] Copy the ngrok URL into Step 2 if needed.
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

:ngrok_too_old
echo [X] ngrok is too old for this account.
echo     Current version: 3.3.1
echo     Need: 3.20.0 or newer
echo     Please update ngrok manually.
echo error > "%ROOT%install_error.flag"
call :open_ngrok_update_guide
pause
exit /b 0

:open_ngrok_update_guide
if exist "%NGROK_GUIDE%" (
  start "" notepad.exe "%NGROK_GUIDE%"
) else (
  echo [X] Guide file missing: %NGROK_GUIDE%
)
exit /b 0

:wait_for_authtoken
set HAS_AUTHTOKEN=0
for /l %%i in (1,1,5) do (
  call :check_authtoken
  if !HAS_AUTHTOKEN!==1 exit /b 0
  echo Waiting for token save... %%i/5
  timeout /t 2 /nobreak >nul
)
exit /b 0

:clean_authtoken
set "USER_TOKEN="
set "CLEAN_TOKEN_FILE=%TEMP%\miniclaw_clean_token.txt"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$matches=[regex]::Matches($env:MINICLAW_RAW_TOKEN,'[A-Za-z0-9_-]{20,}'); if($matches.Count -gt 0){ $matches[$matches.Count-1].Value } else { '' }" > "!CLEAN_TOKEN_FILE!" 2>nul
if exist "!CLEAN_TOKEN_FILE!" set /p USER_TOKEN=<"!CLEAN_TOKEN_FILE!"
del "!CLEAN_TOKEN_FILE!" >nul 2>&1
exit /b 0

:check_authtoken
set HAS_AUTHTOKEN=0
set "TOKEN_CHECK_FILE=%TEMP%\miniclaw_ngrok_token_check.txt"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$paths=@($env:LOCALAPPDATA+'\ngrok\ngrok.yml',$env:APPDATA+'\ngrok\ngrok.yml',$env:USERPROFILE+'\.ngrok2\ngrok.yml'); $ok=$false; foreach($p in $paths){ if(Test-Path -LiteralPath $p){ $raw=Get-Content -LiteralPath $p -Raw -ErrorAction SilentlyContinue; if($raw -match '(?m)^\s*authtoken\s*:\s*\S+'){ $ok=$true } } }; if($ok){ '1' } else { '0' }" > "!TOKEN_CHECK_FILE!" 2>nul
if exist "!TOKEN_CHECK_FILE!" set /p HAS_AUTHTOKEN=<"!TOKEN_CHECK_FILE!"
del "!TOKEN_CHECK_FILE!" >nul 2>&1
if not "!HAS_AUTHTOKEN!"=="1" set HAS_AUTHTOKEN=0
exit /b 0

:check_ngrok_version
set "NGROK_VERSION_OK=0"
set "NGROK_VERSION_FILE=%TEMP%\miniclaw_ngrok_version.txt"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$out=& $env:NGROK_EXE version 2>$null; $ver=''; if($out -match '(\d+\.\d+\.\d+)'){ $ver=$matches[1] }; if($ver -and ([version]$ver -ge [version]'3.20.0')){ '1' } else { '0' }" > "!NGROK_VERSION_FILE!" 2>nul
if exist "!NGROK_VERSION_FILE!" set /p NGROK_VERSION_OK=<"!NGROK_VERSION_FILE!"
del "!NGROK_VERSION_FILE!" >nul 2>&1
if not "!NGROK_VERSION_OK!"=="1" set NGROK_VERSION_OK=0
exit /b 0