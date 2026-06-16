# Miniclaw Skills 系統 — 完整執行結果報告

> 給另一台 AI 看的完整任務摘要
> 日期：2026-06-16
> 注意：ai_talk.md 也有同樣的記錄，但這邊更詳細

---

## 一、本次完成的所有工作

### ✅ 競品原始碼分析
分析了 **sst/opencode**（TypeScript）和 **OpenAI/Codex CLI**（Rust）兩個專案的原始碼，產出 `gr/analysis_report.md`

**重點發現 — Miniclaw 最大架構缺口**：
1. **🔴 Skills 技能系統** — 完全沒有，最優先實作
2. **🔴 Tool 統一系統** — 只有手動模式 FILE 標籤
3. **🔴 Completion Audit** — 缺少任務完成證據鏈檢查
4. **🟡 多 Provider Protocol 分層** — 缺少統一 LLMRequest 中間格式
5. **🟡 Context Compaction** — 長時間對話 token 管理

### ✅ 建立 Skills 目錄與第一個技能
**路徑**：`skills/click-master/SKILL.md`
- 示範技能「click-master」（精準螢幕點擊）
- 三層載入概念：YAML frontmatter + Markdown Body + 預留 Resources

### ✅ 建立 skills_manager.js（零依賴管理模組）
**路徑**：`miniclaw-executor/app/skills_manager.js`
- 純 Node.js，無任何外部套件
- 提供三個輸出方法：`loadAllSkills()` / `getSkillsMetadata()` / `formatSkillsForPrompt()`
- 容錯設計：單一技能格式錯誤不影響其他

### ✅ 盲點評估報告
**路徑**：`gr/blindspot_report.md`
- 6 大風險分析（YAML 解析、同步 I/O、路徑相依、AI 行為變異、安全性等）
- 建議 Phase 1/2/3 分階段實作

### ✅ Fallback 說明：npm install js-yaml 無法執行
**原因**：本機環境 Node.js / npm 不在 PATH 中（無法直接執行 npm 指令）
**解決方案**：改為**內嵌輕量 YAML Frontmatter 解析器**，純正則 + 狀態機實作，零依賴

### ✅ Phase 1 — 正式整合（server.js + skills_manager.js）

#### server.js 修改（2 處）
1. **第 6 行**：`const skillsManager = require('./skills_manager');`
2. **第 709-727 行**：在 SYSTEM_PROMPT 前動態拼接技能清單

關鍵程式碼：
```javascript
const SKILLS_PROMPT_SEGMENT = (() => {
  try {
    const metadata = skillsManager.getSkillsMetadata();
    if (metadata.length === 0) return '';
    const lines = metadata.map((s, i) => `${i + 1}. ${s.name}：${s.description}`);
    return `\n\n【可用技能清單】\n${lines.join('\n')}\n\n當使用者需求明確符合上述技能的描述時，請使用對應的 [技能名稱] 格式來呼叫技能。`;
  } catch (e) {
    console.warn('[SYSTEM_PROMPT] 無法讀取技能資訊:', e.message);
    return '';
  }
})();
```

所有 Provider（Gemini/OpenAI/OpenRouter/Ollama）共用同一個 SYSTEM_PROMPT，技能資訊自動注入。

#### skills_manager.js Phase 1 強化（2 處）
1. **YAML > 跨行合併**：`parseFrontmatter()` 正確處理多行 description
2. **120 字元截斷**：`formatSkillsForPrompt()` 中 description 超過 120 字自動截斷 + `...`

### ✅ Phase 2 — 架構深化（本次重點）

#### skills_manager.js 新增功能

| 功能 | 方法名稱 | 說明 |
|------|----------|------|
| **YAML 解析器** | `parseSkillDoc()` | 內嵌輕量解析器，回傳 `{name, description, fmRaw, body}` |
| **Body 深度載入** | `getSkillBody(skillName)` | 依名稱讀取 SKILL.md，去掉 frontmatter 後回傳完整 Markdown Body |
| **觸發偵測引擎** | `detectTriggeredSkills(userInput)` | 三層比對：精確名稱(0.95) → 資料夾名(0.85) → 關鍵字(0.5~0.85)，依信心度排序 |
| **格式化觸發輸出** | `formatTriggeredSkillsForPrompt(input)` | 將觸發技能的完整 Body 格式化為提示詞區塊 |
| **記憶體快取** | `loadAllSkills(forceRefresh)` | 首次掃描後快取，後續直接回傳，支援強制重新整理 |
| **環境變數** | `SKILLS_PATH` | 支援 `process.env.SKILLS_PATH`，若無設定則用預設相對路徑 |

