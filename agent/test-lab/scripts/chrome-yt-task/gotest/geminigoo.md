第一個window search 應該是一個放大鏡的圖示而已之後第二三張都沒有截圖到最左邊 在精準一些？

明白，再次比對影片與截圖畫面後發現確實有偏差（例如 win_search_lens 誤截成天氣、後面截圖位置過於靠右）。以下為你重新調整最精準的 UI 元素分析。
需要偵測或點擊的 UI 元素

元素一：win_search_icon

外觀描述： 工作列上正方形微凸的純放大鏡圖示（不含旁邊的天氣資訊）。

畫面位置： 螢幕最下方工作列靠左側（影片 0:05 處）。

建議的截圖時機： 影片第 5 秒，滑鼠尚未移至工作列前的乾淨狀態。

操作方式： 點擊。

元素二：chrome_app_btn

外觀描述： Windows 搜尋選單左側「最佳比對」中的 Google Chrome 橫條選項。

畫面位置： 搜尋選單的左上角核心區塊（影片 0:09 處）。

建議的截圖時機： 影片第 9 秒，輸入 "chrome" 後，左側跑出完整的 Chrome 應用程式按鈕。

操作方式： 點擊。

元素三：yahoo_search_bar

外觀描述： Chrome 開啟後的網址列或 Yahoo 頁面正中央橫向的白色輸入框（需靠左對齊輸入起點）。

畫面位置： 瀏覽器視窗中央偏上方（影片 0:15 處）。

建議的截圖時機： 影片第 15 秒，網頁載入後游標尚未點入的原始白色文字框。

操作方式： 點擊。

元素四：yahoo_yt_link

外觀描述： 搜尋結果最上方的藍色帶底線 "YouTube" 字樣。

畫面位置： Yahoo 搜尋結果頁面的左側本文區（影片 0:21 處）。

建議的截圖時機： 影片第 21 秒，搜尋頁面停止滾動且文字清晰呈現時。

操作方式： 點擊。

元素五：yt_search_bar

外觀描述： YouTube 網頁最上方，中間空白、右側帶有放大鏡按鈕的灰色長條搜尋列。

畫面位置： YouTube 頂端正中央（影片 0:28 處）。

建議的截圖時機： 影片第 28 秒，YouTube 首頁完全載入後的空白搜尋框。

操作方式： 點擊。

任務執行順序（Step by Step）

Step 1： 點擊 Windows 工作列上的純放大鏡搜尋圖示。

Step 2： 用鍵盤輸入 chrome。

Step 3： 精準點擊搜尋結果左側「最佳比對」中的 Google Chrome 應用程式。

Step 4： 瀏覽器開啟後，點擊 Yahoo 頁面中央偏左的白色搜尋框。

Step 5： 輸入 yt 並按下 Enter 鍵。

Step 6： 在結果頁面左側點擊藍色的 YouTube 連結進入網站。

Step 7： 等待 YouTube 首頁載入，點擊頂端中央的長條搜尋框。

Step 8： 輸入關鍵字 agent 並按下 Enter 鍵完成任務。

完整自動化腳本

