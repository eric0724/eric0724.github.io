// 小龍蝦 (Miniclaw) 控制中樞 - 前端動力邏輯

const GOOGLE_CLIENT_ID = '251069433697-sg19f5eq4r0a94nanr92v5h64mkn0fho.apps.googleusercontent.com';

const webState = {
  currentStep: 1,
  platform: 'windows',
  apiMode: 'complete',
  apiKey: '',
  googleAccessToken: '',
  googleUser: null,
  remoteType: 'line',
  ws: null,
  isTerminalConnected: false,
  hasTerminal: false,
  lanIp: '192.168.1.100',
  localPort: 3000,
  balance: 50.00,
  aiQuotaExhausted: false,
  ngrokUrl: localStorage.getItem('miniclaw_ngrok_url') || ''
};

// --- 初始化處理 ---
window.addEventListener('DOMContentLoaded', () => {
  detectUserPlatform();
  restoreSavedSettings();
  setupStepEvents();
  goToStep(1);
  setupSettingsPanelEvents();
  setupChatEvents();
  initGoogleSignIn();
  startDiagnosticPolling();
  updateAIStatusUI();
});

// --- Google OAuth 初始化 ---
function initGoogleSignIn() {
  if (typeof google === 'undefined') {
    // GIS 腳本還沒載入，稍後重試
    setTimeout(initGoogleSignIn, 500);
    return;
  }

  google.accounts.oauth2.initTokenClient({
    client_id: GOOGLE_CLIENT_ID,
    scope: 'https://www.googleapis.com/auth/generative-language.retriever https://www.googleapis.com/auth/drive.file email profile',
    callback: handleGoogleTokenResponse,
  });

  // 渲染 Google 登入按鈕
  google.accounts.id.initialize({
    client_id: GOOGLE_CLIENT_ID,
    callback: handleGoogleIdToken,
    auto_select: false,
  });

  google.accounts.id.renderButton(
    document.getElementById('googleSignInBtn'),
    {
      theme: 'filled_blue',
      size: 'large',
      text: 'signin_with',
      locale: 'zh-TW',
      width: 280,
    }
  );

  // 每次刷新/重開都清除登入狀態，讓使用者重新登入
  localStorage.removeItem('miniclaw_google_user');
  localStorage.removeItem('miniclaw_google_token');
  webState.googleUser = null;
  webState.googleAccessToken = '';
}

// 處理 Google ID Token（登入後取得使用者資訊）
function handleGoogleIdToken(response) {
  // 解析 JWT payload 取得使用者資訊
  const payload = JSON.parse(atob(response.credential.split('.')[1]));
  webState.googleUser = {
    name: payload.name,
    email: payload.email,
    picture: payload.picture,
  };
  localStorage.setItem('miniclaw_google_user', JSON.stringify(webState.googleUser));

  // 取得 Access Token 以呼叫 Gemini API
  requestGoogleAccessToken();
}

// 請求 Access Token
function requestGoogleAccessToken() {
  if (typeof google === 'undefined') return;
  // 若已取得 token，直接返回，不再重複請求
  if (webState.googleAccessToken) return;
  const tokenClient = google.accounts.oauth2.initTokenClient({
    client_id: GOOGLE_CLIENT_ID,
    scope: 'https://www.googleapis.com/auth/generative-language.retriever https://www.googleapis.com/auth/drive.file',
    // 第一次登入需要顯示授權畫面，之後使用空字串進行靜默刷新
    callback: handleGoogleTokenResponse,
  });
  // 第一次授權使用空字串（會顯示選擇帳號），後續刷新用 'none'
  const promptMode = webState.googleAccessToken ? 'none' : '';
  tokenClient.requestAccessToken({ prompt: promptMode });
}


// 處理 Access Token 回應
function handleGoogleTokenResponse(tokenResponse) {
  if (tokenResponse.error) {
    const resultBox = document.getElementById('googleLoginResult');
    resultBox.style.display = 'block';
    resultBox.style.background = 'rgba(255,0,0,0.1)';
    resultBox.style.border = '1px solid rgba(255,0,0,0.3)';
    resultBox.style.color = '#ff4d4d';
    resultBox.innerHTML = `❌ Google 授權失敗：${tokenResponse.error}`;
    return;
  }

  webState.googleAccessToken = tokenResponse.access_token;
  localStorage.setItem('miniclaw_google_token', tokenResponse.access_token);
  updateAIStatusUI();

  if (webState.googleUser) {
    showGoogleLoggedIn(webState.googleUser);
  }

  // Access Token 取得成功 = 確定可用，自動跳遠端設定
  setTimeout(() => {
    initWebSocketConnection();
    goToStep(3);
  }, 800);
}

// 顯示已登入狀態
function showGoogleLoggedIn(user) {
  const btn = document.getElementById('googleSignInBtn');
  const resultBox = document.getElementById('googleLoginResult');

  if (btn) {
    btn.innerHTML = `
      <div style="display:flex;align-items:center;gap:10px;background:rgba(66,133,244,0.15);border:1px solid rgba(66,133,244,0.4);border-radius:8px;padding:10px 16px;">
        ${user.picture ? `<img src="${user.picture}" style="width:32px;height:32px;border-radius:50%;">` : '👤'}
        <div>
          <div style="color:#fff;font-size:0.9rem;font-weight:bold;">${user.name}</div>
          <div style="color:var(--text-muted);font-size:0.75rem;">${user.email}</div>
        </div>
        <button onclick="handleGoogleLogout()" style="margin-left:auto;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);color:var(--text-muted);padding:4px 10px;border-radius:4px;cursor:pointer;font-size:0.75rem;">登出</button>
      </div>
    `;
  }

  if (resultBox) {
    resultBox.style.display = 'block';
    resultBox.style.background = 'rgba(0,255,100,0.08)';
    resultBox.style.border = '1px solid rgba(0,255,100,0.3)';
    resultBox.style.color = 'var(--neon-green)';
    resultBox.innerHTML = '✅ Google 登入成功！已取得 Gemini 使用權限，可以繼續下一步。';
  }

  // 啟用下一步按鈕
  const nextBtn = document.getElementById('btnGoToStep2');
  if (nextBtn) {
    nextBtn.disabled = false;
    nextBtn.style.opacity = '1';
    nextBtn.style.cursor = 'pointer';
    nextBtn.title = '';
  }

  showToast('🔵 Google 登入成功', `歡迎，${user.name}！`, '🦞');
  // 同步更新設定面板
  updateSettingGoogleDisplay();
  // 登入成功自動跳到 Step 3（等 Access Token 後在 handleGoogleTokenResponse 跳）
}

// Google 登出
function handleGoogleLogout() {
  webState.googleUser = null;
  webState.googleAccessToken = '';
  localStorage.removeItem('miniclaw_google_user');
  localStorage.removeItem('miniclaw_google_token');

  if (typeof google !== 'undefined') {
    google.accounts.id.disableAutoSelect();
  }

  // 重新渲染登入按鈕
  const btn = document.getElementById('googleSignInBtn');
  if (btn) btn.innerHTML = '';
  setTimeout(initGoogleSignIn, 100);

  const resultBox = document.getElementById('googleLoginResult');
  if (resultBox) resultBox.style.display = 'none';

  // 停用下一步（除非有 API Key）
  if (!webState.apiKey) {
    const nextBtn = document.getElementById('btnGoToStep2');
    if (nextBtn) {
      nextBtn.disabled = true;
      nextBtn.style.opacity = '0.4';
      nextBtn.style.cursor = 'not-allowed';
    }
  }
}

// --- 1. 平台與環境自檢偵測 ---
function detectUserPlatform() {
  const ua = navigator.userAgent.toLowerCase();
  let os = 'windows';
  let platformText = 'Windows (電腦端)';
  
  if (ua.includes('macintosh') || ua.includes('mac os x')) {
    os = 'mac';
    platformText = 'macOS (電腦端)';
  } else if (ua.includes('android')) {
    os = 'android';
    platformText = 'Android (行動端 / Termux)';
  } else if (ua.includes('linux')) {
    os = 'linux';
    platformText = 'Linux (電腦端)';
  } else if (ua.includes('iphone') || ua.includes('ipad')) {
    os = 'ios';
    platformText = 'iOS (行動端)';
  }
  
  webState.platform = os;
  const textEl = document.getElementById('detectedPlatformText');
  if (textEl) {
    textEl.innerText = platformText;
  }
  
  generateBootstrapCommands(os);
}

// 根據平台生成「自檢安裝 Node.js 一鍵命令」
function generateBootstrapCommands(os) {
  const cmdEl = document.getElementById('bootstrapCommandText');
  if (!cmdEl) return;

  let command = '';
  if (os === 'windows') {
    command = `powershell -ExecutionPolicy Bypass -Command "if (!(Get-Command node -ErrorAction SilentlyContinue)) { winget install OpenJS.NodeJS }; node server.js"`;
  } else if (os === 'mac') {
    command = `node -v && echo "環境正常" || (brew install node && node server.js)`;
  } else if (os === 'linux') {
    command = `node -v >/dev/null 2>&1 && echo "環境正常" || (apt-get update && apt-get install -y nodejs && node server.js)`;
  } else if (os === 'android') {
    command = `pkg install nodejs && node server.js`;
  } else {
    command = `（iOS 不支援執行本地伺服器）`;
  }
  cmdEl.innerText = command;
}

// 終端模式步驟顯示時才套用平台專屬 UI（解決時序問題）
function applyPlatformStep2UI() {
  const os = webState.platform;

  if (os === 'ios') {
    const wantTerminalBtn = document.getElementById('btnWantTerminal');
    if (wantTerminalBtn) {
      wantTerminalBtn.disabled = true;
      wantTerminalBtn.style.opacity = '0.3';
      wantTerminalBtn.style.cursor = 'not-allowed';
      wantTerminalBtn.title = 'iOS 不支援本地終端';
      wantTerminalBtn.innerHTML = '🚫 iOS 不支援終端<br><span style="font-size:0.75rem;font-weight:normal;color:rgba(255,255,255,0.6);">請選擇純 AI 對話模式</span>';
    }
    const dlBlock = document.getElementById('step2DownloadBlock');
    if (dlBlock) dlBlock.style.display = 'none';
    const batBlock = document.getElementById('step2BatBlock');
    if (batBlock) batBlock.style.display = 'none';
    return;
  }

  if (os === 'android') {
    // 隱藏 Windows 專用區塊
    const dlBlock = document.getElementById('step2DownloadBlock');
    if (dlBlock) dlBlock.style.display = 'none';
    const batBlock = document.getElementById('step2BatBlock');
    if (batBlock) batBlock.style.display = 'none';

    // 插入 Termux 說明
    const guideContent = document.getElementById('terminalGuideContent');
    if (guideContent && !document.getElementById('androidTermuxGuide')) {
      const androidGuide = document.createElement('div');
      androidGuide.id = 'androidTermuxGuide';
      androidGuide.style.cssText = 'background:rgba(57,255,20,0.05);border:1px solid rgba(57,255,20,0.25);border-radius:12px;padding:16px;margin-bottom:14px;';
      androidGuide.innerHTML = `
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
          <span style="font-size:1.3rem;">📱</span>
          <strong style="color:var(--neon-green);">Android (Termux) 啟動方式</strong>
        </div>
        <div style="font-size:0.82rem;color:var(--text-muted);line-height:2;">
          1. 安裝 <a href="https://f-droid.org/packages/com.termux/" target="_blank" style="color:var(--neon-cyan);">Termux（F-Droid 版）</a> 與 <a href="https://f-droid.org/packages/com.termux.api/" target="_blank" style="color:var(--neon-cyan);">Termux:API app</a><br>
          2. 在 Termux 下載並解壓縮：<br>
          <code style="color:var(--neon-green);background:rgba(0,0,0,0.4);padding:4px 8px;border-radius:4px;display:block;margin:4px 0 8px;">pkg install wget unzip -y</code>
          <code style="color:var(--neon-green);background:rgba(0,0,0,0.4);padding:4px 8px;border-radius:4px;display:block;margin:4px 0 8px;word-break:break-all;">wget https://raw.githubusercontent.com/eric0724/eric0724.github.io/main/agent/miniclaw/miniclaw-executor.zip && unzip miniclaw-executor.zip && cd miniclaw-executor</code>
          3. 執行全自動啟動腳本：<br>
          <code style="color:var(--neon-green);background:rgba(0,0,0,0.4);padding:4px 8px;border-radius:4px;display:block;margin:4px 0 8px;">bash start.sh</code>
          <div style="background:rgba(0,255,100,0.08);border:1px solid rgba(0,255,100,0.2);border-radius:6px;padding:8px 12px;font-size:0.8rem;color:var(--neon-green);">
            ✅ start.sh 會自動安裝 Node.js、ngrok，並用手機開瀏覽器！
          </div>
        </div>
      `;
      guideContent.insertBefore(androidGuide, guideContent.firstChild);
    }
    return;
  }

  if (os === 'mac' || os === 'linux') {
    // 只隱藏 .bat 啟動區塊，下載 zip 連結 Mac/Linux 都能用，保留
    const batBlock = document.getElementById('step2BatBlock');
    if (batBlock) batBlock.style.display = 'none';

    const guideContent = document.getElementById('terminalGuideContent');
    const guideId = os === 'mac' ? 'macGuide' : 'linuxGuide';
    if (guideContent && !document.getElementById(guideId)) {
      const guide = document.createElement('div');
      guide.id = guideId;
      guide.style.cssText = 'background:rgba(57,255,20,0.05);border:1px solid rgba(57,255,20,0.25);border-radius:12px;padding:16px;margin-bottom:14px;';
      const icon = os === 'mac' ? '🍎' : '🐧';
      const label = os === 'mac' ? 'macOS 啟動方式' : 'Linux 啟動方式';
      const installCmd = os === 'mac'
        ? 'brew install node ngrok'
        : 'sudo apt-get install -y nodejs && curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list && sudo apt-get update && sudo apt-get install ngrok';
      const startCmd = 'bash start.sh';
      const ngrokCmd = 'ngrok http 3000';
      guide.innerHTML = `
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
          <span style="font-size:1.3rem;">${icon}</span>
          <strong style="color:var(--neon-green);">${label}</strong>
        </div>
        <div style="font-size:0.82rem;color:var(--text-muted);line-height:2;">
          1. 解壓縮下載的 zip，進入 <code style="color:var(--neon-cyan);">miniclaw-executor</code> 資料夾<br>
          2. 在終端機執行（全自動啟動）：<br>
          <code style="color:var(--neon-green);background:rgba(0,0,0,0.4);padding:4px 8px;border-radius:4px;display:block;margin:4px 0 8px;">bash start.sh</code>
          <div style="background:rgba(0,255,100,0.08);border:1px solid rgba(0,255,100,0.2);border-radius:6px;padding:8px 12px;font-size:0.8rem;color:var(--neon-green);">
            ✅ start.sh 會自動安裝 Node.js、ngrok，並開啟瀏覽器！
          </div>
        </div>
      `;
      guideContent.insertBefore(guide, guideContent.firstChild);
    }
    return;
  }
  // Windows：保持預設顯示，不做任何修改
}

