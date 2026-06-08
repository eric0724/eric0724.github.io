// 霓虹太空電玩城 - Cyber-Break (霓虹打磚塊) 遊戲引擎

let breakoutState = {
  running: false,
  score: 0,
  lives: 3,
  level: 1,
  
  paddle: { x: 340, y: 460, width: 120, height: 12, speed: 9, targetWidth: 120 },
  balls: [],
  bricks: [],
  particles: [],
  powerups: [],
  lasers: [],
  
  laserActive: false,
  laserAmmo: 0,
  shieldActive: false,
  
  keys: {},
  canvas: null,
  ctx: null,
  animationId: null
};

// 磚塊屬性
const BRICK_COLS = 8;
const BRICK_ROWS = 4;
const BRICK_HEIGHT = 20;
const BRICK_PADDING = 10;
const BRICK_TOP_OFFSET = 70;

// 道具屬性
const POWERUP_TYPES = [
  { type: 'multiball', label: '🟢', color: '#39ff14', desc: '多球分身' },
  { type: 'laser', label: '⚡', color: '#ff007f', desc: '雷射加農' },
  { type: 'grow', label: '📏', color: '#ffbd03', desc: '加長擋板' },
  { type: 'shield', label: '🛡️', color: '#00f0ff', desc: '能量底盾' }
];

function initBreakoutGame() {
  breakoutState.canvas = document.getElementById('gameCanvas');
  breakoutState.ctx = breakoutState.canvas.getContext('2d');
  breakoutState.running = true;
  
  // 重置數值
  breakoutState.score = 0;
  breakoutState.lives = 3;
  breakoutState.level = 1;
  breakoutState.balls = [];
  breakoutState.bricks = [];
  breakoutState.particles = [];
  breakoutState.powerups = [];
  breakoutState.lasers = [];
  breakoutState.laserActive = false;
  breakoutState.laserAmmo = 0;
  breakoutState.shieldActive = false;
  breakoutState.paddle.width = 120;
  breakoutState.paddle.targetWidth = 120;
  
  // 設定 UI 標題與 HUD
  document.getElementById('gameTitle').innerText = 'CYBER-BREAK';
  document.getElementById('gameTitle').style.color = 'var(--neon-pink)';
  document.getElementById('gameTitle').style.textShadow = 'var(--neon-pink-glow)';
  
  document.getElementById('gameCanvas').className = 'game-canvas-element neon-pink-glow-border';
  
  document.getElementById('hudLabel1').innerText = '分數:';
  document.getElementById('hudLabel2').innerText = '生命:';
  document.getElementById('hudExtraContainer').style.display = 'block';
  document.getElementById('hudLabel3').innerText = '關卡:';
  
  updateBreakoutHUD();
  setupBreakoutBricks();
  spawnBall(400, 430, 4, -4);
  
  // 顯示準備畫面覆蓋層
  showBreakoutOverlay('READY', '左右滑動或使用方向鍵控制擋板，擊碎所有磚塊！', '開始闖關');
  
  // 監聽鍵盤與滑鼠事件
  window.addEventListener('keydown', handleBreakoutKeyDown);
  window.addEventListener('keyup', handleBreakoutKeyUp);
  breakoutState.canvas.addEventListener('mousemove', handleBreakoutMouseMove);
  breakoutState.canvas.addEventListener('click', handleBreakoutCanvasClick);
  breakoutState.canvas.addEventListener('touchstart', handleBreakoutTouch, { passive: true });
  breakoutState.canvas.addEventListener('touchmove', handleBreakoutTouch, { passive: true });
}

function shutdownBreakoutGame() {
  breakoutState.running = false;
  if (breakoutState.animationId) {
    cancelAnimationFrame(breakoutState.animationId);
  }
  
  // 移除事件監聽
  window.removeEventListener('keydown', handleBreakoutKeyDown);
  window.removeEventListener('keyup', handleBreakoutKeyUp);
  if (breakoutState.canvas) {
    breakoutState.canvas.removeEventListener('mousemove', handleBreakoutMouseMove);
    breakoutState.canvas.removeEventListener('click', handleBreakoutCanvasClick);
    breakoutState.canvas.removeEventListener('touchstart', handleBreakoutTouch);
    breakoutState.canvas.removeEventListener('touchmove', handleBreakoutTouch);
  }
}

