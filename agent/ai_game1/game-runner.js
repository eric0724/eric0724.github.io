// 霓虹太空電玩城 - Cosmo-Rider (星際星航者) 遊戲引擎

let runnerState = {
  running: false,
  score: 0,
  lives: 3,
  combo: 0,
  comboTimer: 0,
  scrollSpeed: 4.5,
  
  ship: { x: 80, y: 250, width: 38, height: 22, speed: 8.5 },
  obstacles: [],
  crystals: [],
  lasers: [],
  particles: [],
  stars: [],
  
  keys: {},
  canvas: null,
  ctx: null,
  animationId: null,
  spawnTimer: 0,
  crystalTimer: 0
};

// 隕石爆炸色彩
const METEOR_COLORS = ['#ffbd03', '#ff5500', '#7a5a00'];

function initRunnerGame() {
  runnerState.canvas = document.getElementById('gameCanvas');
  runnerState.ctx = runnerState.canvas.getContext('2d');
  runnerState.running = true;
  
  // 重置數值
  runnerState.score = 0;
  runnerState.lives = 3;
  runnerState.combo = 1;
  runnerState.comboTimer = 0;
  runnerState.scrollSpeed = 4.5;
  runnerState.obstacles = [];
  runnerState.crystals = [];
  runnerState.lasers = [];
  runnerState.particles = [];
  runnerState.ship.y = 250;
  
  // 建立星空背景層 (深度景深效果)
  runnerState.stars = [];
  for (let i = 0; i < 40; i++) {
    runnerState.stars.push({
      x: Math.random() * runnerState.canvas.width,
      y: Math.random() * runnerState.canvas.height,
      size: Math.random() * 2 + 0.5,
      speed: Math.random() * 1.5 + 0.5
    });
  }
  
  // 設定 UI 標題與 HUD
  document.getElementById('gameTitle').innerText = 'COSMO-RIDER';
  document.getElementById('gameTitle').style.color = 'var(--neon-cyan)';
  document.getElementById('gameTitle').style.textShadow = 'var(--neon-cyan-glow)';
  
  document.getElementById('gameCanvas').className = 'game-canvas-element neon-cyan-glow-border';
  
  document.getElementById('hudLabel1').innerText = '分數:';
  document.getElementById('hudLabel2').innerText = '生命:';
  document.getElementById('hudExtraContainer').style.display = 'block';
  document.getElementById('hudLabel3').innerText = '連擊:';
  
  updateRunnerHUD();
  
  // 顯示準備畫面覆蓋層
  showRunnerOverlay('READY', '滑動或使用鍵盤 [W/S] 控制飛船，點擊畫布或按 [空白鍵] 發射雷射炸碎隕石並吃發光水晶！', '啟航進入深空');
  
  // 監聽鍵盤與滑鼠事件
  window.addEventListener('keydown', handleRunnerKeyDown);
  window.addEventListener('keyup', handleRunnerKeyUp);
  runnerState.canvas.addEventListener('mousemove', handleRunnerMouseMove);
  runnerState.canvas.addEventListener('click', handleRunnerCanvasClick);
  runnerState.canvas.addEventListener('touchstart', handleRunnerTouch, { passive: true });
  runnerState.canvas.addEventListener('touchmove', handleRunnerTouch, { passive: true });
}

function shutdownRunnerGame() {
  runnerState.running = false;
  if (runnerState.animationId) {
    cancelAnimationFrame(runnerState.animationId);
  }
  
  // 移除事件監聽
  window.removeEventListener('keydown', handleRunnerKeyDown);
  window.removeEventListener('keyup', handleRunnerKeyUp);
  if (runnerState.canvas) {
    runnerState.canvas.removeEventListener('mousemove', handleRunnerMouseMove);
    runnerState.canvas.removeEventListener('click', handleRunnerCanvasClick);
    runnerState.canvas.removeEventListener('touchstart', handleRunnerTouch);
    runnerState.canvas.removeEventListener('touchmove', handleRunnerTouch);
  }
}

function updateRunnerHUD() {
  document.getElementById('hudVal1').innerText = runnerState.score;
  document.getElementById('hudVal2').innerText = runnerState.lives;
  document.getElementById('hudVal3').innerText = `x${runnerState.combo}`;
}