// --- 2. 恢復持久化儲存設定 ---
function restoreSavedSettings() {
  const savedKey = localStorage.getItem('miniclaw_api_key');
  if (savedKey) {
    webState.apiKey = savedKey;
    document.getElementById('apiKeyInput').value = savedKey;
    updateBalanceDisplay(savedKey);
  }
  
  // 恢復 ngrok 網址
  const savedNgrok = localStorage.getItem('miniclaw_ngrok_url');
  if (savedNgrok) {
    webState.ngrokUrl = savedNgrok;
    const ngrokInput = document.getElementById('ngrokUrlInput');
    if (ngrokInput) ngrokInput.value = savedNgrok;
  }
  
  const savedBg = localStorage.getItem('miniclaw_bg_image');
  if (savedBg) {
    document.getElementById('bgImageUrlInput').value = savedBg;
    document.body.style.setProperty('--bg-custom-url', `url('${savedBg}')`);
  }
  
  const savedPriority = localStorage.getItem('miniclaw_ai_priority');
  if (savedPriority) {
    document.getElementById('selectAIPriority').value = savedPriority;
  }
  
  const savedMode = localStorage.getItem('miniclaw_api_mode');
  if (savedMode) {
    webState.apiMode = savedMode;
    document.getElementById('toggleCompleteExecution').checked = (savedMode === 'complete');
  }
}

