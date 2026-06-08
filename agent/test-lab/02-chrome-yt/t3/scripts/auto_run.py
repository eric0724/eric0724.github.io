"""
auto_run.py — 自動執行：開啟 YouTube
控制視窗：停止按鈕置頂，自動避開點擊座標
"""

import pyautogui
import threading
import time
import ctypes
import tkinter as tk

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2

# ══════════════════════════════════════════════
#  步驟定義（從 recorder 產出的座標）
# ══════════════════════════════════════════════
STEPS = [
    ("click",    (396, 747), "點擊 Windows 查詢列"),
    ("write",    "google",   "輸入 google"),
    ("click",    (331, 223), "點擊搜尋建議"),
    ("click",    (160, 645), "點擊 Google 搜尋結果"),
    ("click",    (343, 76),  "點擊網址列"),
    ("hotkey",   ("ctrl","a"), "全選網址"),
    ("write",    "yt",       "輸入 yt"),
    ("press",    "enter",    "按 Enter"),
    ("press",    "enter",    "按 Enter"),
    ("click",    (148, 318), "點擊 YouTube 連結"),
    ("click",    (865, 67),  "點擊最終目標"),
]

WAIT = {  # 每個步驟後的等待秒數
    0: 0.8,   # 查詢列開啟
    2: 1.5,   # 搜尋建議出現
    3: 2.0,   # Google 載入
    4: 0.3,
    7: 0.4,
    8: 2.5,   # YouTube 載入
    9: 2.5,
}

# ══════════════════════════════════════════════
#  控制視窗
# ══════════════════════════════════════════════
stop_flag = threading.Event()
_win = None

def _safe_pos(click_coords):
    """找一個不會蓋到任何點擊座標的視窗位置（右上角優先）"""
    sw = pyautogui.size().width
    W, H = 180, 120

    candidates = [
        (sw - W - 10, 10),       # 右上
        (10, 10),                 # 左上
        (10, pyautogui.size().height - H - 50),   # 左下
        (sw - W - 10, pyautogui.size().height - H - 50),  # 右下
    ]

    for cx, cy in candidates:
        win_rect = (cx, cy, cx + W, cy + H)
        conflict = False
        for step in click_coords:
            px, py = step
            if win_rect[0]-30 < px < win_rect[2]+30 and \
               win_rect[1]-30 < py < win_rect[3]+30:
                conflict = True
                break
        if not conflict:
            return cx, cy

    return candidates[0]  # fallback

def build_window():
    global _win
    # 收集所有點擊座標
    click_coords = [s[1] for s in STEPS if s[0] == "click"]
    wx, wy = _safe_pos(click_coords)

    _win = tk.Tk()
    _win.title("執行中")
    _win.configure(bg="#0d0d1a")
    _win.attributes("-topmost", True)
    _win.attributes("-alpha", 0.92)
    _win.geometry(f"180x110+{wx}+{wy}")
    _win.resizable(False, False)

    # 停止按鈕放最頂（縮小也看得到）
    tk.Button(_win, text="■ 停止  (F8)",
              command=lambda: stop_flag.set(),
              bg="#440000", fg="#ff4444",
              font=("Arial", 11, "bold"),
              relief="flat", pady=6).pack(fill=tk.X, padx=6, pady=(8,4))

    # 狀態 log
    _win.log = tk.Label(_win, text="準備中...",
                         bg="#0d0d1a", fg="#aaaacc",
                         font=("Arial", 8), wraplength=160, justify="left")
    _win.log.pack(fill=tk.X, padx=6)

    tk.Label(_win, text="移到左上角可緊急停止",
             bg="#0d0d1a", fg="#444455",
             font=("Arial", 7)).pack(pady=(4,2))

    return _win

def log(msg):
    if _win:
        _win.after(0, lambda: _win.log.configure(text=msg))

# ══════════════════════════════════════════════
#  F8 熱鍵監聽
# ══════════════════════════════════════════════
def _hotkey_thread():
    while not stop_flag.is_set():
        if ctypes.windll.user32.GetAsyncKeyState(0x77) & 0x8000:
            stop_flag.set()
        time.sleep(0.05)

# ══════════════════════════════════════════════
#  執行任務
# ══════════════════════════════════════════════
def run_task():
    time.sleep(1.5)
    log("開始執行...")

    for i, step in enumerate(STEPS):
        if stop_flag.is_set():
            log("已停止")
            return

        action = step[0]
        param  = step[1]
        desc   = step[2]
        log(f"[{i+1}/{len(STEPS)}] {desc}")

        if action == "click":
            pyautogui.click(param[0], param[1])
        elif action == "write":
            pyautogui.write(param, interval=0.05)
        elif action == "press":
            pyautogui.press(param)
        elif action == "hotkey":
            pyautogui.hotkey(*param)

        wait = WAIT.get(i, 0.3)
        # 分段等待，讓停止更即時
        for _ in range(int(wait / 0.1)):
            if stop_flag.is_set():
                log("已停止")
                return
            time.sleep(0.1)

    log("✅ 完成")

# ══════════════════════════════════════════════
if __name__ == "__main__":
    win = build_window()
    threading.Thread(target=_hotkey_thread, daemon=True).start()
    threading.Thread(target=run_task, daemon=True).start()
    win.mainloop()
