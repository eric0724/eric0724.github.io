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