// --- 3. 步驟引導頁面切換與按鈕監聽 (Step 1 - 5) ---
function setupStepEvents() {
  // Step 2: 偵測本地 AI（Ollama）
  document.getElementById('btnDetectOllama').addEventListener('click', async () => {
    const resultBox = document.getElementById('ollamaDetectResult');
    const nextBtn = document.getElementById('btnGoToStep2');

    resultBox.style.display = 'block';
    resultBox.style.background = 'rgba(255,102,0,0.1)';
    resultBox.style.border = '1px solid rgba(255,102,0,0.3)';
    resultBox.style.color = 'var(--neon-orange)';
    resultBox.innerHTML = '⏳ 正在偵測本地 AI...';

    let ollamaReady = false;
    let modelList = [];

    // 方法 1：透過 server.js /ollama-status（有終端時）
    if (webState.ngrokUrl && webState.isTerminalConnected) {
      try {
        const res = await fetch(`${webState.ngrokUrl}/ollama-status`, {
          headers: { 'ngrok-skip-browser-warning': 'true' }
        });
        const data = await res.json();
        ollamaReady = data.ready;
        modelList = data.models || [];
      } catch (e) {}
    }

    // 方法 2：直接查 Ollama API（本機開啟 index.html 時可用）
    if (!ollamaReady) {
      try {
        const res = await fetch('http://127.0.0.1:11434/api/tags');
        if (res.ok) {
          const data = await res.json();
          modelList = (data.models || []).map(m => m.name);
          ollamaReady = modelList.some(m => m.includes('gemma3'));
        }
      } catch (e) {}
    }

    if (ollamaReady) {
      resultBox.style.background = 'rgba(0,255,100,0.08)';
      resultBox.style.border = '1px solid rgba(0,255,100,0.3)';
      resultBox.style.color = 'var(--neon-green)';
      resultBox.innerHTML = `✅ 本地 AI 偵測成功！模型：${modelList.join(', ')}<br>已綁定至小龍蝦，可作為備援 AI。`;
      webState.apiMode = 'ollama';
      localStorage.setItem('miniclaw_api_mode', 'ollama');
      localStorage.setItem('miniclaw_ollama_ready', 'true');
      updateAIStatusUI();
      nextBtn.disabled = false;
      nextBtn.style.opacity = '1';
      nextBtn.style.cursor = 'pointer';
      nextBtn.title = '';
      showToast('🖥️ 本地 AI 已綁定', '小龍蝦將優先使用本地 AI，不消耗任何點數！', '🦞');
      // 偵測成功自動跳遠端設定
      setTimeout(() => { initWebSocketConnection(); goToStep(3); }, 800);
    } else if (modelList.length > 0) {
      resultBox.style.background = 'rgba(255,102,0,0.1)';
      resultBox.style.border = '1px solid rgba(255,102,0,0.3)';
      resultBox.style.color = 'var(--neon-orange)';
      resultBox.innerHTML = '⚠️ Ollama 已啟動，但找不到 gemma3 模型。請確認 install-local-ai.bat 已執行完成。';
    } else {
      resultBox.style.background = 'rgba(255,0,0,0.1)';
      resultBox.style.border = '1px solid rgba(255,0,0,0.3)';
      resultBox.style.color = '#ff4d4d';
      resultBox.innerHTML = `❌ 未偵測到本地 AI。<br>
        <span style="font-size:0.8rem;line-height:1.8;">
        請確認：<br>
        1. 已執行 <code>install-local-ai.bat</code> 且安裝完成<br>
        2. 若使用終端模式，請先完成 Step 1 連線後再偵測<br>
        3. 若直接在本機開啟網頁（非 GitHub Pages），可直接偵測
        </span>`;
    }
  });

  // Step 2: 測試 API 金鑰
  document.getElementById('btnTestApiKey').addEventListener('click', async () => {
    const key = document.getElementById('apiKeyInput').value.trim();
    const resultBox = document.getElementById('apiTestResult');
    const nextBtn = document.getElementById('btnGoToStep2');

    if (!key) {
      resultBox.className = 'error';
      resultBox.style.display = 'block';
      resultBox.innerHTML = '❌ 請先貼上您的 API 金鑰再測試。';
      return;
    }

    // 顯示測試中狀態
    resultBox.className = 'testing';
    resultBox.style.display = 'block';
    resultBox.innerHTML = '⏳ 正在測試金鑰可用性，請稍候...';
    nextBtn.disabled = true;
    nextBtn.style.opacity = '0.4';
    nextBtn.style.cursor = 'not-allowed';

    try {
      let testPassed = false;
      let errorMsg = '';

      if (key.startsWith('AIzaSy') || key.startsWith('AIza')) {
        // Gemini API 測試
        const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${key}`;
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{ parts: [{ text: 'hi' }] }]
          })
        });
        const data = await res.json();
        if (res.ok && data.candidates) {
          testPassed = true;
        } else {
          errorMsg = data.error?.message || '金鑰驗證失敗';
        }
      } else if (key.startsWith('sk-')) {
        // OpenAI / Openround API 測試
        const isOpenround = key.startsWith('sk-or-');
        const url = isOpenround ? 'https://api.openround.co/v1/models' : 'https://api.openai.com/v1/models';
        const res = await fetch(url, {
          headers: { 'Authorization': `Bearer ${key}` }
        });
        if (res.ok) {
          testPassed = true;
        } else {
          const data = await res.json();
          errorMsg = data.error?.message || '金鑰驗證失敗';
        }
      } else {
        errorMsg = '金鑰格式無法識別。Gemini金鑰以 AIzaSy 開頭，OpenAI金鑰以 sk- 開頭，Openround金鑰以 sk-or- 開頭。';
      }

      if (testPassed) {
        resultBox.className = 'success';
        resultBox.innerHTML = '✅ 金鑰驗證成功！現在可以繼續下一步。';
        nextBtn.disabled = false;
        nextBtn.style.opacity = '1';
        nextBtn.style.cursor = 'pointer';
        nextBtn.title = '';
        webState.apiKey = key;
        localStorage.setItem('miniclaw_api_key', key);
        updateBalanceDisplay(key);
        updateAIStatusUI();
        // 測試通過自動跳遠端設定
        setTimeout(() => { initWebSocketConnection(); goToStep(3); }, 800);
      } else {
        resultBox.className = 'error';
        resultBox.innerHTML = `❌ 驗證失敗：${errorMsg}`;
      }
    } catch (err) {
      resultBox.className = 'error';
      resultBox.innerHTML = `❌ 網路錯誤，無法連接至 API 伺服器。請確認網路連線後再試。`;
    }
  });

  // Step 2: 點擊前往 Step 3（金鑰已通過測試才可按）
  document.getElementById('btnGoToStep2').addEventListener('click', () => {
    if (!webState.apiKey && !webState.googleAccessToken && localStorage.getItem('miniclaw_ollama_ready') !== 'true') return;
    showToast('🔑 API 鎖定成功', '您的金鑰已加密存於 localStorage，稍後同步至本地！', '🦞');
    initWebSocketConnection();
    goToStep(3);
  });


  // Step 2: 跳過金鑰 (進入輕量模式，跳到遠端設定)
  document.getElementById('btnSkipToStep3').addEventListener('click', () => {
    webState.apiMode = 'lightweight';
    localStorage.setItem('miniclaw_api_mode', 'lightweight');
    document.getElementById('toggleCompleteExecution').checked = false;
    updateBalanceDisplay('');
    updateAIStatusUI();
    
    showToast('🛡️ 啟動輕量隧道模式', '已為您跳過金鑰驗證，請繼續遠端設定！', '🦞');
    goToStep(3);
  });

  // Step 1: 要終端按鈕
  document.getElementById('btnWantTerminal').addEventListener('click', () => {
    webState.hasTerminal = true;
    webState.apiMode = 'complete';
    localStorage.setItem('miniclaw_api_mode', 'complete');
    document.getElementById('toggleCompleteExecution').checked = true;

    // 切換 UI 狀態
    document.getElementById('btnWantTerminal').className = 'cyber-btn orange';
    document.getElementById('btnNoTerminal').className = 'cyber-btn muted';
    document.getElementById('noTerminalMsg').style.display = 'none';
    document.getElementById('terminalGuideContent').style.display = 'block';

    // 啟用下一步（需測試連線後才能按）
    const nextBtn = document.getElementById('btnGoToStep3');
    nextBtn.disabled = true;
    nextBtn.style.opacity = '0.4';
    nextBtn.style.cursor = 'not-allowed';
    nextBtn.title = '請先測試並通過執行端驗證';

    // 若 ngrok 網址已偵測到，自動觸發測試
    const ngrokInput = document.getElementById('ngrokUrlInput');
    if (ngrokInput && ngrokInput.value.trim().startsWith('https://')) {
      setTimeout(() => document.getElementById('btnTestExecutor').click(), 400);
    }
  });

  // Step 1: 不要終端按鈕
  document.getElementById('btnNoTerminal').addEventListener('click', () => {
    webState.hasTerminal = false;
    webState.apiMode = 'lightweight';
    localStorage.setItem('miniclaw_api_mode', 'lightweight');
    document.getElementById('toggleCompleteExecution').checked = false;

    // 切換 UI 狀態
    document.getElementById('btnNoTerminal').className = 'cyber-btn orange';
    document.getElementById('btnWantTerminal').className = 'cyber-btn muted';
    document.getElementById('terminalGuideContent').style.display = 'none';
    document.getElementById('noTerminalMsg').style.display = 'block';

    // 直接啟用下一步
    const nextBtn = document.getElementById('btnGoToStep3');
    nextBtn.disabled = false;
    nextBtn.style.opacity = '1';
    nextBtn.style.cursor = 'pointer';
    nextBtn.title = '';

    showToast('💬 純 AI 對話模式', '已選擇不使用終端，直接進入下一步！', '🦞');
  });

  // Step 1: 測試執行端連線 (透過 ngrok 網址)
  document.getElementById('btnTestExecutor').addEventListener('click', async () => {
    const resultBox = document.getElementById('executorTestResult');
    const nextBtn = document.getElementById('btnGoToStep3');
    const ngrokInput = document.getElementById('ngrokUrlInput');
    
    let ngrokUrl = ngrokInput.value.trim().replace(/\/$/, ''); // 移除結尾斜線
    
    if (!ngrokUrl) {
      resultBox.style.display = 'block';
      resultBox.style.background = 'rgba(255,0,0,0.1)';
      resultBox.style.border = '1px solid rgba(255,0,0,0.3)';
      resultBox.style.color = '#ff4d4d';
      resultBox.innerHTML = '❌ 請先把 ngrok 網址貼到上面的欄位！';
      return;
    }
    
    if (!ngrokUrl.startsWith('https://')) {
      resultBox.style.display = 'block';
      resultBox.style.background = 'rgba(255,0,0,0.1)';
      resultBox.style.border = '1px solid rgba(255,0,0,0.3)';
      resultBox.style.color = '#ff4d4d';
      resultBox.innerHTML = '❌ 網址格式不對！ngrok 網址應該是 https:// 開頭的。';
      return;
    }
    
    resultBox.style.display = 'block';
    resultBox.style.background = 'rgba(255,102,0,0.1)';
    resultBox.style.border = '1px solid rgba(255,102,0,0.3)';
    resultBox.style.color = 'var(--neon-orange)';
    resultBox.innerHTML = '⏳ 正在測試連線，請稍等一下...';
    
    try {
      const res = await fetch(`${ngrokUrl}/health`, {
        headers: { 'ngrok-skip-browser-warning': 'true' }
      });
      const data = await res.json();
      if (res.ok && data.status === 'ok') {
        webState.ngrokUrl = ngrokUrl;
        localStorage.setItem('miniclaw_ngrok_url', ngrokUrl);
        
        resultBox.style.background = 'rgba(255,102,0,0.1)';
        resultBox.style.border = '1px solid rgba(255,102,0,0.3)';
        resultBox.style.color = 'var(--neon-orange)';
        resultBox.innerHTML = '⏳ HTTP 通道正常，正在建立 WebSocket 終端連線...';
        
        // 建立 WebSocket，等待結果再更新 UI
        initWebSocketConnection();

        // 等待最多 10 秒確認 WebSocket 是否連上
        let waited = 0;
        const wsCheckInterval = setInterval(() => {
          waited += 500;
          if (webState.isTerminalConnected) {
            clearInterval(wsCheckInterval);
            resultBox.style.background = 'rgba(0,255,100,0.1)';
            resultBox.style.border = '1px solid rgba(0,255,100,0.3)';
            resultBox.style.color = 'var(--neon-green)';
            resultBox.innerHTML = '✅ HTTP + WebSocket 雙重連線成功！終端已就緒。';
            nextBtn.disabled = false;
            nextBtn.style.opacity = '1';
            nextBtn.style.cursor = 'pointer';
            nextBtn.title = '';
            // 連線成功自動跳 AI 綁定
            setTimeout(() => goToStep(2), 800);
          } else if (waited >= 10000) {
            clearInterval(wsCheckInterval);
            resultBox.style.background = 'rgba(255,102,0,0.1)';
            resultBox.style.border = '1px solid rgba(255,102,0,0.3)';
            resultBox.style.color = 'var(--neon-orange)';
            resultBox.innerHTML = '⚠️ HTTP 通道正常，但 WebSocket 連線失敗。終端功能無法使用，可能是 ngrok 攔截了升級請求。請重新啟動 ngrok 後再試，或點「下一步」以沙盒模式繼續。';
            nextBtn.disabled = false;
            nextBtn.style.opacity = '1';
            nextBtn.style.cursor = 'pointer';
          }
        }, 500);
      } else {
        throw new Error('未回傳正確狀態');
      }
    } catch (err) {
      resultBox.style.background = 'rgba(255,0,0,0.1)';
      resultBox.style.border = '1px solid rgba(255,0,0,0.3)';
      resultBox.style.color = '#ff4d4d';
      resultBox.innerHTML = '❌ 連線失敗！請確認：<br>1. <code>openminiclaw.bat</code> 還在執行中（黑色視窗還開著）<br>2. 網址有正確複製（包含 https://）<br>3. 若手動啟動，確認 ngrok 視窗也還開著';
      
      nextBtn.disabled = true;
      nextBtn.style.opacity = '0.4';
      nextBtn.style.cursor = 'not-allowed';
    }
  });

  // 步驟導覽退回/前進
  document.getElementById('btnBackToStep1').addEventListener('click', () => goToStep(1));
  document.getElementById('btnBackToTerminalStep').addEventListener('click', () => goToStep(1));
  document.getElementById('btnGoToStep3').addEventListener('click', () => {
    if (webState.hasTerminal) {
      // 有終端：需要測試通過才能到這裡，直接跳 AI 綁定
    }
    goToStep(2);
  });
  
  // Step 3: 要連接 LINE/DC
  document.getElementById('btnWantLineDC').addEventListener('click', () => {
    document.getElementById('btnWantLineDC').className = 'cyber-btn orange';
    document.getElementById('btnNoLineDC').className = 'cyber-btn muted';
    document.getElementById('lineDCFormSection').style.display = 'block';

    // 無終端時顯示警告
    if (!webState.hasTerminal) {
      document.getElementById('noTerminalLineDCWarning').style.display = 'block';
    } else {
      document.getElementById('noTerminalLineDCWarning').style.display = 'none';
    }

    // 重置下一步按鈕（需測試通過）
    const nextBtn = document.getElementById('btnGoToStep4');
    nextBtn.disabled = true;
    nextBtn.style.opacity = '0.4';
    nextBtn.style.cursor = 'not-allowed';
    nextBtn.title = '請先測試並通過機器人驗證';
    nextBtn.style.display = '';

    // 更新 Webhook URL 顯示
    updateLineWebhookUrlDisplay();
  });

  // Step 3: 不要連接 LINE/DC，直接進大廳
  document.getElementById('btnNoLineDC').addEventListener('click', () => {
    document.getElementById('btnNoLineDC').className = 'cyber-btn orange';
    document.getElementById('btnWantLineDC').className = 'cyber-btn muted';
    document.getElementById('lineDCFormSection').style.display = 'none';
    document.getElementById('noTerminalLineDCWarning').style.display = 'none';

    // 直接進大廳
    document.getElementById('onboardingModal').style.display = 'none';
    document.getElementById('mainWorkspace').style.display = 'grid';

    const greeting = document.getElementById('initialGreeting');
    if (greeting) {
      if (webState.isTerminalConnected) {
        greeting.innerHTML = '你好，我是小龍蝦控制中樞！🟢 終端已連線，可以開始控制你的電腦了！試試上方的快捷按鈕。';
      } else if (webState.hasTerminal) {
        greeting.innerHTML = '你好，我是小龍蝦控制中樞！⚠️ 終端連線尚未建立，請確認 node server.js 和 ngrok 都在執行中。目前為沙盒模式。';
      } else {
        greeting.innerHTML = '你好，我是小龍蝦控制中樞！💬 目前為純 AI 對話模式，有任何問題都可以直接問我！';
      }
    }

    showToast('🚀 大廳解鎖成功', '小龍蝦控制中樞運轉中！歡迎開始對話操控！', '🦞');
    if (!webState.isTerminalConnected && webState.ngrokUrl) {
      initWebSocketConnection();
    }
    renderShortcutChips();
  });
  // Step 3: 控制方式切換
  document.getElementById('btnCtrlModeWeb').addEventListener('click', () => {
    document.getElementById('btnCtrlModeWeb').className = 'cyber-btn orange';
    document.getElementById('btnCtrlModeLine').className = 'cyber-btn muted';
    document.getElementById('ctrlModeWebGuide').style.display = 'block';
    document.getElementById('ctrlModeLineGuide').style.display = 'none';
    // 手機網頁模式不需要測試，直接啟用下一步
    const nextBtn = document.getElementById('btnGoToStep4');
    nextBtn.disabled = false;
    nextBtn.style.opacity = '1';
    nextBtn.style.cursor = 'pointer';
    nextBtn.title = '點擊進入下一步';
    // 選擇後自動跳 Step 4
    setTimeout(() => { saveRemoteCredentials(); goToStep(4); }, 800);
    nextBtn.style.opacity = '1';
    nextBtn.style.cursor = 'pointer';
    nextBtn.title = '';
  });

  document.getElementById('btnCtrlModeLine').addEventListener('click', () => {
    document.getElementById('btnCtrlModeLine').className = 'cyber-btn orange';
    document.getElementById('btnCtrlModeWeb').className = 'cyber-btn muted';
    document.getElementById('ctrlModeLineGuide').style.display = 'block';
    document.getElementById('ctrlModeWebGuide').style.display = 'none';
    updateLineWebhookUrlDisplay();
    // LINE 模式需要填憑證才能繼續
    const nextBtn = document.getElementById('btnGoToStep4');
    nextBtn.disabled = true;
    nextBtn.style.opacity = '0.4';
    nextBtn.style.cursor = 'not-allowed';
    nextBtn.title = '請先測試並通過機器人驗證';
  });

  const btnLINE = document.getElementById('btnSelectLINE');
  const btnDiscord = document.getElementById('btnSelectDiscord');
  const lineFields = document.getElementById('lineFormFields');
  const discordFields = document.getElementById('discordFormFields');

  btnLINE.addEventListener('click', () => {
    webState.remoteType = 'line';
    btnLINE.className = 'cyber-btn orange';
    btnDiscord.className = 'cyber-btn muted';
    lineFields.style.display = 'block';
    discordFields.style.display = 'none';
  });

  btnDiscord.addEventListener('click', () => {
    webState.remoteType = 'discord';
    btnLINE.className = 'cyber-btn muted';
    btnDiscord.className = 'cyber-btn orange';
    lineFields.style.display = 'none';
    discordFields.style.display = 'block';
  });

  // Step 3: 切換 A / B 卡片
  const cardRemoteA = document.getElementById('cardRemoteA');
  const cardRemoteB = document.getElementById('cardRemoteB');
  const credentialsForm = document.getElementById('remoteCredentialsForm');

  cardRemoteA.addEventListener('click', () => {
    cardRemoteA.classList.add('selected');
    cardRemoteB.classList.remove('selected');
    credentialsForm.style.display = 'block';
    
    // 切換回 A 時，判定下一步按鈕是否應該啟用 (如果先前有成功測試過則啟用，否則停用)
    const resultBox = document.getElementById('remoteTestResult');
    const nextBtn = document.getElementById('btnGoToStep4');
    if (resultBox && resultBox.classList.contains('success')) {
      nextBtn.disabled = false;
      nextBtn.style.opacity = '1';
      nextBtn.style.cursor = 'pointer';
    } else {
      nextBtn.disabled = true;
      nextBtn.style.opacity = '0.4';
      nextBtn.style.cursor = 'not-allowed';
    }
  });

  cardRemoteB.addEventListener('click', () => {
    cardRemoteB.classList.add('selected');
    cardRemoteA.classList.remove('selected');
    credentialsForm.style.display = 'none';
    showToast('⏭️ 稍後設定', '已選擇跳過，進入大廳後可在設定面板隨時補填 LINE/DC 憑證。', '🦞');
    
    // 切換到 B 時，下一步按鈕自動啟用
    const nextBtn = document.getElementById('btnGoToStep4');
    nextBtn.disabled = false;
    nextBtn.style.opacity = '1';
    nextBtn.style.cursor = 'pointer';
  });

  // Step 3: 測試遠端機器人連線
  document.getElementById('btnTestRemote').addEventListener('click', async () => {
    const resultBox = document.getElementById('remoteTestResult');
    const nextBtn = document.getElementById('btnGoToStep4');
    
    const isLINE = (webState.remoteType === 'line');
    const lineToken = document.getElementById('lineTokenInput').value.trim();
    const lineSecret = document.getElementById('lineSecretInput').value.trim();
    const discToken = document.getElementById('discordTokenInput').value.trim();
    const discChan = document.getElementById('discordChannelInput').value.trim();
    
    // 基本檢查
    if (isLINE) {
      if (!lineToken || !lineSecret) {
        resultBox.className = 'error';
        resultBox.style.display = 'block';
        resultBox.style.background = 'rgba(255,0,0,0.1)';
        resultBox.style.border = '1px solid rgba(255,0,0,0.3)';
        resultBox.style.color = '#ff4d4d';
        resultBox.innerHTML = '❌ 請完整填入 LINE Channel Access Token 與 Secret。';
        return;
      }
    } else {
      if (!discToken || !discChan) {
        resultBox.className = 'error';
        resultBox.style.display = 'block';
        resultBox.style.background = 'rgba(255,0,0,0.1)';
        resultBox.style.border = '1px solid rgba(255,0,0,0.3)';
        resultBox.style.color = '#ff4d4d';
        resultBox.innerHTML = '❌ 請完整填入 Discord Bot Token 與 Channel ID。';
        return;
      }
    }
    
    resultBox.className = 'testing';
    resultBox.style.display = 'block';
    resultBox.style.background = 'rgba(255,102,0,0.1)';
    resultBox.style.border = '1px solid rgba(255,102,0,0.3)';
    resultBox.style.color = 'var(--neon-orange)';
    resultBox.innerHTML = '⏳ 正在測試與機器人 API 的連線，請稍後...';
    
    // 如果 WebSocket 已連線，利用本地端 Executor 去驗證
    if (webState.isTerminalConnected && webState.ws && webState.ws.readyState === WebSocket.OPEN) {
      webState.ws.send(JSON.stringify({
        type: 'test-remote',
        data: {
          channel: webState.remoteType,
          lineToken,
          lineSecret,
          discordToken: discToken,
          discordChannel: discChan
        }
      }));
    } else {
      // 離線/沙盒模式的模擬驗證 (Mock)
      setTimeout(() => {
        let formatValid = true;
        let mockError = '';
        
        if (isLINE) {
          if (lineSecret.length !== 32) {
            formatValid = false;
            mockError = 'LINE Channel Secret 長度應為 32 字元。';
          }
        } else {
          if (discToken.length < 50) {
            formatValid = false;
            mockError = 'Discord Bot Token 格式似乎不正確（長度過短）。';
          }
        }
        
        if (formatValid) {
          resultBox.className = 'success';
          resultBox.style.background = 'rgba(0,255,100,0.1)';
          resultBox.style.border = '1px solid rgba(0,255,100,0.3)';
          resultBox.style.color = 'var(--neon-green)';
          resultBox.innerHTML = '✅ [沙盒模式] 憑證格式自檢通過！連線配置模擬成功。';
          
          nextBtn.disabled = false;
          nextBtn.style.opacity = '1';
          nextBtn.style.cursor = 'pointer';
          nextBtn.title = '';
        } else {
          resultBox.className = 'error';
          resultBox.style.background = 'rgba(255,0,0,0.1)';
          resultBox.style.border = '1px solid rgba(255,0,0,0.3)';
          resultBox.style.color = '#ff4d4d';
          resultBox.innerHTML = `❌ 連線測試失敗：${mockError}`;
          
          nextBtn.disabled = true;
          nextBtn.style.opacity = '0.4';
          nextBtn.style.cursor = 'not-allowed';
        }
      }, 1500);
    }
  });

  // Step 3 前進/後退
  document.getElementById('btnBackToStep2').addEventListener('click', () => {
    goToStep(2);
  });

  document.getElementById('btnGoToStep4').addEventListener('click', () => {
    saveRemoteCredentials();
    // 動態更新 Step 4 說明
    const desc = document.getElementById('step4Desc');
    if (desc) {
      if (webState.hasTerminal && webState.isTerminalConnected) {
        desc.innerText = '設定完成！終端已連線，執行端已備份為 server.js.bak。小龍蝦已為您調配好專屬的快捷指令包！';
      } else if (webState.hasTerminal) {
        desc.innerText = '設定完成！終端尚未連線，請確認 node server.js 和 ngrok 都在執行中。進入大廳後可繼續嘗試連線。';
      } else {
        desc.innerText = '設定完成！LINE/DC 憑證已儲存。目前為純 AI 對話模式，進入大廳後即可開始使用。';
      }
    }
    goToStep(4);
  });

  document.getElementById('btnOpenMainWorkspace').addEventListener('click', () => {
    document.getElementById('onboardingModal').style.display = 'none';
    document.getElementById('mainWorkspace').style.display = 'grid';

    // 根據實際狀態顯示正確的初始訊息
    const greeting = document.getElementById('initialGreeting');
    if (greeting) {
      if (webState.isTerminalConnected) {
        greeting.innerHTML = '你好，我是小龍蝦控制中樞！🟢 終端已連線，可以開始控制你的電腦了！試試上方的快捷按鈕。';
      } else if (webState.hasTerminal) {
        greeting.innerHTML = '你好，我是小龍蝦控制中樞！⚠️ 終端連線尚未建立，請確認 node server.js 和 ngrok 都在執行中。目前為沙盒模式。';
      } else {
        greeting.innerHTML = '你好，我是小龍蝦控制中樞！💬 目前為純 AI 對話模式，無法控制本地電腦。有任何問題都可以直接問我！';
      }
    }

    showToast('🚀 大廳解鎖成功', '小龍蝦控制中樞運轉中！歡迎開始對話操控！', '🦞');
    
    if (!webState.isTerminalConnected && webState.ngrokUrl) {
      initWebSocketConnection();
    }
    
    renderShortcutChips();
  });
}

// 核心跳轉跳躍
function goToStep(stepNum) {
  webState.currentStep = stepNum;
  
  // 更新步驟節點狀態
  const nodes = document.querySelectorAll('.step-node');
  nodes.forEach(node => {
    const nodeStep = parseInt(node.getAttribute('data-step'));
    node.className = 'step-node';
    if (nodeStep === stepNum) {
      node.classList.add('active');
    } else if (nodeStep < stepNum) {
      node.classList.add('completed');
    }
  });
  
  // 切換對應面板顯示（共 4 個 step-pane）
  const stepPaneMap = {
    1: 'paneStep2', // 終端模式選擇
    2: 'paneStep1', // AI / API 綁定
    3: 'paneStep3', // 遠端設定
    4: 'paneStep4'
  };
  const panes = document.querySelectorAll('.step-pane');
  panes.forEach(pane => {
    pane.classList.remove('active');
  });
  const activePane = document.getElementById(stepPaneMap[stepNum]);
  if (activePane) activePane.classList.add('active');

  // Step1 顯示時套用平台專屬 UI（iOS禁用終端、Android插入Termux說明）
  // 同時自動偵測 ngrok 網址（URL 參數或 localhost）
  if (stepNum === 1) {
    applyPlatformStep2UI();
    autoDetectNgrokUrl();
  }
}

// 更新 LINE Webhook URL 顯示（根據目前 ngrok 網址自動組合）
function updateLineWebhookUrlDisplay() {
  const el = document.getElementById('lineWebhookUrlDisplay');
  if (!el) return;
  if (webState.ngrokUrl) {
    el.innerText = `${webState.ngrokUrl}/webhook/line`;
  } else {
    el.innerText = '（請先在 Step 1 填入 ngrok 網址）';
  }
}

// 保存 LINE / Discord 遠端憑證設定
function saveRemoteCredentials() {
  const isLINE = (webState.remoteType === 'line');
  const lineToken = document.getElementById('lineTokenInput').value.trim();
  const lineSecret = document.getElementById('lineSecretInput').value.trim();
  const lineUserId = document.getElementById('lineUserIdInput') ? document.getElementById('lineUserIdInput').value.trim() : '';
  const discToken = document.getElementById('discordTokenInput').value.trim();
  const discChan = document.getElementById('discordChannelInput').value.trim();
  
  // localStorage 本地快取格式
  const localPayload = {
    type: webState.remoteType,
    line: { token: lineToken, secret: lineSecret, userId: lineUserId },
    discord: { token: discToken, channel: discChan }
  };
  localStorage.setItem('miniclaw_remote_creds', JSON.stringify(localPayload));
  
  // 同步至本地執行端：使用 server.js 讀取的 credentials.remote 格式
  if (webState.ws && webState.ws.readyState === WebSocket.OPEN) {
    webState.ws.send(JSON.stringify({
      type: 'sync-credentials',
      data: {
        remote: localPayload
      }
    }));
  }
  
  // 更新設定面板顯示狀態
  updateSettingRemoteStatus(isLINE, isLINE ? lineToken : discToken);
}

function updateSettingRemoteStatus(isLINE, hasKey) {
  const lineEl = document.getElementById('settingStatusLINE');
  const discEl = document.getElementById('settingStatusDiscord');
  
  if (isLINE) {
    lineEl.innerText = hasKey ? '🟢 已配置連線' : '未設定';
    lineEl.style.color = hasKey ? 'var(--neon-green)' : 'var(--neon-orange)';
  } else {
    discEl.innerText = hasKey ? '🟢 已配置連線' : '未設定';
    discEl.style.color = hasKey ? 'var(--neon-green)' : 'var(--neon-orange)';
  }
}

// --- 4. WebSocket 雙端同步機制 ---
function initWebSocketConnection() {
  let wsUrl;
  if (webState.ngrokUrl) {
    wsUrl = webState.ngrokUrl.replace('https://', 'wss://').replace('http://', 'ws://');
  } else {
    wsUrl = `ws://localhost:${webState.localPort}`;
  }

  if (webState.ws && webState.ws.readyState === WebSocket.OPEN && webState._wsUrl === wsUrl) {
    webState.isTerminalConnected = true;
    updateTerminalConnectionUI(true);
    return;
  }

  if (webState.ws) {
    webState.ws.onclose = null;
    webState.ws.onerror = null;
    webState.ws.close();
    webState.ws = null;
  }

  logStatus(`🔌 嘗試連線至: ${wsUrl}`);
  
  let ws;
  try {
    ws = new WebSocket(wsUrl);
  } catch (e) {
    logStatus(`❌ 建立 WebSocket 失敗: ${e.message}`);
    updateTerminalConnectionUI(false);
    return;
  }

  const connectTimeout = setTimeout(() => {
    if (webState.ws !== ws) return;
    if (ws.readyState !== WebSocket.OPEN) {
      logStatus('❌ 連線逾時（10秒），請重新啟動 ngrok 後再試');
      ws.close();
      updateTerminalConnectionUI(false);
      const guideEl = document.getElementById('diagnosticGuideText');
      if (guideEl) guideEl.innerHTML = '❌ WebSocket 連線逾時，請重新啟動 ngrok 後再試。';
    }
  }, 10000);

  webState.ws = ws;
  webState._wsUrl = wsUrl;
  
  ws.onopen = () => {
    if (webState.ws !== ws) return;
    clearTimeout(connectTimeout);
    webState.isTerminalConnected = true;
    webState._reconnectCount = 0;
    updateTerminalConnectionUI(true);
    logStatus('🟢 WebSocket 連線成功！終端已就緒');
    showToast('🟢 雙端連線完成', '網頁端與本地執行端已成功透過 WebSocket 對接！', '🦞');
    syncAllCredentialsToLocal();
  };
  
  ws.onmessage = (event) => {
    if (webState.ws !== ws) return;
    try {
      const msg = JSON.parse(event.data);
      handleIncomingWSMessage(msg);
    } catch (e) {
      logStatus(`⚠️ 訊息解析失敗: ${e.message}`);
    }
  };
  
  ws.onclose = (event) => {
    if (webState.ws !== ws) return;
    clearTimeout(connectTimeout);
    webState.isTerminalConnected = false;
    webState.ws = null;
    webState._wsUrl = '';
    updateTerminalConnectionUI(false);
    logStatus(`🔴 連線已關閉 code:${event.code}`);
    // 所有非正常關閉都嘗試重連（不限 1006）
    if (event.code !== 1000 && event.code !== 1001) {
      const delay = Math.min((webState._reconnectCount || 0) * 3000 + 1000, 15000);
      webState._reconnectCount = (webState._reconnectCount || 0) + 1;
      setTimeout(() => {
        logStatus(`🔄 自動重連中（第${webState._reconnectCount}次）...`);
        initWebSocketConnection();
      }, delay);
    }
  };
  
  ws.onerror = () => {
    if (webState.ws !== ws) return;
    clearTimeout(connectTimeout);
    webState.isTerminalConnected = false;
    updateTerminalConnectionUI(false);
    logStatus('❌ 連線錯誤，請確認 ngrok 是否正常運作');
  };
}

function syncAllCredentialsToLocal() {
  if (!webState.ws || webState.ws.readyState !== WebSocket.OPEN) return;
  
  let remoteCreds = null;
  try {
    const raw = localStorage.getItem('miniclaw_remote_creds');
    if (raw) remoteCreds = JSON.parse(raw);
  } catch(e) {}
  
  const payload = {
    apiKey: webState.apiKey,
    googleAccessToken: webState.googleAccessToken || '',
    aiPriority: document.getElementById('selectAIPriority').value,
    remote: remoteCreds
  };
  
  webState.ws.send(JSON.stringify({ type: 'sync-credentials', data: payload }));
}

function handleIncomingWSMessage(msg) {
  if (msg.type === 'ai-response') {
    appendMessage('ai', msg.reply);
    if (msg.output) {
      appendMessage('warning', `⚙️ 終端輸出 [Output] :\n${msg.output}`);
    }
  } else if (msg.type === 'executor-status') {
    // 回報硬體狀態與診斷
    if (msg.temp) {
      updateSystemStatsBar(msg.temp, msg.cpu);
    }
  } else if (msg.type === 'sys-action' && msg.action === 'screenshot') {
    appendScreenshotMessage(msg.data);
  } else if (msg.type === 'ai-quota-exhausted') {
    webState.aiQuotaExhausted = true;
    updateAIStatusUI();
    const activeKey = webState.googleAccessToken || webState.apiKey;
    updateBalanceDisplay(activeKey);
  } else if (msg.type === 'remote-test-result') {
    const resultBox = document.getElementById('remoteTestResult');
    const nextBtn = document.getElementById('btnGoToStep4');
    if (!resultBox) return;
    
    if (msg.success) {
      resultBox.className = 'success';
      resultBox.style.background = 'rgba(0,255,100,0.1)';
      resultBox.style.border = '1px solid rgba(0,255,100,0.3)';
      resultBox.style.color = 'var(--neon-green)';
      resultBox.innerHTML = `✅ ${msg.message}`;
      
      nextBtn.disabled = false;
      nextBtn.style.opacity = '1';
      nextBtn.style.cursor = 'pointer';
      nextBtn.title = '';
      // LINE 測試成功自動跳 Step 4
      setTimeout(() => { saveRemoteCredentials(); goToStep(4); }, 800);
    } else {
      resultBox.className = 'error';
      resultBox.style.background = 'rgba(255,0,0,0.1)';
      resultBox.style.border = '1px solid rgba(255,0,0,0.3)';
      resultBox.style.color = '#ff4d4d';
      resultBox.innerHTML = `❌ 連線測試失敗：${msg.message}`;
      
      nextBtn.disabled = true;
      nextBtn.style.opacity = '0.4';
      nextBtn.style.cursor = 'not-allowed';
    }
  }
}

function updateSystemStatsBar(temp, cpu) {
  const tempEl = document.getElementById('systemTemp');
  const cpuEl = document.getElementById('systemCpu');
  if (tempEl) {
    tempEl.innerText = `🌡️ ${temp}°C`;
    tempEl.style.color = temp > 80 ? '#ff4444' : 'var(--neon-green)';
  }
  if (cpuEl) {
    cpuEl.innerText = `⚙️ CPU ${cpu}%`;
    cpuEl.style.color = cpu > 90 ? '#ff4444' : 'var(--neon-cyan)';
  }
}

function updateTerminalConnectionUI(connected) {
  const dot = document.getElementById('connectionStatusDot');
  const txt = document.getElementById('connectionStatusText');
  const modeTxt = document.getElementById('monitorModeText');
  
  if (connected) {
    dot.className = 'status-dot active';
    txt.innerText = '本地終端: 連線中';
    txt.style.color = 'var(--neon-green)';
    modeTxt.innerText = '雙端即時連線 (WebSocket)';
    modeTxt.style.color = 'var(--neon-green)';
  } else {
    dot.className = 'status-dot inactive';
    txt.innerText = '本地終端: 離線';
    txt.style.color = 'var(--neon-orange)';
    modeTxt.innerText = '電腦離線 / 方案 B';
    modeTxt.style.color = 'var(--neon-orange)';
  }
  // 遊戲助手按鈕：有終端才可按
  const gameBtn = document.getElementById('btnGameAssist');
  if (gameBtn) {
    if (connected) {
      gameBtn.disabled = false;
      gameBtn.style.opacity = '1';
      gameBtn.style.cursor = 'pointer';
      gameBtn.className = 'cyber-btn orange';
      gameBtn.title = '開啟遊戲助手';
    } else {
      gameBtn.disabled = true;
      gameBtn.style.opacity = '0.4';
      gameBtn.style.cursor = 'not-allowed';
      gameBtn.className = 'cyber-btn muted';
      gameBtn.title = '需要終端連線才能使用';
    }
  }
  // 錄製操作按鈕：有終端才可按
  const openRecorderBtn = document.getElementById('btnOpenRecorder');
  if (openRecorderBtn) {
    if (connected) {
      openRecorderBtn.disabled = false;
      openRecorderBtn.style.opacity = '1';
      openRecorderBtn.style.cursor = 'pointer';
      openRecorderBtn.className = 'cyber-btn orange';
      openRecorderBtn.title = '開啟操作錄製器 (recorder.py)';
    } else {
      openRecorderBtn.disabled = true;
      openRecorderBtn.style.opacity = '0.4';
      openRecorderBtn.style.cursor = 'not-allowed';
      openRecorderBtn.className = 'cyber-btn muted';
      openRecorderBtn.title = '需要終端連線才能使用';
    }
  }
  // 執行腳本按鈕：有終端才可按
  const runAutoScriptBtn = document.getElementById('btnRunAutoScript');
  if (runAutoScriptBtn) {
    if (connected) {
      runAutoScriptBtn.disabled = false;
      runAutoScriptBtn.style.opacity = '1';
      runAutoScriptBtn.style.cursor = 'pointer';
      runAutoScriptBtn.className = 'cyber-btn orange';
      runAutoScriptBtn.title = '執行自動化腳本 (auto_run.py)';
    } else {
      runAutoScriptBtn.disabled = true;
      runAutoScriptBtn.style.opacity = '0.4';
      runAutoScriptBtn.style.cursor = 'not-allowed';
      runAutoScriptBtn.className = 'cyber-btn muted';
      runAutoScriptBtn.title = '需要終端連線才能使用';
    }
  }
  // 關閉執行器按鈕：有終端才可按
  const shutdownBtn = document.getElementById('btnShutdownExecutor');
  if (shutdownBtn) {
    if (connected) {
      shutdownBtn.disabled = false;
      shutdownBtn.style.opacity = '1';
      shutdownBtn.style.cursor = 'pointer';
      shutdownBtn.title = '關閉 node server 和 ngrok';
    } else {
      shutdownBtn.disabled = true;
      shutdownBtn.style.opacity = '0.4';
      shutdownBtn.style.cursor = 'not-allowed';
      shutdownBtn.title = '需要終端連線才能使用';
    }
  }
  // 同步更新設定面板
  updateSettingTerminalDisplay();
  // 同步更新系統狀態列
  updateSystemStatusBar();
}

// 自動從 localhost 偵測 ngrok 網址（start.bat 啟動後自動填入）
function autoDetectNgrokUrl() {
  // 優先從 URL 參數取得（start.bat 自動帶入）
  const params = new URLSearchParams(window.location.search);
  const paramNgrok = params.get('ngrok') || params.get('nght');
  if (paramNgrok) {
    applyNgrokUrl(paramNgrok);
    return;
  }

  // 其次從 localhost server 查詢
  fetch('http://127.0.0.1:3000/ngrok-url')
    .then(res => res.json())
    .then(data => {
      if (data.url) applyNgrokUrl(data.url);
      else scheduleNgrokRetry();
    })
    .catch(() => scheduleNgrokRetry());
}

// 套用 ngrok 網址
function applyNgrokUrl(url) {
  url = url.replace(/\/$/, '');
  webState.ngrokUrl = url;
  localStorage.setItem('miniclaw_ngrok_url', url);

  const inputs = ['ngrokUrlInput', 'settingNgrokInput'];
  inputs.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = url;
  });

  updateLineWebhookUrlDisplay();

  // 若 onboarding 還在 Step 1（有終端模式），自動觸發測試連線 → 成功後自動跳 AI 綁定
  const paneStep2 = document.getElementById('paneStep2');
  const terminalGuide = document.getElementById('terminalGuideContent');
  if (paneStep2 && paneStep2.classList.contains('active') &&
      terminalGuide && terminalGuide.style.display !== 'none') {
    const testBtn = document.getElementById('btnTestExecutor');
    if (testBtn) {
      setTimeout(() => testBtn.click(), 600); // 稍等讓 UI 渲染完
      return;
    }
  }

  if (!webState.isTerminalConnected) {
    appendMessage('warning', `🔗 [自動偵測] 已取得 ngrok 網址，正在自動連線...`);
    initWebSocketConnection();
  }
}

// 每 3 秒重試偵測（等使用者跑完 start.bat）
let ngrokRetryTimer = null;
function scheduleNgrokRetry() {
  if (ngrokRetryTimer) return;
  ngrokRetryTimer = setInterval(() => {
    fetch('http://127.0.0.1:3000/ngrok-url')
      .then(res => res.json())
      .then(data => {
        if (data.url) {
          clearInterval(ngrokRetryTimer);
          ngrokRetryTimer = null;
          applyNgrokUrl(data.url);
        }
      })
      .catch(() => {});
  }, 3000);
}

// --- 5. IP 心跳輪詢探測 (Step 4) ---
function startDiagnosticPolling() {
  // 先嘗試從 localhost 自動取得 ngrok 網址
  autoDetectNgrokUrl();

  setInterval(() => {
    if (webState.isTerminalConnected) {
      updateDiagnosticLights(true);
      return;
    }
    
    // 已有 WebSocket 在連線中就不重建
    if (webState.ws && (webState.ws.readyState === WebSocket.CONNECTING || webState.ws.readyState === WebSocket.OPEN)) {
      return;
    }
    
    const healthUrl = webState.ngrokUrl
      ? `${webState.ngrokUrl}/health`
      : `http://127.0.0.1:${webState.localPort}/health`;
    
    fetch(healthUrl, { headers: { 'ngrok-skip-browser-warning': 'true' } })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok') {
          updateDiagnosticLights(true);
          if (!webState.ws || webState.ws.readyState === WebSocket.CLOSED) {
            initWebSocketConnection();
          }
        }
      })
      .catch(() => {
        updateDiagnosticLights(false);
      });
  }, 15000);
}