// --- 遊戲畫面覆蓋管理 ---
function showRunnerOverlay(type, desc, btnText) {
  const overlay = document.getElementById('gameOverlay');
  const title = document.getElementById('overlayTitle');
  const descEl = document.getElementById('overlayDesc');
  const btn = document.getElementById('btnOverlayAction');
  const submitArea = document.getElementById('highScoreSubmitArea');
  
  overlay.style.display = 'flex';
  submitArea.style.display = 'none';
  btn.className = 'overlay-btn cyan';
  
  if (type === 'READY') {
    title.innerText = 'COSMO-RIDER 準備啟動';
    title.style.color = 'var(--neon-cyan)';
    title.style.textShadow = 'var(--neon-cyan-glow)';
    descEl.innerText = desc;
    btn.innerText = btnText;
    btn.onclick = startRunnerLoop;
  } else if (type === 'GAMEOVER') {
    title.innerText = '戰機損毀 GAME OVER';
    title.style.color = 'var(--neon-pink)';
    title.style.textShadow = 'var(--neon-pink-glow)';
    descEl.innerHTML = `您的最終得分是：<strong style="color:var(--neon-cyan); font-size:1.5rem;">${runnerState.score}</strong><br>上傳您的傳奇代號至大廳排行榜！`;
    
    // 顯示名字上傳輸入
    submitArea.style.display = 'flex';
    document.getElementById('playerNameInput').value = localStorage.getItem('player_name_prefix') || 'PLAYER';
    
    btn.innerText = '上傳並重新啟航';
    btn.onclick = submitRunnerScore;
  }
}

function startRunnerLoop() {
  document.getElementById('gameOverlay').style.display = 'none';
  // 解鎖音效
  if (typeof SoundEffects !== 'undefined') SoundEffects.break();
  
  runnerState.running = true;
  runRunnerGameLoop();
}

function submitRunnerScore() {
  const input = document.getElementById('playerNameInput');
  const name = input.value.trim().toUpperCase() || 'PLAYER';
  localStorage.setItem('player_name_prefix', name);
  
  if (typeof addLeaderboardEntry !== 'undefined') {
    addLeaderboardEntry(name, runnerState.score, 'Cosmo-Rider');
  }
  
  // 重新啟動
  initRunnerGame();
}

// --- 事件處理常式 ---
function handleRunnerKeyDown(e) {
  runnerState.keys[e.key] = true;
  if (e.key === ' ' || e.key === 'Spacebar') {
    shootRunnerLaser();
    e.preventDefault();
  }
}

function handleRunnerKeyUp(e) {
  runnerState.keys[e.key] = false;
}

function handleRunnerMouseMove(e) {
  const rect = runnerState.canvas.getBoundingClientRect();
  const scaleY = runnerState.canvas.height / rect.height;
  const relativeY = (e.clientY - rect.top) * scaleY;
  
  if (relativeY > 0 && relativeY < runnerState.canvas.height) {
    runnerState.ship.y = relativeY - runnerState.ship.height / 2;
    boundaryKeepShip();
  }
}

function handleRunnerTouch(e) {
  if (e.touches && e.touches.length > 0) {
    const rect = runnerState.canvas.getBoundingClientRect();
    const scaleY = runnerState.canvas.height / rect.height;
    const relativeY = (e.touches[0].clientY - rect.top) * scaleY;
    
    if (relativeY > 0 && relativeY < runnerState.canvas.height) {
      runnerState.ship.y = relativeY - runnerState.ship.height / 2;
      boundaryKeepShip();
    }
  }
}

function handleRunnerCanvasClick() {
  shootRunnerLaser();
}

function boundaryKeepShip() {
  if (runnerState.ship.y < 10) runnerState.ship.y = 10;
  if (runnerState.ship.y + runnerState.ship.height > runnerState.canvas.height - 10) {
    runnerState.ship.y = runnerState.canvas.height - runnerState.ship.height - 10;
  }
}

// --- 射擊雷射砲 ---
function shootRunnerLaser() {
  // 從飛船頭部射出雙重電漿雷射
  runnerState.lasers.push({
    x: runnerState.ship.x + runnerState.ship.width,
    y: runnerState.ship.y + runnerState.ship.height / 2,
    radius: 3,
    speed: 12
  });
  
  if (typeof SoundEffects !== 'undefined') SoundEffects.shoot();
}

// --- 跑酷引擎核心邏輯 ---
function runRunnerGameLoop() {
  if (!runnerState.running) return;
  
  updateRunnerPhysics();
  drawRunnerBoard();
  
  runnerState.animationId = requestAnimationFrame(runRunnerGameLoop);
}

