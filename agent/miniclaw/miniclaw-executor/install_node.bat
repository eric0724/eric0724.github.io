@echo off
chcp 65001 >nul
title Installing Node.js for Miniclaw...
echo ============================================
echo  📦 正在安裝 Node.js ...
echo ============================================
echo.
winget install OpenJS.NodeJS
echo.
if %errorlevel% neq 0 (
    echo [X] 安裝失敗，請手動至 https://nodejs.org 下載
    pause
    exit /b 1
)
echo [OK] Node.js 安裝完成！
echo 請關閉此視窗。
pause
exit /b 0