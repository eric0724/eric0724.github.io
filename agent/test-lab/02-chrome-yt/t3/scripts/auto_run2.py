"""
auto_run2.py — 自動執行
由 Miniclaw Recorder 紀錄產出
"""

import pyautogui
import threading
import time
import ctypes
import tkinter as tk
from tkinter import ttk

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2

STEPS = [
    ("click", (403, 742), "點擊 (403, 742)"),
    ("click", (291, 175), "點擊 (291, 175)"),
    ("click", (193, 622), "點擊 (193, 622)"),
    ("click", (844,  84), "點擊 (844, 84)"),
]

WAIT = {
    0: 0.8,
    1: 2.0,
    2: 2.0,
    3: 0.5,
}

paused    = threading.Event()
stop_flag = threading.Event()
_win      = None
_btn      = None
_task_thread = None

# 設定值
cfg = {
    "loop_mode":     "次數",   # "次數" | "無限"
    "loop_count":    1,
    "loop_interval": 1.0,      # 每輪間隔秒數
}

# ══════════════════════════════════════════════
#  工具
# ══════════════════════════════════════════════
def _safe_pos(click_coords):
    sw = pyautogui.size().width
    sh = pyautogui.size().height
    W, H = 200, 160
    candidates = [
        (sw - W - 10, 10),
        (10, 10),
        (10, sh - H - 50),
        (sw - W - 10, sh - H - 50),
    ]
    for cx, cy in candidates:
        conflict = False
        for px, py in click_coords:
            if cx-30 < px < cx+W+30 and cy-30 < py < cy+H+30:
                conflict = True
                break
        if not conflict:
            return cx, cy
    return candidates[0]

def log(msg):
    if _win and _win.winfo_exists():
        _win.after(0, lambda: _win.log.configure(text=msg))

def toggle_pause():
    if paused.is_set():
        paused.clear()
        _btn.configure(text="■ 暫停  (F8)", bg="#440000", fg="#ff4444")
        log("繼續執行...")
    else:
        paused.set()
        _btn.configure(text="▶ 繼續  (F8)", bg="#003300", fg="#00ff88")
        log("已暫停")

# ══════════════════════════════════════════════
#  設定面板（Toplevel）
# ══════════════════════════════════════════════
def open_settings():
    s = tk.Toplevel(_win)
    s.title("設定")
    s.configure(bg="#0d0d1a")
    s.attributes("-topmost", True)
    s.resizable(False, True)
    s.geometry("220x280")

    PAD = dict(padx=12, pady=4)
    lbl = dict(bg="#0d0d1a", fg="#aaaacc", font=("Arial", 9))
    ent = dict(bg="#1a1a2e", fg="#00f0ff", font=("Arial", 9),
               relief="flat", insertbackground="white", justify="center")

    # 循環模式
    tk.Label(s, text="循環模式", **lbl).pack(anchor="w", **PAD)
    mode_var = tk.StringVar(value=cfg["loop_mode"])
    mode_frame = tk.Frame(s, bg="#0d0d1a")
    mode_frame.pack(fill=tk.X, padx=12)
    for m in ["次數", "無限"]:
        tk.Radiobutton(mode_frame, text=m, variable=mode_var, value=m,
                       bg="#0d0d1a", fg="#aaaacc", selectcolor="#1a1a2e",
                       activebackground="#0d0d1a",
                       font=("Arial", 9)).pack(side=tk.LEFT, padx=6)

    # 執行次數
    tk.Label(s, text="執行次數（次數模式）", **lbl).pack(anchor="w", **PAD)
    count_var = tk.StringVar(value=str(cfg["loop_count"]))
    tk.Entry(s, textvariable=count_var, width=8, **ent).pack(**PAD)

    # 每輪間隔
    tk.Label(s, text="每輪結束間隔（秒）", **lbl).pack(anchor="w", **PAD)
    interval_var = tk.StringVar(value=str(cfg["loop_interval"]))
    tk.Entry(s, textvariable=interval_var, width=8, **ent).pack(**PAD)

    def save():
        cfg["loop_mode"] = mode_var.get()
        try:
            cfg["loop_count"] = max(1, int(count_var.get()))
        except ValueError:
            pass
        try:
            cfg["loop_interval"] = max(0.0, float(interval_var.get()))
        except ValueError:
            pass
        s.destroy()

    tk.Button(s, text="✅ 儲存",
              command=save,
              bg="#003322", fg="#00ff88",
              relief="flat", font=("Arial", 10, "bold"),
              pady=4).pack(fill=tk.X, padx=12, pady=8)

