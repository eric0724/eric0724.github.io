#!/bin/bash
# Miniclaw Executor - Unix/Mac/Android(Termux) 全自動啟動腳本
# 對齊 openminiclaw.bat 功能：自動安裝依賴、啟動 ngrok、開瀏覽器

ROOT="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$ROOT/app"
cd "$APP_DIR"

echo "============================================"
echo " 小龍蝦執行器啟動中..."
echo "============================================"

# --- 偵測平台 ---
if [ -n "$TERMUX_VERSION" ] || echo "$PREFIX" | grep -q "com.termux"; then
  PLATFORM="android"
else
  case "$(uname -s)" in
    Darwin) PLATFORM="mac" ;;
    Linux)  PLATFORM="linux" ;;
    *)      PLATFORM="linux" ;;
  esac
fi
echo "[OK] 偵測到平台：$PLATFORM"

# --- [1/5] 檢查 Node.js ---
echo "[1/5] 檢查 Node.js 環境..."
if ! command -v node &> /dev/null; then
  echo "[!] 未偵測到 Node.js，正在自動安裝..."
  if [ "$PLATFORM" = "android" ]; then
    pkg install nodejs -y
  elif [ "$PLATFORM" = "mac" ]; then
    if command -v brew &> /dev/null; then
      brew install node
    else
      echo "[X] 請先安裝 Homebrew：https://brew.sh"
      read -p "按 Enter 繼續..."
      exit 1
    fi
  else
    sudo apt-get update && sudo apt-get install -y nodejs npm
  fi
fi
echo "[OK] Node.js $(node --version)"

# --- [2/5] 安裝依賴 ---
if [ ! -d "node_modules" ]; then
  echo "[2/5] 首次執行，安裝依賴套件..."
  npm install
fi
echo "[OK] 依賴套件就緒"

# --- [3/5] 啟動 server.js（背景） ---
echo "[3/5] 啟動小龍蝦伺服器（背景）..."
node server.js &
SERVER_PID=$!
sleep 2
echo "[OK] 伺服器已啟動 (PID: $SERVER_PID)"

# --- [4/5] 檢查並啟動 ngrok ---
echo "[4/5] 檢查 ngrok..."
if ! command -v ngrok &> /dev/null; then
  echo "[!] 未偵測到 ngrok，正在自動安裝..."
  if [ "$PLATFORM" = "android" ]; then
    pkg install ngrok -y
  elif [ "$PLATFORM" = "mac" ]; then
    brew install ngrok/ngrok/ngrok
  else
    curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc > /dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
    sudo apt-get update && sudo apt-get install ngrok -y
  fi
fi
echo "[OK] ngrok 已就緒"

# --- 檢查 ngrok authtoken ---
if ! ngrok config check > /dev/null 2>&1; then
  echo ""
  echo "============================================"
  echo " ngrok authtoken 未設定"
  echo " 請前往取得 authtoken："
  echo " https://dashboard.ngrok.com/get-started/your-authtoken"
  echo "============================================"
  echo ""
  if [ "$PLATFORM" = "android" ]; then
    termux-open-url "https://dashboard.ngrok.com/get-started/your-authtoken" 2>/dev/null
  elif [ "$PLATFORM" = "mac" ]; then
    open "https://dashboard.ngrok.com/get-started/your-authtoken"
  else
    xdg-open "https://dashboard.ngrok.com/get-started/your-authtoken" 2>/dev/null
  fi
  echo -n "請貼上你的 authtoken: "
  read -r USER_TOKEN
  USER_TOKEN=$(echo "$USER_TOKEN" | tr -d '[:space:]')
  if [ -z "$USER_TOKEN" ]; then
    echo "[X] 未輸入 token，請重新執行。"
    kill $SERVER_PID 2>/dev/null
    exit 1
  fi
  ngrok config add-authtoken "$USER_TOKEN"
  if [ $? -ne 0 ]; then
    echo "[X] authtoken 設定失敗，請確認 token 是否正確。"
    kill $SERVER_PID 2>/dev/null
    exit 1
  fi
  echo "[OK] authtoken 設定完成"
fi
echo "[OK] ngrok authtoken OK"
ngrok http 3000 &
NGROK_PID=$!
echo "等待 ngrok 取得公開網址（5秒）..."
sleep 5

# --- 取得 ngrok 網址 ---
NGROK_URL=$(node -e "
const h=require('http');
h.get('http://127.0.0.1:4040/api/tunnels',function(r){
  var d='';
  r.on('data',function(c){d+=c;});
  r.on('end',function(){
    try{
      var t=JSON.parse(d).tunnels.find(function(x){return x.proto==='https';});
      console.log(t?t.public_url:'');
    }catch(e){console.log('');}
  });
}).on('error',function(){console.log('');});
" 2>/dev/null)

# --- 開瀏覽器 ---
OPEN_URL="https://eric0724.github.io/agent/miniclaw/miniclaw-web/index.html"
if [ -n "$NGROK_URL" ]; then
  echo "[OK] ngrok 網址：$NGROK_URL"
  OPEN_URL="${OPEN_URL}?ngrok=${NGROK_URL}"
else
  echo "[!] 無法自動取得 ngrok 網址，請手動複製 ngrok 視窗中的 https:// 網址貼到網頁 Step 2。"
fi

echo "正在開啟小龍蝦網頁..."
if [ "$PLATFORM" = "android" ]; then
  termux-open-url "$OPEN_URL" 2>/dev/null || echo "[!] 請手動開啟：$OPEN_URL"
elif [ "$PLATFORM" = "mac" ]; then
  open "$OPEN_URL"
else
  xdg-open "$OPEN_URL" 2>/dev/null || echo "[!] 請手動開啟：$OPEN_URL"
fi

echo ""
echo "============================================"
echo " 小龍蝦已在背景執行中！"
echo " 網頁已自動開啟，請在瀏覽器完成設定。"
echo "============================================"
echo ""
echo "按 Enter 停止所有服務並關閉，或 Ctrl+C 直接關閉（服務繼續在背景跑）"
read -r

echo "正在停止所有服務..."
kill $SERVER_PID 2>/dev/null
kill $NGROK_PID 2>/dev/null
echo "[OK] 所有服務已停止。"
