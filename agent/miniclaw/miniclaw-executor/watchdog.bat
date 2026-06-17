@echo off
setlocal enabledelayedexpansion

:: ============================================
:: Miniclaw Watchdog v4 — 純依賴檢查 + 啟動
:: ============================================
::  只檢查 Node.js 和 ngrok 是否已安裝
::  用 timeout 等固定秒數 + where 檢查
::  不監控進程，不安裝，單純啟動
:: ============================================

set "ROOT=%~dp0"
set "BAT_PATH=%ROOT%openminiclaw.bat"

echo ============================================
echo  🦞 Miniclaw Watchdog v4 啟動管理員
echo ============================================
echo  1. 檢查 Node.js
echo  2. 檢查 ngrok
echo  3. 啟動 Miniclaw
echo ============================================
echo.

:: ─── 步驟 1：檢查 Node.js ────────────────
echo [1/3] 檢查 Node.js...
where node >nul 2>&1
if !errorlevel! neq 0 (
    echo [!] Node.js 尚未安裝，正在安裝...
    start /min "" "%ROOT%install_node.bat"
    echo [*] 等待 30 秒讓安裝完成...
    timeout /t 30 /nobreak >nul
    
    :: 再次檢查
    where node >nul 2>&1
    if !errorlevel! neq 0 (
        echo [X] Node.js 似乎尚未安裝完成
        echo     請關閉安裝視窗後重新執行 watchdog.bat
        pause
        exit /b 1
    )
)
for /f "tokens=*" %%i in ('where node') do echo [OK] Node.js：%%i
echo.

:: ─── 步驟 2：檢查 ngrok ──────────────────
echo [2/3] 檢查 ngrok...
where ngrok >nul 2>&1
if !errorlevel! neq 0 (
    :: 也檢查 winget 安裝路徑
    set NGROK_FOUND=0
    if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\ngrok.ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" set NGROK_FOUND=1
    if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" set NGROK_FOUND=1
    
    if !NGROK_FOUND! equ 0 (
        echo [!] ngrok 尚未安裝，正在安裝...
        start /min "" "%ROOT%install_ngrok.bat"
        echo [*] 等待 30 秒讓安裝完成...
        timeout /t 30 /nobreak >nul
        
        :: 再次檢查 PATH 或 winget 路徑
        where ngrok >nul 2>&1
        if !errorlevel! equ 0 (
            set NGROK_FOUND=1
        ) else (
            if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\ngrok.ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" set NGROK_FOUND=1
            if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" set NGROK_FOUND=1
        )
        
        if !NGROK_FOUND! equ 0 (
            echo [X] ngrok 似乎尚未安裝完成
            echo     請關閉安裝視窗後重新執行 watchdog.bat
            pause
            exit /b 1
        )
    )
)
if !NGROK_FOUND! equ 1 (
    echo [OK] ngrok：已透過 winget 安裝
) else (
    for /f "tokens=*" %%i in ('where ngrok') do echo [OK] ngrok：%%i
)
echo.

:: ─── 步驟 3：啟動 ────────────────────────
echo [3/3] 啟動 Miniclaw...
echo.
start "" cmd /c ""%BAT_PATH%" & pause"
echo [OK] 已啟動！
echo.
echo  你可以關閉此視窗。
pause
exit /b 0