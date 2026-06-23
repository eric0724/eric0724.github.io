@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
set "ROOT=%~dp0"
set "NGROK_GUIDE=%ROOT%docs\ngrok_update_guide.md"

echo ============================================
echo  🦞 Miniclaw - ngrok 與 API 設定
echo ============================================
echo.
echo  這個視窗會幫你設定：
echo  1. 檢查/更新 ngrok
echo  2. 設定 ngrok authtoken（遠端連線用）
echo  3. 設定 API Key（AI 對話用）
echo.
echo  完成後請關閉此視窗，watchdog 會繼續啟動。
echo ============================================
echo.

:: ─── Step 1: 檢查 ngrok ──────────────────
echo [Step 1/3] 檢查 ngrok...
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
  echo.
  echo  [!] ngrok 未安裝或不在 PATH 中。
  echo.
  echo  請選擇：
  echo   1 - 用 winget 安裝 ngrok（推薦）
  echo   2 - 我已經下載了，手動設定
  echo   3 - 跳過 ngrok（僅本地連線）
  echo.
  set /p NGROK_CHOICE="請輸入 1/2/3: "
  
  if "!NGROK_CHOICE!"=="1" (
    echo [*] 正在安裝 ngrok...
    winget install ngrok.ngrok --accept-source-agreements --accept-package-agreements
    if !errorlevel! neq 0 (
      echo [X] 安裝失敗，請手動下載：https://ngrok.com/download
      pause
    ) else (
      echo [OK] ngrok 安裝完成！
    )
  ) else if "!NGROK_CHOICE!"=="2" (
    echo [*] 請手動將 ngrok.exe 複製到系統 PATH 中
    echo     或放到與 start_watch.bat 相同的資料夾
    pause
  ) else (
    echo [*] 跳過 ngrok 設定
    goto :step_api
  )
) else (
  echo [OK] ngrok 已安裝
)

:: ─── Step 2: 設定 ngrok authtoken ────────
:step_authtoken
echo.
echo [Step 2/3] 設定 ngrok authtoken...
echo.
echo  需要 ngrok authtoken 才能使用遠端連線。
echo  請前往 https://dashboard.ngrok.com/get-started/your-authtoken
echo  登入後複製你的 authtoken（以 ngrok_ 開頭）
echo.
start /b "" cmd /c "start https://dashboard.ngrok.com/get-started/your-authtoken"
start /b "" notepad.exe "%NGROK_GUIDE%"
echo.
set /p NGROK_TOKEN="請輸入 ngrok authtoken（或直接按 Enter 跳過）: "
if not "!NGROK_TOKEN!"=="" (
  echo [!] 正在設定 authtoken...
  ngrok config add-authtoken !NGROK_TOKEN!
  if !errorlevel! equ 0 (
    echo [OK] ngrok authtoken 設定完成！
  ) else (
    echo [X] authtoken 設定失敗
  )
) else (
  echo [*] 跳過 authtoken 設定
)

:: ─── Step 3: 設定 API Key ────────────────
:step_api
echo.
echo [Step 3/3] 設定 API Key（選填）...
echo.
echo  如果要使用 AI 對話功能，需要 API Key。
echo  請前往 https://aistudio.google.com/apikey 取得 Gemini API Key
echo.
start /b "" cmd /c "start https://aistudio.google.com/apikey"
echo.
set /p API_KEY="請輸入 Gemini API Key（或直接按 Enter 跳過）: "
if not "!API_KEY!"=="" (
  echo [!] 正在儲存 API Key...
  :: 寫入到 app 目錄下的 .env 檔案供 server.js 讀取
  echo GEMINI_API_KEY=!API_KEY! > "%ROOT%app\.env"
  echo [OK] API Key 已儲存！
) else (
  echo [*] 跳過 API Key 設定
)

:: ─── 完成 ────────────────────────────────
echo.
echo ============================================
echo  ✅ 設定完成！
echo.
echo  你可以關閉此視窗了。
echo  watchdog 會自動啟動 ngrok 並開啟瀏覽器。
echo ============================================
echo.
pause
exit /b 0