以下為你把所有程式打出來，保持原本註解，並在這次精準調整修改處加上 //："""
Chrome 與 YouTube 自動化搜尋腳本
========================
任務：從 Windows 搜尋開啟 Chrome，透過搜尋進入 YouTube 並查詢 agent
偵測方式：pyautogui.locateOnScreen() 圖案比對
範本圖片放在：../templates/
"""

import os, time, threading
import tkinter as tk
from tkinter import scrolledtext
import pyautogui
from PIL import ImageGrab
import ctypes

# 強制讀取原始解析度，避免螢幕縮放導致圖案比對失效
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.2

stop_flag   = threading.Event()
task_region = None

_DIR     = os.path.dirname(os.path.abspath(__file__))
_TPL_DIR = os.path.join(_DIR, "..", "templates")

# ── 在這裡列出所有精準修正後的範本 ──
TPL_WIN_SEARCH   = os.path.join(_TPL_DIR, "template_win_search_lens.png") #** 修正為純放大鏡圖示
TPL_CHROME_APP   = os.path.join(_TPL_DIR, "template_chrome_app_left.png") #** 修正為搜尋選單左側最佳比對
TPL_YAHOO_BAR    = os.path.join(_TPL_DIR, "template_yahoo_bar_left.png") #** 修正為包含左側邊界的搜尋框
TPL_YAHOO_YT     = os.path.join(_TPL_DIR, "template_yahoo_yt_link.png") #** 搜尋結果藍字連結
TPL_YT_SEARCH    = os.path.join(_TPL_DIR, "template_yt_search_center.png") #** YT頂端中央搜尋框


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
    try:
        loc = pyautogui.locateOnScreen(tpl_path, confidence=confidence, region=region)
        if loc:
            return pyautogui.center(loc)
    except Exception:
        pass
    return None

def locate_retry(tpl_path, log_fn, label="", timeout=5.0, confidence=0.7, region=None):
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
#  主任務（依修正畫面微調等待）
# ══════════════════════════════════════════════════════

def run_task(w):
    stop_flag.clear()
    log("="*40, w)
    log("▶ 任務開始", w)

    try:
        # 加入循環控制控制整體流程
        while not stop_flag.is_set():
            # ── Step 1：點擊純放大鏡圖示 ── #**
            pos_search_icon = locate_retry(TPL_WIN_SEARCH, lambda m: log(m,w), label="Win純放大鏡", timeout=5.0) #**
            if not pos_search_icon:
                log("❌ 找不到 Win純放大鏡圖示", w); return
            pyautogui.click(pos_search_icon[0], pos_search_icon[1])
            time.sleep(1.0)

            # ── Step 2：輸入 chrome 並點擊左側最佳比對 ── #**
            pyautogui.write("chrome")
            time.sleep(1.5) #** 多留時間給搜尋選單跑出
            pos_chrome_app = locate_retry(TPL_CHROME_APP, lambda m: log(m,w), label="Chrome左側最佳比對", timeout=5.0) #**
            if not pos_chrome_app:
                log("❌ 找不到 Chrome 應用程式項目", w); return
            pyautogui.click(pos_chrome_app[0], pos_chrome_app[1])
            time.sleep(4.0) # 等待瀏覽器與 Yahoo 首頁載入 //**

            # ── Step 3：網頁中央偏左搜尋框輸入 yt ── #**
            pos_yahoo_bar = locate_retry(TPL_YAHOO_BAR, lambda m: log(m,w), label="Yahoo偏左搜尋框", timeout=6.0) #**
            if not pos_yahoo_bar:
                log("❌ 找不到 Yahoo 網頁搜尋列", w); return
            pyautogui.click(pos_yahoo_bar[0], pos_yahoo_bar[1])
            pyautogui.write("yt")
            pyautogui.press("enter")
            time.sleep(3.5) # 等待搜尋結果載入 //**

            # ── Step 4：點擊 YouTube 藍字連結 ── #**
            pos_yahoo_yt = locate_retry(TPL_YAHOO_YT, lambda m: log(m,w), label="Yahoo結果藍字連結", timeout=6.0) #**
            if not pos_yahoo_yt:
                log("❌ 找不到 YouTube 搜尋結果連結", w); return
            pyautogui.click(pos_yahoo_yt[0], pos_yahoo_yt[1])
            time.sleep(6.0) # 等待 YouTube 頁面完全載入 //**

            # ── Step 5：在 YT 搜尋列輸入 agent ── #**
            pos_yt_search = locate_retry(TPL_YT_SEARCH, lambda m: log(m,w), label="YT中央搜尋列", timeout=10.0) #**
            if not pos_yt_search:
                log("❌ 找不到 YouTube 搜尋列", w); return
            pyautogui.click(pos_yt_search[0], pos_yt_search[1])
            time.sleep(0.5)
            pyautogui.write("agent")
            pyautogui.press("enter")
            
            log("✅ 任務完成", w)
            break # 任務完成，跳出循環

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

        self.log_box = tk.scrolledtext.ScrolledText(
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
    App().run() #**