"""
Miniclaw 示範腳本：桌面建立資料夾（圖案比對版）
=================================================
用 pyautogui.locateOnScreen() 圖案比對取代 OCR，速度更快
支援 Win10 / Win11 兩種右鍵選單

範本檔（放在同目錄）：
  template_xinjian.png  ← 右鍵選單「新增」那一行
  template_folder.png   ← 子選單「資料夾」那一行

流程：
  1. Win+D 跳桌面
  2. 確認資料夾是否已存在
  3. 截圖找空白區域
  4. 右鍵點空白處
  5. 圖案比對找「新增」→ 移過去等子選單
  6. 圖案比對找「資料夾」→ 點擊
  7. 貼名稱 → Enter
  8. 確認建立成功
"""

import os, time, threading
import tkinter as tk
from tkinter import scrolledtext
import pyautogui
from PIL import ImageGrab

TARGET_FOLDER_NAME = "我的第一個資料夾"
pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.2

stop_flag   = threading.Event()
task_region = None

# 範本路徑（../templates/）
_DIR        = os.path.dirname(os.path.abspath(__file__))
_TPL_DIR    = os.path.join(_DIR, "..", "templates")
TPL_XINJIAN = os.path.join(_TPL_DIR, "template_xinjian.png")
TPL_FOLDER  = os.path.join(_TPL_DIR, "template_folder.png")


# ══════════════════════════════════════════════════════
#  工具函數
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
    """
    用圖案比對找範本，回傳螢幕絕對座標 (cx, cy) 或 None
    region: (x, y, w, h) 限制搜尋範圍
    """
    try:
        loc = pyautogui.locateOnScreen(
            tpl_path,
            confidence=confidence,
            region=region  # None = 全螢幕
        )
        if loc:
            return pyautogui.center(loc)
    except Exception:
        pass
    return None


def locate_retry(tpl_path, log_fn, label="", timeout=5.0, confidence=0.7, region=None):
    """持續重試圖案比對直到找到或超時"""
    deadline = time.time() + timeout
    attempt = 0
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


def find_empty_spot(img, offset=(0,0)):
    """找桌面空白區域（顏色最均勻的候選點）"""
    w, h = img.size
    candidates = [
        (int(w*0.7), int(h*0.4)),
        (int(w*0.6), int(h*0.5)),
        (int(w*0.8), int(h*0.3)),
        (int(w*0.5), int(h*0.6)),
    ]
    pixels = img.load()
    best = candidates[0]
    best_score = float('inf')
    for cx, cy in candidates:
        colors = []
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                px, py = min(max(cx+dx,0),w-1), min(max(cy+dy,0),h-1)
                colors.append(pixels[px,py][:3])
        avg = [sum(c[i] for c in colors)/len(colors) for i in range(3)]
        var = sum(sum((c[i]-avg[i])**2 for i in range(3)) for c in colors)
        if var < best_score:
            best_score = var
            best = (cx, cy)
    return (best[0]+offset[0], best[1]+offset[1])


def get_desktop_path():
    up = os.environ.get("USERPROFILE","")
    for p in [os.path.join(up,"Desktop"), os.path.join(up,"OneDrive","桌面"),
              os.path.join(up,"OneDrive","Desktop"), os.path.join(up,"桌面")]:
        if os.path.exists(p): return p
    return os.path.join(up,"Desktop")


# ══════════════════════════════════════════════════════
#  主任務
# ══════════════════════════════════════════════════════

