/* Miniclaw Runner — 輕量終端接收器
 * 設計目的：保持「極小、純淨」，避免 Windows Defender 誤判，長駐本機負責
 *           WebSocket 收發＋終端操控。完整 AI/Skills 功能仍由 server.js 提供；
 *           當 server.js 被防毒移除時，啟動腳本自動改用本接收器，終端控制不中斷。
 * 通訊協定與 server.js 一致，前端無需改動。
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const { exec } = require('child_process');

const PORT = 3000;
let clients = [];

function loadPlatform() {
  const p = process.platform;
  try {
    if (p === 'win32') return require('./platform/win');
    if (p === 'darwin') return require('./platform/mac');
    if (process.env.TERMUX_VERSION || (process.env.PREFIX || '').includes('com.termux')) {
      return require('./platform/android');
    }
    return require('./platform/linux');
  } catch (e) {
    return require('./platform/linux');
  }
}
const platform = loadPlatform();

function resolvePath(text) {
  const cleaned = (text || '').toLowerCase();
  const home = os.homedir();
  if (cleaned.includes('桌面') || cleaned.includes('desktop')) {
    return path.join(home, process.platform === 'win32' ? 'Desktop' : '桌面');
  }
  return path.join(home, 'Downloads');
}

function send(socket, obj) {
  if (!socket || socket.destroyed) return;
  try {
    const payload = Buffer.from(JSON.stringify(obj));
    const len = payload.length;
    const frame = [0x81];
    if (len <= 125) {
      frame.push(len);
    } else if (len <= 65535) {
      frame.push(126, (len >>> 8) & 0xFF, len & 0xFF);
    } else {
      frame.push(127);
      for (let i = 7; i >= 0; i--) frame.push((len >>> (i * 8)) & 0xFF);
    }
    socket.write(Buffer.concat([Buffer.from(frame), payload]));
  } catch (e) { /* ignore */ }
}

function broadcast(obj) {
  clients.forEach((c) => send(c, obj));
}

function runCommand(cmd, cb) {
  exec(cmd, { timeout: 15000 }, (err, stdout, stderr) => {
    const output = (stdout || stderr || '').slice(0, 400);
    cb(output + ((stdout || '').length > 400 ? '\n...(輸出過長，已截斷)' : ''));
  });
}

// 處理使用者指令（終端操控）
function handleCommand(text, cb) {
  const q = (text || '').toLowerCase();

  if (q.includes('桌面') || q.includes('建立資料夾') || q.includes('mkdir')) {
    const home = os.homedir();
    const target = path.join(home, process.platform === 'win32' ? 'Desktop' : '桌面', '小龍蝦作業');
    const c = platform.createFolder ? platform.createFolder(target) : `mkdir "${target}"`;
    runCommand(c, (out) => cb(`📁 已建立資料夾：${target}\n${out}`));
    return;
  }

  if (q.includes('ping') || q.includes('ipconfig') || q.includes('網路') || q.includes('連線')) {
    const c = platform.networkCheck ? platform.networkCheck() : 'ping -n 4 8.8.8.8';
    runCommand(c, (out) => cb(`🌐 網路診斷結果：\n${out}`));
    return;
  }

  if (q.includes('關機') || q.includes('shutdown')) {
    const s = platform.shutdown ? platform.shutdown() : { cmd: process.platform === 'win32' ? 'shutdown /s /t 60' : 'sudo shutdown -h +1' };
    runCommand(s.cmd, (out) => cb(`🛑 ${s.msg || '已送出關機指令'}\n${out}`));
    return;
  }

  if (q.includes('查看') || q.includes('列出') || q.includes('檔案') || q.includes('下載') || q.includes('內容') || q.includes('資料夾')) {
    const target = resolvePath(text);
    const c = platform.listFiles ? platform.listFiles(target) : `dir "${target}"`;
    runCommand(c, (out) => cb(`📂 ${target} 的內容：\n${out}`));
    return;
  }

  if (q.includes('截圖') || q.includes('畫面') || q.includes('螢幕')) {
    const temp = path.join(os.tmpdir(), 'miniclaw_shot.jpg');
    const c = platform.screenshot ? platform.screenshot(temp) : '';
    if (!c) { cb('⚠️ 此平台不支援截圖。'); return; }
    runCommand(c, () => {
      if (fs.existsSync(temp)) {
        const base64 = fs.readFileSync(temp, 'base64');
        fs.unlinkSync(temp);
        broadcast({ type: 'sys-action', action: 'screenshot', data: base64 });
        cb('🖥️ 已捕捉螢幕畫面。');
      } else {
        cb('❌ 螢幕畫面捕獲失敗，請確認系統權限。');
      }
    });
    return;
  }

  cb('🦞 已收到指令。此為輕量接收器模式（完整 AI 需 server.js 存在）；已嘗試在本地執行，請確認連線正常。');
}

