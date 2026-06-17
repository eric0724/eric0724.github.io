@echo off
setlocal enabledelayedexpansion

:: ============================================
:: Miniclaw Watchdog — 自動偵測與重啟守護程式
:: ============================================
:: 功能：監控 openminiclaw.bat 啟動的服務
::       若 node.exe 或 ngrok.exe 意外終止，
::       自動重新啟動 openminiclaw.bat
:: ============================================

set "ROOT=%~dp0"
set "APP_DIR=%ROOT%app"
set "BAT_PATH=%ROOT%openminiclaw.bat"

:: 設定：最大重啟次數（避免無限循環）
set MAX_RESTART=10
set RESTART_COUNT=0

:: 設定：檢查間隔（秒）
set CHECK_INTERVAL=10

:: 設定：重啟前等待（秒）
set RESTART_DELAY=5

echo ============================================
echo  🦞 Miniclaw Watchdog 守護程式
echo ============================================
echo  監控服務：node.exe + ngrok.exe
echo  檢查間隔：%CHECK_INTERVAL% 秒
echo  最大重啟：%MAX_RESTART% 次
echo  重啟延遲：%RESTART_DELAY% 秒
echo ============================================
echo.

:: 檢查 openminiclaw.bat 是否存在
if not exist "%BAT_PATH%" (
    echo [X] 錯誤：找不到 openminiclaw.bat
    echo     路徑：%BAT_PATH%
    echo     請確認 watchdog.bat 與 openminiclaw.bat 在同一目錄。
    pause
    exit /b 1
)

:: 首次啟動
echo [1/!] 正在首次啟動 Miniclaw...
call "%BAT_PATH%"
if !errorlevel! neq 0 (
    echo [!] openminiclaw.bat 回傳錯誤碼：!errorlevel!
    echo     守護程式將嘗試重新啟動...
)

:watch_loop

:: 檢查 node.exe 是否在執行
tasklist /fi "imagename eq node.exe" 2>nul | find /i "node.exe" >nul
set NODE_RUNNING=!errorlevel!

:: 檢查 ngrok.exe 是否在執行
tasklist /fi "imagename eq ngrok.exe" 2>nul | find /i "ngrok.exe" >nul
set NGROK_RUNNING=!errorlevel!

:: 顯示狀態
set TIMESTAMP=%TIME%
if !NODE_RUNNING!==0 (
    set NODE_STATUS=✅ 執行中
) else (
    set NODE_STATUS=❌ 已停止
)
if !NGROK_RUNNING!==0 (
    set NGROK_STATUS=✅ 執行中
) else (
    set NGROK_STATUS=❌ 已停止
)

echo [!TIMESTAMP!] node: !NODE_STATUS!  |  ngrok: !NGROK_STATUS!  |  重啟次數：!RESTART_COUNT!/%MAX_RESTART%

:: 判斷是否需要重啟
:: 條件：node.exe 或 ngrok.exe 任一停止
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
        echo      請手動檢查問題：
        echo      1. 開啟工作管理員，確認 node.exe 是否卡住
        echo      2. 檢查 ngrok 版本是否過舊
        echo      3. 手動執行 openminiclaw.bat 查看錯誤訊息
        echo ============================================
        pause
        exit /b 1
    )
    
    echo.
    echo ============================================
    echo  [%RESTART_COUNT%/%MAX_RESTART%] 正在重新啟動 Miniclaw...
    echo  等待 %RESTART_DELAY% 秒後重啟...
    echo ============================================
    echo.
    
    :: 先清理殘留進程
    echo [*] 清理殘留進程...
    taskkill /f /im node.exe >nul 2>&1
    taskkill /f /im ngrok.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    
    :: 重新啟動
    echo [*] 正在啟動 openminiclaw.bat...
    start "" cmd /c ""%BAT_PATH%""
    
    :: 等待服務啟動
    echo [*] 等待服務啟動（%RESTART_DELAY% 秒）...
    timeout /t %RESTART_DELAY% /nobreak >nul
    
    echo [OK] 重啟完成，繼續監控...
    echo.
)

:: 等待下一次檢查
timeout /t %CHECK_INTERVAL% /nobreak >nul
goto watch_loop