def run_task(w):
    stop_flag.clear()
    log("="*40, w)
    log("▶ 任務開始", w)

    try:
        # ── Step 1：跳桌面 ──
        log("[1] Win+D 跳桌面...", w)
        pyautogui.hotkey("win","d")
        time.sleep(1.2)
        if stop_flag.is_set(): return

        # ── Step 2：確認資料夾是否已存在 ──
        desktop = get_desktop_path()
        target = os.path.join(desktop, TARGET_FOLDER_NAME)
        if os.path.isdir(target):
            log(f"[2] ✅ 「{TARGET_FOLDER_NAME}」已存在，不需新增", w)
            log("\n任務完成 ✓", w)
            return
        log(f"[2] ❌ 「{TARGET_FOLDER_NAME}」不存在，開始建立", w)
        if stop_flag.is_set(): return

        # ── Step 3：截圖找空白處 ──
        log("[3] 截圖找桌面空白區域...", w)
        img, offset = screenshot(task_region)
        click_x, click_y = find_empty_spot(img, offset)
        log(f"    空白點：({click_x}, {click_y})", w)
        if stop_flag.is_set(): return

        # ── Step 4：右鍵，直接進 OCR 偵測（不用 screen_changed）──
        log("[4] 右鍵點擊空白處...", w)
        pyautogui.click(click_x, click_y)   # 先點確保桌面焦點
        time.sleep(0.4)
        pyautogui.rightClick(click_x, click_y)
        log("    右鍵已點，等待選單...", w)
        time.sleep(0.3)
        if stop_flag.is_set(): return

        # ── Step 5：圖案比對找「新增」──
        log("[5] 圖案比對找「新增」...", w)
        pos_new = locate_retry(TPL_XINJIAN, lambda m: log(m,w),
                               label="新增", timeout=5.0, confidence=0.7)
        if not pos_new:
            log("    ❌ 找不到「新增」範本，請重新裁切 template_xinjian.png", w)
            return
        log(f"    點擊「新增」{pos_new}，等子選單展開...", w)
        pyautogui.click(pos_new[0], pos_new[1])
        time.sleep(0.5)
        if stop_flag.is_set(): return

        # ── Step 6：圖案比對找「資料夾」點擊 ──
        log("[6] 圖案比對找「資料夾」...", w)
        pos_folder = locate_retry(TPL_FOLDER, lambda m: log(m,w),
                                  label="資料夾", timeout=5.0, confidence=0.7)
        if not pos_folder:
            log("    ❌ 找不到「資料夾」範本，請重新裁切 template_folder.png", w)
            return
        log(f"    點擊「資料夾」{pos_folder}", w)
        pyautogui.click(pos_folder[0], pos_folder[1])
        time.sleep(0.8)
        if stop_flag.is_set(): return

        # ── Step 8：截圖確認輸入框，貼名稱 ──
        log("[8] 確認輸入框並輸入名稱...", w)
        pyautogui.hotkey("ctrl","a")
        time.sleep(0.15)
        try:
            import pyperclip
            pyperclip.copy(TARGET_FOLDER_NAME)
            pyautogui.hotkey("ctrl","v")
        except ImportError:
            pyautogui.write(TARGET_FOLDER_NAME, interval=0.05)
        time.sleep(0.3)
        pyautogui.press("enter")
        time.sleep(0.8)
        if stop_flag.is_set(): return

        # ── Step 9：確認結果 ──
        log("[9] 確認資料夾是否建立成功...", w)
        if os.path.isdir(target):
            log(f"\n✅ 任務完成！「{TARGET_FOLDER_NAME}」已建立", w)
            log(f"   路徑：{target}", w)
            log("   桌面雙擊即可開啟", w)
        else:
            log("    ⚠️ 檔案系統未偵測到，可能名稱不同或建立中", w)
            log("    請手動確認桌面", w)

    except Exception as e:
        log(f"⚠️ 發生錯誤：{e}", w)
    finally:
        stop_flag.clear()


# ══════════════════════════════════════════════════════
#  範圍選取
# ══════════════════════════════════════════════════════

