# 📥 小龍蝦 (Miniclaw) 控制中樞 - 核心架構與檔案關聯圖

本文件作為「小龍蝦」控制中樞的**最高指導架構圖**，定義了所有檔案的職責、關聯性與資料傳遞流向。在後續階段中，我們將基於此骨架逐步實現每一個檔案，您可以隨時返回此文件查閱各模組之間的對接關係。

---

## 📂 專案目錄骨架預覽 (Directory Tree)

我們將在打包區內建立以下純淨結構，劃分為「生產者大龍蝦資源包」與「執行者小龍蝦核心」：

```text
miniclaw/
├── ARCHITECT_MINICLAW.md           # [本文檔] 核心架構與關聯對照表
├── RULES_MINI.md                   # 規範層：開發鐵律與備份修復聲明
├── miniclaw-web/                   # 🖥️ [小龍蝦] 網頁端控制中樞 (Web UI)
│   ├── index.html                  # 網頁主介面、彈出式引導流程、常駐設定面板
│   ├── style.css                   # 霓虹橘色警示風格、毛玻璃質感 UI、全平台響應式樣式
│   └── client.js                   # 前端邏輯：Step 1-5 引導、WebSocket 連線、餘額計算
└── miniclaw-executor/              # ⚙️ [小龍蝦] 本地執行端 (Executor - Full Setup Pack)
    ├── server.js                   # 核心邏輯：WebSocket 路由、API 故障轉移、系統命令自癒
    ├── start.bat                   # Windows 啟動腳本 (CMD)
    ├── start.ps1                   # Windows 啟動腳本 (PowerShell)
    ├── start.sh                    # Linux / macOS / Termux 啟動腳本
    └── credentials/
        └── auth-profiles.json      # 憑證存儲：API Key、LINE/DC Token 密鑰 (自動同步)
```

---

## 🔗 檔案關聯與資料流向 (Data Flow & Events Map)

小龍蝦系統採用 **雙向 WebSocket (Socket.io) + HTTP API** 機制，將網頁端與本地/遠端執行端緊密相連：

```mermaid
graph TD
    subgraph 🖥️ 小龍蝦網頁端 (Web UI)
        A[index.html] <--> B[style.css]
        A <--> C[client.js]
    end

    subgraph ⚙️ 小龍蝦執行端 (Executor)
        D[server.js] <--> E[credentials/auth-profiles.json]
        D --> F[server.js.bak 備份]
    end

    subgraph ☁️ 遠端整合 (Tunnel & Webhook)
        G[LINE / Discord] <-->|Webhook 異步| D
        H[LLM APIs: Gemini/Claude/OpenAI] <-->|自動故障切換| D
    end

    C <-->|1. 傳送 API Key / 2. 傳送聊天 & 截圖指令| D
    D <-->|3. 回傳執行結果 & 系統溫度| C
```

---

## 📝 核心檔案職責與連結細則

### 1. 規範防護：[RULES_MINI.md](file:///c:/Users/user/Downloads/tt/RULES_MINI.md)
* **職責**：小龍蝦開發防線，限制 AI 不得覆蓋核心代碼。
* **關聯性**：`server.js` 與 `client.js` 的最前列均需參照此規範，確保所有寫入為 `Add-Only`（唯增模式）。

### 2. 網頁控制中樞：[index.html](file:///c:/Users/user/Downloads/tt/miniclaw-web/index.html)
* **職責**：玩家登入的第一站。
* **關聯性**：
  * 載入 `style.css` 渲染 UI 與 `client.js` 處理事件。
  * 提供 **Step 1 至 Step 5** 的引導流程 HTML（包含 API Key 鎖定、一鍵平台指令、Webhook 跳轉、IP 輪詢偵測、AI 聊天視窗與快捷指令卡片）。

### 3. 前端動力源：[client.js](file:///c:/Users/user/Downloads/tt/miniclaw-web/client.js)
* **職責**：
  * **Step 1 (API 鎖定)**：讀寫 `localStorage` 中的 API Key，連線成功後透過 WebSocket 同步至 Executor。
  * **Step 2 (平台辨識)**：偵測瀏覽器 UserAgent，自動切換下載路徑或顯示一鍵環境自檢指令。
  * **Step 3 (LINE/DC)**：動態管理 Webhook 狀態燈（綠/橘燈）。
  * **Step 4 (心跳輪詢)**：定時 fetch `localhost:3000` 與 `127.0.0.1:3000` 探測執行端狀態。
  * **Step 5 (AI 與快捷範例)**：動態偵測 Executor 是 PC 還是 Android，自動切換顯示截圖/定位快捷鍵。
  * **餘額監控**：即時計算並呈現場駐額度。

### 4. 終端執行大腦：[server.js](file:///c:/Users/user/Downloads/tt/miniclaw-executor/server.js)
* **職責**：本地守護進程，使用 Node.js 22 + WebSocket。
* **關聯性**：
  * **自我修復機制**：啟動時檢測，若無 `server.js.bak` 則自動複製備份。
  * **Add-Only 守護**：寫入憑證與配置時，不允許重寫已有的核心邏輯。
  * **API 故障轉移**：當 AI 模型 API 出現 `401/429/500` 時，自動輪詢下一個配置。
  * **命令執行與截圖**：對接 Node.js 原生 `child_process` 執行電腦指令，使用 `desktop-screenshot` 或系統命令捕獲畫面，並回傳至網頁端或推播至 LINE/DC Webhook。

---

## 🔄 關鍵通訊協定 (WebSocket Events)

網頁端與本地端透過以下 WebSocket 事件進行實時高速同步：

| 事件名稱 (Event) | 傳送方 (Sender) | 接收方 (Receiver) | 攜帶資料 (Payload) | 說明 |
| :--- | :--- | :--- | :--- | :--- |
| `sync-credentials` | 網頁端 | 執行端 | `{ apiKey: "..." }` | 同步存檔至 `auth-profiles.json` |
| `executor-status` | 執行端 | 網頁端 | `{ platform: "android/pc", temp: 42, cpu: 12 }` | 回報環境與硬體診斷狀態 |
| `user-command` | 網頁端 | 執行端 | `{ text: "幫我截圖", env: "pc" }` | 統一包裝發送給 AI 的命令 |
| `ai-response` | 執行端 | 網頁端 | `{ reply: "...", output: "..." }` | 雙向同步 AI 回覆與命令執行輸出 |
| `sys-action` | 執行端 | 網頁端 | `{ type: "screenshot", data: "base64..." }` | 異步推播截圖等大型系統資產 |

---

## 🚀 下一階段預告
本架構將作為後續開發的「大龍蝦資源池」。在您回覆「同意」後，我將立即在 `implementation_plan.md` 中為您梳理第一階段的具體實作，並逐步生成各檔案代碼！
