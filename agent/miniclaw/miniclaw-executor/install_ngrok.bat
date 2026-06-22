@echo off
chcp 65001 >nul
title Installing ngrok for Miniclaw...
echo ============================================
echo  📦 正在安裝 ngrok ...
echo ============================================
echo.
winget install ngrok.ngrok
echo.
if %errorlevel% neq 0 (
    echo [X] 安裝失敗，請手動至 https://ngrok.com/download 下載
    pause
    exit /b 1
)
echo [OK] ngrok 安裝完成！
echo 請關閉此視窗，Watchdog 會自動繼續。
pause
exit /b 0