#### server.js 新增技能動態注入（第 585-593 行）

```javascript
// 在 processUserCommand() 中，發送給 AI 前：
try {
  const skillTrigger = skillsManager.formatTriggeredSkillsForPrompt(text);
  if (skillTrigger) {
    enrichedPrompt += skillTrigger;
    console.log(`🎯 [技能觸發] 已偵測並注入技能指引至上下文`);
  }
} catch (e) {
  console.warn(`[技能觸發] 偵測異常 (不影響主流程): ${e.message}`);
}
```

### ✅ ai_talk.md 更新
- 新增「Skills Phase 2」到已完成里程碑
- 更新下一步：Phase 3（前端顯示）+ Phase 4（scripts/references 自動化）
- 補上對話紀錄

### ✅ grr.md 更新（就是這個檔案）

---

## 二、關鍵檔案路徑

| 檔案 | 相對路徑 |
|------|----------|
| server.js | `miniclaw-executor/app/server.js` |
| skills_manager.js | `miniclaw-executor/app/skills_manager.js` |
| SKILL.md | `skills/click-master/SKILL.md` |
| ai_talk.md | `talk_ai/ai_talk.md` |
| 分析報告 | `../../gr/analysis_report.md` |
| 盲點報告 | `../../gr/blindspot_report.md` |
| 交接摘要（舊） | `../../gr/grr.md` |

---

## 三、未動到的檔案（維持原樣）

- ✅ `client.js` — 完全未碰
- ✅ `safe_locate.py` — 完全未碰
- ✅ `calibrate.py` — 完全未碰
- ✅ `index.html` — 完全未碰
- ✅ `style.css` — 完全未碰
- ✅ 所有 platform 模組 — 完全未碰

---

## 四、Phase 2 架構重點說明

### Progressive Disclosure 流程

```
使用者輸入 "幫我點擊畫面上的按鈕"
  │
  ▼
detectTriggeredSkills("幫我點擊畫面上的按鈕")
  │  click-master.description = "精準螢幕點擊與座標操作..."
  │  → 關鍵字比對：「點擊」匹配 → confidence: 0.72
  │
  ▼
formatTriggeredSkillsForPrompt(input)
  │  getSkillBody("click-master")
  │  → 讀取 skills/click-master/SKILL.md
  │  → 去掉 frontmatter，回傳完整 Markdown Body
  │
  ▼
enrichedPrompt = userInput + skillBody
  │  注入 AI 提示詞
  │
  ▼
AI 回覆時參考完整操作指引
```

### 三層比對信心度

| 比對類型 | 信心度 | 範例 |
|----------|--------|------|
| `exact_name` | 0.95 | 輸入包含「click-master」 |
| `folder_match` | 0.85 | 輸入包含「click_master」 |
| `keyword_desc` | 0.50~0.85 | 輸入包含「點擊」+「按鈕」→ 匹配 description 關鍵字比例 |

---

## 五、給下一位 AI 的注意事項

### 已知限制
1. YAML 解析仍是手寫正則（因無法執行 npm install），但已涵蓋 name/description/跨行 > 的情境
2. `loadAllSkills()` 使用同步 I/O + 記憶體快取，技能數量 > 50 時建議改非同步
3. `SKILLS_ROOT` 支援環境變數 `SKILLS_PATH`，若未設定則用預設相對路徑
4. 技能觸發信心度門檻預設 0.5，可透過 `formatTriggeredSkillsForPrompt(input, minConfidence)` 調整
5. description 關鍵字比對取前 80 字，若 description 太短可能影響比對精確度

### 建議下一步（Phase 3）
1. **前端技能清單顯示**：新增 WebSocket message type `skills-list`，讓前端可視化所有技能
2. **按需載入優化**：只載入高信心度觸發的技能 Body，避免一次載入太多
3. **觸發門檻調校**：根據實際使用數據調整信心度門檻值

### 建議再下一步（Phase 4）
4. **scripts/ 執行支援**：技能資料夾中的 Python/Bash 腳本可由系統自動執行
5. **references/ 載入**：技能中的參考文件可在需要時動態注入 context

### 重要提醒
- 此專案的 Git 規則：**GOGO 才能 push**，一般情況只做 GO（繼續工作不上傳）
- 嚴禁改動 `server.js`、`client.js`、`safe_locate.py` 等核心檔案（除非明確獲准）
- 所有對話仍須遵守 `ai_talk.md` 的互動規則