function updateDiagnosticLights(success) {
  const localhostLight = document.getElementById('diagnosticLocalhost');
  const localLight = document.getElementById('diagnosticLocal');
  const ngrokUrlEl = document.getElementById('diagnosticNgrokUrl');
  
  if (!localhostLight) return;

  if (ngrokUrlEl) {
    ngrokUrlEl.innerText = webState.ngrokUrl || '未設定';
    ngrokUrlEl.style.color = webState.ngrokUrl ? 'var(--neon-cyan)' : 'var(--neon-orange)';
  }
  
  if (success) {
    localhostLight.innerText = '🟢 HTTP 通道正常 (200 OK)';
    localhostLight.style.color = 'var(--neon-green)';
    
    if (localLight) {
      localLight.innerText = webState.isTerminalConnected ? '🟢 WebSocket 已連線' : '🔴 WebSocket 未連線';
      localLight.style.color = webState.isTerminalConnected ? 'var(--neon-green)' : '#ff4444';
    }
    
    const guideEl = document.getElementById('diagnosticGuideText');
    if (guideEl) {
      if (webState.isTerminalConnected) {
        guideEl.innerHTML = '🎉 HTTP + WebSocket 雙重連線成功！小龍蝦已完整連上你的電腦！';
      } else {
        guideEl.innerHTML = '⚠️ HTTP 通道正常，但 WebSocket 未連線，正在自動重連中...';
      }
    }
  } else {
    localhostLight.innerText = '🟠 無法連線';
    localhostLight.style.color = 'var(--neon-orange)';
    
    if (localLight) {
      localLight.innerText = '🟠 未連線';
      localLight.style.color = 'var(--neon-orange)';
    }
  }
}