class RegionSelector:
    def __init__(self, callback):
        self.callback = callback
        self.start_x = self.start_y = 0
        self.rect = None
        self.root = tk.Toplevel()
        self.root.attributes("-fullscreen",True)
        self.root.attributes("-alpha",0.3)
        self.root.attributes("-topmost",True)
        self.root.configure(bg="black")
        self.canvas = tk.Canvas(self.root, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        tk.Label(self.canvas, text="拖曳選取範圍  |  ESC 取消",
                 fg="white", bg="black", font=("Arial",16,"bold")
                 ).place(relx=0.5, rely=0.05, anchor="center")
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
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
        x1=min(self.start_x,e.x); y1=min(self.start_y,e.y)
        rw=abs(e.x-self.start_x); rh=abs(e.y-self.start_y)
        self.root.destroy()
        if rw>10 and rh>10: self.callback(x1,y1,rw,rh)


# ══════════════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════════════

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Miniclaw 任務控制台")
        self.root.geometry("480x420")
        self.root.resizable(False, False)
        self.root.configure(bg="#0d0d1a")
        self.root.attributes("-topmost", True)
        self.region_var = tk.StringVar(value="🖥  操作範圍：全螢幕")
        self._build_ui()
        self.task_thread = None

    def _build_ui(self):
        tk.Label(self.root, text="🦞 Miniclaw 任務控制台",
                 fg="#ff6600", bg="#0d0d1a",
                 font=("Arial",14,"bold")).pack(pady=(14,4))
        tk.Label(self.root, textvariable=self.region_var,
                 fg="#00f0ff", bg="#0d0d1a",
                 font=("Consolas",9)).pack(pady=(0,8))

        bf = tk.Frame(self.root, bg="#0d0d1a")
        bf.pack(pady=4)
        cfg = dict(font=("Arial",11,"bold"), width=9, relief="flat", cursor="hand2", pady=6)

        self.btn_start = tk.Button(bf, text="▶  開始",
            bg="#1a6e2e", fg="white", activebackground="#27a844",
            command=self.start_task, **cfg)
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_stop = tk.Button(bf, text="■  停止",
            bg="#6e1a1a", fg="white", activebackground="#a82727",
            command=self.stop_task, state="disabled", **cfg)
        self.btn_stop.grid(row=0, column=1, padx=5)

        tk.Button(bf, text="🔲 選取範圍",
            bg="#1a3a6e", fg="white", activebackground="#2756a8",
            command=self.pick_region, **cfg).grid(row=0, column=2, padx=5)

        tk.Button(bf, text="🖥  全範圍",
            bg="#2a2a3a", fg="#aaaaaa", activebackground="#3a3a5a",
            command=self.reset_region, **cfg).grid(row=0, column=3, padx=5)

        tk.Button(bf, text="✕  關閉",
            bg="#2a2a2a", fg="#888888", activebackground="#444444",
            command=self.root.destroy, **cfg).grid(row=0, column=4, padx=5)

        tk.Label(self.root, text="執行日誌",
                 fg="#666688", bg="#0d0d1a", font=("Arial",9)
                 ).pack(anchor="w", padx=16, pady=(10,2))

        self.log_box = scrolledtext.ScrolledText(
            self.root, height=14, state="disabled",
            bg="#07070f", fg="#c8ffc8",
            font=("Consolas",9), relief="flat", wrap=tk.WORD, padx=8, pady=6)
        self.log_box.pack(fill=tk.BOTH, padx=14, pady=(0,14))
        log("準備就緒。按「▶ 開始」執行任務。", self.log_box)

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
        log("■ 停止指令已送出...", self.log_box)
        self.btn_stop.config(state="disabled")

    def pick_region(self):
        self.root.iconify()
        time.sleep(0.3)
        def on_sel(x,y,rw,rh):
            global task_region
            task_region=(x,y,rw,rh)
            self.region_var.set(f"🔲 操作範圍：({x},{y}) {rw}×{rh}px")
            log(f"[範圍] ({x},{y}) {rw}×{rh}px", self.log_box)
            self.root.deiconify()
        RegionSelector(on_sel)

    def reset_region(self):
        global task_region
        task_region=None
        self.region_var.set("🖥  操作範圍：全螢幕")
        log("[範圍] 已重置為全螢幕", self.log_box)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
