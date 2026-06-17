/* 警告：必須遵守 RULES_MINI.md 規範，嚴禁隨意變更此防線！ */

const http = require('http');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const skillsManager = require('./skills_manager');

const PORT = 3000;
const AUTH_FILE_PATH = path.join(__dirname, 'credentials', 'auth-profiles.json');
const BACKUP_PATH = path.join(__dirname, 'server.js.bak');

// Phase 11: 手勢自動觸發巨集開關（全域狀態）
let gestureAutoTriggerEnabled = false;  // 預設關閉

// Phase 12: 技能執行隊列與互斥鎖（防止併發搶奪滑鼠控制權）
const skillExecutionQueue = {
  isRunning: false,
  queue: [],
  maxQueueSize: 10,  // 最大隊列長度，超過則拒絕
};

// 追蹤所有活躍的 Python 子進程（用於僵死進程清理）
const activeProcesses = new Map(); // pid -> { skillName, startTime, killed }
const STALE_THRESHOLD = 120000; // 2 分鐘未完成視為僵死
const CLEANUP_INTERVAL = 30000; // 每 30 秒清理一次

// Phase 13: 日誌檔案大小限制與自動封存
const LOG_SIZE_THRESHOLD = 5 * 1024 * 1024;  // 5MB
const LOG_BACKUP_SUFFIX = '_bak';

/**
 * 檢查日誌檔案大小，超過閾值則自動封存
 * @param {string} logPath - 日誌檔案完整路徑
 */
function rotateLogIfNeeded(logPath) {
  try {
    if (!fs.existsSync(logPath)) return;
    
    const stats = fs.statSync(logPath);
    if (stats.size >= LOG_SIZE_THRESHOLD) {
      const ext = path.extname(logPath);
      const base = logPath.slice(0, -ext.length);
      const backupPath = `${base}${LOG_BACKUP_SUFFIX}${ext}`;
      
      // 如果備份已存在，直接刪除（保留最新一版）
      if (fs.existsSync(backupPath)) {
        fs.unlinkSync(backupPath);
      }
      
      // 重新命名當前日誌為備份
      fs.renameSync(logPath, backupPath);
      console.log('\x1b[33m%s\x1b[0m', `📦 [日誌封存] ${path.basename(logPath)} → ${path.basename(backupPath)}（${(stats.size / 1024 / 1024).toFixed(2)}MB）`);
    }
  } catch (err) {
    console.error('\x1b[31m%s\x1b[0m', `[日誌封存] 失敗：${err.message}`);
  }
}

// Phase 13: 啟動自我健康檢查
function performHealthCheck() {
  console.log('\x1b[36m%s\x1b[0m', '🔍 [啟動檢查] 開始系統環境驗證...');
  const warnings = [];
  
  // 1. 檢查 Python 環境
  try {
    const { execSync } = require('child_process');
    const pythonVersion = execSync('py --version', { encoding: 'utf8', stdio: 'pipe' }).trim();
    console.log('\x1b[32m%s\x1b[0m', `  ✅ Python：${pythonVersion}`);
  } catch (e) {
    warnings.push('Python 環境未安裝或不在 PATH 中（py 指令無效）');
  }
  
  // 2. 檢查必要套件
  const requiredPackages = ['pyautogui', 'Pillow', 'pynput'];
  for (const pkg of requiredPackages) {
    try {
      execSync(`py -m pip show ${pkg}`, { encoding: 'utf8', stdio: 'pipe' });
      console.log(`\x1b[32m%s\x1b[0m`, `  ✅ 套件 ${pkg}：已安裝`);
    } catch (e) {
      warnings.push(`套件 ${pkg} 未安裝（執行 py -m pip install ${pkg}）`);
    }
  }
  
  // 3. 檢查 skills/ 目錄結構
  const skillsRoot = path.resolve(__dirname, '../../skills');
  if (!fs.existsSync(skillsRoot)) {
    warnings.push('skills/ 目錄不存在');
  } else {
    const skills = fs.readdirSync(skillsRoot, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);
    console.log('\x1b[32m%s\x1b[0m', `  ✅ Skills 目錄：找到 ${skills.length} 個技能（${skills.join(', ')}）`);
    
    // 檢查每個技能是否有 SKILL.md
    for (const skill of skills) {
      const skillMd = path.join(skillsRoot, skill, 'SKILL.md');
      if (!fs.existsSync(skillMd)) {
        warnings.push(`技能 ${skill} 缺少 SKILL.md`);
      }
    }
  }
  
  // 4. 檢查執行器目錄結構
  const appDir = path.resolve(__dirname, '../..');
  const criticalFiles = [
    'miniclaw-executor/app/server.js',
    'miniclaw-executor/app/skills_manager.js',
    'miniclaw-web/index.html',
    'miniclaw-web/client.js'
  ];
  for (const file of criticalFiles) {
    if (!fs.existsSync(path.join(appDir, file))) {
      warnings.push(`關鍵檔案缺失：${file}`);
    }
  }
  
  // 輸出警告（黃色）
  if (warnings.length > 0) {
    console.log('\x1b[33m%s\x1b[0m', '⚠️ [啟動檢查] 發現以下問題：');
    warnings.forEach(w => console.log('\x1b[33m%s\x1b[0m', `   - ${w}`));
    console.log('\x1b[33m%s\x1b[0m', '   系統將繼續啟動，但部分功能可能無法正常運作。');
  } else {
    console.log('\x1b[32m%s\x1b[0m', '✅ [啟動檢查] 所有環境驗證通過！');
  }
}

// --- 對話記憶（Session 內滾動記憶，最多保留 20 輪）---
const chatHistory = [];
const MAX_CHAT_HISTORY = 20;

function addToChatHistory(role, text) {
  chatHistory.push({ role, text: text.slice(0, 500) });
  if (chatHistory.length > MAX_CHAT_HISTORY * 2) {
    chatHistory.splice(0, chatHistory.length - MAX_CHAT_HISTORY * 2);
  }
}

function getChatHistoryForAPI() {
  return chatHistory.map(h => ({
    role: h.role === 'user' ? 'user' : 'model',
    parts: [{ text: h.text }]
  }));
}

// 讀取本機 chat_history.txt（短期記憶，供「繼續上次」使用）
function readLocalChatHistory() {
  try {
    const logFile = path.resolve(__dirname, '../../talk_ai/chat_history.txt');
    if (!fs.existsSync(logFile)) return '';
    const content = fs.readFileSync(logFile, 'utf8');
    // 只取最後 2000 字避免 context 過長
    return content.slice(-2000);
  } catch (e) {
    return '';
  }
}

// --- 0. 載入平台模組 ---
function loadPlatformModule() {
  const p = process.platform;
  try {
    if (p === 'win32')  return require('./platform/win');
    if (p === 'darwin') return require('./platform/mac');
    // 嘗試偵測 Android (Termux 環境變數)
    if (process.env.TERMUX_VERSION || process.env.PREFIX?.includes('com.termux')) {
      return require('./platform/android');
    }
    return require('./platform/linux');
  } catch (e) {
    console.log('\x1b[33m%s\x1b[0m', `⚠️ [平台模組] 載入失敗，使用 linux 預設模組: ${e.message}`);
    return require('./platform/linux');
  }
}
const platform = loadPlatformModule();
console.log('\x1b[36m%s\x1b[0m', `🖥️ [平台模組] 已載入：${platform.name}`);