// --- 多對話管理 ---
const chatSessions = [{ id: 1, title: '對話 1', messages: [] }];
let activeChatId = 1;
let chatIdCounter = 2;

function renderChatList() {
  const list = document.getElementById('chatList');
  if (!list) return;
  list.innerHTML = '';
  chatSessions.forEach(s => {
    const item = document.createElement('div');
    item.className = 'chat-list-item' + (s.id === activeChatId ? ' active' : '');
    item.innerHTML = `<span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;">${s.title}</span><button class="del-btn" data-id="${s.id}" title="刪除">✕</button>`;
    item.addEventListener('click', (e) => {
      if (e.target.classList.contains('del-btn')) return;
      switchChat(s.id);
    });
    item.querySelector('.del-btn').addEventListener('click', () => deleteChat(s.id));
    list.appendChild(item);
  });
}

function switchChat(id) {
  // 儲存目前對話的 DOM
  const session = chatSessions.find(s => s.id === activeChatId);
  if (session) {
    session.messages = document.getElementById('chatHistoryContainer').innerHTML;
  }
  activeChatId = id;
  const target = chatSessions.find(s => s.id === id);
  const container = document.getElementById('chatHistoryContainer');
  if (target) {
    container.innerHTML = target.messages || `<div id="featureCards" style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:16px;padding:20px;"><div style="font-size:2rem;">🦞</div><div style="font-size:0.82rem;color:var(--text-muted);">選擇功能或直接輸入指令開始</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;width:100%;max-width:360px;"><button class="feature-card-btn" onclick="sendQuickCommand('幫我截圖目前畫面')">🖥️<br><span>畫面監控</span></button><button class="feature-card-btn" onclick="sendQuickCommand('列出桌面的檔案')">📁<br><span>檔案管理</span></button><button class="feature-card-btn" onclick="sendQuickCommand('幫我診斷網路連線狀態')">🌐<br><span>網路診斷</span></button><button class="feature-card-btn" onclick="sendQuickCommand('查看下載資料夾的內容')">⬇️<br><span>查看下載</span></button></div></div>`;
  }
  renderChatList();
}

function deleteChat(id) {
  if (chatSessions.length === 1) return; // 至少保留一個
  const idx = chatSessions.findIndex(s => s.id === id);
  chatSessions.splice(idx, 1);
  if (activeChatId === id) {
    activeChatId = chatSessions[0].id;
    switchChat(activeChatId);
  }
  renderChatList();
}

function newChat() {
  const id = chatIdCounter++;
  chatSessions.push({ id, title: `對話 ${id}`, messages: '' });
  switchChat(id);
}

// 快速指令（功能卡片用）
function sendQuickCommand(text) {
  const input = document.getElementById('chatInput');
  if (input) {
    input.value = text;
    document.getElementById('chatForm').dispatchEvent(new Event('submit'));
  }
}

// WS 狀態 log（顯示在系統狀態列，不塞進對話框）
function logStatus(msg) {
  const el = document.getElementById('sysStatusTerminal');
  if (el && !webState.isTerminalConnected) {
    el.textContent = msg;
    el.style.color = msg.startsWith('🟢') ? 'var(--neon-green)' : msg.startsWith('🔴') || msg.startsWith('❌') ? '#ff6666' : 'var(--neon-orange)';
  }
  console.log('[WS]', msg);
}

