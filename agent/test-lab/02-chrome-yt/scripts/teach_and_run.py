"""
teach_and_run.py — 教學模式
=============================
流程：
  教學階段：使用者把滑鼠移到每個目標位置，py 記住座標 + 截圖
  執行階段：py 自動按照記住的座標依序點擊

不需要 GPT，不需要範本圖，完全靠使用者示範
"""

import os, time, threading, json
import tkinter as tk
from tkinter import scrolledtext
import pyautogui
from PIL import ImageGrab, ImageTk, ImageDraw
import ctypes

try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.15

stop_flag  = threading.Event()
_hotkey    = ["F8"]
SW, SH     = pyautogui.size()

# 記住的步驟清單
# 每個步驟：{ "name": str, "x": int, "y": int, "action": str, "input": str, "screenshot": PIL.Image }
_steps = []

# 預覽歷史
_preview_win   = [None]
_preview_label = [None]


# ══════════════════════════════════════════════════════
#  熱鍵監聽
# ══════════════════════════════════════════════════════

def _hotkey_listener():
    VK_MAP = {f"F{i}": 0x6F+i for i in range(1, 13)}
    while True:
        vk = VK_MAP.get(_hotkey[0], 0x77)
        if ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000:
            if not stop_flag.is_set():
                stop_flag.set()
        time.sleep(0.1)

threading.Thread(target=_hotkey_listener, daemon=True).start()


# ══════════════════════════════════════════════════════
#  工具函數
# ══════════════════════════════════════════════════════

def log(msg, w):
    w.configure(state="normal")
    w.insert(tk.END, msg + "\n")
    w.see(tk.END)
    w.configure(state="disabled")

def show_preview(img, title="截圖"):
    """把截圖加到歷史列表"""
    def _show():
        try:
            w, h = img.size
            scale = min(380/w, 200/h, 1.0)
            disp  = img.resize((int(w*scale), int(h*scale)))
            photo = ImageTk.PhotoImage(disp)

            if _preview_win[0] is None or not _preview_win[0].winfo_exists():
                win = tk.Toplevel()
                win.title("截圖歷史")
                win.configure(bg="#0d0d1a")
                win.attributes("-topmost", True)
                win.geometry("420x500+10+10")
                canvas = tk.Canvas(win, bg="#0d0d1a", highlightthickness=0)
                sb = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
                canvas.configure(yscrollcommand=sb.set)
                sb.pack(side="right", fill="y")
                canvas.pack(side="left", fill="both", expand=True)
                frame = tk.Frame(canvas, bg="#0d0d1a")
                canvas_win = canvas.create_window((0,0), window=frame, anchor="nw")
                frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
                _preview_win[0]   = win
                _preview_label[0] = (canvas, frame)

            canvas, frame = _preview_label[0]
            item = tk.Frame(frame, bg="#1a1a2e", bd=1, relief="solid")
            item.pack(fill="x", padx=4, pady=3)
            tk.Label(item, text=title, fg="#00f0ff", bg="#1a1a2e",
                     font=("Consolas", 8), anchor="w").pack(fill="x", padx=4, pady=(3,0))
            lbl = tk.Label(item, image=photo, bg="#1a1a2e")
            lbl.image = photo
            lbl.pack(padx=4, pady=(0,4))
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.yview_moveto(1.0)
        except Exception:
            pass

    try:
        import tkinter as _tk
        if _tk._default_root:
            _tk._default_root.after(0, _show)
    except Exception:
        pass

def grab_screenshot(mark_pos=None):
    """截全螢幕，可選在指定位置畫綠點標記"""
    img = pyautogui.screenshot()
    if mark_pos:
        draw = ImageDraw.Draw(img)
        x, y = mark_pos
        draw.ellipse([x-12, y-12, x+12, y+12], fill="lime", outline="white", width=3)
        draw.line([x-20, y, x+20, y], fill="white", width=2)
        draw.line([x, y-20, x, y+20], fill="white", width=2)
    return img

def countdown(w, seconds, msg):
    """倒數計時，顯示在 log"""
    for i in range(seconds, 0, -1):
        if stop_flag.is_set(): return False
        log(f"  {msg} {i}...", w)
        time.sleep(1.0)
    return True


# ══════════════════════════════════════════════════════
#  教學階段
# ══════════════════════════════════════════════════════

