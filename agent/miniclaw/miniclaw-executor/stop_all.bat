﻿@echo off
chcp 65001 >nul
echo ============================================
echo   Miniclaw - 停止所有服務
echo ============================================
echo.
echo [1/3] 停止 node.exe...
taskkill /f /im node.exe >nul 2>&1
if %errorlevel% equ 0 (echo [OK] node.exe 已停止) else (echo [*] node.exe 未在執行)
echo.
echo [2/3] 停止 ngrok.exe...
taskkill /f /im ngrok.exe >nul 2>&1
if %errorlevel% equ 0 (echo [OK] ngrok.exe 已停止) else (echo [*] ngrok.exe 未在執行)
echo.
echo [3/3] 停止 ollama serve...
taskkill /f /im ollama.exe >nul 2>&1
if %errorlevel% equ 0 (echo [OK] ollama.exe 已停止) else (echo [*] ollama.exe 未在執行)
echo.
echo ============================================
echo   完成！所有服務已停止。
echo ============================================
echo.
pause
