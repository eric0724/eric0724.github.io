@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
set "ROOT=%~dp0"
set "APP_DIR=%ROOT%app"
set "STARTUP_TIPS=%ROOT%docs\startup_tips.md"

echo ============================================
echo  ^>^> Miniclaw - 啟動與設定
echo ============================================
echo  第一次執行會自動安裝必要元件
echo  安裝過程請勿關閉此視窗
echo ============================================
echo.

:: 開啟啟動提示筆記本
if exist "%STARTUP_TIPS%" start /b "" notepad.exe "%STARTUP_TIPS%"

:: ============================================
:: Step 1: Node.js 檢查 / 安裝
:: ============================================
echo [1/5] 檢查 Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Node.js 未安裝，正在透過 winget 安裝...
    echo     請稍候，安裝完成後會自動繼續。
    echo.
    winget install OpenJS.NodeJS --accept-source-agreements --accept-package-agreements
    set "INST=!errorlevel!"
    if !INST! neq 0 (
        echo.
        echo [X] Node.js 安裝失敗。
        echo     請手動前往 https://nodejs.org 下載安裝，完成後重新執行本程式。
        pause
        exit /b 1
    )
    echo.
    echo [OK] Node.js 安裝完成，刷新環境變數...
    call :refresh_path
    where node >nul 2>&1
    if !errorlevel! neq 0 (
        echo [!] 刷新後仍找不到 node.exe。
        echo     請關閉此視窗並重新執行 start_watch.bat。
        pause
        exit /b 1
    )
)
echo [OK] Node.js 就緒
echo.

:: ============================================
:: Step 2: 安裝 npm 套件（首次執行）
:: ============================================
if not exist "%APP_DIR%\node_modules" (
    echo [2/5] 首次執行，安裝 npm 套件...
    pushd "%APP_DIR%"
    call npm install
    popd
    echo.
) else (
    echo [2/5] npm 套件已就緒
)

:: ============================================
:: Step 2.5: 下載 / 更新 server.js 與核心 JS
:: ============================================
echo [2.5/5] 檢查伺服器核心檔 (server.js)...
if not exist "%APP_DIR%\server.js" (
    echo [!] 本地缺乏 server.js，正在從 GitHub 下載最新版本...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/eric0724/eric0724.github.io/main/agent/miniclaw/miniclaw-executor/app/server.js' -OutFile '%APP_DIR%\server.js'"
    if not exist "%APP_DIR%\server.js" (
        echo [X] server.js 下載失敗！請確認網路連線。
        pause
        exit /b 1
    )
    echo [OK] server.js 下載完成！
)
if not exist "%APP_DIR%\skills_manager.js" (
    echo [!] 正在從 GitHub 下載 skills_manager.js...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/eric0724/eric0724.github.io/main/agent/miniclaw/miniclaw-executor/app/skills_manager.js' -OutFile '%APP_DIR%\skills_manager.js'"
)

:: ============================================
:: Step 3: 啟動 Server
:: ============================================
echo [3/5] 啟動 server...
pushd "%APP_DIR%"
start /b "" node server.js >nul 2>&1
popd
timeout /t 2 /nobreak >nul
echo [OK] Server 啟動中（http://localhost:3000）
echo.

:: ============================================
:: Step 4: ngrok 檢查 / 安裝 / authtoken 設定
:: ============================================
echo [4/5] 檢查 ngrok...
set "NGROK_EXE="

:: 先試 PATH
where ngrok >nul 2>&1
if %errorlevel% equ 0 (
    set "NGROK_EXE=ngrok"
    goto :ngrok_found
)

:: 試 WinGet Links 資料夾（winget 常見 shim 位置）
if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\ngrok.exe" (
    set "NGROK_EXE=%LOCALAPPDATA%\Microsoft\WinGet\Links\ngrok.exe"
    goto :ngrok_found
)

:: 試 WinGet Packages 資料夾（glob 搜尋）
for /d %%D in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\ngrok*") do (
    if exist "%%D\ngrok.exe" set "NGROK_EXE=%%D\ngrok.exe"
)
if defined NGROK_EXE goto :ngrok_found

:: 找不到就安裝
echo [!] ngrok 未安裝，正在透過 winget 安裝...
winget install ngrok.ngrok --accept-source-agreements --accept-package-agreements
if %errorlevel% neq 0 (
    echo [*] ngrok 安裝失敗，將以僅本地連線模式繼續。
    goto :step_api
)
call :refresh_path

