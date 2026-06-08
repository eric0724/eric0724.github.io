# Miniclaw 遊戲助手 — AI 提示指南

> 使用者說完遊戲內容和玩法後，Miniclaw 依照此文件一次產出所有檔案。

---

## 完整流程（兩種方式）

### 方式 A：上傳影片（全自動，推薦）
```
1. 錄一段遊戲操作影片（30秒~2分鐘即可）
2. 執行 extract_templates.py 自動裁切範本
3. 執行 run_task.bat 開始自動化
```
```
py scripts/extract_templates.py --video 你的影片.mp4 --task "每隔3秒點攻擊按鈕"
```
腳本會自動：切幀 → Gemini 分析 → 裁切範本存到 templates/ → 印出腳本片段

### 方式 B：手動截圖（不需 Gemini API）
```
1. 對遊戲畫面截圖，手動裁切要偵測的元素
2. 存到 templates/ 資料夾
3. 執行 run_task.bat
```

---

## 前置需求（告訴使用者先準備好）

```
1. 安裝 Python 3.10+（https://python.org，安裝時勾選 Add to PATH）
2. 安裝依賴：在 test-lab/ 資料夾開終端執行
   pip install pyautogui Pillow pyperclip opencv-python
3. 準備截圖工具（Windows 內建 Snipping Tool 即可）
4. 把遊戲開到你要自動化的畫面，截圖裁切出要偵測的元素
   存到 test-lab/templates/ 資料夾，檔名自訂（例如 template_attack_btn.png）
```

---

## Miniclaw 收到遊戲說明後的流程

### Step 1：詢問使用者
```
請問：
1. 你的螢幕解析度？（例如 1920x1080）
2. 要自動化的具體任務是什麼？（例如：每隔 3 秒點一次攻擊按鈕）
3. 請截一張遊戲畫面傳給我，我幫你分析要偵測哪些元素
```

### Step 2：分析截圖，產出元素清單
收到截圖後，用以下提示詞分析：

```
你是遊戲自動化助手。使用者傳來遊戲截圖，請分析畫面中需要偵測或點擊的元素。

回傳格式（JSON）：
{
  "elements": [
    {
      "name": "變數名稱（英文，例如 attack_btn）",
      "description": "外觀描述（顏色、形狀、文字）",
      "action": "click / hover / wait / read",
      "timing": "觸發時機（例如：每3秒 / 出現時立刻 / 血量低於30%）",
      "template_file": "建議的範本檔名（例如 template_attack_btn.png）"
    }
  ],
  "task_flow": [
    "Step 1: 說明",
    "Step 2: 說明"
  ]
}
```

### Step 3：產出腳本
根據 JSON 結果，填入下方模板的 `# ── 主任務 ──` 區塊，一次產出完整腳本。

---

## 腳本模板（完整可用版）