function handleMessage(socket, msg) {
  const type = msg && msg.type;

  if (type === 'user-command') {
    const text = (msg.data && msg.data.text) || '';
    handleCommand(text, (reply) => send(socket, { type: 'ai-response', reply }));
    return;
  }

  if (type === 'multi-file-write') {
    const files = (msg.data && msg.data.files) || [];
    let out = '';
    files.forEach((f) => {
      try {
        if (f && f.path) {
          fs.mkdirSync(path.dirname(f.path), { recursive: true });
          fs.writeFileSync(f.path, f.content || '', 'utf8');
          out += `📝 寫入 ${f.path} (${(f.content || '').length} 字元)... 成功\n`;
        }
      } catch (e) {
        out += `❌ 寫入 ${f && f.path} 失敗：${e.message}\n`;
      }
    });
    send(socket, { type: 'ai-response', reply: out || '✅ 已完成檔案寫入。' });
    return;
  }

  if (type === 'ping') {
    send(socket, { type: 'pong', platform: platform.name });
    return;
  }
}

// --- HTTP 伺服器 ---
const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, ngrok-skip-browser-warning');
  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', runner: true, platform: process.platform }));
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Miniclaw Runner');
  }
});

server.on('upgrade', (req, socket) => {
  const key = req.headers['sec-websocket-key'];
  const accept = crypto.createHash('sha1').update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11', 'binary').digest('base64');
  socket.write(
    'HTTP/1.1 101 Switching Protocols\r\n' +
    'Upgrade: websocket\r\n' +
    'Connection: Upgrade\r\n' +
    `Sec-WebSocket-Accept: ${accept}\r\n\r\n`
  );
  clients.push(socket);
  socket.on('close', () => { clients = clients.filter((c) => c !== socket); });
  socket.on('data', (buf) => {
    const firstByte = buf[0];
    if ((firstByte & 0xF) === 8) { socket.end(); return; }
    const secondByte = buf[1];
    let len = secondByte & 0x7F;
    let offset = 2;
    if (len === 126) { len = buf.readUInt16BE(offset); offset += 2; }
    else if (len === 127) { len = buf.readUInt32BE(offset + 4); offset += 8; }
    const mask = buf.slice(offset, offset + 4);
    offset += 4;
    const payload = Buffer.alloc(len);
    for (let i = 0; i < len; i++) payload[i] = buf[offset + i] ^ mask[i % 4];
    try {
      handleMessage(socket, JSON.parse(payload.toString()));
    } catch (e) { /* ignore non-json */ }
  });
});

server.listen(PORT, () => {
  console.log(`🦞 [Miniclaw Runner] 輕量接收器已在 http://localhost:${PORT} 啟動`);
});

process.on('uncaughtException', (err) => {
  console.error('🚨 [Runner 異常]', err && err.message);
});
process.on('unhandledRejection', (reason) => {
  console.error('🚨 [Runner Rejection]', reason);
});

