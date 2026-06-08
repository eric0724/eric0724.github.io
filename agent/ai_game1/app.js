// 霓虹太空電玩城 - 主控與音效引擎核心

// --- 全域狀態 ---
const state = {
  activeGame: null,
  musicEnabled: false,
  soundEnabled: true,
  audioCtx: null,
  bgmInterval: null,
  leaderboard: [],
  unlockedAchievements: []
};

// --- 成就清單定義 ---
const ACHIEVEMENTS = [
  { id: 'b_first', name: '首碎星辰', desc: '在打磚塊中擊破第 1 塊磚', icon: '💎' },
  { id: 'b_laser', name: '雷射狂飆', desc: '在打磚塊中拾取雷射道具並擊發', icon: '⚡' },
  { id: 'b_gold', name: '千分殿堂', desc: '在打磚塊中單局獲得 1,000 分', icon: '🏆' },
  { id: 'r_first', name: '啟航者', desc: '在星際星航者中成功擊毀 1 顆隕石', icon: '🚀' },
  { id: 'r_combo', name: '極速狂熱', desc: '在星際星航者中達到 x5 連擊 Combo', icon: '🔥' },
  { id: 'r_gold', name: '星空主宰', desc: '在星際星航者中單局獲得 1,000 分', icon: '👑' }
];

// --- 初始化程序 ---
window.addEventListener('DOMContentLoaded', () => {
  initBackgroundStars();
  initMouseInteractiveCards();
  initLeaderboard();
  initAchievements();
  setupEventHandlers();
  startMiniPreviews();
});

// --- 1. 背景與動態特效 ---
function initBackgroundStars() {
  const container = document.getElementById('starsContainer');
  if (!container) return;
  
  const starCount = 50;
  for (let i = 0; i < starCount; i++) {
    const star = document.createElement('div');
    star.className = 'star';
    
    const size = Math.random() * 3 + 1;
    const left = Math.random() * 100;
    const duration = Math.random() * 10 + 8;
    const opacity = Math.random() * 0.7 + 0.3;
    const drift = (Math.random() - 0.5) * 100;
    
    star.style.width = `${size}px`;
    star.style.height = `${size}px`;
    star.style.left = `${left}%`;
    star.style.setProperty('--duration', `${duration}s`);
    star.style.setProperty('--opacity', opacity);
    star.style.setProperty('--drift', `${drift}px`);
    star.style.top = `${Math.random() * 100}vh`;
    
    container.appendChild(star);
  }
}

// 磁吸 3D 傾斜卡片特效
function initMouseInteractiveCards() {
  const cards = document.querySelectorAll('.game-card');
  cards.forEach(card => {
    card.addEventListener('mousemove', e => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
    });
  });
}

// --- 2. Web Audio 即時音效/音樂引擎 ---
function initAudio() {
  if (state.audioCtx) return;
  state.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
}