```python
"""
<遊戲名稱> 自動化腳本
========================
任務：<使用者描述的任務>
範本圖片放在：../templates/
執行方式：雙擊 run_task.bat
"""

import os, time, threading
import tkinter as tk
from tkinter import scrolledtext
import pyautogui
from PIL import ImageGrab

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.2

stop_flag   = threading.Event()
task_region = None

_DIR     = os.path.dirname(os.path.abspath(__file__))
_TPL_DIR = os.path.join(_DIR, "..", "templates")

# ── 範本路徑（依遊戲修改）──
# TPL_ATTACK = os.path.join(_TPL_DIR, "template_attack_btn.png")
# TPL_HEAL   = os.path.join(_TPL_DIR, "template_heal_btn.png")


# ══════════════════════════════════════════════════════
#  工具函數（固定，不需修改）
# ══════════════════════════════════════════════════════

def log(msg, w):
    w.configure(state="normal")
    w.insert(tk.END, msg + "\n")
    w.see(tk.END)
    w.configure(state="disabled")

def screenshot(region=None):
    if region:
        x, y, rw, rh = region
        return ImageGrab.grab(bbox=(x, y, x+rw, y+rh)), (x, y)
    return pyautogui.screenshot(), (0, 0)

def locate_template(tpl_path, confidence=0.7, region=None):
    """圖案比對，回傳螢幕絕對座標 (cx, cy) 或 None"""
    try:
        loc = pyautogui.locateOnScreen(tpl_path, confidence=confidence, region=region)
        if loc:
            return pyautogui.center(loc)
    except Exception:
        pass
    return None

def locate_retry(tpl_path, log_fn, label="", timeout=5.0, confidence=0.7, region=None):
    """持續重試圖案比對直到找到或超時"""
    deadline = time.time() + timeout
    attempt  = 0
    while time.time() < deadline:
        if stop_flag.is_set(): return None
        attempt += 1
        pos = locate_template(tpl_path, confidence=confidence, region=region)
        if pos:
            log_fn(f"    找到「{label}」{pos}（第{attempt}次）")
            return pos
        log_fn(f"    第{attempt}次未找到「{label}」，繼續...")
        time.sleep(0.25)
    return None


# ══════════════════════════════════════════════════════
#  主任務（依遊戲修改這裡）
# ══════════════════════════════════════════════════════

def run_task(w):
    stop_flag.clear()
    log("="*40, w)
    log("▶ 任務開始", w)

    try:
        while not stop_flag.is_set():

            # ── 範例：找到攻擊按鈕就點擊 ──
            # pos = locate_retry(TPL_ATTACK, lambda m: log(m,w),
            #                    label="攻擊", timeout=3.0, confidence=0.7)
            # if pos:
            #     pyautogui.click(pos[0], pos[1])
            #     log(f"    點擊攻擊 {pos}", w)
            #     time.sleep(3.0)   # 冷卻時間
            # else:
            #     log("    未找到攻擊按鈕，等待...", w)
            #     time.sleep(1.0)

            pass  # 刪掉這行，填入上方範例

        log("■ 任務已停止", w)

    except Exception as e:
        log(f"⚠️ 錯誤：{e}", w)
    finally:
        stop_flag.clear()


# ══════════════════════════════════════════════════════
#  GUI（固定，不需修改）
# ══════════════════════════════════════════════════════

class RegionSelector:
    def __init__(self, callback):
        self.callback = callback
        self.start_x = self.start_y = 0
        self.rect = None
        self.root = tk.Toplevel()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")
        self.canvas = tk.Canvas(self.root, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        tk.Label(self.canvas, text="Drag to select region  |  ESC to cancel",
                 fg="white", bg="black", font=("Arial", 16, "bold")
                 ).place(relx=0.5, rely=0.05, anchor="center")
        self.canvas.bind("<ButtonPress-1>",   self.on_press)
        self.canvas.bind("<B1-Motion>",       self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def on_press(self, e):
        self.start_x, self.start_y = e.x, e.y
        if self.rect: self.canvas.delete(self.rect)

    def on_drag(self, e):
        if self.rect: self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, e.x, e.y,
            outline="#00ff88", width=2, fill="#00ff88", stipple="gray25")

    def on_release(self, e):
        x1 = min(self.start_x, e.x); y1 = min(self.start_y, e.y)
        rw = abs(e.x - self.start_x); rh = abs(e.y - self.start_y)
        self.root.destroy()
        if rw > 10 and rh > 10:
            self.callback(x1, y1, rw, rh)


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Miniclaw Task")
        self.root.geometry("480x420")
        self.root.resizable(False, False)
        self.root.configure(bg="#0d0d1a")
        self.root.attributes("-topmost", True)
        self.region_var = tk.StringVar(value="Screen: Full")
        self._build_ui()
        self.task_thread = None

    def _build_ui(self):
        tk.Label(self.root, text="Miniclaw Task",
                 fg="#ff6600", bg="#0d0d1a",
                 font=("Arial", 14, "bold")).pack(pady=(14, 4))
        tk.Label(self.root, textvariable=self.region_var,
                 fg="#00f0ff", bg="#0d0d1a",
                 font=("Consolas", 9)).pack(pady=(0, 8))

        bf  = tk.Frame(self.root, bg="#0d0d1a")
        bf.pack(pady=4)
        cfg = dict(font=("Arial", 11, "bold"), width=9, relief="flat", cursor="hand2", pady=6)

        self.btn_start = tk.Button(bf, text="Start",
            bg="#1a6e2e", fg="white", activebackground="#27a844",
            command=self.start_task, **cfg)
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_stop = tk.Button(bf, text="Stop",
            bg="#6e1a1a", fg="white", activebackground="#a82727",
            command=self.stop_task, state="disabled", **cfg)
        self.btn_stop.grid(row=0, column=1, padx=5)

        tk.Button(bf, text="Region",
            bg="#1a3a6e", fg="white", activebackground="#2756a8",
            command=self.pick_region, **cfg).grid(row=0, column=2, padx=5)

        tk.Button(bf, text="Full",
            bg="#2a2a3a", fg="#aaaaaa", activebackground="#3a3a5a",
            command=self.reset_region, **cfg).grid(row=0, column=3, padx=5)

        tk.Button(bf, text="Close",
            bg="#2a2a2a", fg="#888888", activebackground="#444444",
            command=self.root.destroy, **cfg).grid(row=0, column=4, padx=5)

        tk.Label(self.root, text="Log",
                 fg="#666688", bg="#0d0d1a",
                 font=("Arial", 9)).pack(anchor="w", padx=16, pady=(10, 2))

        self.log_box = scrolledtext.ScrolledText(
            self.root, height=14, state="disabled",
            bg="#07070f", fg="#c8ffc8",
            font=("Consolas", 9), relief="flat", wrap=tk.WORD, padx=8, pady=6)
        self.log_box.pack(fill=tk.BOTH, padx=14, pady=(0, 14))
        log("Ready. Press Start.", self.log_box)

    def start_task(self):
        if self.task_thread and self.task_thread.is_alive(): return
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.task_thread = threading.Thread(
            target=lambda: [run_task(self.log_box),
                            self.root.after(0, self._done)], daemon=True)
        self.task_thread.start()

    def _done(self):
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")

    def stop_task(self):
        stop_flag.set()
        log("Stop signal sent...", self.log_box)
        self.btn_stop.config(state="disabled")

    def pick_region(self):
        self.root.iconify()
        time.sleep(0.3)
        def on_sel(x, y, rw, rh):
            global task_region
            task_region = (x, y, rw, rh)
            self.region_var.set(f"Region: ({x},{y}) {rw}x{rh}px")
            log(f"[Region] ({x},{y}) {rw}x{rh}px", self.log_box)
            self.root.deiconify()
        RegionSelector(on_sel)

    def reset_region(self):
        global task_region
        task_region = None
        self.region_var.set("Screen: Full")
        log("[Region] Reset to full screen", self.log_box)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
```