function updateRunnerPhysics() {
  // 1. 鍵盤控制飛船
  if (runnerState.keys['ArrowUp'] || runnerState.keys['w']) {
    runnerState.ship.y -= runnerState.ship.speed;
  }
  if (runnerState.keys['ArrowDown'] || runnerState.keys['s']) {
    runnerState.ship.y += runnerState.ship.speed;
  }
  boundaryKeepShip();
  
  // 飛船尾噴粒子流 (Thrust Particle)
  if (Math.random() < 0.6) {
    runnerState.particles.push({
      x: runnerState.ship.x - 2,
      y: runnerState.ship.y + runnerState.ship.height / 2 + (Math.random() - 0.5) * 8,
      dx: -Math.random() * 3 - 2,
      dy: (Math.random() - 0.5) * 1.5,
      color: 'rgba(0, 240, 255, 0.8)',
      size: Math.random() * 3 + 1,
      life: 15,
      maxLife: 15
    });
  }
  
  // 2. 背景景深星空流動
  runnerState.stars.forEach(star => {
    star.x -= star.speed + runnerState.scrollSpeed * 0.15;
    if (star.x < 0) {
      star.x = runnerState.canvas.width;
      star.y = Math.random() * runnerState.canvas.height;
    }
  });
  
  // 3. 難度隨分數遞增 (加快滾動速度)
  runnerState.scrollSpeed = 4.5 + (runnerState.score / 2000);
  
  // 4. 定時生成障礙隕石與水晶
  runnerState.spawnTimer++;
  const spawnRate = Math.max(30, 70 - Math.floor(runnerState.score / 150));
  if (runnerState.spawnTimer >= spawnRate) {
    runnerState.spawnTimer = 0;
    
    // 生成隕石
    const size = Math.random() * 30 + 15;
    const hp = size > 35 ? 2 : 1; // 大隕石需要擊打 2 次
    runnerState.obstacles.push({
      x: runnerState.canvas.width + 50,
      y: Math.random() * (runnerState.canvas.height - 80) + 40,
      size: size,
      speed: Math.random() * 2 + 3 + (runnerState.scrollSpeed * 0.3),
      hp: hp,
      maxHp: hp,
      rotation: 0,
      rotationSpeed: (Math.random() - 0.5) * 0.05
    });
  }
  
  runnerState.crystalTimer++;
  if (runnerState.crystalTimer >= 130) {
    runnerState.crystalTimer = 0;
    
    // 生成水晶 (青色一般、金色連擊)
    const isGold = Math.random() < 0.25;
    runnerState.crystals.push({
      x: runnerState.canvas.width + 50,
      y: Math.random() * (runnerState.canvas.height - 80) + 40,
      size: 9,
      speed: 3.5 + (runnerState.scrollSpeed * 0.2),
      isGold: isGold
    });
  }
  
  // 5. 雷射子彈飛行與碰撞
  for (let l = runnerState.lasers.length - 1; l >= 0; l--) {
    const laser = runnerState.lasers[l];
    laser.x += laser.speed;
    
    if (laser.x > runnerState.canvas.width + 10) {
      runnerState.lasers.splice(l, 1);
      continue;
    }
    
    // 雷射碰撞隕石
    let laserHit = false;
    for (let o = 0; o < runnerState.obstacles.length; o++) {
      const meteor = runnerState.obstacles[o];
      
      const dx = laser.x - meteor.x;
      const dy = laser.y - meteor.y;
      const distance = Math.sqrt(dx*dx + dy*dy);
      
      if (distance < meteor.size) {
        laserHit = true;
        meteor.hp--;
        
        if (meteor.hp <= 0) {
          // 摧毀隕石
          spawnRunnerExplosion(meteor.x, meteor.y, METEOR_COLORS[Math.floor(Math.random() * METEOR_COLORS.length)], 14);
          
          // 連擊與得分系統
          runnerState.comboTimer = 220; // 重置連擊計時器 (約 3.6 秒)
          runnerState.score += 50 * runnerState.combo;
          
          // 獲得第 1 次擊碎隕石成就
          if (typeof unlockAchievement !== 'undefined') {
            unlockAchievement('r_first');
            if (runnerState.combo >= 5) unlockAchievement('r_combo');
            if (runnerState.score >= 1000) unlockAchievement('r_gold');
          }
          
          runnerState.combo++;
          updateRunnerHUD();
          
          runnerState.obstacles.splice(o, 1);
          triggerScreenShake();
          if (typeof SoundEffects !== 'undefined') SoundEffects.hit();
        } else {
          // 打擊火花
          spawnRunnerExplosion(laser.x, laser.y, '#fff', 4);
          if (typeof SoundEffects !== 'undefined') SoundEffects.break();
        }
        
        break;
      }
    }
    
    if (laserHit) {
      runnerState.lasers.splice(l, 1);
    }
  }
  
  // 6. 連擊計時器遞減
  if (runnerState.combo > 1) {
    runnerState.comboTimer--;
    if (runnerState.comboTimer <= 0) {
      runnerState.combo = 1;
      updateRunnerHUD();
    }
  }
  
  // 7. 隕石移動與碰撞戰機
  for (let o = runnerState.obstacles.length - 1; o >= 0; o--) {
    const meteor = runnerState.obstacles[o];
    meteor.x -= meteor.speed;
    meteor.rotation += meteor.rotationSpeed;
    
    if (meteor.x < -50) {
      runnerState.obstacles.splice(o, 1);
      continue;
    }
    
    // 與戰機碰撞
    const shipCenterX = runnerState.ship.x + runnerState.ship.width / 2;
    const shipCenterY = runnerState.ship.y + runnerState.ship.height / 2;
    
    const dx = shipCenterX - meteor.x;
    const dy = shipCenterY - meteor.y;
    const distance = Math.sqrt(dx*dx + dy*dy);
    
    if (distance < meteor.size + 10) {
      // 戰機撞毀
      spawnRunnerExplosion(shipCenterX, shipCenterY, '#ff007f', 20);
      runnerState.obstacles.splice(o, 1);
      
      runnerState.lives--;
      runnerState.combo = 1;
      updateRunnerHUD();
      
      triggerScreenShake();
      if (typeof SoundEffects !== 'undefined') SoundEffects.gameover();
      
      if (runnerState.lives <= 0) {
        runnerState.running = false;
        showRunnerOverlay('GAMEOVER');
      }
    }
  }
  
  // 8. 水晶移動與收集
  for (let c = runnerState.crystals.length - 1; c >= 0; c--) {
    const crystal = runnerState.crystals[c];
    crystal.x -= crystal.speed;
    
    if (crystal.x < -20) {
      runnerState.crystals.splice(c, 1);
      continue;
    }
    
    // 水晶碰撞飛船
    const shipCenterX = runnerState.ship.x + runnerState.ship.width / 2;
    const shipCenterY = runnerState.ship.y + runnerState.ship.height / 2;
    
    const dx = shipCenterX - crystal.x;
    const dy = shipCenterY - crystal.y;
    const distance = Math.sqrt(dx*dx + dy*dy);
    
    if (distance < 20) {
      // 拾取水晶
      const pts = crystal.isGold ? 300 : 100;
      runnerState.score += pts * runnerState.combo;
      
      if (crystal.isGold) {
        runnerState.comboTimer = 220;
        runnerState.combo += 2; // 金色直接大增連擊
      }
      
      updateRunnerHUD();
      
      // 收集特效粒子
      spawnRunnerExplosion(crystal.x, crystal.y, crystal.isGold ? 'var(--neon-gold)' : 'var(--neon-cyan)', 8);
      runnerState.crystals.splice(c, 1);
      
      if (typeof SoundEffects !== 'undefined') SoundEffects.powerup();
    }
  }
  
  // 9. 粒子飛行遞減
  for (let p = runnerState.particles.length - 1; p >= 0; p--) {
    const particle = runnerState.particles[p];
    particle.x += particle.dx;
    particle.y += particle.dy;
    particle.life--;
    if (particle.life <= 0) {
      runnerState.particles.splice(p, 1);
    }
  }
}