// 產生一顆球
function spawnBall(x, y, dx, dy) {
  breakoutState.balls.push({
    x: x,
    y: y,
    dx: dx,
    dy: dy,
    radius: 7,
    speed: Math.sqrt(dx*dx + dy*dy)
  });
}

// 初始化關卡磚塊
function setupBreakoutBricks() {
  const colors = ['#ff007f', '#bd00ff', '#00f0ff', '#39ff14']; // 霓虹粉、紫、青、綠
  const width = (breakoutState.canvas.width - BRICK_PADDING * (BRICK_COLS + 1)) / BRICK_COLS;
  
  breakoutState.bricks = [];
  for (let r = 0; r < BRICK_ROWS; r++) {
    for (let c = 0; c < BRICK_COLS; c++) {
      // 根據行數設定砖塊生命值 (最上面一排為 2 次擊打)
      const hp = (r === 0) ? 2 : 1;
      
      breakoutState.bricks.push({
        x: BRICK_PADDING + c * (width + BRICK_PADDING),
        y: BRICK_TOP_OFFSET + r * (BRICK_HEIGHT + BRICK_PADDING),
        width: width,
        height: BRICK_HEIGHT,
        color: colors[r % colors.length],
        hp: hp,
        maxHp: hp,
        points: (BRICK_ROWS - r) * 100
      });
    }
  }
}

function updateBreakoutHUD() {
  document.getElementById('hudVal1').innerText = breakoutState.score;
  document.getElementById('hudVal2').innerText = breakoutState.lives;
  document.getElementById('hudVal3').innerText = breakoutState.level;
}

// --- 遊戲畫面覆蓋管理 ---
function showBreakoutOverlay(type, desc, btnText) {
  const overlay = document.getElementById('gameOverlay');
  const title = document.getElementById('overlayTitle');
  const descEl = document.getElementById('overlayDesc');
  const btn = document.getElementById('btnOverlayAction');
  const submitArea = document.getElementById('highScoreSubmitArea');
  
  overlay.style.display = 'flex';
  submitArea.style.display = 'none';
  btn.className = 'overlay-btn pink';
  
  if (type === 'READY') {
    title.innerText = `LEVEL ${breakoutState.level}`;
    title.style.color = 'var(--neon-cyan)';
    title.style.textShadow = 'var(--neon-cyan-glow)';
    descEl.innerText = desc;
    btn.innerText = btnText;
    btn.onclick = startBreakoutLoop;
  } else if (type === 'GAMEOVER') {
    title.innerText = '電網崩潰 GAME OVER';
    title.style.color = 'var(--neon-pink)';
    title.style.textShadow = 'var(--neon-pink-glow)';
    descEl.innerHTML = `您的最終得分是：<strong style="color:var(--neon-gold); font-size:1.5rem;">${breakoutState.score}</strong><br>上傳您的傳奇代號至大廳排行榜！`;
    
    // 顯示名字上傳輸入
    submitArea.style.display = 'flex';
    document.getElementById('playerNameInput').value = localStorage.getItem('player_name_prefix') || 'PLAYER';
    
    btn.innerText = '上傳並重玩';
    btn.onclick = submitBreakoutScore;
  } else if (type === 'VICTORY') {
    title.innerText = '關卡淨化 VICTORY';
    title.style.color = 'var(--neon-green)';
    title.style.textShadow = 'var(--neon-green-glow)';
    descEl.innerText = desc;
    btn.innerText = btnText;
    btn.onclick = () => {
      breakoutState.level++;
      setupBreakoutBricks();
      breakoutState.balls = [];
      spawnBall(400, 430, 4, -4);
      showBreakoutOverlay('READY', `進入第 ${breakoutState.level} 關，速度更快，防禦更高！`, '開始挑戰');
    };
  }
}

function startBreakoutLoop() {
  document.getElementById('gameOverlay').style.display = 'none';
  // 解鎖音效
  if (typeof SoundEffects !== 'undefined') SoundEffects.break();
  
  // 啟動主迴圈
  breakoutState.running = true;
  runBreakoutGameLoop();
}

function submitBreakoutScore() {
  const input = document.getElementById('playerNameInput');
  const name = input.value.trim().toUpperCase() || 'PLAYER';
  localStorage.setItem('player_name_prefix', name);
  
  if (typeof addLeaderboardEntry !== 'undefined') {
    addLeaderboardEntry(name, breakoutState.score, 'Cyber-Break');
  }
  
  // 重新啟動
  initBreakoutGame();
}