:: 安裝後再找一次
where ngrok >nul 2>&1
if %errorlevel% equ 0 (
    set "NGROK_EXE=ngrok"
    goto :ngrok_found
)
if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\ngrok.exe" (
    set "NGROK_EXE=%LOCALAPPDATA%\Microsoft\WinGet\Links\ngrok.exe"
    goto :ngrok_found
)
for /d %%D in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\ngrok*") do (
    if exist "%%D\ngrok.exe" set "NGROK_EXE=%%D\ngrok.exe"
)
if not defined NGROK_EXE (
    echo [*] 安裝後仍找不到 ngrok.exe，將以僅本地連線模式繼續。
    goto :step_api
)

:ngrok_found
echo [OK] ngrok 就緒：!NGROK_EXE!
echo.

:: ─── authtoken 檢查 ───────────────────────────
echo [4.1] 檢查 ngrok authtoken...
call :check_authtoken
if !HAS_TOKEN!==1 (
    echo [OK] authtoken 已設定，跳過
    goto :step_api
)

echo.
echo ============================================
echo  需要 ngrok authtoken 才能使用遠端連線
echo  瀏覽器將自動開啟 ngrok 取得 token 頁面
echo ============================================
start /b "" cmd /c "start https://dashboard.ngrok.com/get-started/your-authtoken"
echo.
set /p NGROK_TOKEN="  請貼上 authtoken（直接按 Enter 可跳過）: "
if not "!NGROK_TOKEN!"=="" (
    "!NGROK_EXE!" config add-authtoken !NGROK_TOKEN!
    if !errorlevel! equ 0 (
        echo [OK] authtoken 設定完成
    ) else (
        echo [X] authtoken 設定失敗，請確認 token 是否正確
    )
) else (
    echo [*] 跳過 authtoken 設定（僅本地連線）
)
echo.

:: ============================================
:: Step 5: API Key 設定
:: ============================================
:step_api
echo [5/5] 檢查 API Key...

:: 如果 .env 已有 key 就跳過
set "HAS_API=0"
if exist "%APP_DIR%\.env" (
    findstr /i "GEMINI_API_KEY=" "%APP_DIR%\.env" >nul 2>&1
    if !errorlevel! equ 0 set "HAS_API=1"
)
if !HAS_API!==1 (
    echo [OK] API Key 已設定，跳過
    goto :done
)

echo.
echo ============================================
echo  設定 Gemini API Key（AI 對話功能用）
echo  瀏覽器將自動開啟 AI Studio 取得 Key 頁面
echo ============================================
start /b "" cmd /c "start https://aistudio.google.com/apikey"
echo.
set /p API_KEY="  請貼上 Gemini API Key（直接按 Enter 可跳過）: "
if not "!API_KEY!"=="" (
    echo GEMINI_API_KEY=!API_KEY!> "%APP_DIR%\.env"
    echo [OK] API Key 已儲存
) else (
    echo [*] 跳過 API Key 設定
)

:: ============================================
:: 完成
:: ============================================
:done
echo.
echo ============================================
echo  OK 設定完成！
echo  請等候瀏覽器自動開啟...
echo ============================================
echo.
exit /b 0

:: ============================================
:: 函式：從 Registry 刷新 PATH（不需重開視窗）
:: ============================================
:refresh_path
set "SYS_PATH="
set "USR_PATH="
for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%B"
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USR_PATH=%%B"
if defined SYS_PATH (
    if defined USR_PATH (
        set "PATH=!SYS_PATH!;!USR_PATH!"
    ) else (
        set "PATH=!SYS_PATH!"
    )
)
exit /b 0

:: ============================================
:: 函式：檢查 ngrok authtoken 是否已設定
:: ============================================
:check_authtoken
set "HAS_TOKEN=0"
set "TMP_FILE=%TEMP%\miniclaw_token_chk.txt"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$paths=@($env:LOCALAPPDATA+'\ngrok\ngrok.yml',$env:APPDATA+'\ngrok\ngrok.yml',$env:USERPROFILE+'\.ngrok2\ngrok.yml'); $ok=$false; foreach($p in $paths){ if(Test-Path $p){ $raw=Get-Content $p -Raw -ErrorAction SilentlyContinue; if($raw -match '(?m)^\s*authtoken\s*:\s*\S+'){ $ok=$true } } }; if($ok){ '1' } else { '0' }" > "!TMP_FILE!" 2>nul
if exist "!TMP_FILE!" set /p HAS_TOKEN=<"!TMP_FILE!"
del "!TMP_FILE!" >nul 2>&1
if not "!HAS_TOKEN!"=="1" set "HAS_TOKEN=0"
exit /b 0