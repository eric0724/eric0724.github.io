@echo off
title Chrome YT Task
cd /d "%~dp0"

echo [Check] Installing dependencies...
pip install pyautogui Pillow pyperclip opencv-python --quiet

echo.
echo [Step 1] Extracting templates from video...
py make_templates.py
if errorlevel 1 (
    echo [Error] Template extraction failed.
    pause
    exit /b
)

echo.
echo [Step 2] Starting task...
py chrome_yt_task.py

pause