// --- 事件處理常式 ---
function handleBreakoutKeyDown(e) {
  breakoutState.keys[e.key] = true;
  // 空白鍵射擊
  if (e.key === ' ' && breakoutState.laserActive) {
    shootBreakoutLaser();
    e.preventDefault();
  }
}

function handleBreakoutKeyUp(e) {
  breakoutState.keys[e.key] = false;
}

function handleBreakoutMouseMove(e) {
  const rect = breakoutState.canvas.getBoundingClientRect();
  // 響應式座標轉換
  const scaleX = breakoutState.canvas.width / rect.width;
  const relativeX = (e.clientX - rect.left) * scaleX;
  
  if (relativeX > 0 && relativeX < breakoutState.canvas.width) {
    breakoutState.paddle.x = relativeX - breakoutState.paddle.width / 2;
    // 邊界防禦
    if (breakoutState.paddle.x < 0) breakoutState.paddle.x = 0;
    if (breakoutState.paddle.x + breakoutState.paddle.width > breakoutState.canvas.width) {
      breakoutState.paddle.x = breakoutState.canvas.width - breakoutState.paddle.width;
    }
  }
}

function handleBreakoutTouch(e) {
  if (e.touches && e.touches.length > 0) {
    const rect = breakoutState.canvas.getBoundingClientRect();
    const scaleX = breakoutState.canvas.width / rect.width;
    const relativeX = (e.touches[0].clientX - rect.left) * scaleX;
    
    if (relativeX > 0 && relativeX < breakoutState.canvas.width) {
      breakoutState.paddle.x = relativeX - breakoutState.paddle.width / 2;
      // 邊界防禦
      if (breakoutState.paddle.x < 0) breakoutState.paddle.x = 0;
      if (breakoutState.paddle.x + breakoutState.paddle.width > breakoutState.canvas.width) {
        breakoutState.paddle.x = breakoutState.canvas.width - breakoutState.paddle.width;
      }
    }
  }
}

function handleBreakoutCanvasClick() {
  if (breakoutState.laserActive) {
    shootBreakoutLaser();
  }
}

// --- 射擊雷射 ---
function shootBreakoutLaser() {
  if (breakoutState.laserAmmo <= 0) {
    breakoutState.laserActive = false;
    return;
  }
  
  // 從擋板左右邊緣射出雙重電漿雷射
  breakoutState.lasers.push({ x: breakoutState.paddle.x, y: breakoutState.paddle.y - 10 });
  breakoutState.lasers.push({ x: breakoutState.paddle.x + breakoutState.paddle.width, y: breakoutState.paddle.y - 10 });
  
  breakoutState.laserAmmo--;
  if (typeof SoundEffects !== 'undefined') SoundEffects.shoot();
  
  // 解鎖成就
  if (typeof unlockAchievement !== 'undefined') unlockAchievement('b_laser');
}

// --- 遊戲運算核心邏輯 ---
function runBreakoutGameLoop() {
  if (!breakoutState.running) return;
  
  updateGamePhysics();
  drawGameBoard();
  
  breakoutState.animationId = requestAnimationFrame(runBreakoutGameLoop);
}

