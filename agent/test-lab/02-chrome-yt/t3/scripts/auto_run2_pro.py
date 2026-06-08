"""
auto_run2_pro.py — 自動執行（圖案比對版）
步驟 1 用圖案比對找目標位置，解決多視窗時位置不固定的問題
"""

import pyautogui
import threading
import time
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
import os

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.2

# 圖案範本路徑（絕對路徑）
TEMPLATE = r"c:\Users\fff\Downloads\TT\antigravity\antigravity\_github_clone\agent\test-lab\02-chrome-yt\t3\captures\s4_region.png"

# 固定座標步驟（步驟1改用圖案比對）
STEPS = [
    ("locate", TEMPLATE, "圖案比對找目標並點擊", {
        "origin": (354, 745),  # 錄製時的座標
        "mode":   "nearby",    # exact=±50 / nearby=±200 / full=全螢幕
        "radius": 200,
    }),
    ("click",  (253, 174), "點擊 (253, 174)", {}),
    ("click",  (154, 639), "點擊 (154, 639)", {}),
]

WAIT = {
    0: 0.8,
    1: 2.0,
    2: 2.0,
}

paused    = threading.Event()
stop_flag = threading.Event()
_win      = None
_btn      = None

cfg = {
    "loop_mode":     "次數",
    "loop_count":    1,
    "loop_interval": 1.0,
    "confidence":    0.8,   # 圖案比對信心值 0~1
}

# ══════════════════════════════════════════════
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

# ══════════════════════════════════════════════
#  設定面板
# ══════════════════════════════════════════════
def open_settings():
    s = tk.Toplevel(_win)
    s.title("設定")
    s.configure(bg="#0d0d1a")
    s.attributes("-topmost", True)
    s.resizable(False, False)
    s.geometry("220x230")

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

    tk.Label(s, text="圖案比對信心值（0.5~1.0）", **lbl).pack(anchor="w", **PAD)
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

# ══════════════════════════════════════════════
#  視窗
# ══════════════════════════════════════════════
def build_window():
    global _win, _btn
    click_coords = [s[1] for s in STEPS if s[0] == "click"]
    wx, wy = _safe_pos(click_coords)

    _win = tk.Tk()
    _win.title("執行中 (Pro)")
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

    tk.Button(_win, text="⚙ 設定",
              command=open_settings,
              bg="#1a1a2e", fg="#888888",
              relief="flat", font=("Arial", 9), pady=2).pack(fill=tk.X, padx=6)

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
    for _ in range(max(1, int(secs / 0.1))):
        if stop_flag.is_set(): return False
        while paused.is_set():
            if stop_flag.is_set(): return False
            time.sleep(0.1)
        time.sleep(0.1)
    return True

