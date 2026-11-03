﻿﻿@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================
echo   小龍蝦本地 AI 設定程式
echo ============================================
echo.

:: ============================================
:: Step 1: 檢查 / 安裝 Ollama
:: ============================================
echo [1/3] 檢查 Ollama 是否已安裝...
where ollama >nul 2>&1
if %errorlevel% equ 0 (
  echo [OK] Ollama 已安裝，跳過下載。
  goto :start_service
)

echo [!] 未偵測到 Ollama，正在透過 winget 自動安裝...
echo     （約 1GB，請耐心等候）
winget install Ollama.Ollama --accept-source-agreements --accept-package-agreements
if %errorlevel% neq 0 (
  echo.
  echo [X] winget 安裝失敗。
  echo     請手動前往 https://ollama.com/download 下載安裝後再執行此腳本。
  pause
  exit /b 1
)
echo [OK] Ollama 安裝完成。

:: 刷新 PATH
for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYS_PATH=%%B"
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USR_PATH=%%B"
if defined SYS_PATH (
  if defined USR_PATH (
    set "PATH=!SYS_PATH!;!USR_PATH!"
  ) else (
    set "PATH=!SYS_PATH!"
  )
)

:: ============================================
:: Step 2: 啟動 Ollama 服務
:: ============================================
:start_service
echo.
echo [2/3] 啟動 Ollama 服務...
start /b ollama serve >nul 2>&1
timeout /t 3 /nobreak >nul

:: ============================================
:: Step 3: 查詢已有模型 + 顯示選單
:: ============================================
echo [3/3] 查詢目前已有的模型...
echo.

:: 取得已有模型清單
set "HAVE_MODELS=0"
set "MODEL_COUNT=0"

for /f "skip=1 tokens=1" %%M in ('ollama list 2^>nul') do (
  set /a MODEL_COUNT+=1
  set "EXISTING_!MODEL_COUNT!=%%M"
  set "HAVE_MODELS=1"
)

echo ============================================
echo   請選擇要使用的本地 AI 模型
echo ============================================
echo.

set "OPTION=0"

if !HAVE_MODELS! equ 1 (
  echo === 您已擁有的模型 ===
  for /l %%i in (1,1,!MODEL_COUNT!) do (
    set /a OPTION+=1
    set "MENU_!OPTION!=!EXISTING_%%i!"
    echo   [!OPTION!] !EXISTING_%%i!
  )
  echo.
)

echo === 建議下載（免費 / 輕量）===
set /a OPTION+=1
set "REC1=!OPTION!"
set "MENU_!OPTION!=gemma3:4b"
echo   [!OPTION!] gemma3:4b         （約 3GB，平衡速度與品質，推薦 ⭐）

set /a OPTION+=1
set "REC2=!OPTION!"
set "MENU_!OPTION!=qwen2.5:7b"
echo   [!OPTION!] qwen2.5:7b        （約 4.7GB，中文能力強）

set /a OPTION+=1
set "REC3=!OPTION!"
set "MENU_!OPTION!=llama3.2:3b"
echo   [!OPTION!] llama3.2:3b       （約 2GB，速度快）

set /a OPTION+=1
set "REC4=!OPTION!"
set "MENU_!OPTION!=phi4-mini:3.8b"
echo   [!OPTION!] phi4-mini:3.8b    （約 2.5GB，推理能力佳）

echo.
echo ============================================
set /p "CHOICE=  請輸入數字選擇（按 Enter 取消）: "

if "!CHOICE!"=="" (
  echo.
  echo [*] 已取消，Ollama 服務保持運行中。
  goto :end
)

:: 驗證輸入是數字且在範圍內
set "SELECTED_MODEL="
for /l %%i in (1,1,!OPTION!) do (
  if "!CHOICE!"=="%%i" set "SELECTED_MODEL=!MENU_%%i!"
)

if "!SELECTED_MODEL!"=="" (
  echo [X] 無效的選項，請重新執行並輸入正確數字。
  pause
  exit /b 1
)

echo.
echo [OK] 已選擇：!SELECTED_MODEL!

:: 判斷是否需要下載（已有模型直接跳過）
set "NEED_PULL=1"
for /l %%i in (1,1,!MODEL_COUNT!) do (
  if "!SELECTED_MODEL!"=="!EXISTING_%%i!" set "NEED_PULL=0"
)

if !NEED_PULL! equ 0 (
  echo [OK] 此模型已在本機，無需下載！
  goto :save_and_done
)

echo.
echo [下載] 正在下載 !SELECTED_MODEL!...
echo        （依模型大小可能需要數分鐘，請耐心等候）
ollama pull !SELECTED_MODEL!
if %errorlevel% neq 0 (
  echo.
  echo [X] 模型下載失敗，請確認網路連線後重試。
  pause
  exit /b 1
)
echo [OK] 模型下載完成！

:: ============================================
:: 儲存選擇的模型名稱供 Miniclaw 讀取
:: ============================================
:save_and_done
echo !SELECTED_MODEL! > "%~dp0app\local_model.txt"

:: ============================================
:: 完成提示
:: ============================================
:end
echo.
echo ============================================
echo   完成！
echo.
echo   模型：!SELECTED_MODEL!  已就緒
echo   Ollama 服務運行於 http://localhost:11434
echo.
echo   ✅ 現在請回到小龍蝦網頁，
echo      點「我裝好了，偵測看看！」按鈕即可繼續。
echo ============================================
echo.
pause
exit /b 0