function updateGamePhysics() {
  // 1. 鍵盤控制擋板
  if (breakoutState.keys['ArrowLeft'] || breakoutState.keys['a']) {
    breakoutState.paddle.x -= breakoutState.paddle.speed;
    if (breakoutState.paddle.x < 0) breakoutState.paddle.x = 0;
  }
  if (breakoutState.keys['ArrowRight'] || breakoutState.keys['d']) {
    breakoutState.paddle.x += breakoutState.paddle.speed;
    if (breakoutState.paddle.x + breakoutState.paddle.width > breakoutState.canvas.width) {
      breakoutState.paddle.x = breakoutState.canvas.width - breakoutState.paddle.width;
    }
  }
  
  // 2. 平滑緩動擋板寬度
  if (breakoutState.paddle.width !== breakoutState.paddle.targetWidth) {
    breakoutState.paddle.width += (breakoutState.paddle.targetWidth - breakoutState.paddle.width) * 0.1;
  }
  
  // 3. 雷射飛行與碰撞
  for (let l = breakoutState.lasers.length - 1; l >= 0; l--) {
    const laser = breakoutState.lasers[l];
    laser.y -= 7;
    
    // 超出螢幕
    if (laser.y < 0) {
      breakoutState.lasers.splice(l, 1);
      continue;
    }
    
    // 碰撞磚塊
    let hit = false;
    for (let b = 0; b < breakoutState.bricks.length; b++) {
      const brick = breakoutState.bricks[b];
      if (laser.x > brick.x && laser.x < brick.x + brick.width &&
          laser.y > brick.y && laser.y < brick.y + brick.height) {
        
        hitBrick(b);
        hit = true;
        break;
      }
    }
    
    if (hit) {
      breakoutState.lasers.splice(l, 1);
    }
  }
  
  // 4. 道具墜落與收集
  for (let p = breakoutState.powerups.length - 1; p >= 0; p--) {
    const power = breakoutState.powerups[p];
    power.y += 2.2;
    
    // 落出螢幕
    if (power.y > breakoutState.canvas.height) {
      breakoutState.powerups.splice(p, 1);
      continue;
    }
    
    // 與擋板碰撞
    if (power.y + 12 > breakoutState.paddle.y &&
        power.x > breakoutState.paddle.x &&
        power.x < breakoutState.paddle.x + breakoutState.paddle.width) {
      
      triggerPowerup(power.type);
      breakoutState.powerups.splice(p, 1);
      if (typeof SoundEffects !== 'undefined') SoundEffects.powerup();
      continue;
    }
  }
  
  // 5. 球體移動與碰撞
  if (breakoutState.balls.length === 0) {
    handleBallLoss();
    return;
  }
  
  for (let i = breakoutState.balls.length - 1; i >= 0; i--) {
    const ball = breakoutState.balls[i];
    ball.x += ball.dx;
    ball.y += ball.dy;
    
    // 左右牆壁碰撞
    if (ball.x + ball.radius > breakoutState.canvas.width || ball.x - ball.radius < 0) {
      ball.dx = -ball.dx;
      ball.x = (ball.x - ball.radius < 0) ? ball.radius : breakoutState.canvas.width - ball.radius;
      if (typeof SoundEffects !== 'undefined') SoundEffects.hit();
    }
    
    // 上牆壁碰撞
    if (ball.y - ball.radius < 0) {
      ball.dy = -ball.dy;
      ball.y = ball.radius;
      if (typeof SoundEffects !== 'undefined') SoundEffects.hit();
    }
    
    // 底部護盾碰撞
    if (breakoutState.shieldActive && ball.y + ball.radius >= breakoutState.canvas.height - 12) {
      ball.dy = -ball.dy;
      ball.y = breakoutState.canvas.height - 12 - ball.radius;
      breakoutState.shieldActive = false; // 一次性護盾
      triggerScreenShake();
      if (typeof SoundEffects !== 'undefined') SoundEffects.hit();
    }
    
    // 墜落底線
    if (ball.y + ball.radius > breakoutState.canvas.height) {
      breakoutState.balls.splice(i, 1);
      continue;
    }
    
    // 與擋板碰撞 (具備弧度反彈算法，擊中邊角會反彈更陡)
    if (ball.y + ball.radius >= breakoutState.paddle.y &&
        ball.y - ball.radius <= breakoutState.paddle.y + breakoutState.paddle.height &&
        ball.x + ball.radius >= breakoutState.paddle.x &&
        ball.x - ball.radius <= breakoutState.paddle.x + breakoutState.paddle.width) {
      
      // 確保球是由上往下落時才碰撞
      if (ball.dy > 0) {
        const relativeX = ball.x - (breakoutState.paddle.x + breakoutState.paddle.width / 2);
        const normalizedRelativeX = relativeX / (breakoutState.paddle.width / 2);
        const bounceAngle = normalizedRelativeX * (Math.PI / 3.2); // 最大反彈角約 56 度
        
        ball.dx = ball.speed * Math.sin(bounceAngle);
        ball.dy = -ball.speed * Math.cos(bounceAngle);
        ball.y = breakoutState.paddle.y - ball.radius;
        
        if (typeof SoundEffects !== 'undefined') SoundEffects.hit();
      }
    }
    
    // 與磚塊碰撞
    let hit = false;
    for (let b = 0; b < breakoutState.bricks.length; b++) {
      const brick = breakoutState.bricks[b];
      
      // AABB 簡單碰撞檢測
      if (ball.x + ball.radius > brick.x && ball.x - ball.radius < brick.x + brick.width &&
          ball.y + ball.radius > brick.y && ball.y - ball.radius < brick.y + brick.height) {
        
        // 決定反彈軸向
        const overlapX = Math.min(ball.x + ball.radius - brick.x, brick.x + brick.width - (ball.x - ball.radius));
        const overlapY = Math.min(ball.y + ball.radius - brick.y, brick.y + brick.height - (ball.y - ball.radius));
        
        if (overlapX < overlapY) {
          ball.dx = -ball.dx;
        } else {
          ball.dy = -ball.dy;
        }
        
        hitBrick(b);
        hit = true;
        break;
      }
    }
  }
  
  // 6. 粒子模擬
  for (let p = breakoutState.particles.length - 1; p >= 0; p--) {
    const particle = breakoutState.particles[p];
    particle.x += particle.dx;
    particle.y += particle.dy;
    particle.life--;
    if (particle.life <= 0) {
      breakoutState.particles.splice(p, 1);
    }
  }
}