// --- 1. RULES_MINI.md 自動備份自癒守護 ---
function executeSelfBackup() {
  try {
    if (!fs.existsSync(BACKUP_PATH)) {
      fs.copyFileSync(__filename, BACKUP_PATH);
      console.log('\x1b[33m%s\x1b[0m', '💡 [RULES_MINI] 檢測到尚未備份，已自動為您建立 server.js.bak 守護檔案。');
    }
  } catch (err) {
    console.error('建立自動備份出錯:', err);
  }
}
executeSelfBackup();

// --- 2. 憑證與配置檔增量安全寫入 ---
function saveCredentialsSafely(newCreds) {
  try {
    if (!newCreds || typeof newCreds !== 'object') return;
    const dir = path.dirname(AUTH_FILE_PATH);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    let currentCreds = {};
    if (fs.existsSync(AUTH_FILE_PATH)) {
      currentCreds = JSON.parse(fs.readFileSync(AUTH_FILE_PATH, 'utf8'));
    }
    
    // Add-Only 增量合併，不覆蓋既有其他設定
    const merged = { ...currentCreds, ...newCreds };
    fs.writeFileSync(AUTH_FILE_PATH, JSON.stringify(merged, null, 2), 'utf8');
    console.log('\x1b[32m%s\x1b[0m', '💾 [憑證守護] API 金鑰與通訊資料已安全增量同步至 credentials/auth-profiles.json。');
  } catch (err) {
    console.error('安全寫入憑證失敗:', err);
  }
}

// --- 3. 建立原生 HTTP 伺服器與 WebSocket 支援 ---
const server = http.createServer((req, res) => {
  // CORS 跨域支援，讓本地 client.js 可順利 Fetch 輪詢
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, ngrok-skip-browser-warning');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', platform: process.platform }));
  } else if (req.url === '/ollama-status') {
    // 偵測 Ollama 是否在跑，並嘗試綁定（確認 gemma3:3b 可用）
    fetch('http://127.0.0.1:11434/api/tags')
      .then(r => r.json())
      .then(data => {
        const models = (data.models || []).map(m => m.name);
        const hasGemma = models.some(m => m.includes('gemma3'));
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ running: true, models, ready: hasGemma }));
      })
      .catch(() => {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ running: false, models: [], ready: false }));
      });
  } else if (req.url === '/ngrok-url') {
    // 從 ngrok 本地 API 取得公開網址
    fetch('http://127.0.0.1:4040/api/tunnels')
      .then(r => r.json())
      .then(data => {
        const tunnel = (data.tunnels || []).find(t => t.proto === 'https');
        const url = tunnel ? tunnel.public_url : null;
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ url }));
      })
      .catch(() => {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ url: null }));
      });
  } else if (req.url === '/save-local-log' && req.method === 'POST') {
    // 接收前端發來的對話紀錄，附加至本機 chat_history.txt
    let body = '';
    req.on('data', chunk => { body += chunk.toString(); });
    req.on('end', () => {
      try {
        const { role, text, ts } = JSON.parse(body);
        const logDir  = path.resolve(__dirname, '../../talk_ai');
        const logFile = path.join(logDir, 'chat_history.txt');
        if (!fs.existsSync(logDir)) fs.mkdirSync(logDir, { recursive: true });
        
        // Phase 13: 寫入前檢查日誌大小，超過 5MB 自動封存
        rotateLogIfNeeded(logFile);
        
        const line = `[${ts || new Date().toISOString()}] ${role || 'user'}: ${(text || '').slice(0, 500)}\n`;
        fs.appendFileSync(logFile, line, 'utf8');
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: e.message }));
      }
    });
  } else if (req.url === '/webhook/line' && req.method === 'POST') {
    handleLineWebhook(req, res);
  } else {
    res.writeHead(404);
    res.end();
  }
});

// 使用簡易原生 WebSocket 連線升級 (不依賴 socket.io 以保證極速無錯)
const clients = new Set();
server.on('upgrade', (req, socket, head) => {
  if (req.headers['upgrade'] !== 'websocket') {
    socket.destroy();
    return;
  }
  
  // 建立 WebSocket 交握回應（加上 ngrok 相容 header）
  const key = req.headers['sec-websocket-key'];
  const acceptKey = generateWebSocketAcceptKey(key);
  
  socket.write(
    'HTTP/1.1 101 Switching Protocols\r\n' +
    'Upgrade: WebSocket\r\n' +
    'Connection: Upgrade\r\n' +
    'ngrok-skip-browser-warning: true\r\n' +
    `Sec-WebSocket-Accept: ${acceptKey}\r\n\r\n`
  );
  
  clients.add(socket);
  console.log('\x1b[36m%s\x1b[0m', `🔌 [WebSocket] 網頁端主控台已成功對接！當前連接數: ${clients.size}`);
  
  // Phase 3: 連線建立後主動推送技能清單
  try {
    const skillsMetadata = skillsManager.getSkillsMetadata();
    sendWSMessage(socket, { type: 'skills-list', skills: skillsMetadata });
    console.log('\x1b[36m%s\x1b[0m', `📦 [Skills] 已推送技能清單至前端 (${skillsMetadata.length} 個技能)`);
  } catch (e) {
    console.warn('[Skills] 推送技能清單失敗:', e.message);
  }
  
  // 處理 incoming 資料幀
  socket.on('data', (buffer) => {
    const parsed = parseWebSocketFrame(buffer);
    if (parsed) {
      handleClientMessage(parsed, socket);
    }
  });
  
  socket.on('close', () => {
    clients.delete(socket);
    console.log('🔌 [WebSocket] 網頁端已中斷連線。');
  });
  
  socket.on('error', () => {
    clients.delete(socket);
  });
});

// --- 4. WebSocket 事件轉發與指令分發 ---
function handleClientMessage(msg, socket) {
  if (msg.type === 'sync-credentials') {
    saveCredentialsSafely(msg.data);
  } else if (msg.type === 'sys-restore') {
    triggerSelfHealRestoration(socket);
  } else if (msg.type === 'sys-status') {
    // 回傳真實系統狀態，不走 AI
    const os = require('os');
    const uptime = Math.floor(os.uptime() / 60);
    const freeMem = Math.round(os.freemem() / 1024 / 1024);
    const totalMem = Math.round(os.totalmem() / 1024 / 1024);
    const usedMem = totalMem - freeMem;
    const memPct = Math.round(usedMem / totalMem * 100);
    const reply = `🖥️ 系統狀態回報\n` +
      `平台：${platform.name} (${process.platform})\n` +
      `Node.js：${process.version}\n` +
      `記憶體：${usedMem}MB / ${totalMem}MB (${memPct}%)\n` +
      `系統運行時間：${uptime} 分鐘\n` +
      `✅ 終端連線正常，伺服器運作中。`;
    sendWSMessage(socket, { type: 'ai-response', reply });
  } else if (msg.type === 'shutdown') {
    sendWSMessage(socket, { type: 'ai-response', reply: '🔴 執行器正在關閉...' });
    setTimeout(() => process.exit(0), 500);
  } else if (msg.type === 'user-command') {
    processUserCommand(msg.data.text, msg.data.platform, socket);
  } else if (msg.type === 'test-remote') {
    testRemoteCredentials(msg.data, socket);
  } else if (msg.type === 'multi-file-write') {
    handleMultiFileWrite(msg.data, socket);
  } else if (msg.type === 'sync-gesture-setting') {
    // Phase 11: 同步手勢自動觸發開關狀態
    gestureAutoTriggerEnabled = msg.data.enabled;
    console.log(`🎯 [手勢設定] 自動觸發巨集：${gestureAutoTriggerEnabled ? '啟用' : '關閉'}`);
  }
}

