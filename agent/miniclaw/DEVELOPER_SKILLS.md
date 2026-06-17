# Miniclaw 開發者外掛開發手冊

> 版本：v1.0  
> 更新日期：2026-06-17  
> 使用者操作手冊請見 USER_GUIDE.md

---

## 目錄

1. [外掛架構總覽](#1-外掛架構總覽)
2. [SKILL.md 格式規範](#2-skillmd-格式規範)
3. [後端執行機制深度解析](#3-後端執行機制深度解析)
4. [開發新技能完整指南](#4-開發新技能完整指南)
5. [進階主題](#5-進階主題)
6. [API 參考](#6-api-參考)

---

## 1. 外掛架構總覽

### 1.1 Miniclaw Skills 系統設計理念

Miniclaw 採用模組化外掛架構，讓開發者可以輕鬆擴充系統功能，而无需修改核心程式碼。

**設計原則：**
- **零依賴**：技能腳本不依賴額外 npm 套件
- **隔離性**：每個技能獨立運作，不互相干擾
- **可發現性**：系統自動掃描並載入技能
- **安全性**：隊列機制防止併發衝突

### 1.2 架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Frontend)                        │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │   index.html  │ ◄─────► │   client.js  │                  │
│  │  (UI 介面)    │ WebSocket│ (通訊邏輯)  │                  │
│  └──────────────┘         └──────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      後端 (Backend)                           │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │   server.js  │ ◄─────► │skills_manager│                  │
│  │ (核心控制器) │  呼叫   │  .js (技能管理)│                  │
│  └──────────────┘         └──────────────┘                  │
│         │                         │                          │
│         │  executeSkillScript()   │  loadAllSkills()         │
│         │  executeSkillWithQueue()│  getSkillBody()          │
│         │  detectTriggeredSkills()│  parseSkillTags()        │
│         ▼                         ▼                          │
│  ┌──────────────────────────────────────┐                   │
│  │   Phase 12: 隊列與互斥鎖機制          │                   │
│  │   - skillExecutionQueue              │                   │
│  │   - 僵死進程清理 (activeProcesses)   │                   │
│  └──────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      技能層 (Skills Layer)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ click-master │  │gesture-      │  │macro-recorder│       │
│  │ (點擊控制)   │  │recognizer    │  │ (巨集錄製)   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │calibration-  │  │visual-trail  │  │  (其他技能)  │       │
│  │  master      │  │ (視覺軌跡)   │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                │                  │                │
│         ▼                ▼                  ▼                │
│  ┌──────────────────────────────────────────────────┐       │
│  │              Python 自動化腳本 (run.py)            │       │
│  │  - pyautogui (滑鼠鍵盤控制)                       │       │
│  │  - Pillow (圖像處理)                              │       │
│  │  - pynput (輸入監控)                              │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      AI 模型層 (AI Models)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Gemini     │  │   OpenAI     │  │   Ollama     │       │
│  │  (Google)    │  │   (GPT-4o)   │  │  (本地)      │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 核心模組職責

| 模組 | 檔案 | 職責 |
|------|------|------|
| **核心控制器** | `server.js` | WebSocket 伺服器、指令分發、隊列管理、進程清理 |
| **技能管理員** | `skills_manager.js` | 技能掃描、載入、觸發偵測、腳本執行 |
| **前端介面** | `index.html` + `client.js` | 使用者介面、WebSocket 通訊、狀態顯示 |
| **平台模組** | `platform/*.js` | 跨平台指令封裝（Windows/Mac/Android/Linux） |

---

## 2. SKILL.md 格式規範

### 2.1 YAML Frontmatter 結構

每個技能必須包含 `SKILL.md` 檔案，開頭使用 YAML frontmatter：

```yaml
---
name: 技能名稱（英文，用於程式識別）
description: 技能功能描述（最多 120 字，用於 AI 觸發偵測）
---

# 技能標題

## 功能說明
詳細描述這個技能能做什麼...

## 使用方式
如何在對話中觸發這個技能...

## 參數說明
- 參數1：說明
- 參數2：說明

## 注意事項
任何限制或特殊條件...
```

### 2.2 欄位說明

**name（必填）**
- 格式：英文、數字、連字號（-）
- 範例：`click-master`、`gesture-recognizer`
- 用途：程式識別、檔案夾名稱、觸發關鍵字

**description（必填）**
- 長度：最多 120 字（超過會自動截斷）
- 內容：清楚描述技能功能
- 用途：AI 觸發偵測、前端顯示

**範例：**
```yaml
---
name: click-master
description: 智慧點擊控制，支援安全座標計算、圖片模板比對、多螢幕支援
---
```

### 2.3 Body 內容撰寫規範

**Markdown 格式：**
- 使用標準 Markdown 語法
- 支援標題、列表、程式碼區塊
- 不支援 HTML 標籤（會自動移除）

**內容結構建議：**
```markdown
# 技能名稱

## 功能說明
簡短描述（1-2 句話）

## 觸發方式
- 關鍵字1
- 關鍵字2
- 使用格式：[技能名稱 參數]

## 參數說明
- `param1`：說明
- `param2`：說明

## 執行流程
1. 步驟1
2. 步驟2
3. 步驟3

## 錯誤處理
- 錯誤類型1：處理方式
- 錯誤類型2：處理方式

## 範例
```bash
# 使用範例
[click-master 100 200]
```
```

### 2.4 動態載入機制

**getSkillBody() 函數：**
```javascript
// 讀取技能的完整 Body（去掉 frontmatter）
const skillBody = skillsManager.getSkillBody('click-master');
// 回傳：{ found, name, description, body, path }
```

**使用時機：**
- AI 觸發技能時，動態注入完整指引到 prompt
- 前端顯示技能詳細資訊
- 開發者除錯

---

## 3. 後端執行機制深度解析

### 3.1 executeSkillScript 完整流程

```javascript
async function executeSkillScript(skillName, args = '') {
  // 1. 查找技能
  const match = skills.find(s => 
    s.folder.toLowerCase() === skillName.toLowerCase()
  );
  
  // 2. 檢查 scripts/ 目錄
  const scriptsDir = path.join(SKILLS_ROOT, match.folder, 'scripts');
  
  // 3. 優先尋找 run.py，其次 run.js
  const scriptPath = fs.existsSync(runPy) ? runPy : runJs;
  
  // 4. 建構指令
  const command = process.platform === 'win32' ? 'py' : 'python3';
  const scriptArgs = [scriptPath, ...args.split(/\s+/).filter(Boolean)];
  
  // 5. 執行腳本（60 秒超時）
  const { stdout, stderr } = await execAsync(fullCommand, {
    timeout: 60000,
    maxBuffer: 1024 * 1024,
    cwd: path.dirname(scriptPath)
  });
  
  // 6. 回傳結果
  return { success: true, output: stdout, error: null };
}
```

### 3.2 隊列與互斥鎖機制（Phase 12）

**問題：**
- 多個 Python 腳本同時執行會搶奪滑鼠控制權
- 導致系統崩潰或行為不可預測

**解決方案：**
```javascript
const skillExecutionQueue = {
  isRunning: false,      // 是否正在執行
  queue: [],              // 等待隊列
  maxQueueSize: 10       // 最大隊列長度
};
```

**執行流程：**
```
任務提交
    ↓
檢查 isRunning
    ↓
isRunning = false → 直接執行
isRunning = true  → 加入 queue
    ↓
執行完畢
    ↓
檢查 queue 是否有下一個
    ↓
有 → 延遲 100ms 後執行下一個
無 → 標記為空閒
```

**關鍵程式碼：**
```javascript
async function executeSkillWithQueue(skillName, args) {
  // 檢查隊列是否已滿
  if (skillExecutionQueue.queue.length >= skillExecutionQueue.maxQueueSize) {
    return { success: false, error: '隊列已滿', queueFull: true };
  }
  
  const task = {
    skillName,
    args,
    resolve,
    reject,
    timestamp: Date.now(),
    id: `${skillName}_${Date.now()}_${random}`
  };
  
  if (skillExecutionQueue.isRunning) {
    skillExecutionQueue.queue.push(task);  // 排隊
    return;
  }
  
  executeSkillTask(task);  // 直接執行
}

async function executeSkillTask(task) {
  skillExecutionQueue.isRunning = true;
  
  try {
    const result = await skillsManager.executeSkillScript(
      task.skillName, 
      task.args
    );
    task.resolve(result);
  } catch (error) {
    task.resolve({ success: false, error: error.message });
  } finally {
    skillExecutionQueue.isRunning = false;
    
    // 執行下一個（延遲 100ms）
    if (skillExecutionQueue.queue.length > 0) {
      const nextTask = skillExecutionQueue.queue.shift();
      setTimeout(() => executeSkillTask(nextTask), 100);
    }
  }
}
```

**保護機制：**
1. **隊列滿載保護**：超過 10 個任務直接拒絕
2. **執行間隔**：100ms 延遲讓系統喘口氣
3. **任務 ID 追蹤**：每個任務有唯一 ID 便於除錯

### 3.3 僵死進程清理防禦

**問題：**
- Python 腳本可能崩潰或卡住
- 留下背景僵死進程
- 消耗系統資源

**解決方案：**
```javascript
const activeProcesses = new Map(); // pid -> { skillName, startTime, killed }
const STALE_THRESHOLD = 120000;    // 2 分鐘
const CLEANUP_INTERVAL = 30000;    // 30 秒
```

**清理邏輯：**
```javascript
setInterval(() => {
  const now = Date.now();
  
  for (const [pid, info] of activeProcesses.entries()) {
    const age = now - info.startTime;
    
    // 超過 2 分鐘且未被標記為已殺死
    if (age > STALE_THRESHOLD && !info.killed) {
      console.log(`[Cleanup] 清理僵死進程 PID: ${pid}`);
      
      try {
        // 強制殺死主進程
        process.kill(pid, 'SIGKILL');
        info.killed = true;
        
        // 清理子進程樹
        killChildProcesses(pid);
      } catch (e) {
        info.killed = true;
      }
    }
  }
}, CLEANUP_INTERVAL);
```

**跨平台清理：**
```javascript
function killChildProcesses(parentPid) {
  if (platform === 'win32') {
    // Windows：taskkill /F /T /PID
    exec(`taskkill /F /T /PID ${parentPid}`);
  } else {
    // Linux/Mac：kill 進程群組
    process.kill(-parentPid, 'SIGKILL');
  }
}
```

**追蹤機制：**
```javascript
// 在 executeSkillScript 中記錄
const child = exec(command);
activeProcesses.set(child.pid, {
  skillName,
  startTime: Date.now(),
  killed: false
});

// 執行完畢後刪除
child.on('exit', () => {
  activeProcesses.delete(child.pid);
});
```

---

## 4. 開發新技能完整指南

### 4.1 目錄結構規範

**基本結構：**
```
skills/
  your-skill-name/
    ├── SKILL.md          # 技能說明文件（必填）
    └── scripts/
        ├── run.py        # Python 主腳本（推薦）
        └── run.js        # 或 Node.js 腳本
```

**完整範例（click-master）：**
```
skills/click-master/
  ├── SKILL.md
  └── scripts/
      ├── run.py          # 主腳本
      └── safe_locate.py  # 輔助模組
```

**命名規則：**
- 資料夾名稱：小寫英文、連字號（kebab-case）
- 範例：`click-master`、`gesture-recognizer`、`macro-recorder`

### 4.2 腳本規範

**Python 腳本（run.py）**

**輸入參數：**
```python
import sys

def main():
    # 參數從 sys.argv 取得
    # sys.argv[0] = 腳本路徑
    # sys.argv[1] = 第一個參數
    # sys.argv[2] = 第二個參數
    
    args = sys.argv[1:]
    print(f"收到參數：{args}")
```

**輸出格式：**
```python
# 成功時輸出到 stdout
print("✅ 執行成功")
print("結果內容...")

# 錯誤時輸出到 stderr
import sys
print("❌ 執行失敗", file=sys.stderr)
sys.exit(1)  # 非零退出碼表示失敗
```

**完整範例：**
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json

def main():
    try:
        # 1. 解析參數
        args = sys.argv[1:]
        if not args:
            print("❌ 請提供參數", file=sys.stderr)
            sys.exit(1)
        
        x = int(args[0]) if len(args) > 0 else 0
        y = int(args[1]) if len(args) > 1 else 0
        
        # 2. 執行邏輯
        print(f"正在點擊座標：({x}, {y})")
        
        # 3. 回傳結果
        result = {
            "x": x,
            "y": y,
            "success": True
        }
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ 錯誤：{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
```

**注意事項：**
- 腳本路徑可能包含中文或空格，使用 `sys.argv` 而非手動解析
- 輸出控制在 1MB 以內（`maxBuffer: 1024 * 1024`）
- 執行時間限制 60 秒（`timeout: 60000`）

### 4.3 測試與除錯

**本地測試：**
```bash
# 進入技能目錄
cd skills/your-skill/scripts

# 執行腳本
py run.py 參數1 參數2

# 查看輸出
echo %ERRORLEVEL%  # Windows：查看退出碼
echo $?            # Linux/Mac：查看退出碼
```

**除錯技巧：**
```python
# 1. 加入詳細日誌
import logging
logging.basicConfig(level=logging.DEBUG)
logging.debug(f"變數 x = {x}")

# 2. 輸出到檔案
with open('debug.log', 'w', encoding='utf-8') as f:
    f.write(f"除錯資訊：{data}\n")

# 3. 使用 try-except 捕獲異常
try:
    # 危險操作
    risky_operation()
except Exception as e:
    print(f"❌ 錯誤：{e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
```

**查看執行日誌：**
```bash
# 查看 chat_history.txt
tail -f talk_ai/chat_history.txt

# 查看伺服器輸出（server.js 的 console.log）
# 會在執行器視窗中顯示
```

### 4.4 註冊技能

**自動註冊：**
- 系統會自動掃描 `skills/` 目錄
- 只要資料夾內有 `SKILL.md` 就會自動載入
- 无需額外註冊

**手動觸發測試：**
```javascript
// 在 client.js 或 server.js 中測試
const skills = skillsManager.loadAllSkills();
console.log('已載入技能：', skills.map(s => s.name));

// 測試觸發偵測
const triggers = skillsManager.detectTriggeredSkills('幫我點擊按鈕');
console.log('觸發的技能：', triggers);
```

---

## 5. 進階主題

### 5.1 跨平台相容

**平台偵測：**
```javascript
const platform = process.platform;
// 'win32' | 'darwin' | 'linux' | 'android'
```

**指令差異：**
```javascript
// Python 指令
const pythonCmd = process.platform === 'win32' ? 'py' : 'python3';

// 路徑分隔符
const pathSep = process.platform === 'win32' ? '\\' : '/';

// 換行符號
const newline = process.platform === 'win32' ? '\r\n' : '\n';
```

**平台模組：**
```javascript
// platform/win.js
module.exports = {
  name: 'Windows',
  screenshot: (path) => `powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen.Bounds"`,
  openBrowser: (url) => `start ${url}`,
  // ...
};
```

### 5.2 錯誤處理最佳實踐

**分級錯誤處理：**
```javascript
// 1. 預期內錯誤（可恢復）
try {
  const result = await riskyOperation();
} catch (e) {
  console.log('⚠️ 操作失敗，使用備用方案');
  result = await fallbackOperation();
}

// 2. 嚴重錯誤（需通知使用者）
try {
  await criticalOperation();
} catch (e) {
  sendWSMessage(socket, {
    type: 'ai-response',
    reply: `❌ 嚴重錯誤：${e.message}`
  });
  return;
}

// 3. 未預期錯誤（記錄但不中斷）
process.on('uncaughtException', (err) => {
  console.error('🚨 未捕獲異常：', err);
  // 繼續運行，不中斷伺服器
});
```

**錯誤碼規範：**
```javascript
// 0：成功
// 1：一般錯誤
// 2：參數錯誤
// 3：權限不足
// 4：資源不存在

sys.exit(2);  // 參數錯誤
```

### 5.3 效能優化建議

**1. 減少 I/O 操作：**
```python
# ❌ 不好：重複讀取檔案
for i in range(100):
    data = read_file('config.json')

# ✅ 好：一次性讀取
data = read_file('config.json')
for i in range(100):
    process(data[i])
```

**2. 使用快取：**
```javascript
// skills_manager.js 已實作記憶體快取
let skillsCache = null;
let skillsCacheLoaded = false;

function loadAllSkills(forceRefresh = false) {
  if (skillsCacheLoaded && !forceRefresh) {
    return skillsCache;  // 直接回傳快取
  }
  // ... 重新掃描
}
```

**3. 非阻塞操作：**
```javascript
// ❌ 不好：同步操作阻塞事件迴圈
const data = fs.readFileSync('file.txt');

// ✅ 好：非同步操作
const data = await fs.promises.readFile('file.txt');
```

### 5.4 安全考量

**1. 路徑驗證：**
```javascript
// 防止路徑遍歷攻擊
function validatePath(userPath) {
  const normalized = path.normalize(userPath);
  if (normalized.includes('..')) {
    throw new Error('不允許存取上層目錄');
  }
  return normalized;
}
```

**2. 指令注入防護：**
```javascript
// ❌ 危險：直接拼接使用者輸入
const cmd = `py script.py ${userInput}`;

// ✅ 安全：使用參數陣列
const args = [scriptPath, userInput];
const cmd = `${pythonCmd} ${args.map(a => `"${a}"`).join(' ')}`;
```

**3. 權限控制：**
```javascript
// 檢查是否在允許的目錄內
const allowedDirs = ['C:\\Users\\user\\Desktop', 'C:\\miniclaw'];
function isPathAllowed(targetPath) {
  return allowedDirs.some(dir => targetPath.startsWith(dir));
}
```

---

## 6. API 參考

### 6.1 skills_manager.js 公開函數

**loadAllSkills(forceRefresh?)**
```javascript
// 載入所有技能清單
const skills = skillsManager.loadAllSkills();
// 回傳：Array<{ folder, name, description, path }>
```

**getSkillsMetadata()**
```javascript
// 取得技能中繼資料（name + description）
const metadata = skillsManager.getSkillsMetadata();
// 回傳：Array<{ name, description }>
```

**getSkillBody(skillName)**
```javascript
// 取得技能的完整 Body（去掉 frontmatter）
const body = skillsManager.getSkillBody('click-master');
// 回傳：{ found, name, description, body, path }
```

**detectTriggeredSkills(userInput)**
```javascript
// 偵測使用者輸入是否觸發技能
const triggers = skillsManager.detectTriggeredSkills('幫我點擊按鈕');
// 回傳：Array<{ name, folder, matchType, confidence }>
// matchType: 'exact_name' | 'keyword_desc' | 'folder_match'
```

**formatTriggeredSkillsForPrompt(userInput, minConfidence?)**
```javascript
// 格式化觸發的技能為 prompt 區塊
const prompt = skillsManager.formatTriggeredSkillsForPrompt(
  '幫我點擊按鈕',
  0.5  // 最低信心門檻
);
// 回傳：string（可直接附加到 AI prompt）
```

**executeSkillScript(skillName, args?)**
```javascript
// 執行技能腳本
const result = await skillsManager.executeSkillScript('click-master', '100 200');
// 回傳：{ success, output, error }
```

**parseSkillTags(text)**
```javascript
// 從文字中解析 [技能名稱 參數] 標籤
const tags = skillsManager.parseSkillTags('請[click-master 100 200]點擊');
// 回傳：Array<{ skillName, args }>
```

### 6.2 WebSocket 訊息格式

**客戶端 → 伺服器：**

```javascript
// 使用者指令
{
  type: 'user-command',
  data: {
    text: '幫我截圖',
    platform: 'win32'
  }
}

// 同步手勢設定
{
  type: 'sync-gesture-setting',
  data: {
    enabled: true
  }
}

// 同步憑證
{
  type: 'sync-credentials',
  data: {
    apiKey: 'AIzaSy...',
    googleAccessToken: '...'
  }
}
```

**伺服器 → 客戶端：**

```javascript
// AI 回覆
{
  type: 'ai-response',
  reply: '聊天內容',
  output: '指令輸出'  // 可選
}

// 技能執行結果
{
  type: 'ai-response',
  reply: '✅ [click-master] 執行成功：\n點擊完成'
}

// 系統狀態
{
  type: 'sys-action',
  action: 'screenshot',
  data: 'base64...'
}

// AI 額度耗盡
{
  type: 'ai-quota-exhausted'
}

// 技能清單
{
  type: 'skills-list',
  skills: [
    { name: 'click-master', description: '...' },
    { name: 'gesture-recognizer', description: '...' }
  ]
}
```

### 6.3 技能觸發偵測機制

**觸發類型：**

1. **exact_name（精確名稱匹配）**
   ```
   使用者輸入：「使用 click-master 點擊」
   匹配：skill.name = 'click-master'
   信心度：0.95
   ```

2. **folder_match（資料夾名稱匹配）**
   ```
   使用者輸入：「啟動 gesture-recognizer」
   匹配：skill.folder = 'gesture-recognizer'
   信心度：0.85
   ```

3. **keyword_desc（關鍵字描述匹配）**
   ```
   使用者輸入：「幫我辨識手勢」
   匹配：skill.description 包含 '手勢'、'辨識'
   信心度：0.5 ~ 0.85（根據匹配比例）
   ```

**信心度計算：**
```javascript
// 關鍵字匹配比例
const matchRatio = matchCount / descKeywords.length;

// 最終信心度
const confidence = Math.min(0.5 + matchRatio * 0.3, 0.85);
```

**使用建議：**
- 在 `description` 中加入多個關鍵字
- 使用通用詞彙提高匹配機會
- 避免過於專業的術語

---

## 附錄

### A. 開發環境設定

**1. 克隆專案：**
```bash
git clone https://github.com/eric0724/eric0724.github.io.git
cd eric0724.github.io/agent/miniclaw
```

**2. 安裝依賴：**
```bash
cd miniclaw-executor/app
npm install
```

**3. 啟動開發伺服器：**
```bash
node server.js
```

**4. 開啟網頁：**
```
在瀏覽器開啟 miniclaw-web/index.html
```

### B. 除錯工具

**1. 查看技能清單：**
```bash
node -e "const sm = require('./skills_manager'); console.log(sm.loadAllSkills())"
```

**2. 測試技能觸發：**
```bash
node -e "const sm = require('./skills_manager'); console.log(sm.detectTriggeredSkills('幫我點擊'))"
```

**3. 查看隊列狀態：**
```javascript
// 在 server.js 中加入
console.log(getQueueStatus());
```

### C. 貢獻指南

**提交 Pull Request：**
1. Fork 專案
2. 建立功能分支（`git checkout -b feature/your-skill`）
3. 提交變更（`git commit -am 'Add new skill'`）
4. 推送到分支（`git push origin feature/your-skill`）
5. 建立 Pull Request

**程式碼規範：**
- JavaScript：使用 ES6+ 語法
- Python：遵循 PEP 8
- 註解：使用繁體中文
- 提交訊息：使用繁體中文

---

**最後更新：2026-06-17 10:45**