// 擊中磚塊
function hitBrick(index) {
  const brick = breakoutState.bricks[index];
  brick.hp--;
  
  if (brick.hp <= 0) {
    // 產生爆炸粒子
    spawnNeonParticles(brick.x + brick.width / 2, brick.y + brick.height / 2, brick.color, 12);
    
    // 累計得分
    breakoutState.score += brick.points;
    updateBreakoutHUD();
    
    // 解鎖成就
    if (typeof unlockAchievement !== 'undefined') {
      unlockAchievement('b_first');
      if (breakoutState.score >= 1000) unlockAchievement('b_gold');
    }
    
    // 隨機掉落道具 (20% 機率)
    if (Math.random() < 0.22) {
      const pType = POWERUP_TYPES[Math.floor(Math.random() * POWERUP_TYPES.length)];
      breakoutState.powerups.push({
        x: brick.x + brick.width / 2,
        y: brick.y + brick.height,
        type: pType.type,
        label: pType.label,
        color: pType.color
      });
    }
    
    // 移除磚塊
    breakoutState.bricks.splice(index, 1);
    triggerScreenShake();
    
    if (typeof SoundEffects !== 'undefined') SoundEffects.break();
    
    // 檢查是否通關
    if (breakoutState.bricks.length === 0) {
      handleBreakoutVictory();
    }
  } else {
    // 未破裂但受擊
    spawnNeonParticles(brick.x + brick.width / 2, brick.y + brick.height / 2, '#fff', 4);
    if (typeof SoundEffects !== 'undefined') SoundEffects.hit();
  }
}

// 畫面震動
function triggerScreenShake() {
  const container = document.getElementById('gameWorkspace');
  container.classList.add('canvas-shake');
  setTimeout(() => {
    container.classList.remove('canvas-shake');
  }, 150);
}

// 產生霓虹炫光粒子
function spawnNeonParticles(x, y, color, count) {
  for (let i = 0; i < count; i++) {
    const angle = Math.random() * Math.PI * 2;
    const speed = Math.random() * 3 + 1.5;
    const life = Math.random() * 20 + 20;
    
    breakoutState.particles.push({
      x: x,
      y: y,
      dx: Math.cos(angle) * speed,
      dy: Math.sin(angle) * speed,
      color: color,
      size: Math.random() * 3 + 1.5,
      life: life,
      maxLife: life
    });
  }
}

// 道具觸發邏輯
function triggerPowerup(type) {
  if (type === 'multiball') {
    // 分裂當前所有的球
    const count = breakoutState.balls.length;
    for (let i = 0; i < count; i++) {
      const ball = breakoutState.balls[i];
      if (ball) {
        // 多發兩顆有夾角的球
        spawnBall(ball.x, ball.y, ball.dx - 1.5, ball.dy + 0.5);
        spawnBall(ball.x, ball.y, ball.dx + 1.5, ball.dy - 0.5);
      }
    }
  } else if (type === 'laser') {
    breakoutState.laserActive = true;
    breakoutState.laserAmmo = 5; // 限制可發射 5 次雙重雷射
  } else if (type === 'grow') {
    breakoutState.paddle.targetWidth = 200;
    // 10 秒後恢復原狀
    setTimeout(() => {
      breakoutState.paddle.targetWidth = 120;
    }, 10000);
  } else if (type === 'shield') {
    breakoutState.shieldActive = true;
  }
}

function handleBallLoss() {
  breakoutState.lives--;
  updateBreakoutHUD();
  
  if (breakoutState.lives <= 0) {
    // 遊戲結束
    breakoutState.running = false;
    if (typeof SoundEffects !== 'undefined') SoundEffects.gameover();
    showBreakoutOverlay('GAMEOVER');
  } else {
    // 重新部署一顆球
    spawnBall(400, 430, 4, -4);
    breakoutState.laserActive = false;
    breakoutState.laserAmmo = 0;
    breakoutState.shieldActive = false;
  }
}