// 多檔案寫入處理（手動模式 FILE 標籤分流）
function handleMultiFileWrite(data, socket) {
  const files = data.files || [];
  if (files.length === 0) {
    sendWSMessage(socket, { type: 'ai-response', reply: '⚠️ 未收到任何檔案資料。' });
    return;
  }

  let results = [];
  for (const file of files) {
    const targetPath = file.path;
    const content = file.content;
    try {
      // 確保目錄存在
      const dir = path.dirname(targetPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.writeFileSync(targetPath, content, 'utf8');
      results.push(`✅ ${targetPath} (${content.length} 字元)`);
      console.log(`📝 [多檔案寫入] 已寫入: ${targetPath}`);
    } catch (err) {
      results.push(`❌ ${targetPath}: ${err.message}`);
      console.error(`⚠️ [多檔案寫入] 失敗: ${targetPath} - ${err.message}`);
    }
  }

  const replyText = `📁 多檔案寫入結果 (${files.length} 個檔案):\n${results.join('\n')}`;
  sendWSMessage(socket, { type: 'ai-response', reply: replyText, output: results.join('\n') });
  triggerExternalWebhook(replyText);
}

// 驗證遠端 LINE / Discord 機器人憑證連線
async function testRemoteCredentials(data, socket) {
  const { channel, lineToken, lineSecret, discordToken, discordChannel } = data;
  console.log(`🤖 收到遠端憑證測試請求 [${channel.toUpperCase()}]`);

  if (channel === 'discord') {
    try {
      const response = await fetch('https://discord.com/api/v10/users/@me', {
        headers: { Authorization: `Bot ${discordToken}` }
      });
      if (response.ok) {
        const userInfo = await response.json();
        sendWSMessage(socket, {
          type: 'remote-test-result',
          success: true,
          message: `Discord 機器人連線成功！已成功識別為: ${userInfo.username}#${userInfo.discriminator || '0000'}`
        });
      } else {
        const errData = await response.json().catch(() => ({}));
        const errMsg = errData.message || `HTTP 錯誤碼: ${response.status}`;
        sendWSMessage(socket, {
          type: 'remote-test-result',
          success: false,
          message: `Discord API 驗證失敗: ${errMsg}`
        });
      }
    } catch (err) {
      sendWSMessage(socket, {
        type: 'remote-test-result',
        success: false,
        message: `無法連線至 Discord 伺服器: ${err.message}`
      });
    }
  } else if (channel === 'line') {
    try {
      const response = await fetch('https://api.line.me/v2/bot/info', {
        headers: { Authorization: `Bearer ${lineToken}` }
      });
      if (response.ok) {
        const botInfo = await response.json();
        sendWSMessage(socket, {
          type: 'remote-test-result',
          success: true,
          message: `LINE 機器人連線成功！已成功識別 Bot 名稱: ${botInfo.displayName}`
        });
      } else {
        const errData = await response.json().catch(() => ({}));
        const errMsg = errData.message || `HTTP 錯誤碼: ${response.status}`;
        sendWSMessage(socket, {
          type: 'remote-test-result',
          success: false,
          message: `LINE API 驗證失敗: ${errMsg}`
        });
      }
    } catch (err) {
      sendWSMessage(socket, {
        type: 'remote-test-result',
        success: false,
        message: `無法連線至 LINE 伺服器: ${err.message}`
      });
    }
  } else {
    sendWSMessage(socket, {
      type: 'remote-test-result',
      success: false,
      message: '未知的遠端渠道類型'
    });
  }
}

// 實施代碼自癒還原
function triggerSelfHealRestoration(socket) {
  try {
    if (fs.existsSync(BACKUP_PATH)) {
      fs.copyFileSync(BACKUP_PATH, __filename);
      console.log('\x1b[31m%s\x1b[0m', '⚠️ [自癒還原] 收到網頁端還原指令！已將 server.js.bak 覆蓋主執行程式。');
      
      broadcast({
        type: 'ai-response',
        reply: '⚙️ <b>[自癒系統防線]</b>：已將 core 邏輯完美復原！正在重啟伺服器確保修復正常...'
      });
      
      // 1.5 秒後重啟進程
      setTimeout(() => {
        process.exit(0); // 配合啟動腳本的無窮迴圈即可完美重啟自癒！
      }, 1500);
    }
  } catch (err) {
    console.error('自癒還原失敗:', err);
  }
}

// --- 5. 核心 AI 命令解析與平台執行 ---
function extractRequestedFolderName(text) {
  const quoted = text.match(/[「『"']([^」』"']{1,80})[」』"']/);
  let name = quoted ? quoted[1] : '';

  if (!name) {
    const beforeFolder = text.match(/(?:新增|建立|創建|創立)\s*(?:一個)?\s*([^，。,.「」"'\s]{1,80})\s*資料夾/);
    const afterFolder = text.match(/資料夾\s*(?:叫|名為|名稱是|是)?\s*([^，。,.「」"'\s]{1,80})/);
    name = (beforeFolder && beforeFolder[1]) || (afterFolder && afterFolder[1]) || '';
  }

  name = name.trim().replace(/[<>:"/\\|?*\x00-\x1F]/g, '_');
  if (!name || name === '一個' || name === '資料夾') return '小龍蝦作業';
  return name.slice(0, 80);
}

function resolveRequestedListPath(text) {
  const home = require('os').homedir();
  const cleaned = text.replace(/[「」『』"']/g, ' ');

  if (cleaned.includes('桌面') || cleaned.toLowerCase().includes('desktop')) {
    return path.join(home, 'Desktop');
  }
  if (cleaned.includes('下載') || cleaned.toLowerCase().includes('downloads')) {
    return path.join(home, 'Downloads');
  }

  const windowsPath = cleaned.match(/[a-zA-Z]:[\\/][^\s，。,.]+/);
  if (windowsPath) return windowsPath[0].replace(/\//g, '\\');

  const slashPath = cleaned.match(/(?:user\/user|users\/user|\/users\/user|~\/[^\s，。,.]+|[^\s，。,.]+\/[^\s，。,.]+)/i);
  if (slashPath) {
    const raw = slashPath[0].replace(/\\/g, '/').replace(/^~\//, '');
    const lower = raw.toLowerCase();
    if (lower === 'user/user' || lower === 'users/user' || lower === '/users/user') return home;
    if (lower.startsWith('user/user/')) return path.join(home, raw.slice('user/user/'.length));
    if (lower.startsWith('users/user/')) return path.join(home, raw.slice('users/user/'.length));
  }

  return path.join(home, 'Downloads');
}

function sendDirectoryListing(socket, targetPath) {
  try {
    const stats = fs.statSync(targetPath);
    if (!stats.isDirectory()) {
      sendWSMessage(socket, { type: 'ai-response', reply: `⚠️ 這不是資料夾：${targetPath}` });
      return;
    }

    const entries = fs.readdirSync(targetPath, { withFileTypes: true })
      .slice(0, 80)
      .map((entry) => `${entry.isDirectory() ? '[DIR] ' : '      '}${entry.name}`);
    const output = entries.length ? entries.join('\n') : '(空資料夾)';
    sendWSMessage(socket, {
      type: 'ai-response',
      reply: `📂 ${targetPath} 的內容：`,
      output
    });
  } catch (err) {
    sendWSMessage(socket, { type: 'ai-response', reply: `⚠️ 無法讀取資料夾：${err.message}` });
  }
}

async function processOfflineFallback(text, clientPlatform, socket) {
  console.log(`🤖 [離線模式] 處理請求 : "${text}"`);
  
  const query = text.toLowerCase();
  
  // 截圖
  if (query.includes('截圖') || query.includes('畫面') || query.includes('螢幕')) {
    executeScreenshotAction(socket);
    return;
  }

  // 開瀏覽器查詢（Android 核心功能，其他平台也支援）
  if (query.includes('開瀏覽器') || query.includes('幫我查') || query.includes('搜尋') || query.includes('查一下')) {
    // 從文字中提取查詢關鍵字
    let searchQuery = text
      .replace(/幫我查|查一下|開瀏覽器查|搜尋|幫我搜尋/g, '')
      .trim();
    const url = `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`;
    const cmd = platform.openBrowser(url);
    executeShellCommand(cmd, socket, `🌐 正在用 ${platform.name} 開瀏覽器搜尋：${searchQuery}`);
    return;
  }

  // Android 專屬：查電量
  if (query.includes('電量') || query.includes('電池')) {
    if (platform.battery) {
      executeShellCommand(platform.battery(), socket, '🔋 正在查詢電池狀態...');
    } else {
      sendWSMessage(socket, { type: 'ai-response', reply: `⚠️ ${platform.name} 不支援電量查詢。` });
    }
    return;
  }

  // Android 專屬：拍照
  if (query.includes('拍照') || query.includes('拍一張') || query.includes('相機')) {
    if (platform.camera) {
      const photoPath = path.join(__dirname, 'temp_photo.jpg');
      executeShellCommand(platform.camera(photoPath), socket, '📸 正在用相機拍照...');
    } else {
      sendWSMessage(socket, { type: 'ai-response', reply: `⚠️ ${platform.name} 不支援遠端拍照。` });
    }
    return;
  }

  // Android 專屬：取得位置
  if (query.includes('定位') || query.includes('位置') || query.includes('gps')) {
    if (platform.location) {
      executeShellCommand(platform.location(), socket, '📍 正在取得 GPS 位置...');
    } else {
      sendWSMessage(socket, { type: 'ai-response', reply: `⚠️ ${platform.name} 不支援 GPS 定位。` });
    }
    return;
  }

  // 關機
  if (query.includes('開關機') || query.includes('關機')) {
    const { cmd, msg } = platform.shutdown();
    executeShellCommand(cmd, socket, msg);
    return;
  }

  // 建立資料夾
  if ((query.includes('資料夾') && (query.includes('建立') || query.includes('新增') || query.includes('創建') || query.includes('創立'))) || query.includes('小龍蝦作業')) {
    const folderName = extractRequestedFolderName(text);
    const desktopPath = path.join(require('os').homedir(), 'Desktop', folderName);
    try {
      fs.mkdirSync(desktopPath, { recursive: true });
      if (folderName === '小龍蝦作業') {
        const introFile = path.join(desktopPath, '介紹.txt');
        fs.writeFileSync(introFile, '小龍蝦自動化 AI 運作正常！', 'utf8');
      }
      const reply = `📁 已為您在桌面成功建立「${folderName}」資料夾！`;
      sendWSMessage(socket, { type: 'ai-response', reply, output: `STATUS: SUCCESS\n${desktopPath}` });
      triggerExternalWebhook(reply);
    } catch (err) {
      sendWSMessage(socket, { type: 'ai-response', reply: `⚠️ 建立資料夾失敗：${err.message}` });
    }
    return;
  }

  // 網路診斷
  if (query.includes('網路狀況') || query.includes('網路連線') || query.includes('檢查網路') ||
      query.includes('連線狀況') || query.includes('查看網路') ||
      query.includes('ping') || query.includes('ipconfig') || query.includes('ifconfig')) {
    executeShellCommand(platform.networkCheck(), socket, '🌐 正在檢測網路狀況...');
    return;
  }

  // 查看檔案
  if (query.includes('查看') || query.includes('列出') || query.includes('看') || query.includes('下載區') ||
      query.includes('下載資料夾') || query.includes('有什麼檔案') || query.includes('有哪些檔案') ||
      query.includes('有什麼') || query.includes('目錄')) {
    sendDirectoryListing(socket, resolveRequestedListPath(text));
    return;
  }

  // 啟動錄製器 (recorder.py)
  if (query.includes('啟動錄製器') || query.includes('開啟錄製器') || query.includes('錄製器')) {
    const recorderPath = path.resolve(__dirname, '../../test-lab/alltest/recorder.py');
    // 先安裝依賴（靜默），再啟動 recorder（新視窗）
    const installCmd = process.platform === 'win32'
      ? `py -m pip install pyautogui Pillow pynput opencv-python --quiet && start cmd /k "py \"${recorderPath}\""`
      : `py -m pip install pyautogui Pillow pynput opencv-python --quiet && py "${recorderPath}" &`;
    sendWSMessage(socket, { type: 'ai-response', reply: '⏺️ 正在啟動操作錄製器，請稍後...' });
    exec(installCmd, { timeout: 60000 }, (err) => {
      if (err && !err.killed) {
        sendWSMessage(socket, { type: 'ai-response', reply: `⚠️ 錄製器啟動失敗：${err.message}` });
      }
    });
    return;
  }

  // 執行自動化腳本 (auto_run.py)
  if (query.includes('執行自動化腳本') || query.includes('執行腳本') || query.includes('auto_run')) {
    const autoRunPath = path.resolve(__dirname, '../../test-lab/alltest/auto_run.py');
    if (!fs.existsSync(autoRunPath)) {
      sendWSMessage(socket, { type: 'ai-response', reply: '❌ 找不到 auto_run.py，請先錄製操作並讓 Miniclaw 生成腳本。' });
      return;
    }
    const runCmd = process.platform === 'win32'
      ? `start cmd /k "py \"${autoRunPath}\""`
      : `py "${autoRunPath}" &`;
    sendWSMessage(socket, { type: 'ai-response', reply: '▶️ 正在啟動自動化腳本...' });
    exec(runCmd, { timeout: 10000 }, (err) => {
      if (err && !err.killed) {
        sendWSMessage(socket, { type: 'ai-response', reply: `⚠️ 腳本啟動失敗：${err.message}` });
      }
    });
    return;
  }
  
  // 其他：無法處理
  return false;
}

async function processUserCommand(text, clientPlatform, socket) {
  console.log(`🤖 收到 AI 處理請求 : "${text}"`);
  
  // 記錄使用者輸入到對話歷史
  addToChatHistory('user', text);
  
  // 偵測「繼續上次」等關鍵字，注入短期記憶
  let enrichedPrompt = text;
  const continueKeywords = ['繼續上次', '繼續之前', '上次做到哪', '之前做過', '繼續做', '繼續'];
  const needsHistory = continueKeywords.some(kw => text.includes(kw));
  if (needsHistory) {
    const localHistory = readLocalChatHistory();
    if (localHistory) {
      enrichedPrompt = `[以下是之前的對話紀錄摘要]\n${localHistory}\n\n[使用者現在的指令]\n${text}`;
      console.log('📚 [對話記憶] 已注入短期記憶（chat_history.txt）');
    }
  }
  
  // Phase 2: 技能觸發偵測 → 動態注入完整 Body（第二層深度載入）
  try {
    const skillTrigger = skillsManager.formatTriggeredSkillsForPrompt(text);
    if (skillTrigger) {
      enrichedPrompt += skillTrigger;
      console.log(`🎯 [技能觸發] 已偵測並注入技能指引至上下文`);
    }
  } catch (e) {
    // 技能觸發失敗不影響主流程，僅記錄警告
    console.warn(`[技能觸發] 偵測異常 (不影響主流程): ${e.message}`);
  }
  
  callAIModelWithFailover(enrichedPrompt, socket, clientPlatform);
}

// 本地原生截圖引擎（使用 platform 模組）
function executeScreenshotAction(socket) {
  const tempImgPath = path.join(__dirname, 'temp_screenshot.jpg');
  const cmd = platform.screenshot(tempImgPath);
  
  exec(cmd, (err) => {
    if (err) {
      console.error('截圖命令出錯:', err);
      sendWSMessage(socket, { type: 'ai-response', reply: `❌ 螢幕畫面捕獲失敗！[${platform.name}] 請確認系統權限。` });
      return;
    }
    try {
      if (fs.existsSync(tempImgPath)) {
        const base64 = fs.readFileSync(tempImgPath, 'base64');
        sendWSMessage(socket, { type: 'sys-action', action: 'screenshot', data: base64 });
        fs.unlinkSync(tempImgPath);
      }
    } catch (e) {
      console.error('讀取截圖失敗:', e);
    }
  });
}

// 執行 Shell 命令並回傳結果
function executeShellCommand(cmd, socket, replyText) {
  exec(cmd, { timeout: 15000 }, (err, stdout, stderr) => {
    const output = (stdout || stderr || '').slice(0, 400);
    sendWSMessage(socket, {
      type: 'ai-response',
      reply: replyText,
      output: output + (((stdout || stderr || '').length > 400) ? '\n...(輸出過長，已截斷)' : '')
    });
    triggerExternalWebhook(replyText + '\n' + output);
  });
}

// --- 6. AI 故障自適應切換引擎 ---
async function callAIModelWithFailover(prompt, socket, clientPlatform) {
  let credentials = {};
  if (fs.existsSync(AUTH_FILE_PATH)) {
    try {
      credentials = JSON.parse(fs.readFileSync(AUTH_FILE_PATH, 'utf8'));
    } catch (e) {}
  }
  
  const providers = ['openrouter', 'gemini', 'openai', 'ollama'];
  const priority = credentials.aiPriority || 'gemini';

  // 重新調整順序，將優先的放最前面
  const order = [priority, ...providers.filter(p => p !== priority)];

  let success = false;
  let replyContent = '';

  // 取得 Google Access Token（前端 OAuth 同步過來的）
  const googleToken = credentials.googleAccessToken || '';

  for (const provider of order) {
    if (success) break;

    // apiKey 可能直接在根層或包在 data 裡
    const key = credentials.apiKey || (credentials.data && credentials.data.apiKey);
    const openrouterKey = credentials.openrouterApiKey || (credentials.data && credentials.data.openrouterApiKey);
    const openrouterModel = credentials.openrouterModel || 'deepseek/deepseek-r1:free';
    if (!key && !googleToken && provider !== 'ollama' && provider !== 'openrouter') continue;
    if (provider === 'openrouter' && !openrouterKey) continue;

    console.log(`📡 正在嘗試呼叫 AI 模組 [${provider.toUpperCase()}] ...`);

    try {
      if (provider === 'gemini') {
        replyContent = await fetchGeminiAPI(prompt, key, googleToken);
        success = true;
      } else if (provider === 'openai') {
        replyContent = await fetchOpenAIAPI(prompt, key);
        success = true;
      } else if (provider === 'ollama') {
        // Ollama 不需要 key，直接嘗試
        replyContent = await fetchOllamaAPI(prompt);
        success = true;
      } else if (provider === 'openrouter') {
        // OpenRouter 免費模型（支援 deepseek-r1 / llama-3.3-70b / qwen-2.5-72b 等）
        replyContent = await fetchOpenRouterAPI(prompt, openrouterKey, openrouterModel);
        success = true;
      }
    } catch (err) {
      // 捕獲 401、429、500 等錯誤，亮橘色日誌警示，自動輪詢下一個配置
      console.log('\x1b[33m%s\x1b[0m', `⚠️ [AI 故障轉移] ${provider.toUpperCase()} 呼叫失敗！錯誤代碼: ${err.message || 500}。正自動尋求下一個備用 AI 配置...`);
    }
  }
  
  if (success) {
    const lines = replyContent.split('\n');
    let chatText = '';
    let cmdToRun = '';
    for (const line of lines) {
      if (line.trim().startsWith('聊天:')) chatText += line.replace('聊天:', '').trim() + '\n';
      else if (line.trim().startsWith('指令:')) cmdToRun = line.replace('指令:', '').trim();
      else if (!chatText && !cmdToRun) chatText += line + '\n';
    }
    chatText = chatText.trim() || replyContent.trim();
    
    // Phase 4: 攔截 [技能名稱 參數] 標籤並執行技能腳本
    const skillTags = skillsManager.parseSkillTags(chatText);
    let skillExecutionResults = [];
    
    if (skillTags.length > 0) {
      console.log(`🎯 [Phase 4] 偵測到 ${skillTags.length} 個技能標籤，準備執行...`);
      
      for (const tag of skillTags) {
        // Phase 12: 使用隊列機制執行技能（防止併發搶奪滑鼠控制權）
        const result = await executeSkillWithQueue(tag.skillName, tag.args);
        if (result.success) {
          skillExecutionResults.push(`✅ [${tag.skillName}] 執行成功：\n${result.output}`);
          
          // Phase 9: 手勢辨識 → 巨集自動觸發聯動（Phase 11 加入開關判斷）
          if (tag.skillName === 'gesture-recognizer' && result.output) {
            const matchedMatch = result.output.match(/\[MATCHED\]\s*([MWOV])/i);
            if (matchedMatch) {
              const gestureChar = matchedMatch[1].toUpperCase();
              
              // Phase 11: 檢查開關狀態
              if (!gestureAutoTriggerEnabled) {
                console.log(`ℹ️ [Phase 9] 手勢辨識到 [${gestureChar}]，但自動觸發功能已關閉`);
                skillExecutionResults.push(`ℹ️ 手勢辨識成功：[MATCHED] ${gestureChar}（自動觸發已關閉）`);
              } else {
                const macroName = `遊戲手勢_${gestureChar}`;
                console.log(`🎯 [Phase 9] 手勢辨識匹配到 [${gestureChar}]，自動觸發巨集：${macroName}`);
                
                // 延遲 500ms 讓使用者看到手勢辨識結果
                await new Promise(resolve => setTimeout(resolve, 500));
                
                // Phase 12: 巨集觸發也使用隊列
                const macroResult = await executeSkillWithQueue('macro-recorder', `play ${macroName}`);
                if (macroResult.success) {
                  skillExecutionResults.push(`✅ [macro-recorder] 手勢巨集觸發成功：\n${macroResult.output}`);
                } else {
                  // 防錯機制：巨集不存在時提供友善提示
                  const errorMsg = macroResult.error || '';
                  if (errorMsg.includes('找不到巨集') || errorMsg.includes('找不到')) {
                    skillExecutionResults.push(`ℹ️ [macro-recorder] 手勢辨識成功，但系統內未找到名為「${macroName}」的預錄巨集，請先使用 macro-recorder 進行錄製。`);
                  } else {
                    skillExecutionResults.push(`❌ [macro-recorder] 巨集執行失敗：\n${macroResult.error}`);
                  }
                }
              }
            }
          }
        } else {
          skillExecutionResults.push(`❌ [${tag.skillName}] 執行失敗：\n${result.error}`);
        }
      }
      
      // 將技能執行結果附加到回覆
      if (skillExecutionResults.length > 0) {
        chatText += '\n\n---\n\n🔧 **技能執行結果**：\n\n' + skillExecutionResults.join('\n\n');
      }
    }
    
    sendWSMessage(socket, { type: 'ai-response', reply: chatText });
    
    if (cmdToRun) {
      if (cmdToRun.startsWith('miniclaw:screenshot')) executeScreenshotAction(socket);
      else executeShellCommand(cmdToRun, socket, `⚙️ AI 正在執行指令...\n> ${cmdToRun}`);
    }
  } else {
    // 所有金鑰皆失敗，向網頁端通知 AI 額度已耗盡/失效
    sendWSMessage(socket, { type: 'ai-quota-exhausted' });
    // 降級為離線控制回覆
    const handled = await processOfflineFallback(prompt, clientPlatform || 'win32', socket);
    if (handled === false) {
      sendWSMessage(socket, {
        type: 'ai-response',
        reply: '🦞 <b>小龍蝦自癒助手 (方案 B 離線模式)</b>：AI 金鑰皆不可用或流量超載。但我依然可以在本地為您代勞電腦控制！您可以試試輸入「<b>幫我截圖</b>」或「<b>桌面建立資料夾</b>」。'
      });
    }
  }
}

// --- 各 AI 接口封裝 (標準 fetch 實作) ---
// 動態載入可用技能清單（僅存在 skills 目錄且有 SKILL.md 時才附加）
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

const SYSTEM_PROMPT = `你現在是『Miniclaw 小龍蝦控制中樞』的專屬本地端 AI 助手。你已被授權最高系統操作權限，可透過終端機執行任意指令。

請務必嚴格遵守以下輸出格式規範：
聊天: [你想對使用者說的話，例如解釋你要做什麼]
指令: [需要執行的終端機指令]

- 如果要求需要控制電腦或查詢系統，請在第二行加上「指令:」並附上終端機指令（若需截圖請用 miniclaw:screenshot）。
- 如果只是純聊天，則「指令:」可留空或不寫。
- 請簡明扼要，聊天長度盡量控制在 100 字內。${SKILLS_PROMPT_SEGMENT}`;

async function fetchGeminiAPI(prompt, key, googleToken) {
  // 使用支援 systemInstruction 的 gemini-1.5-flash
  // 優先用 Google Access Token（Bearer），備援用 API Key（query param）
  const hasToken = googleToken && googleToken.length > 10;
  const hasKey = key && key.length > 10;
  if (!hasToken && !hasKey) throw new Error('no_gemini_auth');

  const geminiUrl = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent';
  const url = hasToken ? geminiUrl : `${geminiUrl}?key=${key}`;
  const authHeader = hasToken ? { 'Authorization': `Bearer ${googleToken}` } : {};
  
  try {
    const response = await fetchWithTimeout(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeader },
      body: JSON.stringify({
        contents: [{ parts: [{ text: `${prompt} (請簡明扼要，控制在 100 字內)` }] }],
        systemInstruction: {
          parts: [{ text: SYSTEM_PROMPT }]
        }
      })
    }, 5000);
    
    if (response.ok) {
      const data = await response.json();
      return data.candidates[0].content.parts[0].text;
    }
    // Google token 過期時改用 apiKey 重試
    if (hasToken && hasKey && response.status === 401) {
      console.log('⚠️ [Gemini] Google Token 過期，改用 API Key ...');
      const retryUrl = `${geminiUrl}?key=${key}`;
      const retry = await fetchWithTimeout(retryUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: `${prompt} (請簡明扼要，控制在 100 字內)` }] }],
          systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] }
        })
      }, 5000);
      if (retry.ok) {
        const d = await retry.json();
        return d.candidates[0].content.parts[0].text;
      }
    }
  } catch (err) {
    console.log('⚠️ [Gemini 1.5] 呼叫失敗，正自動降級至 gemini-pro ...');
  }

  // 降級方案：gemini-pro
  if (!hasKey) throw new Error('no_api_key_for_fallback');
  const fallbackUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${key}`;
  const response = await fetchWithTimeout(fallbackUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents: [{ parts: [{ text: `[系統授權設定: ${SYSTEM_PROMPT}]\n\n使用者指令: ${prompt} (請簡明扼要，控制在 100 字內)` }] }]
    })
  }, 5000);
  
  if (!response.ok) throw new Error(response.status);
  const data = await response.json();
  return data.candidates[0].content.parts[0].text;
}

async function fetchOpenAIAPI(prompt, key) {
  const isOpenround = key && key.startsWith('sk-or-');
  const url = isOpenround ? 'https://openrouter.ai/api/v1/chat/completions' : 'https://api.openai.com/v1/chat/completions';
  const modelName = isOpenround ? 'gpt-4o-mini' : 'gpt-3.5-turbo';

  const response = await fetchWithTimeout(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${key}`
    },
    body: JSON.stringify({
      model: modelName,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: `${prompt} (限制 100 字內)` }
      ]
    })
  }, 5000);

  if (!response.ok) throw new Error(response.status);
  const data = await response.json();
  return data.choices[0].message.content;
}