// 合成 8-bit 音效
const SoundEffects = {
  shoot() {
    if (!state.soundEnabled) return;
    initAudio();
    const ctx = state.audioCtx;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(800, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(150, ctx.currentTime + 0.15);
    
    gain.gain.setValueAtTime(0.12, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15);
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.15);
  },
  
  hit() {
    if (!state.soundEnabled) return;
    initAudio();
    const ctx = state.audioCtx;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(250, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(60, ctx.currentTime + 0.1);
    
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.12);
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.12);
  },

  break() {
    if (!state.soundEnabled) return;
    initAudio();
    const ctx = state.audioCtx;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = 'sine';
    osc.frequency.setValueAtTime(900, ctx.currentTime);
    osc.frequency.setValueAtTime(1200, ctx.currentTime + 0.04);
    
    gain.gain.setValueAtTime(0.1, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15);
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.15);
  },

  powerup() {
    if (!state.soundEnabled) return;
    initAudio();
    const ctx = state.audioCtx;
    const now = ctx.currentTime;
    
    const notes = [261.63, 329.63, 392.00, 523.25]; // C4 -> E4 -> G4 -> C5
    notes.forEach((freq, index) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.type = 'square';
      osc.frequency.setValueAtTime(freq, now + index * 0.08);
      
      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(0.08, now + index * 0.08 + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.001, now + index * 0.08 + 0.15);
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + index * 0.08);
      osc.stop(now + index * 0.08 + 0.2);
    });
  },

  gameover() {
    if (!state.soundEnabled) return;
    initAudio();
    const ctx = state.audioCtx;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(300, ctx.currentTime);
    osc.frequency.linearRampToValueAtTime(80, ctx.currentTime + 0.6);
    
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.6);
  },

  win() {
    if (!state.soundEnabled) return;
    initAudio();
    const ctx = state.audioCtx;
    const now = ctx.currentTime;
    
    const chords = [523.25, 659.25, 783.99, 1046.50]; // C5 -> E5 -> G5 -> C6
    chords.forEach((freq, index) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(freq, now + index * 0.06);
      
      gain.gain.setValueAtTime(0.12, now + index * 0.06);
      gain.gain.exponentialRampToValueAtTime(0.001, now + index * 0.06 + 0.3);
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + index * 0.06);
      osc.stop(now + index * 0.06 + 0.3);
    });
  }
};

// 即時電子合成 BGM 引擎
function startSynthBGM() {
  if (state.bgmInterval) clearInterval(state.bgmInterval);
  
  initAudio();
  const ctx = state.audioCtx;
  let beatIndex = 0;
  
  // 經典 Synthwave 循環貝斯線 (C2 -> Eb2 -> G2 -> Bb2)
  const bassline = [
    65.41, 65.41, 77.78, 77.78,
    98.00, 98.00, 116.54, 116.54
  ];
  
  state.bgmInterval = setInterval(() => {
    if (!state.musicEnabled) return;
    
    // 1. 低音貝斯節奏
    const freq = bassline[beatIndex % bassline.length];
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    
    gain.gain.setValueAtTime(0.04, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.22);
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    
    osc.start();
    osc.stop(ctx.currentTime + 0.25);
    
    // 2. 每4拍點綴一個合成主音
    if (beatIndex % 4 === 0) {
      const melodyOsc = ctx.createOscillator();
      const melodyGain = ctx.createGain();
      
      const leadNotes = [261.63, 311.13, 392.00, 466.16]; // C4 Eb4 G4 Bb4
      const leadFreq = leadNotes[Math.floor(Math.random() * leadNotes.length)];
      
      melodyOsc.type = 'triangle';
      melodyOsc.frequency.setValueAtTime(leadFreq, ctx.currentTime);
      
      melodyGain.gain.setValueAtTime(0.02, ctx.currentTime);
      melodyGain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.45);
      
      melodyOsc.connect(melodyGain);
      melodyGain.connect(ctx.destination);
      
      melodyOsc.start();
      melodyOsc.stop(ctx.currentTime + 0.5);
    }
    
    beatIndex++;
  }, 250); // 120 BPM
}

function stopSynthBGM() {
  if (state.bgmInterval) {
    clearInterval(state.bgmInterval);
    state.bgmInterval = null;
  }
}

// --- 3. 排行榜系統 (localStorage) ---
function initLeaderboard() {
  const localData = localStorage.getItem('neon_arcade_leaderboard');
  if (localData) {
    state.leaderboard = JSON.parse(localData);
  } else {
    // 預設演示資料
    state.leaderboard = [
      { name: 'NEON_PRO', score: 2500, game: 'Cyber-Break', date: '2026-05-27' },
      { name: 'SYNTH_WAVE', score: 1800, game: 'Cosmo-Rider', date: '2026-05-27' },
      { name: 'CYBER_KID', score: 1200, game: 'Cyber-Break', date: '2026-05-27' },
      { name: 'STAR_RUNNER', score: 950, game: 'Cosmo-Rider', date: '2026-05-27' },
      { name: 'PIXEL_HERO', score: 600, game: 'Cyber-Break', date: '2026-05-27' }
    ];
    saveLeaderboard();
  }
  renderLeaderboard();
}

