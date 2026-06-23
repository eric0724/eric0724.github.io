@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================
:: Miniclaw Watchdog v6 — 全新啟動流程
:: ============================================
::  1. 啟動 openminiclaw.bat（安裝 Node.js + 啟動 server）
::  2. 等待 node.exe 啟動
::  3. 啟動 setup_ngrok.bat（新視窗讓玩家設定 ngrok + API key）
::  4. 等待 setup_ngrok.bat 關閉（玩家完成設定）
::  5. 啟動 ngrok 隧道
::  6. 開啟瀏覽器
::  7. 監控 node.exe，停止就重啟
:: ============================================

set "ROOT=%~dp0"
set "BAT_PATH=%ROOT%openminiclaw.bat"
set "SETUP_PATH=%ROOT%setup_ngrok.bat"

echo ============================================
echo  🦞 Miniclaw Watchdog v6
echo ============================================
echo  自動啟動 server 及設定 ngrok/API
echo ============================================
echo.
echo  提示：第一次執行會先安裝必要元件
echo        安裝完成後會開啟設定視窗
echo        請在設定視窗中輸入 ngrok authtoken 和 API Key
echo ============================================
echo.

:startup

:: ─── Step 1: 啟動 openminiclaw.bat ────────
echo [*] 啟動 openminiclaw.bat...
start "Miniclaw-Server" "%BAT_PATH%"

:: ─── Step 2: 等待 node.exe ────────────────
echo [*] 等待 node.exe 啟動（60 秒內）...
set WAIT=0
:wait_node_start
timeout /t 3 /nobreak >nul
if exist "%ROOT%install_error.flag" (
    echo.
    echo ============================================
    echo  [X] 偵測到關鍵安裝錯誤
    echo      請參考已開啟的說明文件手動處理。
    echo ============================================
    echo 5秒後自動關閉...
    timeout /t 5 /nobreak >nul
    exit /b 1
)
tasklist /fi "imagename eq node.exe" 2>nul | find /i "node.exe" >nul
if !errorlevel! equ 0 (
    echo [OK] node.exe 已啟動！
    goto :setup_ngrok_step
)
set /a WAIT+=3
if !WAIT! geq 60 (
    if exist "%ROOT%installing.flag" (
        echo [*] 偵測到系統正在進行環境安裝，繼續等待...
        set WAIT=0
        goto :wait_node_start
    )
    echo [!] node.exe 未啟動（已等 60 秒）
    echo     將關閉視窗並重試...
    taskkill /f /fi "WINDOWTITLE eq Miniclaw-Server" >nul 2>&1
    taskkill /f /im node.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    goto :startup
)
goto :wait_node_start

:: ─── Step 3: 啟動 setup_ngrok.bat ──────
:setup_ngrok_step
echo.
echo [*] 開啟設定視窗（ngrok + API Key）...
echo     請完成設定後關閉該視窗，watchdog 會繼續。
echo.
start /w "Miniclaw-Setup" "%SETUP_PATH%"

:: ─── Step 4: 啟動 ngrok 隧道 ────────────
echo [*] 啟動 ngrok 隧道...
where ngrok >nul 2>&1
if %errorlevel% equ 0 (
    ngrok config check >nul 2>&1
    if !errorlevel! equ 0 (
        start /b "" ngrok http 3000 >nul 2>&1
        echo [OK] ngrok 已啟動
    ) else (
        echo [*] ngrok 尚未設定 authtoken，跳過隧道
    )
) else (
    echo [*] ngrok 未安裝，跳過隧道
)

:: ─── Step 5: 開啟瀏覽器 ────────────────
echo [*] 正在開啟網頁...
start /b "" cmd /c "start https://eric0724.github.io/agent/miniclaw/miniclaw-web/index.html"

:: ─── Step 6: 監控模式 ──────────────────
:monitor
echo.
echo [*] 進入監控模式，每 5 秒檢查 node.exe...
echo.
echo  ============================================
echo   Miniclaw is running.
echo   Close this window to stop all services.
echo  ============================================

:monitor_loop
timeout /t 5 /nobreak >nul

:: 檢查 node.exe
tasklist /fi "imagename eq node.exe" 2>nul | find /i "node.exe" >nul
if !errorlevel! neq 0 (
    echo [!] node.exe 已停止！
    echo     將清理並重新啟動...
    taskkill /f /im ngrok.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    goto :startup
)

goto :monitor_loop