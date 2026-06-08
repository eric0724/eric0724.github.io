"""
auto_run3.py — 自動執行
圖案比對找步驟1，其餘固定座標
"""

import pyautogui
import threading
import time
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import os

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2

TEMPLATE = r"c:\Users\fff\Downloads\TT\antigravity\antigravity\_github_clone\agent\test-lab\02-chrome-yt\t3\captures\s1_region.png"

STEPS = [
    ("locate", TEMPLATE, "圖案比對找查詢列", {
        "origin": (403, 745),
        "mode":   "nearby",
        "radius": 300,         # 範圍大一點，因為會往左右跑
    }),
    ("write",  "googe",   "輸入 googe", {}),
    ("press",  "backspace","按 backspace", {}),
    ("write",  "le",       "輸入 le", {}),
    ("press",  "enter",    "按 Enter", {}),
    ("click",  (309, 231), "點擊搜尋結果 (309, 231)", {}),
    ("click",  (192, 625), "點擊連結 (192, 625)", {}),
]

WAIT = {
    0: 0.8,   # 查詢列開啟
    4: 1.5,   # 等搜尋結果
    5: 2.0,   # 等頁面載入
    6: 0.5,
}

paused    = threading.Event()
stop_flag = threading.Event()
_win      = None
_btn      = None

cfg = {
    "loop_mode":     "次數",
    "loop_count":    1,
    "loop_interval": 1.0,
    "confidence":    0.75,
}

def _safe_pos(click_coords):
    sw = pyautogui.size().width
    sh = pyautogui.size().height
    W, H = 200, 170
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

    tk.Label(s, text="循環模式", **lbl).pack(anchor="w", **PAD)
    mode_var = tk.StringVar(value=cfg["loop_mode"])
    mf = tk.Frame(s, bg="#0d0d1a")
    mf.pack(fill=tk.X, padx=12)
    for m in ["次數", "無限"]:
        tk.Radiobutton(mf, text=m, variable=mode_var, value=m,
                       bg="#0d0d1a", fg="#aaaacc", selectcolor="#1a1a2e",
                       activebackground="#0d0d1a",
                       font=("Arial", 9)).pack(side=tk.LEFT, padx=6)

    tk.Label(s, text="執行次數", **lbl).pack(anchor="w", **PAD)
    count_var = tk.StringVar(value=str(cfg["loop_count"]))
    tk.Entry(s, textvariable=count_var, width=8, **ent).pack(**PAD)

    tk.Label(s, text="每輪間隔（秒）", **lbl).pack(anchor="w", **PAD)
    interval_var = tk.StringVar(value=str(cfg["loop_interval"]))
    tk.Entry(s, textvariable=interval_var, width=8, **ent).pack(**PAD)

    tk.Label(s, text="比對信心值（0.5~1.0）", **lbl).pack(anchor="w", **PAD)
    conf_var = tk.StringVar(value=str(cfg["confidence"]))
    tk.Entry(s, textvariable=conf_var, width=8, **ent).pack(**PAD)

    def save():
        cfg["loop_mode"] = mode_var.get()
        try: cfg["loop_count"]    = max(1,   int(count_var.get()))
        except ValueError: pass
        try: cfg["loop_interval"] = max(0.0, float(interval_var.get()))
        except ValueError: pass
        try: cfg["confidence"]    = max(0.5, min(1.0, float(conf_var.get())))
        except ValueError: pass
        s.destroy()

    tk.Button(s, text="✅ 儲存", command=save,
              bg="#003322", fg="#00ff88",
              relief="flat", font=("Arial", 10, "bold"),
              pady=4).pack(fill=tk.X, padx=12, pady=8)

def build_window():
    global _win, _btn
    click_coords = [s[1] for s in STEPS if s[0] == "click"]
    wx, wy = _safe_pos(click_coords)

    _win = tk.Tk()
    _win.title("執行中")
    _win.configure(bg="#0d0d1a")
    _win.attributes("-topmost", True)
    _win.attributes("-alpha", 0.92)
    _win.geometry(f"200x170+{wx}+{wy}")
    _win.resizable(False, False)

    _btn = tk.Button(_win, text="■ 暫停  (F8)",
                     command=toggle_pause,
                     bg="#440000", fg="#ff4444",
                     font=("Arial", 11, "bold"),
                     relief="flat", pady=6)
    _btn.pack(fill=tk.X, padx=6, pady=(8, 2))

    _win.log = tk.Label(_win, text="準備中...",
                        bg="#0d0d1a", fg="#aaaacc",
                        font=("Arial", 8), wraplength=180, justify="left")
    _win.log.pack(fill=tk.X, padx=8, pady=2)

    ttk.Separator(_win, orient="horizontal").pack(fill=tk.X, pady=4)

    tk.Button(_win, text="⚙ 設定", command=open_settings,
              bg="#1a1a2e", fg="#888888",
              relief="flat", font=("Arial", 9), pady=2).pack(fill=tk.X, padx=6)

    tk.Label(_win, text="移到左上角可緊急停止",
             bg="#0d0d1a", fg="#444455",
             font=("Arial", 7)).pack(pady=(4, 2))
    return _win

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
    for _ in range(max(1, int(secs / 0.1))):
        if stop_flag.is_set(): return False
        while paused.is_set():
            if stop_flag.is_set(): return False
            time.sleep(0.1)
        time.sleep(0.1)
    return True