# ══════════════════════════════════════════════
#  視窗
# ══════════════════════════════════════════════
def build_window():
    global _win, _btn
    click_coords = [s[1] for s in STEPS if s[0] == "click"]
    wx, wy = _safe_pos(click_coords)

    _win = tk.Tk()
    _win.title("執行中")
    _win.configure(bg="#0d0d1a")
    _win.attributes("-topmost", True)
    _win.attributes("-alpha", 0.92)
    _win.geometry(f"200x160+{wx}+{wy}")
    _win.resizable(False, False)

    # 暫停/繼續（最頂）
    _btn = tk.Button(_win, text="■ 暫停  (F8)",
                     command=toggle_pause,
                     bg="#440000", fg="#ff4444",
                     font=("Arial", 11, "bold"),
                     relief="flat", pady=6)
    _btn.pack(fill=tk.X, padx=6, pady=(8, 2))

    # 狀態
    _win.log = tk.Label(_win, text="準備中...",
                        bg="#0d0d1a", fg="#aaaacc",
                        font=("Arial", 8), wraplength=180, justify="left")
    _win.log.pack(fill=tk.X, padx=8, pady=2)

    # 分隔
    ttk.Separator(_win, orient="horizontal").pack(fill=tk.X, pady=4)

    # 設定按鈕
    tk.Button(_win, text="⚙ 設定",
              command=open_settings,
              bg="#1a1a2e", fg="#888888",
              relief="flat", font=("Arial", 9),
              pady=2).pack(fill=tk.X, padx=6)

    tk.Label(_win, text="移到左上角可緊急停止",
             bg="#0d0d1a", fg="#444455",
             font=("Arial", 7)).pack(pady=(4, 2))

    return _win

# ══════════════════════════════════════════════
#  執行
# ══════════════════════════════════════════════
def _hotkey_thread():
    prev = False
    while not stop_flag.is_set():
        pressed = bool(ctypes.windll.user32.GetAsyncKeyState(0x77) & 0x8000)
        if pressed and not prev:
            if _win:
                _win.after(0, toggle_pause)
        prev = pressed
        time.sleep(0.05)

def _wait_interruptible(secs):
    """可被暫停/停止中斷的等待"""
    for _ in range(int(secs / 0.1)):
        if stop_flag.is_set():
            return False
        while paused.is_set():
            if stop_flag.is_set():
                return False
            time.sleep(0.1)
        time.sleep(0.1)
    return True

def run_once(round_num, total):
    """執行一輪所有步驟"""
    prefix = f"[第{round_num}輪]" if total != 1 else ""
    for i, step in enumerate(STEPS):
        if stop_flag.is_set():
            return False
        while paused.is_set():
            if stop_flag.is_set():
                return False
            time.sleep(0.1)

        action, param, desc = step
        log(f"{prefix}[{i+1}/{len(STEPS)}] {desc}")

        if action == "click":
            pyautogui.click(param[0], param[1])
        elif action == "write":
            pyautogui.write(param, interval=0.05)
        elif action == "press":
            pyautogui.press(param)
        elif action == "hotkey":
            pyautogui.hotkey(*param)

        if not _wait_interruptible(WAIT.get(i, 0.3)):
            return False
    return True

def restart_task():
    paused.clear()
    if _btn:
        _btn.configure(text="■ 暫停  (F8)", bg="#440000", fg="#ff4444",
                       command=toggle_pause)
    threading.Thread(target=run_task, daemon=True).start()

def run_task():
    time.sleep(1.5)
    loop = 0
    while not stop_flag.is_set():
        loop += 1
        total = cfg["loop_count"] if cfg["loop_mode"] == "次數" else "∞"
        log(f"開始第 {loop} 輪...")

        ok = run_once(loop, total if total != "∞" else 0)
        if not ok:
            log("已停止")
            return

        if cfg["loop_mode"] == "次數":
            if loop >= cfg["loop_count"]:
                log("✅ 全部完成")
                if _btn:
                    _win.after(0, lambda: _btn.configure(
                        text="▶ 再跑一次", bg="#003366", fg="#00ccff",
                        state=tk.NORMAL,
                        command=restart_task))
                return
        # 輪間等待
        log(f"等待 {cfg['loop_interval']}s 後繼續...")
        if not _wait_interruptible(cfg["loop_interval"]):
            log("已停止")
            return

if __name__ == "__main__":
    win = build_window()
    threading.Thread(target=_hotkey_thread, daemon=True).start()
    threading.Thread(target=run_task,        daemon=True).start()
    win.mainloop()
