# Miniclaw AI 對話紀錄

> 每次新對話開始時請先讀此檔。

---

## 一、當前任務目標

Miniclaw（小龍蝦）：一個讓玩家透過自然語言指令操控電腦的 AI 助手系統。

### 已完成里程碑
- **Web UI**：手風琴折疊面板（終端/帳號/遠端/AI/對話/外觀/安全）+ 聰明預設開關邏輯 + 通行解耦
- **手動模式**：FILE 標籤解析 → WebSocket multi-file-write
- **DPI 偵測**：三重備援（shcore → GDI → 註冊表），Mac/Linux 自動跳過
- **校準系統**：calibrate.py — AI 找位置 → 截 normal/hover 範本 → 點擊前後確認 → 降級手動校準
- **自動化腳本**：recorder.py（錄製）+ auto_run.py（執行）+ safe_locate.py（防崩潰）
- **架構**：run/talk 分流 + 三層日誌（ai_talk.md / chat_history.txt / 雲端）
- **Skills 技能系統（外掛架構）**：競品原始碼分析（opencode + Codex CLI）| 建立 skills/ 目錄 | 首個技能 click-master（SKILL.md）| 零依賴 skills_manager.js 管理模組 | 盲點評估報告
- **Skills Phase 2 — 架構深化**：內嵌輕量 YAML 解析器（零依賴）| SKILL.md Body 第二層深度載入（getSkillBody）| 技能觸發偵測引擎（detectTriggeredSkills）| 記憶體快取 | SKILLS_PATH 環境變數支援 | server.js 動態注入技能 Body

### 已完成里程碑
- **Skills Phase 3 — 前端可視化**：新增 WebSocket `skills-list` 訊息 | 大廳 accordion 技能背包面板 | 動態渲染技能列表（綠色燈號+120字簡介）| XSS 防護 | grr.md 交接文件更新
- **Skills Phase 4 — 終極自動化**：新增 `executeSkillScript()` 腳本執行橋樑 | `parseSkillTags()` 標籤解析 | server.js 自動攔截 [技能名稱] 並執行 | 60秒超時保護 | 結構化結果回傳 | grr.md 交接文件更新
- **Skills Phase 5 — click-master 腳本實作**：建立 `skills/click-master/scripts/safe_locate.py` 防崩潰模組 | 建立 `run.py` 主腳本（pyautogui + 安全檢查 + 結構化日誌）| 完整整合測試 | grr.md 交接文件更新
- **Skills Phase 6 — calibration-master 技能實作**：建立 `skills/calibration-master/SKILL.md` | 建立 `run.py` 校準腳本（GPT-4o Vision 2×放大 + 三種模式 + JSON持久化 + 自動降級）| grr.md 交接文件更新
- **Skills Phase 7 — test-lab 功能外掛化**：建立 `skills/macro-recorder/`（巨集錄製執行）| 建立 `skills/visual-trail/`（視覺軌跡管理 + 時間衰減 + 熱區分析）| 完整結構化日誌 | grr.md 交接文件更新
- **Skills Phase 8 — gesture-recognizer 手勢識別**：建立 `skills/gesture-recognizer/`（M/W/O/V手勢辨識 + 波峰波谷檢測 + 對稱度計算 + 模板匹配）| grr.md 交接文件更新
- **Skills Phase 9 — 手勢巨集聯動**：server.js 重構 | 手勢辨識成功後自動觸發巨集 | 正則匹配 [MATCHED] M/W/O/V | 防錯機制（巨集不存在友善提示）| grr.md 交接文件更新

### 下一步
- 校準流程實測優化（提示詞精度、重試策略）

---

## 二、Agent 互動規則（兩大模式）

### Act Mode（實作模式）
**回答：** 簡短精簡  
**先說明後動手：** 每次先說明問題解法，等使用者說 OK 再改程式碼  
**一次一問題：** 多個問題時一次只解決一個，確認後再處理下一個  
**步驟限制：** 每次最多 3 個「重操作」（讀大檔 >500行、寫檔、執行指令），超過就等待 30 秒再繼續（PowerShell 用 `Start-Sleep -Seconds 30`，Python 用 `time.sleep(30)`，此規則僅 Kiro Agent 需遵守，其他 Agent 不受限制）  
**不准自作主張：** 只改指定檔案，不碰不相關的程式碼  
**時間戳：** 只要有改程式或重新打包壓縮檔（repack）並上傳 Git，都必須更新 `index.html` 底部時間戳（`Get-Date -Format "yyyy-MM-dd HH:mm" -TimeZone "Asia/Taipei"`）

### Plan Mode（規劃模式）
**先說明後動手：** 先規劃方案，等確認後才進 Act Mode 實作  
**一次一問題：** 不跳步驟，不預先實作未確認的改動



### Git 規則
- **GO：** 繼續上次未完成的工作，不 push
- **GOGO：** 做完 → 更新 ai_talk.md → 才 push
- **Git 指令：** `"C:\Program Files\Git\bin\git.exe"`
- **Repo：** `https://github.com/eric0724/eric0724.github.io.git`
- **Pull 後：** 必須先讀 ai_talk.md 了解背景再繼續

