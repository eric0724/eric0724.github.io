@echo off
setlocal enabledelayedexpansion

:: ============================================
:: Miniclaw Watchdog v2 — 自動偵測與重啟守護
:: ============================================
:: 不再用 call 呼叫 openminiclaw.bat（避免被 pause 卡住）
:: 改為 start 新視窗啟動，watchdog 獨立監控進程
:: ============================================

set "ROOT=%~dp0"
set "BAT_PATH=%ROOT%openminiclaw.bat"

:: 設定
set MAX_RESTART=20
set RESTART_COUNT=0
set CHECK_INTERVAL=5
set START_TIMEOUT=60

echo ============================================
echo  🦞 Miniclaw Watchdog v2 守護程式
echo ============================================
echo  監控服務：node.exe + ngrok.exe
echo  檢查間隔：%CHECK_INTERVAL% 秒
echo  最大重啟：%MAX_RESTART% 次
echo ============================================
echo.
echo  [重要] 第一次執行若安裝 Node.js，
echo         安裝完成後會提示「關閉視窗重新執行」。
echo         請直接關閉該視窗，Watchdog 會自動重啟！
echo.

:: 檢查 openminiclaw.bat 是否存在
if not exist "%BAT_PATH%" (
    echo [X] 錯誤：找不到 openminiclaw.bat
    echo     路徑：%BAT_PATH%
    pause
    exit /b 1
)

:: 首次啟動（用 start 新視窗，watchdog 不會被 pause 卡住）
echo [1/!] 首次啟動 Miniclaw...
call :start_miniclaw

:watch_loop

:: 檢查 node.exe 是否在執行
tasklist /fi "imagename eq node.exe" 2>nul | find /i "node.exe" >nul
set NODE_RUNNING=!errorlevel!

:: 檢查 ngrok.exe 是否在執行
tasklist /fi "imagename eq ngrok.exe" 2>nul | find /i "ngrok.exe" >nul
set NGROK_RUNNING=!errorlevel!

:: 顯示狀態
set TIMESTAMP=%TIME%
if !NODE_RUNNING!==0 ( set NODE_STATUS=✅ 執行中 ) else ( set NODE_STATUS=❌ 已停止 )
if !NGROK_RUNNING!==0 ( set NGROK_STATUS=✅ 執行中 ) else ( set NGROK_STATUS=❌ 已停止 )

echo [!TIMESTAMP!] node: !NODE_STATUS!  ^|  ngrok: !NGROK_STATUS!  ^|  重啟次數：!RESTART_COUNT!/%MAX_RESTART%

:: 判斷是否需要重啟
set NEED_RESTART=0

if !NODE_RUNNING! neq 0 (
    echo [!] node.exe 已停止！
    set NEED_RESTART=1
)
if !NGROK_RUNNING! neq 0 (
    echo [!] ngrok.exe 已停止！
    set NEED_RESTART=1
)

if !NEED_RESTART!==1 (
    set /a RESTART_COUNT+=1
    
    if !RESTART_COUNT! gtr %MAX_RESTART% (
        echo.
        echo ============================================
        echo  [X] 已達到最大重啟次數（%MAX_RESTART% 次）
        echo      請手動檢查問題
        echo ============================================
        pause
        exit /b 1
    )
    
    echo.
    echo ============================================
    echo  [%RESTART_COUNT%/%MAX_RESTART%] 正在重新啟動...
    echo ============================================
    echo.
    
    :: 清理殘留進程
    taskkill /f /im node.exe >nul 2>&1
    taskkill /f /im ngrok.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    
    :: 重新啟動
    call :start_miniclaw
    echo.
)

timeout /t %CHECK_INTERVAL% /nobreak >nul
goto watch_loop

:: ─── 啟動 Miniclaw ────────────────────────
:start_miniclaw
    echo [*] 正在啟動 openminiclaw.bat（新視窗）...
    echo [*] 等待服務啟動（最長 %START_TIMEOUT% 秒）...
    
    :: 用 start 新視窗啟動，watchdog 不會被 pause 卡住
    start "Miniclaw" cmd /c ""%BAT_PATH%" & pause"
    
    :: 等待 node.exe 出現（最多 START_TIMEOUT 秒）
    set WAIT_TIME=0
    :wait_loop
        tasklist /fi "imagename eq node.exe" 2>nul | find /i "node.exe" >nul
        if !errorlevel! equ 0 (
            echo [OK] node.exe 已啟動
            goto :wait_done
        )
        timeout /t 1 /nobreak >nul
        set /a WAIT_TIME+=1
        if !WAIT_TIME! geq %START_TIMEOUT% (
            echo [!] node.exe 未在 %START_TIMEOUT% 秒內啟動
            echo    可能是第一次安裝，請關閉安裝視窗，Watchdog 會自動重啟
            goto :wait_done
        )
        goto wait_loop
    :wait_done
    
    exit /b 0