function saveLeaderboard() {
  localStorage.setItem('neon_arcade_leaderboard', JSON.stringify(state.leaderboard));
}

function addLeaderboardEntry(name, score, game) {
  const newEntry = {
    name: name || 'ANON',
    score: parseInt(score),
    game: game,
    date: new Date().toISOString().split('T')[0]
  };
  state.leaderboard.push(newEntry);
  state.leaderboard.sort((a, b) => b.score - a.score);
  state.leaderboard = state.leaderboard.slice(0, 7); // 保留前 7 名
  saveLeaderboard();
  renderLeaderboard();
  updateHighScoreDisplay();
}

function renderLeaderboard() {
  const listEl = document.getElementById('leaderboardList');
  if (!listEl) return;
  listEl.innerHTML = '';
  
  state.leaderboard.forEach((item, index) => {
    const itemEl = document.createElement('div');
    itemEl.className = 'leaderboard-item';
    
    let badgeClass = 'rank-other';
    if (index === 0) badgeClass = 'rank-1';
    else if (index === 1) badgeClass = 'rank-2';
    else if (index === 2) badgeClass = 'rank-3';
    
    itemEl.innerHTML = `
      <span class="rank-badge ${badgeClass}">${index + 1}</span>
      <span class="player-name">${escapeHTML(item.name)} <span style="font-size:0.75rem; color:var(--text-muted);">(${item.game})</span></span>
      <span class="player-score" style="color: ${index === 0 ? 'var(--neon-gold)' : (item.game === 'Cyber-Break' ? 'var(--neon-pink)' : 'var(--neon-cyan)')}">${item.score.toLocaleString()}</span>
    `;
    listEl.appendChild(itemEl);
  });
}

function updateHighScoreDisplay() {
  const breakoutMax = state.leaderboard.filter(e => e.game === 'Cyber-Break').reduce((max, e) => e.score > max ? e.score : max, 0);
  const runnerMax = state.leaderboard.filter(e => e.game === 'Cosmo-Rider').reduce((max, e) => e.score > max ? e.score : max, 0);
  
  document.getElementById('breakoutHighScore').innerText = String(breakoutMax).padStart(5, '0');
  document.getElementById('runnerHighScore').innerText = String(runnerMax).padStart(5, '0');
}

// --- 4. 成就系統 ---
function initAchievements() {
  const localData = localStorage.getItem('neon_arcade_achievements');
  if (localData) {
    state.unlockedAchievements = JSON.parse(localData);
  }
  renderAchievements();
}

function unlockAchievement(id) {
  if (state.unlockedAchievements.includes(id)) return;
  
  state.unlockedAchievements.push(id);
  localStorage.setItem('neon_arcade_achievements', JSON.stringify(state.unlockedAchievements));
  
  const ach = ACHIEVEMENTS.find(a => a.id === id);
  if (ach) {
    showToast(ach.name, ach.desc, ach.icon);
    SoundEffects.win();
  }
  
  renderAchievements();
}

function renderAchievements() {
  const gridEl = document.getElementById('achievementsGrid');
  if (!gridEl) return;
  gridEl.innerHTML = '';
  
  ACHIEVEMENTS.forEach(ach => {
    const isUnlocked = state.unlockedAchievements.includes(ach.id);
    const itemEl = document.createElement('div');
    itemEl.className = `achievement-badge ${isUnlocked ? 'unlocked' : ''}`;
    
    itemEl.innerHTML = `
      <div class="achievement-icon">${ach.icon}</div>
      <div class="achievement-name">${ach.name}</div>
      <div class="achievement-desc">${ach.desc}</div>
    `;
    gridEl.appendChild(itemEl);
  });
}