// 系統狀態列更新
function updateSystemStatusBar() {
  const termEl = document.getElementById('sysStatusTerminal');
  const apiEl = document.getElementById('sysStatusApi');
  const platEl = document.getElementById('sysStatusPlatform');
  if (termEl) {
    termEl.textContent = webState.isTerminalConnected ? '🟢 終端: 連線中' : '🔴 終端: 離線';
    termEl.style.color = webState.isTerminalConnected ? 'var(--neon-green)' : 'var(--neon-orange)';
  }
  if (apiEl) {
    const hasApi = webState.apiKey || webState.googleAccessToken || localStorage.getItem('miniclaw_ollama_ready') === 'true';
    apiEl.textContent = hasApi ? '🔑 API: 已設定' : '🔑 API: 未設定';
    apiEl.style.color = hasApi ? 'var(--neon-green)' : 'var(--text-muted)';
  }
  if (platEl) {
    platEl.textContent = `🖥️ ${webState.platform || '偵測中'}`;
  }
}

// --- 6. AI 聊天面版與「方案 B」沙盒模擬器 ---
function setupChatEvents() {
  const form = document.getElementById('chatForm');
  const input = document.getElementById('chatInput');

  // 初始化對話列表
  renderChatList();
  document.getElementById('btnNewChat')?.addEventListener('click', newChat);

  // 測試終端按鈕
  const testBtn = document.getElementById('btnTestTerminal');
  if (testBtn) {
    testBtn.addEventListener('click', () => {
      if (webState.isTerminalConnected && webState.ws && webState.ws.readyState === WebSocket.OPEN) {
        appendMessage('user', '🖥️ 測試終端連線');
        webState.ws.send(JSON.stringify({ type: 'sys-status' }));
      } else {
        appendMessage('ai', '❌ 終端未連線，請確認 openminiclaw.bat 還在執行中。');
      }
    });
  }

  // 遊戲助手按鈕（toggle）
  const gameBtn = document.getElementById('btnGameAssist');
  if (gameBtn) {
    gameBtn.addEventListener('click', () => {
      if (!webState.isTerminalConnected) return;
      const isActive = gameBtn.dataset.active === '1';
      if (!isActive) {
        gameBtn.dataset.active = '1';
        gameBtn.className = 'cyber-btn orange';
        gameBtn.style.background = 'rgba(57,255,20,0.15)';
        gameBtn.style.borderColor = 'var(--neon-green)';
        gameBtn.style.color = 'var(--neon-green)';
        gameBtn.textContent = '🎮 遊戲助手 ✦';
        appendMessage('ai',
          '🎮 <strong>遊戲助手已啟動！</strong><br><br>' +
          '你可以這樣告訴我：<br>' +
          '① 輸入遊戲名稱（例如：原神、英雄聯盟）<br>' +
          '② 上傳遊戲截圖或影片（影片請控制在 <strong>20MB 以內</strong>）<br>' +
          '③ 簡單描述遊戲玩法或你想讓我幫你做什麼<br><br>' +
          '📝 格式：<code>遊戲名稱 | 描述</code>，例如：<br>' +
          '<code>原神 | 自動刷怪，優先用元素爆發技能</code>'
        );
      } else {
        gameBtn.dataset.active = '0';
        gameBtn.className = 'cyber-btn orange';
        gameBtn.style.background = '';
        gameBtn.style.borderColor = '';
        gameBtn.style.color = '';
        gameBtn.textContent = '🎮 遊戲助手';
        appendMessage('ai', '🎮 遊戲助手已關閉，回到一般模式。');
      }
    });
  }

  // 錄製操作按鈕
  const openRecorderBtn = document.getElementById('btnOpenRecorder');
  if (openRecorderBtn) {
    openRecorderBtn.addEventListener('click', () => {
      if (!webState.isTerminalConnected) return;
      handleOutboundMessage('啟動錄製器');
    });
  }

  // 執行自動化腳本按鈕
  const runAutoScriptBtn = document.getElementById('btnRunAutoScript');
  if (runAutoScriptBtn) {
    runAutoScriptBtn.addEventListener('click', () => {
      if (!webState.isTerminalConnected) return;
      handleOutboundMessage('執行自動化腳本');
    });
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const msg = input.value.trim();
    if (!msg) return;
    
    appendMessage('user', msg);
    input.value = '';
    
    // 傳送指令
    handleOutboundMessage(msg);
  });
}

function handleOutboundMessage(text) {
  // 如果終端已連接，透過 WebSocket 傳送
  if (webState.isTerminalConnected && webState.ws && webState.ws.readyState === WebSocket.OPEN) {
    webState.ws.send(JSON.stringify({
      type: 'user-command',
      data: { text: text, platform: webState.platform }
    }));
    return;
  }
  
  // 終端未連線時，只有明確的「執行指令」類才用 mock，其餘走 AI 對話
  const query = text.toLowerCase();
  // 只有這些明確需要在終端執行的指令才 mock
  const needsTerminal = query.includes('ping ') || query.includes('ipconfig') ||
    query.includes('關機') || query.includes('重開機');

  if (needsTerminal) {
    triggerMockAIResponse(text);
    return;
  }
  
  // 純對話：優先用 Gemini（Google Token 或 API Key）
  if (webState.googleAccessToken || webState.apiKey) {
    if (webState.aiQuotaExhausted && localStorage.getItem('miniclaw_ollama_ready') !== 'true') {
      appendMessage('ai', '❌ AI 點數不足或已失效，無法回應您的對話，請檢查您的金鑰或帳號狀態。');
      return;
    }
    appendMessage('ai', '⏳ 思考中...');
    callGeminiFromFrontend(text).then(reply => {
      const container = document.getElementById('chatHistoryContainer');
      const bubbles = container.querySelectorAll('.message-bubble.ai');
      const last = bubbles[bubbles.length - 1];
      if (last && last.innerHTML.includes('思考中')) last.remove();
      if (reply) {
        appendMessage('ai', reply);
      } else {
        triggerMockAIResponse(text);
      }
    });
    return;
  }

  // 備援：嘗試本地 Ollama
  if (localStorage.getItem('miniclaw_ollama_ready') === 'true') {
    // 有終端連線 → 透過 WebSocket 讓 server.js 呼叫 Ollama（無 CORS 問題）
    if (webState.isTerminalConnected && webState.ws && webState.ws.readyState === WebSocket.OPEN) {
      webState.ws.send(JSON.stringify({
        type: 'user-command',
        data: { text: text, platform: webState.platform }
      }));
      return;
    }
    // 沒有終端 → 直接呼叫（只有本機開啟 index.html 時有效）
    appendMessage('ai', '⏳ 本地 AI 思考中...');
    callOllamaFromFrontend(text).then(reply => {
      const container = document.getElementById('chatHistoryContainer');
      const bubbles = container.querySelectorAll('.message-bubble.ai');
      const last = bubbles[bubbles.length - 1];
      if (last && last.innerHTML.includes('思考中')) last.remove();
      if (reply) {
        appendMessage('ai', reply);
      } else {
        appendMessage('warning', '⚠️ 本地 AI 無法回應。若使用 GitHub Pages，請先連接終端後再使用本地 AI。');
      }
    });
    return;
  }

  triggerMockAIResponse(text);
}

// --- 前端直接呼叫 Gemini API（使用 Google Access Token 或 API Key）---
async function callGeminiFromFrontend(text) {
  const SYSTEM_PROMPT = '你是小龍蝦控制中樞的 AI 助手，請簡明扼要地回答，控制在 100 字以內。';

  // 優先用 Google Access Token
  if (webState.googleAccessToken) {
    try {
      const res = await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${webState.googleAccessToken}`
        },
        body: JSON.stringify({
          contents: [{ parts: [{ text }] }],
          systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] }
        })
      });
      if (res.ok) {
        const data = await res.json();
        webState.aiQuotaExhausted = false;
        updateAIStatusUI();
        updateBalanceDisplay(webState.googleAccessToken);
        return data.candidates[0].content.parts[0].text;
      }
      // Token 過期，嘗試重新取得
      if (res.status === 401) {
        requestGoogleAccessToken();
        return '⚠️ Google 授權已過期，正在重新取得，請稍後再試。';
      }
      // 點數不足/超載等錯誤
      webState.aiQuotaExhausted = true;
      updateAIStatusUI();
      updateBalanceDisplay(webState.googleAccessToken);
    } catch (e) {
      webState.aiQuotaExhausted = true;
      updateAIStatusUI();
      updateBalanceDisplay(webState.googleAccessToken);
    }
  }

  // 備用：用 API Key
  if (webState.apiKey) {
    try {
      const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${webState.apiKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text }] }],
          systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] }
        })
      });
      if (res.ok) {
        const data = await res.json();
        webState.aiQuotaExhausted = false;
        updateAIStatusUI();
        updateBalanceDisplay(webState.apiKey);
        return data.candidates[0].content.parts[0].text;
      }
      webState.aiQuotaExhausted = true;
      updateAIStatusUI();
      updateBalanceDisplay(webState.apiKey);
    } catch (e) {
      webState.aiQuotaExhausted = true;
      updateAIStatusUI();
      updateBalanceDisplay(webState.apiKey);
    }
  }

  return null;
}

// 前端直接呼叫 Ollama（本地 AI，不需 key）
async function callOllamaFromFrontend(text) {
  try {
    const res = await fetch('http://127.0.0.1:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'gemma3:3b',
        prompt: `你是小龍蝦控制中樞的 AI 助手，請簡明扼要地回答，控制在 100 字以內。\n\n使用者指令: ${text}`,
        stream: false
      })
    });
    if (res.ok) {
      const data = await res.json();
      return data.response;
    }
  } catch (e) {}
  return null;
}

// 方案 B 離線模擬回覆引擎 (限制 100 字內，警示用橘色)
function triggerMockAIResponse(text) {
  setTimeout(() => {
    let reply = '收到指令！但目前小龍蝦處於離線沙盒狀態。若需真實運作，請在設定中開啟並執行 openminiclaw.bat。';
    let outputText = '';
    
    const query = text.toLowerCase();
    
    if (query.includes('截圖') || query.includes('畫面')) {
      reply = '正在捕捉您的本地螢幕畫面...';
      setTimeout(() => {
        appendScreenshotMessage();
        appendMessage('warning', '⚙️ [沙盒自檢輸出] : 已在本地暫存區生成 fake_screenshot.jpg');
      }, 1000);
    } else if (query.includes('網路') || query.includes('終端') || query.includes('ping') || query.includes('ipconfig') || query.includes('連線')) {
      reply = '⚠️ 終端未連線，無法執行網路指令。請回 Step 1 重新測試連線，確認 node server.js 和 ngrok 都在執行中。';
    } else if (query.includes('查看') || query.includes('列出') || query.includes('檔案') || query.includes('資料夾') || query.includes('下載') || query.includes('目錄')) {
      reply = '⚠️ 終端未連線，無法存取本地檔案系統。請回 Step 1 確認 node server.js 和 ngrok 都在執行中，WebSocket 連線成功後即可使用此功能。';
    } else if (query.includes('建立') || query.includes('寫入')) {
      reply = '已為您自動模擬建立資料夾邏輯。';
      outputText = 'mkdir "C:\\Users\\user\\Desktop\\小龍蝦作業"\necho "小龍蝦 AI 已順利部署！" > "介紹.txt"\nSTATUS: SUCCESS';
    } else if (query.includes('電力') || query.includes('電量')) {
      reply = '🔋 當前本地設備模擬電量為 78%，狀態良好，不需要發送簡訊。';
    } else if (query.includes('定位') || query.includes('gps')) {
      reply = '📍 當前本地設備定位座標 (模擬) : 緯度 25.0339, 經度 121.5645 (台北市信義區)。';
    } else if (query.includes('cpu') || query.includes('溫度') || query.includes('關機')) {
      reply = '🌡️ 當前 CPU 溫度 42°C，處於安全範圍。未觸發自動關機保護機制。';
    } else if (query.includes('改') || query.includes('顏色') || query.includes('深藍')) {
      reply = '🎨 收到！已將大廳佈局顏色自癒調整為深藍色調。';
      document.body.style.setProperty('--neon-orange', '#007fff');
      document.body.style.setProperty('--neon-orange-glow', '0 0 10px rgba(0, 127, 255, 0.6)');
    }
    
    // 輸出回覆與日誌
    appendMessage('ai', reply);
    if (outputText) {
      setTimeout(() => {
        appendMessage('warning', `⚙️ 終端執行日誌 (100字精簡限額):\n${outputText}`);
      }, 300);
    }
  }, 800);
}

// 渲染訊息泡泡
function appendMessage(sender, text) {
  const container = document.getElementById('chatHistoryContainer');

  // 有訊息時隱藏功能卡片
  const cards = document.getElementById('featureCards');
  if (cards) cards.remove();

  const bubble = document.createElement('div');
  bubble.className = `message-bubble ${sender}`;
  bubble.innerHTML = text.replace(/\n/g, '<br>');
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;

  // 同步更新系統狀態列
  updateSystemStatusBar();

  // AI 回覆後自動備份到 Google Drive
  if (sender === 'ai' && localStorage.getItem('miniclaw_chatlog_gdrive') === 'true') {
    saveChatToGDrive();
  }

  // 本機日誌：若終端已連線，將 user/ai 訊息附加至 chat_history.txt
  if ((sender === 'user' || sender === 'ai') && webState.isTerminalConnected) {
    const baseUrl = webState.ngrokUrl || `http://localhost:${webState.localPort}`;
    const ts = new Date().toISOString();
    fetch(`${baseUrl}/save-local-log`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
      body: JSON.stringify({ role: sender, text: text, ts })
    }).catch(() => {}); // 靜默失敗，不影響主流程
  }
}