def do_locate(template, opt):
    """圖案比對：先原始，找不到再縮放備援"""
    mode   = opt.get("mode", "nearby")
    origin = opt.get("origin", None)
    radius = opt.get("radius", 200)

    sw = pyautogui.size().width
    sh = pyautogui.size().height

    if mode == "full" or origin is None:
        x1, y1, w, h = 0, 0, sw, sh
    else:
        r = radius if mode == "nearby" else 50
        x1 = max(0, origin[0] - r)
        y1 = max(0, origin[1] - r)
        x2 = min(sw, origin[0] + r)
        y2 = min(sh, origin[1] + r)
        w, h = x2 - x1, y2 - y1

    region_img = pyautogui.screenshot(region=(x1, y1, w, h))
    tpl = cv2.imread(template)
    src = cv2.cvtColor(np.array(region_img), cv2.COLOR_RGB2BGR)

    def match(s, t):
        if s.shape[0] < t.shape[0] or s.shape[1] < t.shape[1]:
            return 0, None, None
        res = cv2.matchTemplate(s, t, cv2.TM_CCOEFF_NORMED)
        _, mv, _, ml = cv2.minMaxLoc(res)
        th2, tw2 = t.shape[:2]
        return mv, x1 + ml[0] + tw2//2, y1 + ml[1] + th2//2

    # 第一輪：原始像素
    val, cx, cy = match(src, tpl)
    log(f"原始比對：{val:.2f}")

    if val < cfg["confidence"]:
        # 第二輪：縮放備援
        log("分數不足，縮放比對...")
        NORM = 64
        tpl_n = cv2.resize(tpl, (NORM, NORM))
        th, tw = tpl.shape[:2]
        best_val, best_cx, best_cy = 0, None, None
        step_px = max(4, min(tw, th) // 4)

        for scale in [1.0, 0.85, 1.15, 0.7, 1.3]:
            sw2, sh2 = int(tw*scale), int(th*scale)
            if sw2 > w or sh2 > h:
                continue
            for wy in range(0, h-sh2, step_px):
                for wx in range(0, w-sw2, step_px):
                    crop = src[wy:wy+sh2, wx:wx+sw2]
                    crop_n = cv2.resize(crop, (NORM, NORM))
                    res = cv2.matchTemplate(crop_n, tpl_n, cv2.TM_CCOEFF_NORMED)
                    _, mv, _, _ = cv2.minMaxLoc(res)
                    if mv > best_val:
                        best_val = mv
                        best_cx = x1 + wx + sw2//2
                        best_cy = y1 + wy + sh2//2

        log(f"縮放比對：{best_val:.2f}")
        if best_val >= cfg["confidence"] * 0.85:
            val, cx, cy = best_val, best_cx, best_cy

    return val, cx, cy

def run_once():
    for i, step in enumerate(STEPS):
        if stop_flag.is_set(): return False
        while paused.is_set():
            if stop_flag.is_set(): return False
            time.sleep(0.1)

        action = step[0]
        desc   = step[2]
        log(f"[{i+1}/{len(STEPS)}] {desc}")

        if action == "locate":
            val, cx, cy = do_locate(step[1], step[3])
            if cx is None or val < cfg["confidence"] * 0.85:
                log(f"❌ 找不到圖案（分數:{val:.2f}）")
                if _win:
                    _win.after(0, lambda: messagebox.showerror(
                        "找不到圖案",
                        f"找不到範本圖案（分數:{val:.2f}）\n\n"
                        "・試著調低設定裡的信心值\n"
                        "・或重新錄製範本"))
                if _btn:
                    _win.after(0, lambda: _btn.configure(
                        text="▶ 再跑一次", bg="#003366", fg="#00ccff",
                        command=restart_task))
                return False

            # 直接點擊
            log(f"找到 ({cx},{cy})，點擊")
            pyautogui.moveTo(cx, cy, duration=0.2)
            time.sleep(0.1)
            pyautogui.click(cx, cy)

        elif action == "click":
            pyautogui.click(step[1][0], step[1][1])
        elif action == "write":
            pyautogui.write(step[1], interval=0.05)
        elif action == "press":
            pyautogui.press(step[1])
        elif action == "hotkey":
            pyautogui.hotkey(*step[1])

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
        log(f"第 {loop} 輪...")
        if not run_once():
            log("已停止")
            return
        if cfg["loop_mode"] == "次數":
            if loop >= cfg["loop_count"]:
                log("✅ 完成")
                if _btn:
                    _win.after(0, lambda: _btn.configure(
                        text="▶ 再跑一次", bg="#003366", fg="#00ccff",
                        state=tk.NORMAL, command=restart_task))
                return
        if not _wait_interruptible(cfg["loop_interval"]):
            return

if __name__ == "__main__":
    if not os.path.exists(TEMPLATE):
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("找不到範本", f"找不到：\n{TEMPLATE}")
        root.destroy(); exit(1)

    win = build_window()
    threading.Thread(target=_hotkey_thread, daemon=True).start()
    threading.Thread(target=run_task,        daemon=True).start()
    win.mainloop()