# 要教學的步驟定義
TEACH_STEPS = [
    {"name": "win_search",  "label": "Windows 搜尋圖示",   "action": "click",  "input": ""},
    {"name": "chrome_app",  "label": "Chrome 應用程式",     "action": "click",  "input": "chrome"},
    {"name": "yahoo_bar",   "label": "Chrome 網址列",       "action": "click",  "input": "yt\n"},
    {"name": "yahoo_yt",    "label": "YouTube 搜尋結果連結","action": "click",  "input": ""},
    {"name": "yt_search",   "label": "YouTube 搜尋列",      "action": "click",  "input": "agent\n"},
]

def run_teach(w):
    """教學階段：使用者移滑鼠到每個目標，py 記住座標"""
    stop_flag.clear()
    _steps.clear()

    log("="*40, w)
    log("▶ 教學模式開始", w)
    log("  請依序把滑鼠移到每個目標位置", w)
    log("  每個目標有 5 秒時間，倒數結束時截圖記錄", w)
    log(f"  按 {_hotkey[0]} 可隨時停止", w)
    log("─"*40, w)

    time.sleep(2.0)

    for step in TEACH_STEPS:
        if stop_flag.is_set(): break

        log(f"\n[教學] 目標：{step['label']}", w)
        log(f"  請把滑鼠移到「{step['label']}」上", w)

        if not countdown(w, 5, "截圖倒數"):
            break

        # 記錄滑鼠位置
        mx, my = pyautogui.position()
        log(f"  ✓ 記錄座標：({mx}, {my})", w)

        # 截圖（標記滑鼠位置）
        img = grab_screenshot(mark_pos=(mx, my))
        show_preview(img, f"[教學] {step['label']} ({mx},{my})")

        _steps.append({
            "name":       step["name"],
            "label":      step["label"],
            "x":          mx,
            "y":          my,
            "action":     step["action"],
            "input":      step["input"],
            "screenshot": img
        })

    if stop_flag.is_set():
        log("\n■ 教學已停止", w)
        return

    log("\n─"*40, w)
    log(f"✅ 教學完成！記錄了 {len(_steps)} 個步驟", w)
    for s in _steps:
        log(f"  {s['label']} → ({s['x']},{s['y']})", w)

    # 存座標到 JSON
    save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "templates", "taught_steps.json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump([{k:v for k,v in s.items() if k != "screenshot"} for s in _steps],
                  f, ensure_ascii=False, indent=2)
    log(f"  座標已存到：taught_steps.json", w)


# ══════════════════════════════════════════════════════
#  執行階段
# ══════════════════════════════════════════════════════

def run_execute(w):
    """執行階段：按照記住的座標依序點擊"""
    stop_flag.clear()

    if not _steps:
        # 嘗試從 JSON 載入
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "templates", "taught_steps.json")
        if os.path.exists(save_path):
            with open(save_path, encoding="utf-8") as f:
                loaded = json.load(f)
            for s in loaded:
                _steps.append(s)
            log(f"[載入] 從 taught_steps.json 載入 {len(_steps)} 個步驟", w)
        else:
            log("❌ 尚未教學，請先按「教學」", w)
            return

    log("="*40, w)
    log("▶ 執行開始", w)
    log(f"  共 {len(_steps)} 個步驟，按 {_hotkey[0]} 可停止", w)
    log("─"*40, w)

    time.sleep(1.0)

    for i, step in enumerate(_steps):
        if stop_flag.is_set():
            log("■ 已停止", w)
            return

        log(f"\n[{i+1}/{len(_steps)}] {step['label']} → ({step['x']},{step['y']})", w)

        # 截圖確認當前畫面
        img = grab_screenshot()
        show_preview(img, f"[執行前] {step['label']}")

        # 點擊
        pyautogui.click(step["x"], step["y"])
        log(f"  ✓ 點擊 ({step['x']},{step['y']})", w)

        # 如果有輸入文字
        if step.get("input"):
            time.sleep(0.5)
            text = step["input"].replace("\n", "")
            if text:
                pyautogui.write(text, interval=0.05)
                log(f"  ✓ 輸入：{text}", w)
            if "\n" in step["input"]:
                pyautogui.press("enter")
                log(f"  ✓ Enter", w)

        # 等待畫面變化
        wait = 4.0 if i < len(_steps)-1 else 2.0
        log(f"  等待 {wait}s...", w)
        time.sleep(wait)

        # 截圖確認點擊後
        img2 = grab_screenshot()
        show_preview(img2, f"[執行後] {step['label']}")

    log("\n─"*40, w)
    log("✅ 執行完成！", w)