function showToast(name, desc, icon) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <div class="toast-icon">${icon}</div>
    <div class="toast-body">
      <div class="toast-title">🌟 榮譽成就解鎖！</div>
      <div class="toast-desc"><strong>${name}</strong> - ${desc}</div>
    </div>
  `;
  container.appendChild(toast);
  
  // 5 秒後自動移除
  setTimeout(() => {
    toast.remove();
  }, 5000);
}

// --- 5. 電玩大廳與視窗切換 ---
function setupEventHandlers() {
  // 音效開關
  document.getElementById('toggleMusicBtn').addEventListener('click', () => {
    state.musicEnabled = !state.musicEnabled;
    const txt = document.getElementById('musicStatusText');
    if (state.musicEnabled) {
      txt.innerText = '音樂: 開';
      startSynthBGM();
    } else {
      txt.innerText = '音樂: 關';
      stopSynthBGM();
    }
  });

  document.getElementById('toggleSoundBtn').addEventListener('click', () => {
    state.soundEnabled = !state.soundEnabled;
    document.getElementById('soundStatusText').innerText = state.soundEnabled ? '音效: 開' : '音效: 關';
  });

  // 遊戲啟動按鈕
  document.getElementById('btnPlayBreakout').addEventListener('click', () => openGame('breakout'));
  document.getElementById('cardBreakout').addEventListener('click', (e) => {
    if (e.target.tagName !== 'BUTTON') openGame('breakout');
  });

  document.getElementById('btnPlayRunner').addEventListener('click', () => openGame('runner'));
  document.getElementById('cardRunner').addEventListener('click', (e) => {
    if (e.target.tagName !== 'BUTTON') openGame('runner');
  });

  // 返回大廳按鈕
  document.getElementById('btnExitGame').addEventListener('click', closeGame);
}

function openGame(gameId) {
  initAudio();
  if (state.audioCtx && state.audioCtx.state === 'suspended') {
    state.audioCtx.resume();
  }

  const lobby = document.getElementById('arcadeLobby');
  const viewport = document.getElementById('gameViewport');
  
  lobby.style.display = 'none';
  viewport.style.display = 'flex';
  state.activeGame = gameId;

  // 滾動到遊戲視窗頂部
  window.scrollTo({ top: viewport.offsetTop - 50, behavior: 'smooth' });

  // 停止大廳隨機預覽
  stopMiniPreviews();

  // 根據遊戲初始化對應的 Canvas 模組
  if (gameId === 'breakout') {
    initBreakoutGame();
  } else if (gameId === 'runner') {
    initRunnerGame();
  }
}

function closeGame() {
  if (state.activeGame === 'breakout') {
    shutdownBreakoutGame();
  } else if (state.activeGame === 'runner') {
    shutdownRunnerGame();
  }
  
  state.activeGame = null;
  document.getElementById('gameViewport').style.display = 'none';
  document.getElementById('arcadeLobby').style.display = 'flex';
  
  updateHighScoreDisplay();
  startMiniPreviews();
}

// --- 6. 大廳卡片上的動態 Canvas 小預覽 ---
let previewIntervals = [];

function startMiniPreviews() {
  stopMiniPreviews();
  
  const breakoutCanvas = document.getElementById('breakoutPreviewCanvas');
  const runnerCanvas = document.getElementById('runnerPreviewCanvas');
  
  if (breakoutCanvas) animateBreakoutPreview(breakoutCanvas);
  if (runnerCanvas) animateRunnerPreview(runnerCanvas);
  
  updateHighScoreDisplay();
}

function stopMiniPreviews() {
  previewIntervals.forEach(cancelAnimationFrame);
  previewIntervals = [];
}

// 打磚塊自動預覽動畫
function animateBreakoutPreview(canvas) {
  const ctx = canvas.getContext('2d');
  canvas.width = canvas.parentElement.offsetWidth;
  canvas.height = canvas.parentElement.offsetHeight;
  
  let x = canvas.width / 2;
  let y = canvas.height - 40;
  let dx = 2;
  let dy = -2.5;
  const radius = 6;
  const paddleWidth = 70;
  let paddleX = x - paddleWidth / 2;
  
  function draw() {
    if (state.activeGame) return; // 執行主遊戲時暫停預覽
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 繪製背景裝飾磚塊
    ctx.strokeStyle = 'rgba(255, 0, 127, 0.2)';
    ctx.lineWidth = 1;
    for (let c = 0; c < 5; c++) {
      for (let r = 0; r < 2; r++) {
        ctx.fillStyle = `rgba(255, 0, 127, ${0.05 + r * 0.05})`;
        ctx.fillRect(c * (canvas.width / 5) + 4, r * 20 + 20, (canvas.width / 5) - 8, 15);
        ctx.strokeRect(c * (canvas.width / 5) + 4, r * 20 + 20, (canvas.width / 5) - 8, 15);
      }
    }
    
    // 繪製球
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fillStyle = 'var(--neon-pink)';
    ctx.shadowBlur = 10;
    ctx.shadowColor = 'var(--neon-pink)';
    ctx.fill();
    ctx.closePath();
    ctx.shadowBlur = 0; // 重設
    
    // 繪製板子 (緩慢跟隨球移動)
    paddleX += (x - (paddleX + paddleWidth / 2)) * 0.1;
    ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.fillRect(paddleX, canvas.height - 15, paddleWidth, 8);
    
    // 移動碰撞
    if (x + dx > canvas.width - radius || x + dx < radius) dx = -dx;
    if (y + dy < radius) dy = -dy;
    else if (y + dy > canvas.height - 15) {
      if (x > paddleX && x < paddleX + paddleWidth) {
        dy = -dy;
      } else {
        x = canvas.width / 2;
        y = canvas.height - 40;
        dy = -2.5;
      }
    }
    
    x += dx;
    y += dy;
    
    previewIntervals.push(requestAnimationFrame(draw));
  }
  
  draw();
}

// 跑酷射擊自動預覽動畫
function animateRunnerPreview(canvas) {
  const ctx = canvas.getContext('2d');
  canvas.width = canvas.parentElement.offsetWidth;
  canvas.height = canvas.parentElement.offsetHeight;
  
  let stars = [];
  for (let i = 0; i < 20; i++) {
    stars.push({ x: Math.random() * canvas.width, y: Math.random() * canvas.height, speed: Math.random() * 2 + 1 });
  }
  
  let shipY = canvas.height / 2;
  let time = 0;
  
  function draw() {
    if (state.activeGame) return;
    time += 0.05;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 繪製跑酷背景星空
    ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
    stars.forEach(star => {
      ctx.fillRect(star.x, star.y, 2, 2);
      star.x -= star.speed;
      if (star.x < 0) star.x = canvas.width;
    });
    
    // 飛船上下漂浮
    shipY = canvas.height / 2 + Math.sin(time) * 15;
    
    // 繪製戰機 (簡化版三角形)
    ctx.beginPath();
    ctx.moveTo(35, shipY);
    ctx.lineTo(15, shipY - 10);
    ctx.lineTo(20, shipY);
    ctx.lineTo(15, shipY + 10);
    ctx.fillStyle = 'var(--neon-cyan)';
    ctx.shadowBlur = 10;
    ctx.shadowColor = 'var(--neon-cyan)';
    ctx.fill();
    ctx.closePath();
    ctx.shadowBlur = 0;
    
    // 隨機流星
    if (Math.random() < 0.05) {
      ctx.strokeStyle = 'rgba(0, 240, 255, 0.4)';
      ctx.beginPath();
      ctx.moveTo(canvas.width, Math.random() * canvas.height);
      ctx.lineTo(canvas.width - 50, Math.random() * canvas.height);
      ctx.stroke();
    }
    
    previewIntervals.push(requestAnimationFrame(draw));
  }
  
  draw();
}

// --- 7. 工具程式 ---
function escapeHTML(str) {
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}