// 產生隕石爆炸發光碎屑
function spawnRunnerExplosion(x, y, color, count) {
  for (let i = 0; i < count; i++) {
    const angle = Math.random() * Math.PI * 2;
    const speed = Math.random() * 4 + 2;
    const life = Math.random() * 20 + 15;
    
    runnerState.particles.push({
      x: x,
      y: y,
      dx: Math.cos(angle) * speed,
      dy: Math.sin(angle) * speed,
      color: color,
      size: Math.random() * 4 + 1.5,
      life: life,
      maxLife: life
    });
  }
}

// --- 8. 畫布渲染核心 ---
function drawRunnerBoard() {
  const ctx = runnerState.ctx;
  const canvas = runnerState.canvas;
  
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  // A. 繪製滾動背景星空
  ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
  runnerState.stars.forEach(star => {
    ctx.fillRect(star.x, star.y, star.size, star.size);
  });
  
  // B. 繪製雷射砲子彈 (發光青色線條)
  runnerState.lasers.forEach(laser => {
    ctx.fillStyle = 'var(--neon-cyan)';
    ctx.shadowBlur = 10;
    ctx.shadowColor = 'var(--neon-cyan)';
    ctx.fillRect(laser.x, laser.y - 1.5, 14, 3);
    ctx.shadowBlur = 0;
  });
  
  // C. 繪製星雲水晶 (菱形 / 雙層漸變)
  runnerState.crystals.forEach(crystal => {
    ctx.fillStyle = crystal.isGold ? 'var(--neon-gold)' : 'var(--neon-cyan)';
    ctx.shadowBlur = 12;
    ctx.shadowColor = ctx.fillStyle;
    
    ctx.beginPath();
    ctx.moveTo(crystal.x, crystal.y - crystal.size);
    ctx.lineTo(crystal.x + crystal.size, crystal.y);
    ctx.lineTo(crystal.x, crystal.y + crystal.size);
    ctx.lineTo(crystal.x - crystal.size, crystal.y);
    ctx.closePath();
    ctx.fill();
    ctx.shadowBlur = 0;
  });
  
  // D. 繪製障礙隕石 (具有細緻浮空角度與發光斑駁質感)
  runnerState.obstacles.forEach(meteor => {
    ctx.save();
    ctx.translate(meteor.x, meteor.y);
    ctx.rotate(meteor.rotation);
    
    ctx.fillStyle = '#221a24';
    ctx.strokeStyle = meteor.hp === 2 ? 'var(--neon-gold)' : 'var(--neon-pink)';
    ctx.lineWidth = 2;
    ctx.shadowBlur = 8;
    ctx.shadowColor = ctx.strokeStyle;
    
    // 繪製多邊形隕石 (避免枯燥的圓形)
    ctx.beginPath();
    const steps = 8;
    for (let i = 0; i < steps; i++) {
      const angle = (i / steps) * Math.PI * 2;
      // 增加不規則起伏
      const offset = (Math.sin(angle * 3) + Math.cos(angle * 2)) * 3;
      const radius = meteor.size + offset;
      const rx = Math.cos(angle) * radius;
      const ry = Math.sin(angle) * radius;
      
      if (i === 0) ctx.moveTo(rx, ry);
      else ctx.lineTo(rx, ry);
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    
    // 繪製隕石坑斑駁點綴
    ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.beginPath();
    ctx.arc(-meteor.size/3, -meteor.size/4, meteor.size/4, 0, Math.PI * 2);
    ctx.arc(meteor.size/4, meteor.size/3, meteor.size/5, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.restore();
    ctx.shadowBlur = 0;
  });
  
  // E. 繪製玩家宇宙飛船 (炫酷未來戰機，多重線條與尾部離子發光)
  ctx.save();
  ctx.translate(runnerState.ship.x, runnerState.ship.y);
  
  ctx.fillStyle = 'var(--neon-cyan)';
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 1;
  ctx.shadowBlur = 15;
  ctx.shadowColor = 'var(--neon-cyan)';
  
  // 繪製三角形/星際梭子型戰機
  ctx.beginPath();
  ctx.moveTo(runnerState.ship.width, runnerState.ship.height / 2); // 頂角頭部
  ctx.lineTo(0, 0); // 左尾翼
  ctx.lineTo(runnerState.ship.width * 0.25, runnerState.ship.height / 2); // 中後凹進
  ctx.lineTo(0, runnerState.ship.height); // 右尾翼
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  
  // 駕駛艙高亮
  ctx.fillStyle = '#ffffff';
  ctx.beginPath();
  ctx.moveTo(runnerState.ship.width * 0.75, runnerState.ship.height / 2);
  ctx.lineTo(runnerState.ship.width * 0.45, runnerState.ship.height / 3);
  ctx.lineTo(runnerState.ship.width * 0.35, runnerState.ship.height / 2);
  ctx.lineTo(runnerState.ship.width * 0.45, runnerState.ship.height * 2/3);
  ctx.closePath();
  ctx.fill();
  
  ctx.restore();
  ctx.shadowBlur = 0;
  
  // F. 繪製粒子流
  runnerState.particles.forEach(p => {
    ctx.globalAlpha = p.life / p.maxLife;
    ctx.fillStyle = p.color;
    ctx.fillRect(p.x, p.y, p.size, p.size);
  });
  ctx.globalAlpha = 1.0;
  
  // G. 繪製 Combo 進度條 (若 combo > 1 顯示倒數提示)
  if (runnerState.combo > 1) {
    const width = 120;
    const progress = runnerState.comboTimer / 220;
    
    ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.fillRect(canvas.width - width - 20, 20, width, 6);
    
    ctx.fillStyle = 'var(--neon-cyan)';
    ctx.shadowBlur = 5;
    ctx.shadowColor = 'var(--neon-cyan)';
    ctx.fillRect(canvas.width - width - 20, 20, width * progress, 6);
    ctx.shadowBlur = 0;
  }
}