// OpenRouter 免費模型獨立接口
// 支援：deepseek/deepseek-r1:free、meta-llama/llama-3.3-70b-instruct:free、qwen/qwen-2.5-72b-instruct:free
async function fetchOpenRouterAPI(prompt, key, model) {
  const url = 'https://openrouter.ai/api/v1/chat/completions';
  const useModel = model || 'deepseek/deepseek-r1:free';

  const response = await fetchWithTimeout(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${key}`,
      'HTTP-Referer': 'https://miniclaw.local',
      'X-Title': 'Miniclaw'
    },
    body: JSON.stringify({
      model: useModel,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: `${prompt} (限制 100 字內)` }
      ]
    })
  }, 8000);  // 免費模型 RPM 限制，給 8s timeout

  if (!response.ok) {
    const errText = await response.text().catch(() => '');
    throw new Error(`${response.status}${errText ? ': ' + errText.slice(0, 100) : ''}`);
  }
  const data = await response.json();
  if (!data.choices || data.choices.length === 0) {
    throw new Error('openrouter_no_choices');
  }
  return data.choices[0].message.content;
}

async function fetchOllamaAPI(prompt) {
  const url = 'http://127.0.0.1:11434/api/generate';
  const response = await fetchWithTimeout(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'gemma3:3b',
      prompt: `${SYSTEM_PROMPT}\n\n使用者指令: ${prompt} (請簡明扼要，控制在 100 字內)`,
      stream: false
    })
  }, 30000); // 本地模型給較長 timeout
  if (!response.ok) throw new Error(response.status);
  const data = await response.json();
  return data.response;
}

// --- 7. LINE/DC 遠端 Webhook 推播 ---
function triggerExternalWebhook(text) {
  try {
    let credentials = {};
    if (fs.existsSync(AUTH_FILE_PATH)) {
      try { credentials = JSON.parse(fs.readFileSync(AUTH_FILE_PATH, 'utf8')); } catch (e) {}
    }
    const remote = credentials.remote;
    if (!remote) return;

    // LINE push message
    if (remote.type === 'line' && remote.line && remote.line.token && remote.line.userId) {
      fetch('https://api.line.me/v2/bot/message/push', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${remote.line.token}`
        },
        body: JSON.stringify({
          to: remote.line.userId,
          messages: [{ type: 'text', text: text.slice(0, 500) }]
        })
      }).catch(err => console.error('⚠️ [LINE 推播失敗]:', err.message));
    }

    // Discord channel message
    if (remote.type === 'discord' && remote.discord && remote.discord.token && remote.discord.channel) {
      fetch(`https://discord.com/api/v10/channels/${remote.discord.channel}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bot ${remote.discord.token}`
        },
        body: JSON.stringify({ content: text.slice(0, 2000) })
      }).catch(err => console.error('⚠️ [Discord 推播失敗]:', err.message));
    }
  } catch (err) {
    console.error('⚠️ [Webhook 推播失敗]:', err);
  }
}

