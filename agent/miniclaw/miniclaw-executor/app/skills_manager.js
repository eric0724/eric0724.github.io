/* skills_manager.js — Skills 技能管理模組 (Phase 2)
 *
 * 功能職責：
 *   1. 讀取 skills/ 目錄下所有子資料夾的 SKILL.md
 *   2. 解析 YAML frontmatter，萃取 name 與 description
 *   3. 彙整成結構化清單供注入 AI 提示詞
 *   4. 提供第二層深度載入：依技能名稱讀取完整 Body（去掉 frontmatter）
 *   5. 支援 process.env.SKILLS_PATH 環境變數
 *
 * 設計原則：
 *   - 零依賴：內嵌輕量 YAML frontmatter 解析器，不需 npm install
 *   - 零副作用：所有函數皆為純粹的資料讀取與轉換
 *   - 容錯：單一技能格式錯誤不影響其他技能
 *   - 快取：支援記憶體快取（初始化時一次性掃描）
 */

const fs = require('fs');
const path = require('path');
const { exec, spawn } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

// ─── 設定 ──────────────────────────────────────────────
// 支援 process.env.SKILLS_PATH 環境變數，若無設定則預設相對路徑
const SKILLS_ROOT = process.env.SKILLS_PATH
  ? path.resolve(process.env.SKILLS_PATH)
  : path.resolve(__dirname, '..', '..', 'skills');

// 輸出至 AI prompt 時，description 的最大長度（超過自動截斷）
const MAX_DESC_LENGTH = 120;

// ─── 記憶體快取 ──────────────────────────────────────
let skillsCache = null;          // loadAllSkills 的快取
let skillsCacheLoaded = false;   // 是否已載入快取

/**
 * ─── 內嵌輕量 YAML Frontmatter 解析器 ───
 * 不依賴 js-yaml 套件，純粹使用正則與狀態機。
 * 僅解析 name / description 這兩個 frontmatter 欄位，
 * 以及提取 frontmatter 區塊的原始文字供外部使用。
 *
 * @param {string} raw - SKILL.md 完整原始內容
 * @returns {{ name: string|null, description: string|null, fmRaw: string|null, body: string|null }}
 *   - fmRaw: frontmatter 區塊原始內容（去邊界）
 *   - body: 去掉 frontmatter 後的 Markdown 內文
 */