### 提示詞助手（Prompt Assistant）工作流程
玩家現在會使用 **另一個 AI** 來輔助整理與優化提示詞，再將最終版本傳遞給主要執行 AI（你或其他 Agent）進行檔案修改。

**流程說明：**
1. **提示詞助手 AI** — 負責分析需求、整理上下文、規劃修改方案、產出精確的提示詞
2. **執行 AI（你/其他 Agent）** — 收到已整理好的提示詞後，直接進行檔案修改與實作

**注意事項：**
- 提示詞助手 AI 產出的內容可能包含 `SEARCH/REPLACE` 區塊、指令清單或程式碼片段
- 執行 AI 收到這類內容時，應視為已規劃完成，直接執行而非重新規劃
- 如果提示詞中有不清楚的地方，仍可提問確認，但不要推翻已確定的修改方向
- 所有對話仍須遵守本文件的互動規則（步驟限制、時間戳、紀錄規則等）

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
[2026-06-15 11:46] 大廳設定面板手風琴折疊（7個panel）| 智慧預設開關（依連線/API/遠端狀態）| GOGO push (57ba509)
[2026-06-15 12:02] 手風琴收合修復：inline onclick改addEventListener | CSS移除overflow:hidden | display切換邏輯修正 | GOGO push (6dc80ae)
[2026-06-16 10:11] Skills系統外掛實作：競品原始碼分析(opencode+Codex CLI) | 建立skills/click-master/SKILL.md | 建立skills_manager.js | 盲點評估報告 | 產出grr.md交接摘要
[2026-06-16 10:24] Skills Phase2：內嵌YAML解析器 | getSkillBody深度載入 | detectTriggeredSkills引擎 | 記憶體快取 | SKILLS_PATH環境變數 | server.js動態注入技能Body
[2026-06-17 09:23] Skills Phase3：WebSocket skills-list推送 | 大廳accordion技能背包UI | renderSkillsInventory動態渲染 | escapeHtml XSS防護 | grr.md交接文件更新
[2026-06-17 09:31] Skills Phase4：executeSkillScript腳本執行橋樑 | parseSkillTags標籤解析 | server.js自動攔截[技能名稱] | 60秒超時保護 | 結構化結果回傳 | grr.md交接文件更新
[2026-06-17 09:39] Skills Phase5：click-master腳本實作 | safe_locate.py防崩潰模組 | run.py主腳本(pyautogui+安全檢查) | 結構化日誌輸出 | grr.md交接文件更新
[2026-06-17 09:43] Skills Phase6：calibration-master技能實作 | SKILL.md建立 | run.py校準腳本(GPT-4o Vision+三種模式+JSON持久化) | 自動降級機制 | grr.md交接文件更新
[2026-06-17 09:47] Skills Phase7：macro-recorder巨集錄製執行 | visual-trail視覺軌跡管理(時間衰減+熱區分析) | test-lab功能外掛化整合 | grr.md交接文件更新
[2026-06-17 09:56] Skills Phase8：gesture-recognizer手勢識別(M/W/O/V) | 波峰波谷檢測 | 對稱度計算 | 模板匹配算法 | grr.md交接文件更新
[2026-06-17 09:59] Skills Phase9：手勢辨識與巨集自動觸發聯動 | server.js重構 | 正則匹配[MATCHED] | 防錯機制 | grr.md交接文件更新
[2026-06-17 10:09] Skills Phase10：校準流程實測優化 | GPT-4o Vision提示詞強化(邊界防禦+中心點要求) | StepD重試策略(3次+5px偏移) | index.html時間戳更新 | grr.md交接文件更新
[2026-06-17 10:14] Skills Phase11：大廳手勢自動觸發巨集開關 | index.html新增toggleGestureAutoTrigger | client.js WebSocket發送 | server.js全域狀態+開關判斷 | grr.md交接文件更新
[2026-06-17 10:24] Skills Phase12：多技能併發壓力測試與邊界異常防禦 | server.js隊列機制(skillExecutionQueue) | 僵死進程清理(activeProcesses+killChildProcesses) | 60秒超時+SIGKILL | grr.md交接文件更新
[2026-06-17 10:45] Skills Phase13：全局系統驗證與日誌自動滾動清理 | rotateLogIfNeeded(5MB閾值+_bak備份) | performHealthCheck(Python+套件+skills+關鍵檔案) | grr.md交接文件更新
[2026-06-17 11:06] Skills Phase14：系統白皮書與完整操作/外掛開發手冊生成 | 建立USER_GUIDE.md(使用者操作手冊) | 建立DEVELOPER_SKILLS.md(開發者外掛開發手冊) | grr.md交接文件更新
[2026-06-17 12:26] Watchdog與Openminiclaw安裝標記聯動優化 | openminiclaw.bat新增installing.flag | watchdog.bat檢查installing.flag跳過強殺 | index.html時間戳更新 | 執行_repack_local.ps1壓縮 | grr.md交接文件更新
[2026-06-17 12:56] Watchdog與Openminiclaw語法與路徑相容性優化 | 修正openminiclaw.bat括號內雙冒號註解錯誤 | 簡化watchdog.bat啟動指令支援空格與括號路徑 | index.html時間戳更新 | 執行_repack_local.ps1壓縮 | 移除install_error.flag的git追蹤 | grr.md交接文件更新
[2026-06-22 11:09] 特殊功能面板管理與樣式優化 | 執行_repack_local.ps1壓縮與指令路徑通用化 | index.html時間戳與.gitignore規則更新 | GOGO push
[2026-06-22 11:21] 實作語音喚醒與 Web Speech API 整合 | 修正所有批次檔字元編碼亂碼問題 | 重新執行 _repack_local.ps1 壓縮 | GOGO push
[2026-06-22 11:39] 修復 watchdog.bat 因 ngrok 下載/authtoken 互動提示卡住問題 | openminiclaw.bat 跳過 winget install ngrok（改提示手動安裝）| 跳過 authtoken 互動選單（無 token 時直接跳過 ngrok）| ngrok 啟動移除 & pause 避免卡住 | 無 ngrok 時仍可啟動 server 與網頁（local only）
[2026-06-22 12:25] Step1 終端選擇按鈕可點修復 | iOS 不再禁用要終端 | 全域圓角 UI 變數 | 移除重複 const 避免前端載入失敗 | index.html 時間戳更新 | GOGO push
[2026-06-22 12:35] 遊戲助手特殊功能按鈕修復 | showToast 預設 icon 避免 undefined | Step2 tooltip 改向下顯示避免被彈窗裁切
[2026-06-22 12:43] 特殊功能釘選同步修復 | 釘選功能會出現在主操作列 | 取消釘選會從主操作列隱藏 | 避免重複初始化綁定事件
[2026-06-23 10:03] 批次檔自動關閉優化 | 移除pause命令(timeout替代) | install_node/ngrok/local-ai/openminiclaw/watchdog | 執行_repack_local.ps1壓縮 | index.html時間戳更新
[2026-06-23 10:19] openminiclaw.bat新增ngrok authtoken配置流程 | install_ngrok.bat只下載不配置 | watchdog.bat改名為start_watch.bat | 執行_repack_local.ps1壓縮 | index.html時間戳更新
[2026-06-23 10:25] 整理miniclaw-executor目錄結構 | 玩家會用到的啟動檔(openminiclaw/start_watch/start.sh)保留在最外層 | 其他開發/安裝批次檔移至dev資料夾 | 執行_repack_local.ps1壓縮 | index.html時間戳更新
[2026-06-23 10:34] openminiclaw.bat新增ngrok安裝教學 | 未偵測到ngrok時顯示詳細安裝步驟(winget+authtoken) | 玩家可選擇繼續或關閉 | 執行_repack_local.ps1壓縮 | index.html時間戳更新
[2026-06-23 10:57] openminiclaw.bat配置authtoken時自動開啟ngrok網站+更新說明記事本 | 玩家無需手動搜尋說明文件 | 執行_repack_local.ps1壓縮 | index.html時間戳更新
[2026-06-23 11:06] 统一玩家入口为start_watch.bat | index.html更新说明文字(Windows改用start_watch.bat) | 执行_repack_local.ps1压缩 | index.html时间戳更新
[2026-06-23 11:10] 修复openminiclaw.bat中文echo乱码问题 | ngrok未安装提示改为英文 | 自动打开ngrok_update_guide.md记事本 | 执行_repack_local.ps1压缩 | index.html时间戳更新
[2026-06-23 11:20] 更新ngrok_update_guide.md添加PATH说明(三种方法) | openminiclaw.bat增强ngrok检测(常见路径) | 执行_repack_local.ps1压缩 | index.html时间戳更新
[2026-06-23 11:23] openminiclaw.bat自动使用找到的ngrok路径(NGROK_CMD变量) | 执行_repack_local.ps1压缩 | index.html时间戳更新
[2026-06-23 11:31] 修复for /d循环语法错误(添加路径存在检查) | 修复NGROK_FOUND变量比较问题 | 执行_repack_local.ps1压缩 | index.html时间戳更新
[2026-06-23 11:35] 完全重写openminiclaw.bat ngrok检测逻辑(移除for /d循环) | 执行_repack_local.ps1压缩 | index.html时间戳更新
[2026-06-23 11:43] 简化openminiclaw.bat ngrok检测:找不到直接跳过 | 执行_repack_local.ps1压缩 | index.html时间戳更新
[2026-06-23 11:48] 修复启动顺序:openminiclaw.bat不再自动开浏览器 | start_watch.bat确认node.exe启动后才开浏览器 | 执行_repack_local.ps1压缩 | index.html时间戳更新