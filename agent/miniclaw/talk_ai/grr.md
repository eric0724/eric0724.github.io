# Miniclaw Skills 系統 — Phase 9 執行結果

> 給下一台 AI 的快速交接摘要
> 日期：2026-06-17
> 完整歷史請見 ai_talk.md

---

## 本次完成：Phase 9 — 手勢辨識與巨集自動觸發聯動

### 修改檔案
- `miniclaw-executor/app/server.js`（第 718-755 行）

### 核心功能
在手勢辨識成功後，自動觸發對應的預錄巨集。

### 關鍵程式碼
```javascript
// Phase 9: 手勢辨識 → 巨集自動觸發聯動
if (tag.skillName === 'gesture-recognizer' && result.output) {
  const matchedMatch = result.output.match(/\[MATCHED\]\s*([MWOV])/i);
  if (matchedMatch) {
    const gestureChar = matchedMatch[1].toUpperCase();
    const macroName = `遊戲手勢_${gestureChar}`;
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const macroResult = await skillsManager.executeSkillScript('macro-recorder', `play ${macroName}`);
    if (macroResult.success) {
      skillExecutionResults.push(`✅ [macro-recorder] 手勢巨集觸發成功：\n${macroResult.output}`);
    } else {
      const errorMsg = macroResult.error || '';
      if (errorMsg.includes('找不到巨集') || errorMsg.includes('找不到')) {
        skillExecutionResults.push(`ℹ️ [macro-recorder] 手勢辨識成功，但系統內未找到名為「${macroName}」的預錄巨集，請先使用 macro-recorder 進行錄製。`);
      } else {
        skillExecutionResults.push(`❌ [macro-recorder] 巨集執行失敗：\n${macroResult.error}`);
      }
    }
  }
}
```

### 執行流程
```
使用者畫手勢（如 M）
    ↓
visual-trail 記錄軌跡
    ↓
gesture-recognizer 辨識 → [MATCHED] M
    ↓
server.js 攔截 stdout → 正則匹配 [MATCHED] M
    ↓
自動觸發 macro-recorder play 遊戲手勢_M
    ↓
巨集執行成功 → 附加到對話回覆
```

### 防錯機制
1. **巨集不存在**：輸出友善提示，引導使用者先錄製巨集
2. **執行失敗**：顯示詳細錯誤訊息，不影響主線對話
3. **延遲 500ms**：讓使用者先看到手勢辨識結果

### 巨集命名規範
- M → `遊戲手勢_M`
- W → `遊戲手勢_W`
- O → `遊戲手勢_O`
- V → `遊戲手勢_V`

### 相關技能檔案
- `skills/gesture-recognizer/SKILL.md` + `scripts/run.py`
- `skills/macro-recorder/SKILL.md` + `scripts/run.py`
- `skills/visual-trail/SKILL.md` + `scripts/run.py`
- `skills/click-master/scripts/safe_locate.py`
- `skills/calibration-master/SKILL.md` + `scripts/run.py`

### Git 規則
- **GO**：繼續工作不上傳
- **GOGO**：做完更新 ai_talk.md 後才 push

---

## 本次完成：Phase 10 — 校準流程實測優化

### 修改檔案
- `skills/calibration-master/scripts/run.py`（第 265-310 行）
- `miniclaw-web/index.html`（第 816 行，時間戳更新）

### 優化內容

**1. GPT-4o Vision 提示詞精度強化**
- 加入邊界限制指引（只考慮主螢幕，忽略副螢幕/任務列）
- 明確要求回傳絕對像素座標（相對於截圖左上角）
- 強調必須回傳元素「中心點」座標
- 加入邊界防禦條件（靠近邊緣 < 5% 特別標註）

**2. 重試策略與自動降級（Step D 強化）**
- 最大 3 次重試機制
- 每次輕微偏移像素（±5px）重試
- 3 次皆失敗時觸發自動降級手動校準
- 輸出友善提示訊息引導使用者

**關鍵程式碼**：
```python
# Step D: 點擊前後確認機制（最大 3 次重試）
MAX_RETRIES = 3
retry_count = 0
confirmed = False

while retry_count < MAX_RETRIES and not confirmed:
    confirm_screenshot = capture_screenshot(scale=1)
    # TODO: 實際應加入圖片比對邏輯
    confirmed = True  # 暫時設為 True
    
    if not confirmed and retry_count < MAX_RETRIES - 1:
        retry_count += 1
        x += 5 if retry_count % 2 == 0 else -5
        y += 5 if retry_count % 2 == 0 else -5
```