function parseSkillDoc(raw) {
  const result = {
    name: null,
    description: null,
    fmRaw: null,
    body: null,
  };

  // 確認有正確的 YAML frontmatter 邊界
  if (!raw.startsWith('---\n') && !raw.startsWith('---\r\n')) {
    result.body = raw;
    return result;
  }

  const endFm = raw.indexOf('\n---', 4);
  if (endFm === -1) {
    result.body = raw;
    return result;
  }

  // frontmatter 區塊（去掉開頭的 ---\n）
  const fmRaw = raw.slice(4, endFm).trim();
  result.fmRaw = fmRaw;

  // Body = 關閉 --- 之後的內容
  const bodyStart = raw.indexOf('\n', endFm + 5) + 1; // 跳過 \n---\n
  result.body = bodyStart > 0 ? raw.slice(bodyStart).trim() : '';

  // ─── 解析 frontmatter 中的 name 與 description ───
  const lines = fmRaw.split('\n');
  let inDescBlock = false;
  const descLines = [];

  for (const line of lines) {
    const nameMatch = line.match(/^name\s*:\s*(.+)$/);
    if (nameMatch) {
      result.name = nameMatch[1].trim().replace(/^['"]|['"]$/g, '');
      continue;
    }

    const descStartMatch = line.match(/^description\s*:\s*(.*)$/);
    if (descStartMatch) {
      const remainder = descStartMatch[1].trim();

      // 處理 > 或 >- 跨行折疊模式
      if (remainder === '>' || remainder === '>-' || remainder.startsWith('>')) {
        inDescBlock = true;
        descLines.length = 0;
        const afterFold = remainder.replace(/^>\s*/, '');
        if (afterFold && afterFold !== '') descLines.push(afterFold);
        continue;
      } else if (remainder) {
        // 一般單行 description
        result.description = remainder.replace(/^['"]|['"]$/g, '');
        inDescBlock = false;
        continue;
      } else {
        inDescBlock = false;
        continue;
      }
    }

    // 跨行區塊收集
    if (inDescBlock) {
      const t = line.trim();
      if (t === '') {
        descLines.push('');
      } else {
        descLines.push(t);
      }
    }
  }

  // 合併跨行 description
  if (inDescBlock && descLines.length > 0) {
    result.description = descLines
      .map((l, i, arr) => (l === '' ? '\n' : i < arr.length - 1 && arr[i + 1] === '' ? l : l))
      .join(' ')
      .replace(/\n\s*/g, ' ')
      .replace(/\s{2,}/g, ' ')
      .trim();
  }

  return result;
}

/**
 * 截斷字串至指定長度，若超過則在結尾加上 ...
 */
function truncate(str, maxLen) {
  if (!str || str.length <= maxLen) return str || '';
  return str.slice(0, maxLen) + '...';
}

/**
 * 掃描 skills/ 目錄，讀取所有子資料夾中的 SKILL.md。
 * 使用記憶體快取：首次掃描後快取結果，後續直接回傳。
 *
 * @param {boolean} [forceRefresh=false] - 強制重新掃描
 * @returns {Array<{ folder: string, name: string|null, description: string|null, path: string }>}
 */
function loadAllSkills(forceRefresh = false) {
  // 快取命中
  if (skillsCacheLoaded && !forceRefresh && skillsCache !== null) {
    return skillsCache;
  }

  skillsCache = [];

  if (!fs.existsSync(SKILLS_ROOT)) {
    console.log(`[skills_manager] Skills 目錄不存在：${SKILLS_ROOT}`);
    skillsCacheLoaded = true;
    return skillsCache;
  }

  const entries = fs.readdirSync(SKILLS_ROOT, { withFileTypes: true });

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;

    const skillFolder = path.join(SKILLS_ROOT, entry.name);
    const skillMdPath = path.join(skillFolder, 'SKILL.md');

    if (!fs.existsSync(skillMdPath)) continue;

    try {
      const raw = fs.readFileSync(skillMdPath, 'utf8');
      const { name, description } = parseSkillDoc(raw);

      skillsCache.push({
        folder: entry.name,
        name: name || entry.name,
        description: description || '',
        path: skillMdPath,
      });

      console.log(`[skills_manager] ✅ 已載入技能：${name || entry.name}`);
    } catch (err) {
      console.error(`[skills_manager] ⚠️ 讀取技能失敗 [${entry.name}]：${err.message}`);
    }
  }

  skillsCacheLoaded = true;
  return skillsCache;
}

/**
 * 取得所有技能的 Metadata 清單（僅 name + description，description 截斷至 120 字）。
 */
function getSkillsMetadata() {
  return loadAllSkills().map(({ name, description }) => ({
    name,
    description: truncate(description, MAX_DESC_LENGTH),
  }));
}

/**
 * 將技能 Metadata 格式化為純文字字串，方便嵌入 AI System Prompt。
 */
function formatSkillsForPrompt(separator = '\n') {
  const list = getSkillsMetadata();
  if (list.length === 0) return '';

  const lines = list.map(
    (s, i) => `${i + 1}. ${s.name}：${truncate(s.description, MAX_DESC_LENGTH)}`,
  );

  return `【可用技能清單】${separator}${lines.join(separator)}`;
}

// ═══════════════════════════════════════════════════════
//  Phase 2 新增功能
// ═══════════════════════════════════════════════════════

/**
 * 依技能名稱（folder name 或 frontmatter 中的 name）取得該技能的 SKILL.md Body。
 * Body = 去掉 YAML frontmatter 後的完整 Markdown 內文（第二層深度載入）。
 *
 * @param {string} skillName - 技能名稱（支援 folder name 或 frontmatter name）
 * @returns {{ found: boolean, name: string, description: string, body: string|null, path: string|null }}
 */
function getSkillBody(skillName) {
  // 先從快取中搜尋技能
  const skills = loadAllSkills();
  const match = skills.find(
    (s) => s.folder.toLowerCase() === skillName.toLowerCase()
      || (s.name && s.name.toLowerCase() === skillName.toLowerCase()),
  );

  if (!match) {
    return {
      found: false,
      name: skillName,
      description: '',
      body: null,
      path: null,
    };
  }

  try {
    const raw = fs.readFileSync(match.path, 'utf8');
    const { name, description, body } = parseSkillDoc(raw);

    return {
      found: true,
      name: name || match.folder,
      description: description || '',
      body: body || '',
      path: match.path,
    };
  } catch (err) {
    console.error(`[skills_manager] ⚠️ 讀取技能 Body 失敗 [${skillName}]：${err.message}`);
    return {
      found: true,
      name: match.name,
      description: match.description,
      body: null,
      path: match.path,
      error: err.message,
    };
  }
}

/**
 * 偵測使用者輸入是否觸發了任何已註冊技能。
 * 比對邏輯：使用者輸入的關鍵字是否與技能名稱或 description 中的關鍵字重疊。
 *
 * @param {string} userInput - 使用者輸入的文字
 * @returns {Array<{ name: string, folder: string, matchType: string, confidence: number }>}
 *   - matchType: 'exact_name' | 'keyword_desc' | 'folder_match'
 *   - confidence: 0.0 ~ 1.0
 */
function detectTriggeredSkills(userInput) {
  const triggers = [];
  const input = userInput.toLowerCase();

  const skills = loadAllSkills();
  for (const skill of skills) {
    const skillName = (skill.name || '').toLowerCase();
    const skillDesc = (skill.description || '').toLowerCase();
    const skillFolder = skill.folder.toLowerCase();

    // 精確比對：技能名稱完全出現在輸入中
    if (input.includes(skillName) && skillName.length > 1) {
      triggers.push({
        name: skill.name || skill.folder,
        folder: skill.folder,
        matchType: 'exact_name',
        confidence: 0.95,
      });
      continue;
    }

    // 資料夾名稱比對
    if (input.includes(skillFolder) && skillFolder.length > 1) {
      triggers.push({
        name: skill.name || skill.folder,
        folder: skill.folder,
        matchType: 'folder_match',
        confidence: 0.85,
      });
      continue;
    }

    // 關鍵字比對：從 description 中提取關鍵詞（取前 30 個字）
    const descKeywords = skillDesc.slice(0, 80).split(/[\s，。、,.\s]+/).filter(k => k.length > 1);
    let matchCount = 0;
    for (const kw of descKeywords) {
      if (input.includes(kw)) matchCount++;
    }
    const matchRatio = descKeywords.length > 0 ? matchCount / descKeywords.length : 0;

    if (matchRatio >= 0.3 && matchCount >= 2) {
      triggers.push({
        name: skill.name || skill.folder,
        folder: skill.folder,
        matchType: 'keyword_desc',
        confidence: Math.round(Math.min(0.5 + matchRatio * 0.3, 0.85) * 100) / 100,
      });
    }
  }

  // 依信心度排序（高 → 低）
  triggers.sort((a, b) => b.confidence - a.confidence);
  return triggers;
}

/**
 * 格式化觸發的技能清單為提示詞區塊，供 server.js 動態注入。
 *
 * @param {string} userInput - 使用者輸入
 * @param {number} [minConfidence=0.5] - 最低信心門檻
 * @returns {string} 格式化後的技能指引文字，若無觸發則回傳空字串
 */
function formatTriggeredSkillsForPrompt(userInput, minConfidence = 0.5) {
  const triggers = detectTriggeredSkills(userInput).filter(t => t.confidence >= minConfidence);
  if (triggers.length === 0) return '';

  const parts = [];
  for (const t of triggers) {
    const skillBody = getSkillBody(t.folder);
    if (skillBody.found && skillBody.body) {
      parts.push(
        `=== 技能：${skillBody.name} ===\n${skillBody.body}`,
      );
    }
  }

  if (parts.length === 0) return '';

  return `\n\n【已觸發技能 — 完整操作指引】\n${parts.join('\n\n')}\n\n請參考上述指引來回應使用者需求。`;
}

// ═══════════════════════════════════════════════════════
//  Phase 4 新增功能 — 技能腳本執行橋樑
// ═══════════════════════════════════════════════════════

/**
 * 執行技能內部的自動化腳本
 *
 * @param {string} skillName - 技能名稱（folder name 或 frontmatter name）
 * @param {string} [args=''] - 傳遞給腳本的參數（空白分隔）
 * @returns {Promise<{ success: boolean, output: string, error: string|null }>}
 */
async function executeSkillScript(skillName, args = '') {
  // 先從快取中搜尋技能
  const skills = loadAllSkills();
  const match = skills.find(
    (s) => s.folder.toLowerCase() === skillName.toLowerCase()
      || (s.name && s.name.toLowerCase() === skillName.toLowerCase()),
  );

  if (!match) {
    return {
      success: false,
      output: '',
      error: `找不到技能：${skillName}`,
    };
  }

  const scriptsDir = path.join(match.folder, 'scripts');
  const scriptsFullPath = path.join(SKILLS_ROOT, scriptsDir);

  if (!fs.existsSync(scriptsFullPath)) {
    return {
      success: false,
      output: '',
      error: `技能「${match.name}」沒有 scripts/ 目錄`,
    };
  }

  // 優先尋找 run.py，其次 run.js
  const runPy = path.join(scriptsFullPath, 'run.py');
  const runJs = path.join(scriptsFullPath, 'run.js');
  let scriptPath = null;
  let command = null;
  let scriptArgs = [];

  if (fs.existsSync(runPy)) {
    scriptPath = runPy;
    // Windows 使用 py，其他平台使用 python3
    const pythonCmd = process.platform === 'win32' ? 'py' : 'python3';
    command = pythonCmd;
    scriptArgs = [scriptPath];
    if (args) scriptArgs.push(...args.split(/\s+/).filter(Boolean));
  } else if (fs.existsSync(runJs)) {
    scriptPath = runJs;
    command = 'node';
    scriptArgs = [scriptPath];
    if (args) scriptArgs.push(...args.split(/\s+/).filter(Boolean));
  } else {
    return {
      success: false,
      output: '',
      error: `技能「${match.name}」的 scripts/ 目錄中找不到 run.py 或 run.js`,
    };
  }

  try {
    console.log(`[skills_manager] 🚀 執行技能腳本：${match.name} → ${scriptPath} ${scriptArgs.slice(1).join(' ')}`);

    const fullCommand = `${command} ${scriptArgs.map(a => `"${a}"`).join(' ')}`;
    const { stdout, stderr } = await execAsync(fullCommand, {
      timeout: 60000, // 60 秒超時
      maxBuffer: 1024 * 1024, // 1MB 輸出緩衝
      cwd: path.dirname(scriptPath),
    });

    const output = (stdout || stderr || '').trim();
    console.log(`[skills_manager] ✅ 腳本執行完成：${match.name}（輸出 ${output.length} 字元）`);

    return {
      success: true,
      output: output || '（腳本執行完畢，無輸出）',
      error: null,
    };
  } catch (err) {
    const errorMsg = err.message || err.toString();
    console.error(`[skills_manager] ❌ 腳本執行失敗：${match.name} — ${errorMsg}`);
    return {
      success: false,
      output: '',
      error: errorMsg,
    };
  }
}

/**
 * 從文字中解析 [技能名稱 參數] 標籤
 *
 * @param {string} text - AI 回覆文字
 * @returns {Array<{ skillName: string, args: string }>}
 */
function parseSkillTags(text) {
  const tags = [];
  // 匹配 [技能名稱] 或 [技能名稱 參數1 參數2]
  const regex = /\[([a-zA-Z0-9_-]+)(?:\s+([^\]]+))?\]/g;
  let match;
  while ((match = regex.exec(text)) !== null) {
    tags.push({
      skillName: match[1].trim(),
      args: (match[2] || '').trim(),
    });
  }
  return tags;
}

// ─── 匯出 ──────────────────────────────────────────────
module.exports = {
  SKILLS_ROOT,
  loadAllSkills,
  getSkillsMetadata,
  formatSkillsForPrompt,
  // Phase 2 新增
  getSkillBody,
  detectTriggeredSkills,
  formatTriggeredSkillsForPrompt,
  // Phase 4 新增
  executeSkillScript,
  parseSkillTags,
  // 內部方法也匯出（供測試用）
  parseSkillDoc,
};

// ─── 獨立執行測試 ──────────────────────────────────────
if (require.main === module) {
  console.log('🔍 Skills Manager — 診斷模式 (Phase 2)');
  console.log(`📂 Skills 根目錄：${SKILLS_ROOT}`);
  console.log(`📌 環境變數 SKILLS_PATH：${process.env.SKILLS_PATH || '(未設定，使用預設)'}`);
  console.log('');

  const list = loadAllSkills();
  if (list.length === 0) {
    console.log('⚠️ 尚未找到任何技能。');
  } else {
    console.log(`✅ 共找到 ${list.length} 個技能：\n`);
    for (const s of list) {
      console.log(`  📁 ${s.folder}/`);
      console.log(`     ├─ name:        ${s.name}`);
      console.log(`     ├─ description: ${s.description}`);
      console.log(`     └─ path:        ${s.path}`);

      // 測試第二層 Body 載入
      const body = getSkillBody(s.folder);
      if (body.found && body.body) {
        const preview = body.body.slice(0, 100).replace(/\n/g, '\\n');
        console.log(`     └─ body (預覽): ${preview}...`);
      }
    }
    console.log('');
    console.log('─── 格式化輸出（供提示詞使用）───');
    console.log(formatSkillsForPrompt());
    console.log('');
    console.log('─── 技能觸發偵測測試 ───');
    const testInputs = ['幫我點擊畫面上的按鈕', '今天天氣如何', '請幫我截圖'];
    for (const test of testInputs) {
      const triggers = detectTriggeredSkills(test);
      if (triggers.length > 0) {
        console.log(`  輸入「${test}」→ 觸發：${triggers.map(t => `${t.name}(${t.confidence})`).join(', ')}`);
      } else {
        console.log(`  輸入「${test}」→ 無觸發`);
      }
    }
  }
}