// --- 7.5 LINE Webhook 接收處理 ---
function handleLineWebhook(req, res) {
  let body = '';
  req.on('data', chunk => { body += chunk.toString(); });
  req.on('end', async () => {
    // 立即回 200，LINE 要求 5 秒內回應
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok' }));

    let payload;
    try { payload = JSON.parse(body); } catch (e) { return; }

    const events = payload.events || [];
    for (const event of events) {
      if (event.type !== 'message' || event.message.type !== 'text') continue;

      const userText = event.message.text;
      const replyToken = event.replyToken;
      console.log(`📱 [LINE Webhook] 收到訊息: "${userText}"`);

      // 廣播到所有 WebSocket 客戶端（讓網頁也能看到）
      broadcast({ type: 'ai-response', reply: `📱 [LINE] ${userText}` });

      // 執行指令並取得結果
      const result = await executeCommandAndGetResult(userText);

      // 回覆 LINE
      let credentials = {};
      if (fs.existsSync(AUTH_FILE_PATH)) {
        try { credentials = JSON.parse(fs.readFileSync(AUTH_FILE_PATH, 'utf8')); } catch (e) {}
      }
      const token = credentials.remote && credentials.remote.line && credentials.remote.line.token;

      if (token && replyToken) {
        fetch('https://api.line.me/v2/bot/message/reply', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            replyToken,
            messages: [{ type: 'text', text: result.slice(0, 500) }]
          })
        }).catch(err => console.error('⚠️ [LINE 回覆失敗]:', err.message));
      }

      // 同步廣播結果到網頁
      broadcast({ type: 'ai-response', reply: `🤖 [LINE 指令結果] ${result}` });
    }
  });
}

