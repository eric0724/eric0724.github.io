@echo off
cd /d "%~dp0"
pip install pyautogui Pillow --quiet
py scripts\teach_and_run.py
pause