---

## 校準模式（推薦流程）

### 為什麼需要校準？
- 圖案比對需要範本圖片，但不同電腦解析度/縮放比例不同
- 手動截圖容易截錯位置
- 校準模式讓 AI 自動找位置、自動截範本，使用者只需確認

### 校準流程（每個 UI 元素執行以下步驟）

```
Step A：AI 分析截圖，找到目標位置
Step B：滑鼠移開 → 截「正常狀態」範本（無 hover）
Step C：滑鼠移到目標 → 截「hover 狀態」範本
Step D：截全螢幕，問 AI「滑鼠停的位置是否正確？」
         → 不對就跳過，不執行點擊
Step E：確認正確 → 執行點擊
Step F：等待畫面變化 → 截全螢幕確認「點擊後是否出現預期畫面？」
Step G：兩種範本都存到 templates/，記錄座標到 calibration.json
```

### 之後執行（快速模式）
```
讀取 calibration.json 的座標
→ 用 locateOnScreen() 比對 normal + hover 兩種範本
→ 找到就點擊，不需要呼叫 AI
→ 點擊後仍截圖確認畫面變化
```

### 提示詞（給 Miniclaw 產出校準腳本用）

```
你是自動化腳本助手。使用者要校準一個 UI 自動化任務。

請為每個需要點擊的 UI 元素產出校準步驟，格式如下：

{
  "name": "元素英文名稱",
  "desc": "元素描述（給 GPT-4o 看的，要精確）",
  "region": [x1比例, y1比例, x2比例, y2比例],  // 0.0~1.0，只截相關區域
  "before_confirm": "點擊前確認：滑鼠停在這裡是否正確的描述",
  "after_confirm": "點擊後確認：畫面應該出現什麼",
  "action": "click 或 move"
}

注意事項：
1. region 要盡量小，只包含目標元素所在區域
2. desc 要精確描述外觀（顏色、形狀、文字）
3. before_confirm 要問「滑鼠停的位置對不對」
4. after_confirm 要描述點擊後畫面的明顯變化
5. 每個元素都要截兩種範本：正常狀態（滑鼠移開）和 hover 狀態（滑鼠停上去）
6. 點擊前後都要截圖確認，不確定就不點
```

### 已知問題

| 問題 | 解法 |
|------|------|
| hover 狀態截圖和正常狀態不同導致比對失敗 | 兩種都截，任一匹配就算找到 |
| GPT-4o 回傳座標是相對截圖的，不是螢幕絕對座標 | 截圖時記錄 offset，回傳座標加上 offset |
| 確認步驟用舊截圖（點擊前截的）判斷點擊後結果 | 每次確認都重新截圖 |
| 全螢幕截圖太大，GPT-4o 座標不準 | 只截相關區域（region 比例），縮小範圍 |

| # | 問題 | 解法 |
|---|------|------|
| 1 | Win11「新增」需要點擊才展開子選單，`moveTo` 無效 | 改用 `click()` 再等 0.5 秒 |
| 2 | OCR 每次約 2-3 秒，右鍵選單等不住就關掉 | 改用 `locateOnScreen()` 圖案比對，毫秒級 |
| 3 | `locateOnScreen` 沒裝 opencv 會報錯 | `pip install opencv-python` |
| 4 | 螢幕縮放 125%/150% 導致圖案比對失敗 | 先用 `confidence=0.7`，失敗降到 `0.6`；或重新截圖 |
| 5 | 桌面資料夾偵測不需要 OCR | 直接用 `os.path.isdir()` 讀檔案系統 |
| 6 | easyocr 依賴 torch（123MB），打包有 DLL 錯誤 | 完全移除，改用圖案比對 |
| 7 | PyInstaller 打包後找不到 `../templates/` | 改用 `.bat` 直接跑 py，不打包 |

---

## 範本圖片裁切建議

- 裁切目標元素，周圍留 5-10px 邊距
- 避免裁到會變動的背景（血條數字、計時器）
- 截圖和執行環境的解析度要一致
- 存成 PNG 放到 `templates/` 資料夾
