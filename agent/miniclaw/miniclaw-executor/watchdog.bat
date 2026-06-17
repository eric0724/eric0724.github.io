@echo off
setlocal enabledelayedexpansion

:: ============================================
:: Miniclaw Watchdog v5 — 無限重試啟動模式
:: ============================================
::  不自己做安裝，不檢查 ngrok
::  只做一件事：不斷重試開啟 openminiclaw.bat
::  直到 node.exe 成功啟動為止
::  如果 node.exe 後來停止，也自動重啟
:: ============================================

set "ROOT=%~dp0"
set "BAT_PATH=%ROOT%openminiclaw.bat"

echo ============================================
echo  🦞 Miniclaw Watchdog v5
echo ============================================
echo  自動重試啟動 openminiclaw.bat
echo  直到 node.exe 正常執行
echo ============================================
echo.
echo  提示：第一次執行安裝 Node.js 或 ngrok 時
echo        安裝完成會自動關閉視窗，
echo        Watchdog 會自動再次啟動。
echo        不需要手動關閉任何東西！
echo.

:startup

:: 啟動 openminiclaw.bat（新視窗，不卡住 watchdog）
echo [*] 啟動 openminiclaw.bat...
start "Miniclaw" cmd /c ""%BAT_PATH%""

:: 等待 node.exe 出現（最多等 60 秒）
echo [*] 等待 node.exe 啟動（60 秒內）...
set WAIT=0
:wait_node_start
timeout /t 3 /nobreak >nul
tasklist /fi "imagename eq node.exe" 2>nul | find /i "node.exe" >nul
if !errorlevel! equ 0 (
    echo [OK] node.exe 已啟動！
    goto :monitor
)
set /a WAIT+=3
if !WAIT! geq 60 (
    if exist "%ROOT%installing.flag" (
        echo [*] 偵測到系統正在進行環境安裝，繼續等待...
        set WAIT=0
        goto :wait_node_start
    )
    echo [!] node.exe 未啟動（已等 60 秒且無安裝活動）
    echo     可能是正在安裝，或安裝卡住
    echo     將關閉視窗並重試...
    taskkill /f /fi "WINDOWTITLE eq Miniclaw" >nul 2>&1
    taskkill /f /im node.exe >nul 2>&1
    taskkill /f /im ngrok.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    goto :startup
)
goto :wait_node_start

:: ─── 監控模式 ────────────────────────────
:monitor
echo [*] 進入監控模式，每 5 秒檢查 node.exe...

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

:: 顯示狀態（每 30 秒顯示一次）
set /a COUNT+=1
if !COUNT! geq 6 (
    set COUNT=0
    echo [!TIME!] 監控中：node.exe ✅ 執行中
)

goto :monitor_loop