def run_once(round_num):
    for i, step in enumerate(STEPS):
        if stop_flag.is_set(): return False
        while paused.is_set():
            if stop_flag.is_set(): return False
            time.sleep(0.1)

        action = step[0]
        desc   = step[2]
        log(f"[{i+1}/{len(STEPS)}] {desc}")

        if action == "locate":
            template = step[1]
            opt      = step[3]
            mode     = opt.get("mode", "nearby")
            origin   = opt.get("origin", None)
            radius   = opt.get("radius", 200)

            log(f"[{i+1}] 圖案比對（{mode}）...")
            try:
                import cv2, numpy as np

                sw = pyautogui.size().width
                sh = pyautogui.size().height

                # 決定搜尋區域
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

                def match(src_img, tpl_img):
                    """回傳 (max_val, cx, cy) 全螢幕座標"""
                    if src_img.shape[0] < tpl_img.shape[0] or \
                       src_img.shape[1] < tpl_img.shape[1]:
                        return 0, None, None
                    res = cv2.matchTemplate(src_img, tpl_img, cv2.TM_CCOEFF_NORMED)
                    _, mv, _, ml = cv2.minMaxLoc(res)
                    th, tw = tpl_img.shape[:2]
                    return mv, x1 + ml[0] + tw//2, y1 + ml[1] + th//2

                # ── 第一輪：原始像素比對 ──
                val, cx, cy = match(src, tpl)
                log(f"[{i+1}] 原始比對分數：{val:.2f}")

                if val < cfg["confidence"]:
                    # ── 第二輪：縮放歸一化比對（備援）──
                    log(f"[{i+1}] 分數不足，改用縮放比對...")
                    NORM = 64
                    tpl_n = cv2.resize(tpl, (NORM, NORM))
                    th, tw = tpl.shape[:2]
                    best_val, best_cx, best_cy = 0, None, None

                    # 滑動視窗，每次裁出和範本一樣比例的區域再縮放比對
                    step_size = max(4, min(tw, th) // 4)
                    scales = [1.0, 0.85, 1.15, 0.7, 1.3]
                    for scale in scales:
                        sw2 = int(tw * scale)
                        sh2 = int(th * scale)
                        if sw2 > w or sh2 > h:
                            continue
                        for wy in range(0, h - sh2, step_size):
                            for wx in range(0, w - sw2, step_size):
                                crop = src[wy:wy+sh2, wx:wx+sw2]
                                crop_n = cv2.resize(crop, (NORM, NORM))
                                res = cv2.matchTemplate(
                                    crop_n, tpl_n, cv2.TM_CCOEFF_NORMED)
                                _, mv, _, _ = cv2.minMaxLoc(res)
                                if mv > best_val:
                                    best_val = mv
                                    best_cx = x1 + wx + sw2//2
                                    best_cy = y1 + wy + sh2//2

                    log(f"[{i+1}] 縮放比對分數：{best_val:.2f}")
                    if best_val >= cfg["confidence"] * 0.85:  # 縮放比對門檻稍低
                        val, cx, cy = best_val, best_cx, best_cy

                pos = type('P', (), {'x': cx, 'y': cy})() if cx else None
                if pos:
                    log(f"[{i+1}] 找到 ({pos.x},{pos.y})，點擊")
                    pyautogui.moveTo(pos.x, pos.y, duration=0.2)
                    time.sleep(0.1)
                    pyautogui.click(pos.x, pos.y)
                else:
                    log(f"[{i+1}] ❌ 找不到圖案！已停止")
                    if _win:
                        _win.after(0, lambda: messagebox.showerror(
                            "找不到圖案",
                            "找不到範本圖案，已停止執行。\n\n"
                            "可能原因：\n"
                            "・畫面不一樣（視窗大小、位置改變）\n"
                            "・信心值太高（設定裡調低試試）\n\n"
                            "請確認後重新執行。"))
                    if _btn:
                        _win.after(0, lambda: _btn.configure(
                            text="▶ 再跑一次", bg="#003366", fg="#00ccff",
                            state=tk.NORMAL, command=restart_task))
                    return False
            except Exception as e:
                log(f"[{i+1}] ❌ 比對錯誤：{e}，已停止")
                if _btn:
                    _win.after(0, lambda: _btn.configure(
                        text="▶ 再跑一次", bg="#003366", fg="#00ccff",
                        state=tk.NORMAL, command=restart_task))
                return False

        elif action == "click":
            param = step[1]
            pyautogui.click(param[0], param[1])

        if not _wait_interruptible(WAIT.get(i, 0.3)):
            return False
    return True

def restart_task():
    """完成後重新開始"""
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
        log(f"第 {loop} 輪開始...")
        ok = run_once(loop)
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
        log(f"等待 {cfg['loop_interval']}s...")
        if not _wait_interruptible(cfg["loop_interval"]):
            log("已停止")
            return

if __name__ == "__main__":
    if not os.path.exists(TEMPLATE):
        # 顯示錯誤視窗不直接 exit
        root = tk.Tk()
        root.withdraw()
        tk.messagebox.showerror("找不到範本",
            f"找不到範本圖片：\n{TEMPLATE}\n\n請先跑 extract_screenshots.py")
        root.destroy()
        exit(1)

    win = build_window()
    threading.Thread(target=_hotkey_thread, daemon=True).start()
    threading.Thread(target=run_task,        daemon=True).start()
    win.mainloop()