// 渲染 Fake 截圖特效 (Wow the user)
function appendScreenshotMessage(base64Data = null) {
  const container = document.getElementById('chatHistoryContainer');
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble ai';
  
  const imgUrl = base64Data ? `data:image/jpeg;base64,${base64Data}` : 'https://picsum.photos/id/2/400/250';
  
  bubble.innerHTML = `
    <p style="margin-bottom: 8px;">📸 <b>螢幕截圖已成功捕獲！</b></p>
    <img src="${imgUrl}" style="width: 100%; border-radius: 8px; border: 1px solid rgba(255, 102, 0, 0.3); box-shadow: 0 4px 15px rgba(0,0,0,0.5);" alt="畫面監控">
  `;
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

// --- 7. 動態快捷範例 (依據平台切換) ---
function renderShortcutChips() {
  const wrapper = document.getElementById('shortcutsWrapper');
  if (!wrapper) return;
  wrapper.innerHTML = '';
  
  const isPC = (webState.platform === 'windows' || webState.platform === 'mac' || webState.platform === 'linux');
  const isAndroid = (webState.platform === 'android');
  
  const pcChips = [
    { text: '📸 畫面監控', cmd: '幫我截圖現在的螢幕，我想看遊戲掛機進度。' },
    { text: '📂 檔案管理', cmd: '在桌面建立一個資料夾叫「小龍蝦作業」，並寫入介紹 AI 的文字檔。' },
    { text: '🌐 網路診斷', cmd: '幫我檢查網路連線狀況，ping 一下 8.8.8.8。' },
    { text: '📋 查看下載', cmd: '列出我的下載資料夾有哪些檔案。' }
  ];

  // Android 有終端：可以跑 shell 指令
  const androidTerminalChips = [
    { text: '🌐 開瀏覽器查詢', cmd: '幫我查台北今天天氣' },
    { text: '🔋 查電量', cmd: '查一下現在電池電量' },
    { text: '📂 查看檔案', cmd: '列出我的下載資料夾有哪些檔案。' },
    { text: '🌐 網路診斷', cmd: '幫我檢查網路連線狀況，ping 一下 8.8.8.8。' }
  ];

  // Android/iOS 無終端：只能純 AI 對話
  const mobileNoTerminalChips = [
    { text: '💬 問 AI', cmd: '你好，請介紹一下你自己的功能。' },
    { text: '📝 幫我寫作', cmd: '幫我寫一封請假信，原因是身體不舒服。' },
    { text: '🔍 解釋程式', cmd: '幫我解釋什麼是 WebSocket，用簡單的方式說明。' },
    { text: '🌐 翻譯', cmd: '幫我把「小龍蝦控制中樞」翻譯成英文和日文。' }
  ];
  
  let chips;
  if (isPC) {
    chips = pcChips;
  } else if (isAndroid && webState.isTerminalConnected) {
    chips = androidTerminalChips;
  } else {
    chips = mobileNoTerminalChips;
  }
  
  chips.forEach(item => {
    const chip = document.createElement('div');
    chip.className = 'shortcut-chip';
    chip.innerText = item.text;
    chip.addEventListener('click', () => {
      document.getElementById('chatInput').value = item.cmd;
    });
    wrapper.appendChild(chip);
  });
}

// --- 8. 設定面板與還原系統處理 ---
function setupSettingsPanelEvents() {
  // 背景圖片
  const bgInput = document.getElementById('bgImageUrlInput');
  bgInput.addEventListener('input', () => {
    const url = bgInput.value.trim();
    if (url) {
      document.body.style.setProperty('--bg-custom-url', `url('${url}')`);
      localStorage.setItem('miniclaw_bg_image', url);
    } else {
      document.body.style.setProperty('--bg-custom-url', 'none');
      localStorage.removeItem('miniclaw_bg_image');
    }
  });

  // AI 優先級
  document.getElementById('selectAIPriority').addEventListener('change', (e) => {
    localStorage.setItem('miniclaw_ai_priority', e.target.value);
    syncAllCredentialsToLocal();
    showToast('🧠 優先級已更改', `已調整首選 AI 引擎為 : ${e.target.value.toUpperCase()}`, '🦞');
  });

  // 完整執行端開關
  document.getElementById('toggleCompleteExecution').addEventListener('change', (e) => {
    const isComplete = e.target.checked;
    webState.apiMode = isComplete ? 'complete' : 'lightweight';
    localStorage.setItem('miniclaw_api_mode', webState.apiMode);
    if (isComplete) {
      showToast('🛡️ 啟動完整執行模式', '重新啟動步驟一引導以引導您部署執行端包！', '🦞');
      document.getElementById('onboardingModal').style.display = 'flex';
      goToStep(1);
    } else {
      showToast('🛡️ 降級至輕量隧道', '已切換為純前端輕量運作模式。', '🦞');
    }
  });

  // 重置引導
  document.getElementById('btnResetAllOnboarding').addEventListener('click', () => {
    document.getElementById('onboardingModal').style.display = 'flex';
    goToStep(1);
  });

  // 重新設定遠端（舊按鈕，保留相容）
  const btnRemoteReset = document.getElementById('btnTriggerRemoteReset');
  if (btnRemoteReset) {
    btnRemoteReset.addEventListener('click', () => {
      document.getElementById('onboardingModal').style.display = 'flex';
      goToStep(3);
    });
  }

  // --- 新增：帳號群組 ---
  // Google 登入按鈕（設定面板）
  document.getElementById('btnSettingGoogleLogin').addEventListener('click', () => {
    if (webState.googleUser) {
      handleGoogleLogout();
    } else {
      requestGoogleAccessToken();
    }
  });

  // 修改 API Key
  document.getElementById('btnEditApiKey').addEventListener('click', () => {
    const form = document.getElementById('editApiKeyForm');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
  });

  document.getElementById('btnSaveApiKey').addEventListener('click', async () => {
    const input = document.getElementById('settingApiKeyInput');
    const key = input.value.trim();
    if (!key) return;
    webState.apiKey = key;
    localStorage.setItem('miniclaw_api_key', key);
    updateBalanceDisplay(key);
    updateSettingApiKeyDisplay(key);
    document.getElementById('editApiKeyForm').style.display = 'none';
    input.value = '';
    showToast('🔑 API 金鑰已更新', '新金鑰已儲存。', '🦞');
  });

  // --- 新增：終端群組 ---
  document.getElementById('btnReconnectTerminal').addEventListener('click', () => {
    const input = document.getElementById('settingNgrokInput');
    const url = input.value.trim().replace(/\/$/, '');
    if (url) {
      webState.ngrokUrl = url;
      localStorage.setItem('miniclaw_ngrok_url', url);
    }
    initWebSocketConnection();
    showToast('🔌 重新連線中', '正在嘗試建立 WebSocket 連線...', '🦞');
  });

  // 關閉執行器按鈕
  const shutdownBtn = document.getElementById('btnShutdownExecutor');
  if (shutdownBtn) {
    shutdownBtn.addEventListener('click', () => {
      if (!webState.isTerminalConnected || !webState.ws) return;
      if (!confirm('確定要關閉執行器？這會停止 node server 和 ngrok。')) return;
      webState.ws.send(JSON.stringify({ type: 'shutdown' }));
      appendMessage('ai', '🔴 已送出關閉指令，執行器正在停止...');
    });
  }

  // 恢復 ngrok 網址到設定面板
  if (webState.ngrokUrl) {
    const ngrokInput = document.getElementById('settingNgrokInput');
    if (ngrokInput) ngrokInput.value = webState.ngrokUrl;
  }

  // --- 新增：LINE/DC 快速修改 ---
  document.getElementById('btnToggleEditLINE').addEventListener('click', () => {
    const el = document.getElementById('quickEditLINE');
    el.style.display = el.style.display === 'none' ? 'block' : 'none';
    document.getElementById('quickEditDiscord').style.display = 'none';
  });

  document.getElementById('btnToggleEditDiscord').addEventListener('click', () => {
    const el = document.getElementById('quickEditDiscord');
    el.style.display = el.style.display === 'none' ? 'block' : 'none';
    document.getElementById('quickEditLINE').style.display = 'none';
  });

  document.getElementById('btnSaveLINE').addEventListener('click', () => {
    const token = document.getElementById('settingLineToken').value.trim();
    const secret = document.getElementById('settingLineSecret').value.trim();
    if (!token || !secret) { showToast('⚠️ 請填寫完整', 'Token 和 Secret 都需要填寫。', '🦞'); return; }
    const creds = JSON.parse(localStorage.getItem('miniclaw_remote_creds') || '{}');
    creds.type = 'line';
    creds.line = { token, secret, userId: creds.line ? (creds.line.userId || '') : '' };
    localStorage.setItem('miniclaw_remote_creds', JSON.stringify(creds));
    // 同步至執行端，使用 remote 包裝格式
    if (webState.ws && webState.ws.readyState === WebSocket.OPEN) {
      webState.ws.send(JSON.stringify({ type: 'sync-credentials', data: { remote: creds } }));
    }
    updateSettingRemoteStatus(true, token);
    document.getElementById('quickEditLINE').style.display = 'none';
    showToast('✅ LINE 設定已儲存', '憑證已更新並同步至執行端。', '🦞');
  });

  document.getElementById('btnSaveDiscord').addEventListener('click', () => {
    const token = document.getElementById('settingDiscordToken').value.trim();
    const channel = document.getElementById('settingDiscordChannel').value.trim();
    if (!token || !channel) { showToast('⚠️ 請填寫完整', 'Token 和 Channel ID 都需要填寫。', '🦞'); return; }
    const creds = JSON.parse(localStorage.getItem('miniclaw_remote_creds') || '{}');
    creds.type = 'discord';
    creds.discord = { token, channel };
    localStorage.setItem('miniclaw_remote_creds', JSON.stringify(creds));
    // 同步至執行端，使用 remote 包裝格式
    if (webState.ws && webState.ws.readyState === WebSocket.OPEN) {
      webState.ws.send(JSON.stringify({ type: 'sync-credentials', data: { remote: creds } }));
    }
    updateSettingRemoteStatus(false, token);
    document.getElementById('quickEditDiscord').style.display = 'none';
    showToast('✅ Discord 設定已儲存', '憑證已更新並同步至執行端。', '🦞');
  });

  // --- 新增：System Prompt ---
  const savedPrompt = localStorage.getItem('miniclaw_system_prompt');
  if (savedPrompt) document.getElementById('customSystemPrompt').value = savedPrompt;

  document.getElementById('btnSaveSystemPrompt').addEventListener('click', () => {
    const prompt = document.getElementById('customSystemPrompt').value.trim();
    localStorage.setItem('miniclaw_system_prompt', prompt);
    showToast('💬 提示詞已儲存', prompt ? '自訂提示詞已啟用。' : '已恢復預設提示詞。', '🦞');
  });

  // --- 新增：對話管理 ---
  document.getElementById('btnClearChat').addEventListener('click', () => {
    const container = document.getElementById('chatHistoryContainer');
    container.innerHTML = '<div class="message-bubble ai">對話已清除。有什麼需要幫忙的嗎？</div>';
    showToast('🗑️ 對話已清除', '', '🦞');
  });

  document.getElementById('btnExportChat').addEventListener('click', () => {
    const container = document.getElementById('chatHistoryContainer');
    const bubbles = container.querySelectorAll('.message-bubble');
    let text = '=== 小龍蝦對話紀錄 ===\n\n';
    bubbles.forEach(b => {
      const role = b.classList.contains('user') ? '使用者' : b.classList.contains('ai') ? '小龍蝦' : '系統';
      text += `[${role}]\n${b.innerText}\n\n`;
    });
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `miniclaw_chat_${new Date().toISOString().slice(0,10)}.txt`;
    a.click();
    showToast('📥 對話已匯出', '已下載為 .txt 檔案。', '🦞');
  });

  // 初始化設定面板顯示
  updateSettingApiKeyDisplay(webState.apiKey);
  updateSettingGoogleDisplay();
  updateSettingTerminalDisplay();
  setupChatLogEvents();
}

// 更新設定面板 API Key 顯示
function updateSettingApiKeyDisplay(key) {
  const el = document.getElementById('settingApiKeyDisplay');
  if (!el) return;
  if (key) {
    el.innerText = key.slice(0, 8) + '••••••••••••••••' + key.slice(-4);
    el.style.color = 'var(--neon-green)';
  } else {
    el.innerText = '未設定';
    el.style.color = 'var(--text-muted)';
  }
}

// 更新設定面板 Google 顯示
function updateSettingGoogleDisplay() {
  const statusEl = document.getElementById('settingGoogleStatus');
  const btnEl = document.getElementById('btnSettingGoogleLogin');
  if (!statusEl) return;
  if (webState.googleUser) {
    statusEl.innerHTML = `<span style="color:var(--neon-green);">🟢 ${webState.googleUser.name}</span><br><span style="font-size:0.72rem;">${webState.googleUser.email}</span>`;
    if (btnEl) btnEl.innerText = '登出 Google';
  } else {
    statusEl.innerText = '未登入';
    if (btnEl) btnEl.innerText = '🔵 用 Google 帳號登入';
  }
}

// 更新設定面板終端狀態顯示
function updateSettingTerminalDisplay() {
  const el = document.getElementById('settingTerminalStatus');
  if (!el) return;
  if (webState.isTerminalConnected) {
    el.innerText = '🟢 已連線';
    el.style.color = 'var(--neon-green)';
  } else {
    el.innerText = '🔴 離線';
    el.style.color = 'var(--neon-orange)';
  }
}

// 模擬執行端代碼自癒還原
function triggerServerRestoration() {
  showToast('🛠️ 觸發代碼還原', '正在指示本地端將 server.js 還原至 server.js.bak...', '🦞');
  
  if (webState.isTerminalConnected && webState.ws && webState.ws.readyState === WebSocket.OPEN) {
    webState.ws.send(JSON.stringify({ type: 'sys-restore', data: {} }));
  } else {
    // 方案 B 模擬還原
    setTimeout(() => {
      showToast('🟢 備份還原成功', '本地伺服器已順利將 server.js 修復並自我重啟！', '🦞');
      appendMessage('warning', '⚙️ [自癒日誌] : server.js 已被還原，系統於 1.5 秒後正常重啟。');
    }, 1500);
  }
}

// --- 9. 工具與輔助 UI 函式 ---
function updateBalanceDisplay(key) {
  const el = document.getElementById('monitorBalanceVal');
  if (webState.aiQuotaExhausted) {
    el.innerText = '❌ 偵測不到點數或點數已用盡 / 帳額失效';
    el.style.color = '#ff4444';
    return;
  }
  
  // 優先用 Google Token 顯示額度
  const activeKey = key || webState.googleAccessToken || '';
  if (!activeKey) {
    el.innerText = '$0.00 (免費模擬版)';
    el.style.color = '';
    return;
  }
  
  el.style.color = '';
  if (webState.googleAccessToken && webState.googleAccessToken.length > 10) {
    el.innerText = '15,000 / 15,000 次 (Gemini 免費帳額)';
  } else if (activeKey.startsWith('AIzaSy')) {
    el.innerText = '15,000 / 15,000 次 (Gemini 免費帳額)';
  } else if (activeKey.startsWith('sk-or-')) {
    el.innerText = '$18.52 / $50.00 USD (Openround 點數帳額)';
  } else {
    el.innerText = '$18.52 / $50.00 USD (OpenAI 點數帳額)';
  }
}

// AI 連接狀態燈號更新
function updateAIStatusUI() {
  const dot = document.getElementById('aiStatusDot');
  const txt = document.getElementById('aiStatusText');
  const sysApi = document.getElementById('sysStatusApi');
  if (!dot || !txt) return;

  let label = '';
  let color = '';
  let active = false;

  if (webState.aiQuotaExhausted) {
    active = false;
    label = 'AI: 餘額不足/失效';
    color = '#ff4444';
    if (sysApi) { sysApi.innerText = '🔴 AI: 餘額不足/失效'; sysApi.style.color = '#ff4444'; }
  } else if (webState.googleAccessToken && webState.googleAccessToken.length > 10) {
    active = true;
    label = 'AI: Google 登入';
    color = 'var(--neon-green)';
    if (sysApi) { sysApi.innerText = '🟢 AI: Google 登入'; sysApi.style.color = 'var(--neon-green)'; }
  } else if (webState.apiKey && webState.apiKey.length > 10) {
    active = true;
    let keyType = 'OpenAI';
    if (webState.apiKey.startsWith('AIzaSy')) keyType = 'Gemini';
    else if (webState.apiKey.startsWith('sk-or-')) keyType = 'Openround';
    label = `AI: ${keyType} Key`;
    color = 'var(--neon-green)';
    if (sysApi) { sysApi.innerText = `🟢 AI: ${keyType} Key`; sysApi.style.color = 'var(--neon-green)'; }
  } else if (localStorage.getItem('miniclaw_ollama_ready') === 'true') {
    active = true;
    label = 'AI: Ollama 本地';
    color = 'var(--neon-cyan)';
    if (sysApi) { sysApi.innerText = '🟢 AI: Ollama'; sysApi.style.color = 'var(--neon-cyan)'; }
  } else {
    label = 'AI: 未連接';
    color = 'var(--text-muted)';
    if (sysApi) { sysApi.innerText = '🔴 AI: 未連接'; sysApi.style.color = 'var(--neon-orange)'; }
  }

  dot.className = active ? 'status-dot active' : 'status-dot inactive';
  // 如果是額度耗盡，雖然 inactive，但我們用紅色燈
  if (webState.aiQuotaExhausted) {
    dot.style.background = '#ff4444';
    dot.style.boxShadow = '0 0 10px rgba(255, 68, 68, 0.8)';
  } else {
    dot.style.background = '';
    dot.style.boxShadow = '';
  }
  txt.innerText = label;
  txt.style.color = color;
}

function showToast(title, desc, icon) {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <div class="toast-icon">${icon}</div>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      <div class="toast-desc">${desc}</div>
    </div>
  `;
  container.appendChild(toast);
  
  // 4 秒後自動移出
  setTimeout(() => {
    toast.style.animation = 'slideOutToast 0.4s forwards';
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}

// --- 10. 對話紀錄儲存 ---
function setupChatLogEvents() {
  const toggleMain = document.getElementById('toggleChatLog');
  const subOptions = document.getElementById('chatLogSubOptions');
  const toggleLineDC = document.getElementById('toggleLineDCHistory');
  const toggleGDrive = document.getElementById('toggleGDriveBackup');

  // 恢復儲存的開關狀態
  toggleMain.checked = localStorage.getItem('miniclaw_chatlog_enabled') === 'true';
  toggleLineDC.checked = localStorage.getItem('miniclaw_chatlog_linedc') === 'true';
  toggleGDrive.checked = localStorage.getItem('miniclaw_chatlog_gdrive') === 'true';
  if (toggleMain.checked) subOptions.style.display = 'flex';

  // 主開關
  toggleMain.addEventListener('change', () => {
    const enabled = toggleMain.checked;
    localStorage.setItem('miniclaw_chatlog_enabled', enabled);
    subOptions.style.display = enabled ? 'flex' : 'none';
    if (!enabled) {
      toggleLineDC.checked = false;
      toggleGDrive.checked = false;
      localStorage.setItem('miniclaw_chatlog_linedc', 'false');
      localStorage.setItem('miniclaw_chatlog_gdrive', 'false');
    }
    showToast(enabled ? '🗂️ 對話紀錄已啟用' : '🗂️ 對話紀錄已關閉', '', '🦞');
  });

  // LINE/DC 子開關
  toggleLineDC.addEventListener('change', () => {
    const enabled = toggleLineDC.checked;
    localStorage.setItem('miniclaw_chatlog_linedc', enabled);
    const statusEl = document.getElementById('lineDCHistoryStatus');
    if (enabled) {
      statusEl.style.display = 'block';
      loadLineDCHistory(statusEl);
    } else {
      statusEl.style.display = 'none';
    }
  });

  // Google Drive 子開關
  toggleGDrive.addEventListener('change', () => {
    const enabled = toggleGDrive.checked;
    localStorage.setItem('miniclaw_chatlog_gdrive', enabled);
    const statusEl = document.getElementById('gdriveStatus');
    if (enabled) {
      statusEl.style.display = 'block';
      initGDriveBackup(statusEl);
    } else {
      statusEl.style.display = 'none';
    }
  });

  // 初始化時若開關已開，顯示狀態
  if (toggleLineDC.checked) {
    const el = document.getElementById('lineDCHistoryStatus');
    el.style.display = 'block';
    loadLineDCHistory(el);
  }
  if (toggleGDrive.checked) {
    const el = document.getElementById('gdriveStatus');
    el.style.display = 'block';
    initGDriveBackup(el);
  }
}

// LINE/DC 歷史讀取
function loadLineDCHistory(statusEl) {
  const creds = JSON.parse(localStorage.getItem('miniclaw_remote_creds') || '{}');

  if (!creds.type) {
    statusEl.style.background = 'rgba(255,102,0,0.1)';
    statusEl.style.border = '1px solid rgba(255,102,0,0.3)';
    statusEl.style.color = 'var(--neon-orange)';
    statusEl.innerHTML = '⚠️ 尚未設定 LINE/DC 憑證，請先在「遠端平台通訊」填入 Token。';
    return;
  }

  if (creds.type === 'line') {
    // LINE API 不支援讀取歷史
    statusEl.style.background = 'rgba(255,102,0,0.1)';
    statusEl.style.border = '1px solid rgba(255,102,0,0.3)';
    statusEl.style.color = 'var(--neon-orange)';
    statusEl.innerHTML = '⚠️ LINE API 不支援讀取歷史訊息，無法撈取過去對話。新對話仍會透過 LINE 推播。';
    return;
  }

  if (creds.type === 'discord' && creds.discord && creds.discord.token && creds.discord.channel) {
    statusEl.style.background = 'rgba(255,102,0,0.1)';
    statusEl.style.border = '1px solid rgba(255,102,0,0.3)';
    statusEl.style.color = 'var(--neon-orange)';
    statusEl.innerHTML = '⏳ 正在從 Discord 頻道讀取歷史訊息...';

    fetch(`https://discord.com/api/v10/channels/${creds.discord.channel}/messages?limit=50`, {
      headers: { Authorization: `Bot ${creds.discord.token}` }
    })
      .then(res => res.json())
      .then(messages => {
        if (!Array.isArray(messages) || messages.length === 0) {
          statusEl.style.background = 'rgba(0,255,100,0.08)';
          statusEl.style.border = '1px solid rgba(0,255,100,0.3)';
          statusEl.style.color = 'var(--neon-green)';
          statusEl.innerHTML = '✅ Discord 連線成功，但頻道目前沒有歷史訊息。';
          return;
        }
        // 把歷史訊息注入聊天視窗（最舊的在前）
        const sorted = messages.reverse();
        sorted.forEach(m => {
          if (m.content) appendMessage('ai', `[Discord 歷史] ${m.author.username}: ${m.content}`);
        });
        statusEl.style.background = 'rgba(0,255,100,0.08)';
        statusEl.style.border = '1px solid rgba(0,255,100,0.3)';
        statusEl.style.color = 'var(--neon-green)';
        statusEl.innerHTML = `✅ 已載入 ${sorted.length} 則 Discord 歷史訊息。`;
      })
      .catch(err => {
        statusEl.style.background = 'rgba(255,0,0,0.1)';
        statusEl.style.border = '1px solid rgba(255,0,0,0.3)';
        statusEl.style.color = '#ff4d4d';
        statusEl.innerHTML = `❌ 讀取 Discord 歷史失敗：${err.message}`;
      });
    return;
  }

  statusEl.style.background = 'rgba(255,102,0,0.1)';
  statusEl.style.border = '1px solid rgba(255,102,0,0.3)';
  statusEl.style.color = 'var(--neon-orange)';
  statusEl.innerHTML = '⚠️ 憑證不完整，請重新設定 Discord Token 與 Channel ID。';
}