# ══════════════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════════════

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Miniclaw - 教學模式")
        self.root.geometry("520x500")
        self.root.resizable(False, False)
        self.root.configure(bg="#0d0d1a")
        self.root.attributes("-topmost", True)
        self._build_ui()
        self.task_thread = None

    def _build_ui(self):
        tk.Label(self.root, text="Miniclaw 教學模式",
                 fg="#ff6600", bg="#0d0d1a",
                 font=("Arial", 13, "bold")).pack(pady=(14, 2))
        tk.Label(self.root, text="示範一次 → 自動重複執行",
                 fg="#00f0ff", bg="#0d0d1a",
                 font=("Consolas", 9)).pack(pady=(0, 6))

        bf  = tk.Frame(self.root, bg="#0d0d1a")
        bf.pack(pady=4)
        cfg = dict(font=("Arial", 11, "bold"), width=10, relief="flat", cursor="hand2", pady=6)

        self.btn_teach = tk.Button(bf, text="教學",
            bg="#1a3a6e", fg="white", activebackground="#2756a8",
            command=self.start_teach, **cfg)
        self.btn_teach.grid(row=0, column=0, padx=5)

        self.btn_run = tk.Button(bf, text="執行",
            bg="#1a6e2e", fg="white", activebackground="#27a844",
            command=self.start_execute, **cfg)
        self.btn_run.grid(row=0, column=1, padx=5)

        self.btn_stop = tk.Button(bf, text="停止",
            bg="#6e1a1a", fg="white", activebackground="#a82727",
            command=self.stop_task, state="disabled", **cfg)
        self.btn_stop.grid(row=0, column=2, padx=5)

        tk.Button(bf, text="關閉",
            bg="#2a2a2a", fg="#888888", activebackground="#444444",
            command=self.root.destroy, **cfg).grid(row=0, column=3, padx=5)

        # 熱鍵設定
        hk_frame = tk.Frame(self.root, bg="#0d0d1a")
        hk_frame.pack(pady=(2,4))
        tk.Label(hk_frame, text="⚠ 執行中請勿移動滑鼠  |  停止熱鍵：",
                 fg="#ffaa00", bg="#0d0d1a", font=("Arial",9)).pack(side="left")
        self.hk_var = tk.StringVar(value="F8")
        hk_menu = tk.OptionMenu(hk_frame, self.hk_var,
                                *[f"F{i}" for i in range(5,13)],
                                command=lambda v: _hotkey.__setitem__(0, v))
        hk_menu.configure(bg="#1a1a2e", fg="#00f0ff", relief="flat", font=("Arial",9))
        hk_menu.pack(side="left")

        tk.Label(self.root, text="Log",
                 fg="#666688", bg="#0d0d1a",
                 font=("Arial", 9)).pack(anchor="w", padx=16, pady=(6,2))

        self.log_box = scrolledtext.ScrolledText(
            self.root, height=18, state="disabled",
            bg="#07070f", fg="#c8ffc8",
            font=("Consolas", 9), relief="flat", wrap=tk.WORD, padx=8, pady=6)
        self.log_box.pack(fill=tk.BOTH, padx=14, pady=(0,14))

        # 右鍵複製
        def _copy_all():
            self.root.clipboard_clear()
            self.root.clipboard_append(self.log_box.get("1.0", tk.END))
        ctx = tk.Menu(self.log_box, tearoff=0)
        ctx.add_command(label="複製全部", command=_copy_all)
        self.log_box.bind("<Button-3>", lambda e: ctx.tk_popup(e.x_root, e.y_root))

        log("教學模式：按「教學」後依序把滑鼠移到每個目標。", self.log_box)
        log("執行模式：按「執行」自動重複上次教學的操作。", self.log_box)

    def _run_in_thread(self, fn):
        if self.task_thread and self.task_thread.is_alive(): return
        self.btn_teach.config(state="disabled")
        self.btn_run.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.task_thread = threading.Thread(
            target=lambda: [fn(self.log_box), self.root.after(0, self._done)],
            daemon=True)
        self.task_thread.start()

    def start_teach(self):
        self._run_in_thread(run_teach)

    def start_execute(self):
        self._run_in_thread(run_execute)

    def _done(self):
        self.btn_teach.config(state="normal")
        self.btn_run.config(state="normal")
        self.btn_stop.config(state="disabled")

    def stop_task(self):
        stop_flag.set()
        log("停止指令已送出...", self.log_box)
        self.btn_stop.config(state="disabled")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