// 執行指令並回傳文字結果（供 LINE Webhook 使用）
function executeCommandAndGetResult(text) {
  return new Promise((resolve) => {
    const query = text.toLowerCase();

    if (query.includes('截圖') || query.includes('畫面') || query.includes('螢幕')) {
      resolve('📸 截圖功能需透過網頁端查看，請開啟小龍蝦網頁確認結果。');
      return;
    }

    if (query.includes('開瀏覽器') || query.includes('幫我查') || query.includes('搜尋') || query.includes('查一下')) {
      const searchQuery = text.replace(/幫我查|查一下|開瀏覽器查|搜尋|幫我搜尋/g, '').trim();
      const url = `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`;
      exec(platform.openBrowser(url), { timeout: 5000 }, () => {});
      resolve(`🌐 已在 ${platform.name} 開啟瀏覽器搜尋：${searchQuery}`);
      return;
    }

    if (query.includes('電量') || query.includes('電池')) {
      if (platform.battery) {
        exec(platform.battery(), { timeout: 5000 }, (err, stdout) => {
          resolve(stdout || '無法取得電量資訊');
        });
      } else {
        resolve(`⚠️ ${platform.name} 不支援電量查詢。`);
      }
      return;
    }

    if (query.includes('網路') || query.includes('ping') || query.includes('ipconfig') || query.includes('連線')) {
      exec(platform.networkCheck(), { timeout: 15000 }, (err, stdout, stderr) => {
        resolve((stdout || stderr || '執行完成').slice(0, 400));
      });
      return;
    }

    if (query.includes('查看') || query.includes('列出') || query.includes('檔案') || query.includes('下載')) {
      const downloadsPath = require('os').homedir() + (process.platform === 'win32' ? '\\Downloads' : '/Downloads');
      exec(platform.listFiles(downloadsPath), { timeout: 10000 }, (err, stdout, stderr) => {
        resolve((stdout || stderr || '執行完成').slice(0, 400));
      });
      return;
    }

    if (query.includes('關機')) {
      const { cmd, msg } = platform.shutdown();
      exec(cmd, { timeout: 5000 }, () => {});
      resolve(msg);
      return;
    }

    if (query.includes('取消關機')) {
      const { cancel } = platform.shutdown();
      if (cancel) exec(cancel, { timeout: 5000 }, () => {});
      resolve('✅ 已取消關機指令。');
      return;
    }

    // 其他訊息交給 AI 處理
    let credentials = {};
    if (fs.existsSync(AUTH_FILE_PATH)) {
      try { credentials = JSON.parse(fs.readFileSync(AUTH_FILE_PATH, 'utf8')); } catch (e) {}
    }
    const key = credentials.apiKey || (credentials.data && credentials.data.apiKey);
    if (key) {
      fetchGeminiAPI(text, key)
        .then(reply => resolve(reply))
        .catch(() => resolve('🦞 AI 暫時無法回應，請稍後再試。'));
    } else {
      resolve('🦞 收到！但目前沒有 API 金鑰，無法呼叫 AI。請在網頁端設定金鑰。');
    }
  });
}

