@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================
:: Miniclaw Watchdog v7
:: ============================================
::  1. 開啟 openminiclaw.bat（安裝+設定+啟動server，等它完成）
::  2. 確認 node.exe 有在跑
::  3. 啟動 ngrok 隧道
::  4. 開啟瀏覽器
::  5. 監控 node.exe，停止就重啟
:: ============================================

set "ROOT=%~dp0"
set "BAT_PATH=%ROOT%openminiclaw.bat"

echo ============================================
echo  ^>^> Miniclaw Watchdog v7
echo ============================================
echo  啟動後請在安裝/設定視窗完成操作
echo  完成後瀏覽器會自動開啟
echo ============================================
echo.

:startup

:: ─── Step 1: 開啟 openminiclaw.bat（等完成）─
echo [*] 開啟安裝/設定視窗...
start /w "Miniclaw-Setup" "%BAT_PATH%"

:: ─── Step 2: 確認 node.exe 在跑 ────────────
echo [*] 確認 server 狀態...
tasklist /fi "imagename eq node.exe" 2>nul | find /i "node.exe" >nul
if %errorlevel% neq 0 (
    echo [!] node.exe 未偵測到，5 秒後重試...
    timeout /t 5 /nobreak >nul
    goto :startup
)
echo [OK] node.exe 確認執行中
echo.

:: ─── Step 3: 啟動 ngrok 隧道 ────────────────
echo [*] 啟動 ngrok 隧道...
set "NGROK_CMD="

where ngrok >nul 2>&1
if %errorlevel% equ 0 (
    set "NGROK_CMD=ngrok"
    goto :start_ngrok
)
if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\ngrok.exe" (
    set "NGROK_CMD=%LOCALAPPDATA%\Microsoft\WinGet\Links\ngrok.exe"
    goto :start_ngrok
)
for /d %%D in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\ngrok*") do (
    if exist "%%D\ngrok.exe" set "NGROK_CMD=%%D\ngrok.exe"
)

:start_ngrok
if not defined NGROK_CMD (
    echo [*] 找不到 ngrok，以本地模式繼續
    goto :open_browser
)
:: 確認 authtoken 有設定才啟動隧道
ngrok config check >nul 2>&1
if !errorlevel! equ 0 (
    start /b "" "!NGROK_CMD!" http 3000 >nul 2>&1
    timeout /t 3 /nobreak >nul
    echo [OK] ngrok 隧道已啟動
) else (
    echo [*] ngrok 尚未設定 authtoken，跳過隧道（本地模式）
)

:: ─── Step 4: 開啟瀏覽器 ─────────────────────
:open_browser
echo [*] 開啟瀏覽器...
start /b "" cmd /c "start https://eric0724.github.io/agent/miniclaw/miniclaw-web/index.html"
echo.

:: ─── Step 5: 監控模式 ───────────────────────
echo ============================================
echo  ^>^> Miniclaw 執行中
echo  監控 node.exe 每 5 秒一次
echo  關閉此視窗以停止所有服務
echo ============================================
echo.

:monitor_loop
timeout /t 5 /nobreak >nul
tasklist /fi "imagename eq node.exe" 2>nul | find /i "node.exe" >nul
if %errorlevel% neq 0 (
    echo [!] node.exe 已停止！清理並重新啟動...
    taskkill /f /im ngrok.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    goto :startup
)
goto :monitor_loop