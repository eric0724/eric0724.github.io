@echo off
setlocal enabledelayedexpansion

:: ============================================
:: Miniclaw Watchdog v3 — 順序安裝 + 啟動
:: ============================================
:: 不再監控進程（避免 ngrok 重啟誤判）
:: 改為順序執行：
::   1. 檢查 Node.js → 沒裝就最小化開 install_node.bat，等它完成
::   2. 檢查 ngrok   → 沒裝就最小化開 install_ngrok.bat，等它完成
::   3. 最後正常啟動 openminiclaw.bat
:: ============================================

set "ROOT=%~dp0"
set "BAT_PATH=%ROOT%openminiclaw.bat"
set "NODE_INSTALLER=%ROOT%install_node.bat"
set "NGROK_INSTALLER=%ROOT%install_ngrok.bat"

echo ============================================
echo  🦞 Miniclaw Watchdog v3 啟動管理員
echo ============================================
echo  步驟 1：檢查 Node.js
echo  步驟 2：檢查 ngrok
echo  步驟 3：啟動 Miniclaw
echo ============================================
echo.

:: ─── 步驟 1：檢查 Node.js ────────────────
echo [1/3] 檢查 Node.js...
where node >nul 2>&1
if !errorlevel! neq 0 (
    echo [!] Node.js 尚未安裝。
    echo [*] 正在最小化開啟安裝視窗...
    echo [*] 安裝完成後請關閉該視窗，Watchdog 會自動繼續。
    echo.
    
    :: 最小化開啟安裝程式
    start /min "" "%NODE_INSTALLER%"
    
    :: 等待 node.exe 出現（表示安裝完成）
    :wait_node_install
        timeout /t 3 /nobreak >nul
        where node >nul 2>&1
    if !errorlevel! neq 0 (
        goto wait_node_install
    )
    echo [OK] Node.js 安裝完成！
    echo.
) else (
    for /f "tokens=*" %%i in ('where node') do set NODE_PATH=%%i
    echo [OK] 已安裝：!NODE_PATH!
    echo.
)

:: ─── 步驟 2：檢查 ngrok ──────────────────
echo [2/3] 檢查 ngrok...
where ngrok >nul 2>&1
if !errorlevel! neq 0 (
    :: 也檢查 winget 安裝路徑
    set NGROK_FOUND=0
    if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" set NGROK_FOUND=1
    if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\ngrok.ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" set NGROK_FOUND=1
    
    if !NGROK_FOUND! equ 0 (
        echo [!] ngrok 尚未安裝。
        echo [*] 正在最小化開啟安裝視窗...
        echo [*] 安裝完成後請關閉該視窗，Watchdog 會自動繼續。
        echo.
        
        :: 最小化開啟安裝程式
        start /min "" "%NGROK_INSTALLER%"
        
        :: 等待 ngrok.exe 出現
        :wait_ngrok_install
            timeout /t 3 /nobreak >nul
            where ngrok >nul 2>&1
            if !errorlevel! neq 0 (
                :: 也檢查 winget 安裝路徑
                if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" set NGROK_FOUND=1
                if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\ngrok.ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" set NGROK_FOUND=1
                if !NGROK_FOUND! equ 1 goto :ngrok_installed
            )
        goto wait_ngrok_install
        
        :ngrok_installed
        echo [OK] ngrok 安裝完成！
        echo.
    ) else (
        echo [OK] ngrok 已透過 winget 安裝。
        echo.
    )
) else (
    for /f "tokens=*" %%i in ('where ngrok') do set NGROK_PATH=%%i
    echo [OK] 已安裝：!NGROK_PATH!
    echo.
)

:: ─── 步驟 3：啟動 Miniclaw ───────────────
echo [3/3] 所有依賴已就緒，啟動 Miniclaw...
echo.
echo ============================================
echo  🚀 正在開啟 openminiclaw.bat
echo  完成後可關閉此 Watchdog 視窗
echo ============================================
echo.

:: 直接開啟 openminiclaw.bat（正常視窗，可以看到 ngrok 輸入）
start "" cmd /c ""%BAT_PATH%" & pause"

echo [OK] 已啟動，Watchdog 任務完成！
echo.
echo  你可以隨時關閉此視窗，不影響 Miniclaw 運作。
echo.
pause
exit /b 0