// --- 8. WebSocket 協定框架解析工具 (極致純淨，免依賴安裝) ---
function generateWebSocketAcceptKey(key) {
  const crypto = require('crypto');
  return crypto
    .createHash('sha1')
    .update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11', 'binary')
    .digest('base64');
}

function parseWebSocketFrame(buffer) {
  const firstByte = buffer[0];
  const isFinalFrame = ((firstByte >>> 7) & 0x1) === 1;
  const opCode = firstByte & 0xF;
  
  if (opCode === 8) return null; // 關閉連線幀
  
  const secondByte = buffer[1];
  const isMasked = ((secondByte >>> 7) & 0x1) === 1;
  let payloadLength = secondByte & 0x7F;
  
  let offset = 2;
  if (payloadLength === 126) {
    payloadLength = buffer.readUInt16BE(offset);
    offset += 2;
  } else if (payloadLength === 127) {
    payloadLength = buffer.readUInt32BE(offset + 4);
    offset += 8;
  }
  
  let maskingKey;
  if (isMasked) {
    maskingKey = buffer.slice(offset, offset + 4);
    offset += 4;
  }
  
  const payload = buffer.slice(offset, offset + payloadLength);
  
  if (isMasked) {
    for (let i = 0; i < payload.length; i++) {
      payload[i] = payload[i] ^ maskingKey[i % 4];
    }
  }
  
  try {
    return JSON.parse(payload.toString());
  } catch (e) {
    return null;
  }
}

function sendWSMessage(socket, obj) {
  if (!socket || socket.destroyed) return;
  
  try {
    const json = JSON.stringify(obj);
    const payload = Buffer.from(json);
    const len = payload.length;
    
    let frame = [];
    frame.push(0x81); // Text frame
    
    if (len <= 125) {
      frame.push(len);
    } else if (len <= 65535) {
      frame.push(126);
      frame.push((len >>> 8) & 0xFF);
      frame.push(len & 0xFF);
    } else {
      frame.push(127);
      for (let i = 7; i >= 0; i--) {
        frame.push((len >>> (i * 8)) & 0xFF);
      }
    }
    
    const header = Buffer.from(frame);
    socket.write(Buffer.concat([header, payload]));
  } catch (err) {
    console.error('⚠️ [WebSocket 發送失敗]:', err);
  }
}

