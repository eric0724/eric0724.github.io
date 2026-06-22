@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo  小龍蝦本地 AI 安裝程式 (Ollama + gemma3:3b)
echo ============================================
echo.

echo [1/3] 檢查 Ollama 是否已安裝...
where ollama >nul 2>&1
if %errorlevel% equ 0 (
  echo [OK] Ollama 已安裝，跳過下載。
  goto :pull_model
)

echo [!] 未偵測到 Ollama，正在透過 winget 自動安裝...
winget install Ollama.Ollama --accept-source-agreements --accept-package-agreements
if %errorlevel% neq 0 (
  echo [X] winget 安裝失敗，請手動前往 https://ollama.com/download 下載安裝後再執行此腳本。
  pause
  exit /b 1
)
echo [OK] Ollama 安裝完成。

:pull_model
echo.
echo [2/3] 啟動 Ollama 服務...
start /b ollama serve
timeout /t 3 /nobreak >nul

echo [3/3] 下載 gemma3:3b 模型（約 2GB，請耐心等候）...
ollama pull gemma3:3b
if %errorlevel% neq 0 (
  echo [X] 模型下載失敗，請確認網路連線後重試。
  pause
  exit /b 1
)

echo.
echo ============================================
echo  [OK] 本地 AI 安裝完成！
echo  模型：gemma3:3b 已就緒
echo  回到小龍蝦網頁，點「偵測本地 AI」即可使用。
echo ============================================
echo.
pause