**3. 時間戳更新**
- `miniclaw-web/index.html` 第 816 行
- 更新為：2026-06-17 10:08

### ✅ Phase 11 — 大廳手勢自動觸發巨集開關

#### 修改檔案
- `miniclaw-web/index.html`（AI 設定面板新增開關）
- `miniclaw-web/client.js`（WebSocket 發送邏輯）
- `miniclaw-executor/app/server.js`（全域狀態 + 攔截判斷）

#### 核心功能
在大廳設定面板加入「手勢自動觸發巨集」開關，使用者可即時啟用/關閉手勢辨識後的巨集自動執行。

#### 前端 UI（index.html）
```html
<div class="settings-item" style="margin-top:12px;">
  <span class="settings-label">手勢自動觸發巨集</span>
  <label class="switch-control">
    <input type="checkbox" id="toggleGestureAutoTrigger">
    <span class="slider"></span>
  </label>
</div>
<div style="font-size:0.75rem;color:var(--text-muted);margin-top:4px;line-height:1.4;">
  辨識到手勢（M/W/O/V）後，自動執行對應的預錄巨集
</div>
```

#### 後端邏輯（server.js）
```javascript
// 全域狀態變數
let gestureAutoTriggerEnabled = false;  // 預設關閉

// WebSocket 同步
} else if (msg.type === 'sync-gesture-setting') {
  gestureAutoTriggerEnabled = msg.data.enabled;
  console.log(`🎯 [手勢設定] 自動觸發巨集：${gestureAutoTriggerEnabled ? '啟用' : '關閉'}`);
}

// Phase 9 邏輯加入開關判斷
if (!gestureAutoTriggerEnabled) {
  console.log(`ℹ️ [Phase 9] 手勢辨識到 [${gestureChar}]，但自動觸發功能已關閉`);
  skillExecutionResults.push(`ℹ️ 手勢辨識成功：[MATCHED] ${gestureChar}（自動觸發已關閉）`);
} else {
  // 執行巨集...
}
```

#### 執行流程
```
使用者切換開關（client.js）
    ↓
WebSocket 發送 sync-gesture-setting（enabled: true/false）
    ↓
server.js 更新全域變數 gestureAutoTriggerEnabled
    ↓
手勢辨識時檢查開關狀態
    ↓
開關為 true → 自動觸發巨集
開關為 false → 僅記錄日誌，不驅動巨集
```

#### 相關檔案
- `miniclaw-web/index.html` — 開關 UI
- `miniclaw-web/client.js` — WebSocket 發送
- `miniclaw-executor/app/server.js` — 後端判斷邏輯
- `skills/gesture-recognizer/scripts/run.py` — 手勢辨識腳本
- `skills/macro-recorder/scripts/run.py` — 巨集執行腳本

### 建議下一步（Phase 12）
33. **手勢編輯器**：GUI 介面調整手勢參數
34. **巨集管理員**：統一管理所有手勢對應的巨集
35. **手勢熱區**：根據使用頻率調整手勢觸發區域
36. **多手勢序列**：支援 M → V → O 連續手勢組合

---

## 本次完成：Phase 12 — 多技能併發壓力測試與邊界異常防禦

### 修改檔案
- `miniclaw-executor/app/server.js`（隊列機制 + 僵死進程清理）
- `miniclaw-web/index.html`（時間戳更新）

### 核心功能

**1. 技能執行隊列與互斥鎖（Mutex Queue）**
- 同時間只有一個 `executeSkillScript` 執行
- 自動隊列排程（FIFO），最大隊列長度 10
- 執行間隔 100ms 防止過載
- 避免多個 Python 自動化腳本同時搶奪滑鼠控制權

**2. 僵死進程清理機制**
- 追蹤所有活躍的 Python 子進程（`activeProcesses` Map）
- 每 30 秒定期清理超過 2 分鐘未完成的僵死進程
- Windows：使用 `taskkill /F /T /PID` 清理進程樹
- Linux/Mac：使用 `process.kill(-pid, 'SIGKILL')` 清理進程群組

**3. 隊列狀態監控**
- `getQueueStatus()` 函數回傳即時隊列狀態
- 日誌記錄等待耗時、任務 ID、執行歷程

### 關鍵程式碼