function handleBreakoutVictory() {
  breakoutState.running = false;
  if (typeof SoundEffects !== 'undefined') SoundEffects.win();
  showBreakoutOverlay('VICTORY', `恭喜完成第 ${breakoutState.level} 關！傳送至下一個更高的維度空間...`, '傳送前進');
}

// --- 8. 畫布渲染核心 ---
function drawGameBoard() {
  const ctx = breakoutState.ctx;
  const canvas = breakoutState.canvas;
  
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  // A. 繪製底部能量護盾
  if (breakoutState.shieldActive) {
    ctx.strokeStyle = 'var(--neon-cyan)';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(0, canvas.height - 8);
    ctx.lineTo(canvas.width, canvas.height - 8);
    ctx.shadowBlur = 15;
    ctx.shadowColor = 'var(--neon-cyan)';
    ctx.stroke();
    ctx.shadowBlur = 0; // 重置
  }
  
  // B. 繪製所有磚塊
  breakoutState.bricks.forEach(brick => {
    // 如果 HP 為 2 代表是裝甲磚塊，給予雙層漸變
    if (brick.hp === 2) {
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(brick.x, brick.y, brick.width, brick.height);
      ctx.fillStyle = brick.color;
      ctx.fillRect(brick.x + 2, brick.y + 2, brick.width - 4, brick.height - 4);
    } else {
      ctx.fillStyle = brick.color;
      ctx.fillRect(brick.x, brick.y, brick.width, brick.height);
    }
    
    // 微亮描邊
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
    ctx.lineWidth = 1;
    ctx.strokeRect(brick.x, brick.y, brick.width, brick.height);
  });
  
  // C. 繪製雷射子彈
  breakoutState.lasers.forEach(laser => {
    ctx.fillStyle = 'var(--neon-pink)';
    ctx.shadowBlur = 10;
    ctx.shadowColor = 'var(--neon-pink)';
    ctx.fillRect(laser.x - 2, laser.y, 4, 15);
    ctx.shadowBlur = 0;
  });
  
  // D. 繪製道具
  breakoutState.powerups.forEach(power => {
    ctx.fillStyle = power.color;
    ctx.shadowBlur = 12;
    ctx.shadowColor = power.color;
    ctx.beginPath();
    ctx.arc(power.x, power.y, 11, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
    
    // 繪製道具 icon 文字
    ctx.fillStyle = '#000000';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(power.label, power.x, power.y);
  });
  
  // E. 繪製所有的球
  breakoutState.balls.forEach(ball => {
    ctx.beginPath();
    ctx.arc(ball.x, ball.y, ball.radius, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.shadowBlur = 15;
    ctx.shadowColor = 'var(--neon-pink)';
    ctx.fill();
    ctx.closePath();
    ctx.shadowBlur = 0;
  });
  
  // F. 繪製擋板 (Paddle)
  ctx.fillStyle = 'var(--neon-pink)';
  ctx.shadowBlur = 15;
  ctx.shadowColor = 'var(--neon-pink)';
  ctx.fillRect(breakoutState.paddle.x, breakoutState.paddle.y, breakoutState.paddle.width, breakoutState.paddle.height);
  ctx.shadowBlur = 0;
  
  // 雷射槍管裝飾
  if (breakoutState.laserActive) {
    ctx.fillStyle = '#ffffff';
    // 繪製左右發光砲台
    ctx.fillRect(breakoutState.paddle.x - 2, breakoutState.paddle.y - 6, 6, 6);
    ctx.fillRect(breakoutState.paddle.x + breakoutState.paddle.width - 4, breakoutState.paddle.y - 6, 6, 6);
    
    // 顯示子彈數量
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 9px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(`⚡ ${breakoutState.laserAmmo}`, breakoutState.paddle.x + breakoutState.paddle.width / 2, breakoutState.paddle.y - 6);
  }
  
  // G. 繪製炫酷粒子
  breakoutState.particles.forEach(p => {
    ctx.globalAlpha = p.life / p.maxLife;
    ctx.fillStyle = p.color;
    ctx.fillRect(p.x, p.y, p.size, p.size);
  });
  ctx.globalAlpha = 1.0; // 重置透明度
}
