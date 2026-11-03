@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================
echo   Miniclaw 卸載程式
echo ============================================
echo.
echo 請選擇要執行的項目（可輸入多個數字，空格分隔）：
echo.
echo   [1] 停止所有服務（node / ngrok / ollama）
echo   [2] 刪除下載的核心檔案（server.js / skills_manager.js / platform/）
echo   [3] 卸載 Node.js
echo   [4] 卸載 ngrok
echo   [5] 卸載 Ollama（注意：會同時刪除所有模型！）
echo   [6] 僅刪除 Ollama 模型（保留 Ollama 本體）
echo   [0] 全部執行（1~5）
echo.
echo ============================================
set /p "CHOICES=  請輸入數字（例如 1 2 3）: "

if "!CHOICES!"=="" goto :end

:: 解析選項
set "DO_STOP=0"
set "DO_FILES=0"
set "DO_NODE=0"
set "DO_NGROK=0"
set "DO_OLLAMA=0"
set "DO_MODELS=0"

for %%c in (!CHOICES!) do (
  if "%%c"=="0" ( set "DO_STOP=1" & set "DO_FILES=1" & set "DO_NODE=1" & set "DO_NGROK=1" & set "DO_OLLAMA=1" )
  if "%%c"=="1" set "DO_STOP=1"
  if "%%c"=="2" set "DO_FILES=1"
  if "%%c"=="3" set "DO_NODE=1"
  if "%%c"=="4" set "DO_NGROK=1"
  if "%%c"=="5" set "DO_OLLAMA=1"
  if "%%c"=="6" set "DO_MODELS=1"
)

echo.

:: [1] 停止服務
if !DO_STOP! equ 1 (
  echo [1] 停止所有服務...
  taskkill /f /im node.exe >nul 2>&1
  taskkill /f /im ngrok.exe >nul 2>&1
  taskkill /f /im ollama.exe >nul 2>&1
  echo [OK] 服務已停止
  echo.
)

:: [2] 刪除核心檔案
if !DO_FILES! equ 1 (
  echo [2] 刪除下載的核心檔案...
  set "APP=%~dp0app"
  if exist "!APP!\server.js" del /f "!APP!\server.js" && echo [OK] server.js 已刪除
  if exist "!APP!\miniclaw-runner.js" del /f "!APP!\miniclaw-runner.js" && echo [OK] miniclaw-runner.js 已刪除
  if exist "!APP!\skills_manager.js" del /f "!APP!\skills_manager.js" && echo [OK] skills_manager.js 已刪除
  if exist "!APP!\platform" rd /s /q "!APP!\platform" && echo [OK] platform/ 已刪除
  if exist "!APP!\local_model.txt" del /f "!APP!\local_model.txt" && echo [OK] local_model.txt 已刪除
  echo.
)

:: [3] 卸載 Node.js
if !DO_NODE! equ 1 (
  echo [3] 卸載 Node.js...
  winget uninstall OpenJS.NodeJS --accept-source-agreements >nul 2>&1
  echo [OK] Node.js 卸載完成
  echo.
)

:: [4] 卸載 ngrok
if !DO_NGROK! equ 1 (
  echo [4] 卸載 ngrok...
  winget uninstall ngrok.ngrok --accept-source-agreements >nul 2>&1
  echo [OK] ngrok 卸載完成
  echo.
)

:: [5] 卸載 Ollama
if !DO_OLLAMA! equ 1 (
  echo [5] 卸載 Ollama...
  winget uninstall Ollama.Ollama --accept-source-agreements >nul 2>&1
  echo [OK] Ollama 卸載完成（含所有模型）
  echo.
)

:: [6] 僅刪除模型
if !DO_MODELS! equ 1 (
  echo [6] 刪除 Ollama 模型...
  for /f "skip=1 tokens=1" %%M in ('ollama list 2^>nul') do (
    echo     刪除模型：%%M
    ollama rm %%M >nul 2>&1
  )
  echo [OK] 模型清除完成
  echo.
)

:end
echo ============================================
echo   完成！
echo ============================================
echo.
pause
exit /b 0