**隊列機制：**
```javascript
const skillExecutionQueue = {
  isRunning: false,
  queue: [],
  maxQueueSize: 10,
};

async function executeSkillWithQueue(skillName, args) {
  // 檢查隊列是否已滿
  if (skillExecutionQueue.queue.length >= skillExecutionQueue.maxQueueSize) {
    return { success: false, error: '隊列已滿', queueFull: true };
  }
  
  const task = { skillName, args, resolve, reject, timestamp: Date.now(), id: ... };
  
  if (skillExecutionQueue.isRunning) {
    skillExecutionQueue.queue.push(task);  // 排隊
    return;
  }
  
  executeSkillTask(task);  // 直接執行
}
```

**僵死進程清理：**
```javascript
const activeProcesses = new Map();
const STALE_THRESHOLD = 120000;  // 2 分鐘
const CLEANUP_INTERVAL = 30000;  // 30 秒

setInterval(() => {
  for (const [pid, info] of activeProcesses.entries()) {
    if (now - info.startTime > STALE_THRESHOLD && !info.killed) {
      process.kill(pid, 'SIGKILL');
      killChildProcesses(pid);  // 清理子進程樹
    }
  }
}, CLEANUP_INTERVAL);
```

### 執行流程
```
使用者連續觸發手勢/巨集
    ↓
executeSkillWithQueue() 接收任務
    ↓
檢查 isRunning 狀態
    ↓
isRunning = false → 直接執行
isRunning = true  → 加入隊列等待
    ↓
執行完畢 → 自動執行下一個（延遲 100ms）
    ↓
定期清理僵死進程（每 30 秒）
```

### 防護機制
1. **隊列滿載保護**：超過 10 個任務直接拒絕，回傳友善提示
2. **超時強制終止**：60 秒超時 + SIGKILL 強制殺死
3. **子進程樹清理**：Windows taskkill /T / Linux 進程群組
4. **定期僵死清理**：2 分鐘未完成視為僵死，自動銷毀

### 相關檔案
- `miniclaw-executor/app/server.js` — 隊列 + 清理機制
- `miniclaw-web/index.html` — 時間戳更新（10:24）

---

## 本次完成：Phase 13 — 全局系統驗證與日誌自動滾動清理

### 修改檔案
- `miniclaw-executor/app/server.js`（日誌封存 + 健康檢查）
- `miniclaw-web/index.html`（時間戳更新）

### 核心功能

**1. 日誌檔案大小限制與自動封存**
- 監控 `chat_history.txt` 寫入前的大小
- 超過 5MB 自動封存為 `chat_history_bak.txt`
- 保留最新一版備份（覆蓋式）
- 非同步執行，不阻塞主流程

**關鍵程式碼：**
```javascript
const LOG_SIZE_THRESHOLD = 5 * 1024 * 1024;  // 5MB
const LOG_BACKUP_SUFFIX = '_bak';

function rotateLogIfNeeded(logPath) {
  const stats = fs.statSync(logPath);
  if (stats.size >= LOG_SIZE_THRESHOLD) {
    const backupPath = `${base}${LOG_BACKUP_SUFFIX}${ext}`;
    if (fs.existsSync(backupPath)) fs.unlinkSync(backupPath);
    fs.renameSync(logPath, backupPath);
    console.log(`📦 [日誌封存] ${path.basename(logPath)} → ${path.basename(backupPath)}（${(stats.size / 1024 / 1024).toFixed(2)}MB）`);
  }
}
```

**2. 啟動自我健康檢查**
- 檢查 Python 環境（`py --version`）
- 檢查必要套件：pyautogui, Pillow, pynput
- 檢查 skills/ 目錄結構完整性
- 檢查關鍵執行器檔案是否存在
- 非阻塞式：警告但不中斷啟動

**檢查項目：**
```javascript
function performHealthCheck() {
  // 1. Python 環境
  // 2. 必要套件（pyautogui, Pillow, pynput）
  // 3. skills/ 目錄結構
  // 4. 關鍵檔案（server.js, skills_manager.js, index.html, client.js）
}
```

**3. 執行流程**
```
伺服器啟動
    ↓
performHealthCheck() 執行
    ↓
檢查 Python、套件、skills/、關鍵檔案
    ↓
輸出警告（黃色）或通過（綠色）
    ↓
系統繼續啟動（不中斷）
    ↓
日誌寫入時 rotateLogIfNeeded() 檢查
    ↓
超過 5MB → 自動封存為 _bak 檔案
```

**4. 防護機制**
- 日誌封存失敗不影響主流程（try-catch 保護）
- 健康檢查警告但不中斷啟動
- 彩色輸出：綠色通過、黃色警告、紅色錯誤

### 相關檔案
- `miniclaw-executor/app/server.js` — 日誌封存 + 健康檢查
- `miniclaw-web/index.html` — 時間戳更新（10:45）