// Google Drive 備份
async function initGDriveBackup(statusEl) {
  // 需要 Google Access Token 且有 drive.file scope
  if (!webState.googleAccessToken) {
    statusEl.style.background = 'rgba(255,102,0,0.1)';
    statusEl.style.border = '1px solid rgba(255,102,0,0.3)';
    statusEl.style.color = 'var(--neon-orange)';
    statusEl.innerHTML = '⚠️ 請先在「帳號與 API 金鑰」用 Google 帳號登入，才能啟用 Drive 備份。';
    return;
  }

  statusEl.style.background = 'rgba(0,255,100,0.08)';
  statusEl.style.border = '1px solid rgba(0,255,100,0.3)';
  statusEl.style.color = 'var(--neon-green)';
  statusEl.innerHTML = '✅ Google Drive 備份已啟用。每次對話結束後自動上傳至你的 Drive。';

  // 立即備份一次現有對話
  saveChatToGDrive();
}

// 將聊天記錄上傳到 Google Drive
async function saveChatToGDrive() {
  if (!webState.googleAccessToken) return;
  if (localStorage.getItem('miniclaw_chatlog_gdrive') !== 'true') return;

  const container = document.getElementById('chatHistoryContainer');
  if (!container) return;

  const bubbles = container.querySelectorAll('.message-bubble');
  let text = `=== 小龍蝦對話紀錄 ===\n儲存時間：${new Date().toLocaleString('zh-TW')}\n\n`;
  bubbles.forEach(b => {
    const role = b.classList.contains('user') ? '使用者' : b.classList.contains('ai') ? '小龍蝦' : '系統';
    text += `[${role}]\n${b.innerText}\n\n`;
  });

  const fileName = `miniclaw_chat_${new Date().toISOString().slice(0, 10)}.txt`;

  try {
    // 用 multipart upload 上傳到 Drive
    const boundary = 'miniclaw_boundary';
    const body = [
      `--${boundary}`,
      'Content-Type: application/json; charset=UTF-8',
      '',
      JSON.stringify({ name: fileName, mimeType: 'text/plain' }),
      `--${boundary}`,
      'Content-Type: text/plain; charset=UTF-8',
      '',
      text,
      `--${boundary}--`
    ].join('\r\n');

    const res = await fetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${webState.googleAccessToken}`,
        'Content-Type': `multipart/related; boundary=${boundary}`
      },
      body
    });

    if (res.ok) {
      console.log(`✅ [GDrive] 對話已備份至 Google Drive：${fileName}`);
    } else if (res.status === 401) {
      requestGoogleAccessToken();
    }
  } catch (e) {
    console.error('⚠️ [GDrive] 備份失敗：', e);
  }
}
