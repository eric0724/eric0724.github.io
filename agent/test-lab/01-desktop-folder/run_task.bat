@echo off
title Miniclaw Task - Test
cd /d "%~dp0"

echo [Check] Installing dependencies if needed...
pip install pyautogui Pillow pyperclip opencv-python --quiet

echo [Run] Starting task...
py scripts\desktop_folder_check.py

pause