function broadcast(obj) {
  clients.forEach(client => sendWSMessage(client, obj));
}

// 附帶逾時的 fetch
function fetchWithTimeout(url, options, timeout = 5000) {
  return Promise.race([
    fetch(url, options),
    new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), timeout))
  ]);
}

// Phase 12: 技能執行隊列與互斥鎖實作
async function executeSkillWithQueue(skillName, args) {
  return new Promise((resolve, reject) => {
    // 檢查隊列是否已滿
    if (skillExecutionQueue.queue.length >= skillExecutionQueue.maxQueueSize) {
      console.log(`[Queue] ❌ 技能 ${skillName} 被拒絕：隊列已滿 (${skillExecutionQueue.maxQueueSize})`);
      resolve({
        success: false,
        error: `技能執行隊列已滿，請稍後再試（當前等待數：${skillExecutionQueue.queue.length}）`,
        queueFull: true
      });
      return;
    }

    const task = {
      skillName,
      args,
      resolve,
      reject,
      timestamp: Date.now(),
      id: `${skillName}_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
    };

    // 如果正在執行，加入隊列
    if (skillExecutionQueue.isRunning) {
      skillExecutionQueue.queue.push(task);
      console.log(`[Queue] 📋 技能 ${skillName} 排隊中，當前隊列長度：${skillExecutionQueue.queue.length}`);
      return;
    }

    // 直接執行
    executeSkillTask(task);
  });
}

async function executeSkillTask(task) {
  skillExecutionQueue.isRunning = true;
  skillExecutionQueue.currentProcess = task;

  try {
    console.log(`[Queue] 🚀 開始執行技能：${task.skillName} (任務ID: ${task.id})`);
    const result = await skillsManager.executeSkillScript(task.skillName, task.args);
    task.resolve(result);
  } catch (error) {
    console.error(`[Queue] ❌ 技能執行異常：${task.skillName} — ${error.message}`);
    task.resolve({
      success: false,
      error: error.message || '執行異常',
      taskId: task.id
    });
  } finally {
    // 標記當前任務完成
    skillExecutionQueue.isRunning = false;
    skillExecutionQueue.currentProcess = null;

    // 執行下一個（延遲 100ms 讓系統喘口氣）
    if (skillExecutionQueue.queue.length > 0) {
      const nextTask = skillExecutionQueue.queue.shift();
      const waitTime = Date.now() - nextTask.timestamp;
      console.log(`[Queue] ⏳ 等待耗時：${waitTime}ms，準備執行下一個技能：${nextTask.skillName}`);
      setTimeout(() => executeSkillTask(nextTask), 100);
    } else {
      console.log(`[Queue] ✅ 隊列已清空，系統空閒中`);
    }
  }
}

// Phase 12: 僵死進程清理機制
function killChildProcesses(parentPid) {
  try {
    const platform = process.platform;

    if (platform === 'win32') {
      // Windows：使用 taskkill 強制結束進程樹 (/T = 子進程, /F = 強制)
      exec(`taskkill /F /T /PID ${parentPid}`, (error) => {
        if (error) {
          console.log(`[Cleanup] Windows 子進程清理完成（PID ${parentPid} 可能已不存在）`);
        } else {
          console.log(`[Cleanup] ✅ Windows 進程樹已清理：PID ${parentPid}`);
        }
      });
    } else {
      // Linux/Mac：使用 kill 殺死進程群組（負號表示整個群組）
      try {
        process.kill(-parentPid, 'SIGKILL');
        console.log(`[Cleanup] ✅ Linux/Mac 進程群組已清理：PID ${parentPid}`);
      } catch (e) {
        // 進程群組可能已不存在
        console.log(`[Cleanup] 進程群組清理完成（可能已不存在）`);
      }
    }
  } catch (error) {
    console.error(`[Cleanup] ❌ 子進程清理失敗：${error.message}`);
  }
}

// 定期清理僵死進程（每 30 秒執行一次）
setInterval(() => {
  const now = Date.now();
  let cleanedCount = 0;

  for (const [pid, info] of activeProcesses.entries()) {
    const age = now - info.startTime;

    // 超過 2 分鐘未完成且未被標記為已殺死
    if (age > STALE_THRESHOLD && !info.killed) {
      console.log(`[Cleanup] 🧹 清理僵死進程 PID: ${pid} (技能: ${info.skillName}, 存活: ${Math.floor(age / 1000)}秒)`);

      try {
        // 強制殺死主進程
        process.kill(pid, 'SIGKILL');
        info.killed = true;

        // 清理可能殘留的子進程（Python 腳本可能啟動了子程序）
        killChildProcesses(pid);

        cleanedCount++;
      } catch (e) {
        // 進程可能已自然結束
        info.killed = true;
      }
    }
  }

  if (cleanedCount > 0) {
    console.log(`[Cleanup] 🎯 本次清理僵死進程：${cleanedCount} 個`);
  }

  // 清理已結束超過 5 分鐘的記錄
  for (const [pid, info] of activeProcesses.entries()) {
    if (info.killed && now - info.startTime > 300000) {
      activeProcesses.delete(pid);
    }
  }
}, CLEANUP_INTERVAL);

// 顯示隊列狀態（除錯用）
function getQueueStatus() {
  return {
    isRunning: skillExecutionQueue.isRunning,
    queueLength: skillExecutionQueue.queue.length,
    currentTask: skillExecutionQueue.currentProcess ? {
      skillName: skillExecutionQueue.currentProcess.skillName,
      id: skillExecutionQueue.currentProcess.id,
      runningTime: Date.now() - skillExecutionQueue.currentProcess.timestamp
    } : null,
    activeProcesses: activeProcesses.size
  };
}

// --- 啟動伺服器 ---
server.listen(PORT, () => {
  // Phase 13: 啟動時執行自我健康檢查
  performHealthCheck();
  
  console.log('\x1b[32m%s\x1b[0m', `🦞 [小龍蝦伺服器] 正式在 http://localhost:${PORT} 啟動！`);
  console.log('\x1b[36m%s\x1b[0m', '💡 [自檢說明] 在瀏覽器中開啟 miniclaw-web/index.html 即可立刻與我建立WebSocket連線。');
  console.log('\x1b[33m%s\x1b[0m', `🔧 [Phase 12] 技能執行隊列與僵死進程清理機制已啟動（最大隊列：${skillExecutionQueue.maxQueueSize}，清理間隔：${CLEANUP_INTERVAL / 1000}秒）`);
  console.log('\x1b[33m%s\x1b[0m', `📦 [Phase 13] 日誌自動封存機制已啟動（閾值：${LOG_SIZE_THRESHOLD / 1024 / 1024}MB）`);
});

// --- 9. 全域異常防護 (防止 any 未捕獲例外導致伺服器崩潰) ---
process.on('uncaughtException', (err) => {
  console.error('\x1b[31m%s\x1b[0m', `🚨 [全域未捕獲異常] 攔截到錯誤，伺服器已自動防禦避空: ${err.stack || err.message}`);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('\x1b[31m%s\x1b[0m', `🚨 [全域未處理 Rejection] 攔截到非同步錯誤:`, reason);
});
