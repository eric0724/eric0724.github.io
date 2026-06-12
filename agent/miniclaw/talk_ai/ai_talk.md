# Miniclaw AI 對話紀錄

> 每次新對話開始時請先讀此檔。

---

## 一、當前任務目標

Miniclaw（小龍蝦）：一個讓玩家透過自然語言指令操控電腦的 AI 助手系統。

### 已完成里程碑
- **Web UI**：四折疊面板（Google/API Key/Ollama/手動）+ 通行解耦
- **手動模式**：FILE 標籤解析 → WebSocket multi-file-write
- **DPI 偵測**：三重備援（shcore → GDI → 註冊表），Mac/Linux 自動跳過
- **校準系統**：calibrate.py — AI 找位置 → 截 normal/hover 範本 → 點擊前後確認 → 降級手動校準
- **自動化腳本**：recorder.py（錄製）+ auto_run.py（執行）+ safe_locate.py（防崩潰）
- **架構**：run/talk 分流 + 三層日誌（ai_talk.md / chat_history.txt / 雲端）

### 下一步
- 校準流程實測優化（提示詞精度、重試策略）
- 整合 test-lab 到 Miniclaw 主系統

---

## 二、Agent 互動規則（兩大模式）

### Act Mode（實作模式）
**回答：** 簡短精簡  
**先說明後動手：** 每次先說明問題解法，等使用者說 OK 再改程式碼  
**一次一問題：** 多個問題時一次只解決一個，確認後再處理下一個  
**步驟限制：** 每次最多 3 個「重操作」（讀大檔 >500行、寫檔、執行指令），超過就等待 30 秒再繼續（PowerShell 用 `Start-Sleep -Seconds 30`，Python 用 `time.sleep(30)`）  
**不准自作主張：** 只改指定檔案，不碰不相關的程式碼  
**時間戳：** 改程式後更新 `index.html` 底部時間戳（`Get-Date -Format "yyyy-MM-dd HH:mm" -TimeZone "Asia/Taipei"`）

### Plan Mode（規劃模式）
**先說明後動手：** 先規劃方案，等確認後才進 Act Mode 實作  
**一次一問題：** 不跳步驟，不預先實作未確認的改動

### Git 規則
- **GO：** 繼續上次未完成的工作，不 push
- **GOGO：** 做完 → 更新 ai_talk.md → 才 push
- **Git 指令：** `"C:\Program Files\Git\bin\git.exe"`
- **Repo：** `https://github.com/eric0724/eric0724.github.io.git`
- **Pull 後：** 必須先讀 ai_talk.md 了解背景再繼續

### 紀錄規則
- 每次對話結束補一行 `[YYYY-MM-DD HH:MM] 關鍵字 | 關鍵字`（有改程式才記）
- ai_talk.md 路徑：`_github_clone/agent/miniclaw/talk_ai/ai_talk.md`

---

## 三、技術堆疊與禁忌

### 技術堆疊
| 層級 | 技術 |
|------|------|
| **前端** | HTML + CSS + client.js（深色主題、折疊面板） |
| **後端** | server.js（Node.js + WebSocket + Express） |
| **AI** | Google Gemini / OpenAI GPT-4o / OpenRouter / Ollama（本地） |
| **自動化** | Python（pyautogui + Pillow + pynput） |
| **隧道** | ngrok（authtoken 必要） |
| **校準** | calibrate.py（GPT-4o Vision 2× 放大 + 降級手動） |

### 禁忌
- **不准刪除規則**：ai_talk.md 的規則區塊和架構紀錄不可刪除
- **不准 push**：只有 GOGO 或明確說「上傳 GitHub」才能 push
- **不准改不相關檔案**：只改使用者指定的檔案
- **不准跳過程式審查**：先說明方案，確認後才動手
- **ngrok 不自動 update**：防毒會誤判，改提示玩家手動更新
- **OCR 不用於桌面偵測**：torch 太重，改用 os.path 或圖案比對

### Codex 安裝
玩家提到 codex = OpenAI Codex CLI：
- `powershell -ExecutionPolicy ByPass -c "irm https://chatgpt.com/codex/install.ps1 | iex"`
- 或 `npm install -g @openai/codex`

---

## 對話紀錄（最近 10 筆）

[2026-06-05 17:29-18:30] Google OAuth token同步+API餘額燈號+OpenRouter整合
[2026-06-08 09:48-15:00] run/talk分流實作 | 日誌架構實作 | API餘額自動檢查 | API類型下拉選單
[2026-06-09 10:00-12:13] auto_run.py+safe_locate模組 | OpenRouter provider | 功能長條區+手動轉接DOM | GOGO push
[2026-06-10 11:53] Step1 UI折疊面板 | 手動模式FILE標籤 | DPI三重備援 | 多檔案後端 | GOGO push (38e6283)
[2026-06-10 12:24] calibrate.py：Step D獨立重試+降級手動+提示詞2×放大+解析度注入
[2026-06-10 12:35] ai_talk.md精簡為三大區塊 | 跨平台等待修正 | GOGO push
[2026-06-12 10:28] 新增startup_tips.md（開頭筆記本提示）| openminiclaw.bat開頭加入啟動指引
[2026-06-12 12:02] 手動模式輸入框青色發光+取消按鈕 | 輸入框預設邊框加亮 | 新增cancelManualMode()
[2026-06-12 12:14] 手動模式輸入框鎖定（避免誤打）| 送出回覆後自動取消手動模式 | processManualAIReply自動恢復
