"""
calibrate.py — 校準模式（GUI 版）
===================================
第一次執行：AI 自動找每個 UI 元素位置
截 normal + hover 兩種範本，確認點擊前後畫面
失敗自動重試最多 3 次
存到 templates/ 供之後圖案比對使用
"""

import os, time, threading, json, base64, io, urllib.request
import tkinter as tk
from tkinter import scrolledtext
import pyautogui
from PIL import ImageGrab
import ctypes

try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.1

stop_flag = threading.Event()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

_DIR    = os.path.dirname(os.path.abspath(__file__))
TPL_DIR = os.path.join(_DIR, "..", "templates")
os.makedirs(TPL_DIR, exist_ok=True)

SW, SH = pyautogui.size()
_root_ref = [None]   # 存 tkinter root 供最小化用


# ══════════════════════════════════════════════════════
#  GPT-4o 工具
# ══════════════════════════════════════════════════════

def img_to_b64(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def ask_gpt4o(img, question):
    payload = json.dumps({
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{img_to_b64(img)}", "detail": "high"}}
        ]}],
        "max_tokens": 300
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {OPENAI_API_KEY}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"ERROR:{e}"

def parse_json(text):
    try:
        s = text.find("{"); e = text.rfind("}") + 1
        if s >= 0 and e > s:
            return json.loads(text[s:e])
    except Exception:
        pass
    return {}

def grab_region(x1r, y1r, x2r, y2r):
    x1,y1,x2,y2 = int(x1r*SW),int(y1r*SH),int(x2r*SW),int(y2r*SH)
    return ImageGrab.grab(bbox=(x1,y1,x2,y2)), x1, y1

def crop_around(cx, cy, w=140, h=70):
    x1=max(0,cx-w//2); y1=max(0,cy-h//2)
    x2=min(SW,cx+w//2); y2=min(SH,cy+h//2)
    return ImageGrab.grab(bbox=(x1,y1,x2,y2))

def find_target(img, ox, oy, desc, log_fn):
    q = (f"這是螢幕截圖的局部區域。請找出「{desc}」的中心點。\n"
         f"找到：回傳 {{\"x\":數字,\"y\":數字}}（相對此截圖的像素座標）\n"
         f"找不到：回傳 {{\"x\":null}}\n只回傳 JSON。")
    log_fn(f"  [GPT] 詢問中...")
    answer = ask_gpt4o(img, q)
    log_fn(f"  [GPT] {answer}")
    d = parse_json(answer)
    if d.get("x") is not None:
        return (int(d["x"]) + ox, int(d["y"]) + oy)
    return None

def minimize_win():
    try:
        if _root_ref[0]:
            _root_ref[0].iconify()
            time.sleep(0.4)
    except Exception:
        pass

def restore_win():
    try:
        if _root_ref[0]:
            _root_ref[0].deiconify()
    except Exception:
        pass

def confirm_screen(desc, log_fn):
    """最小化視窗後截全螢幕確認"""
    minimize_win()
    img = pyautogui.screenshot()
    restore_win()
    q = (f"這是螢幕截圖。畫面上是否出現「{desc}」？\n"
         f"只回傳 JSON：{{\"found\":true}} 或 {{\"found\":false}}")
    log_fn(f"  [確認] {desc}")
    answer = ask_gpt4o(img, q)
    log_fn(f"  [確認] {answer}")
    return parse_json(answer).get("found", False)


# ══════════════════════════════════════════════════════
#  校準單一元素（含重試）
# ══════════════════════════════════════════════════════

def calibrate_element(name, desc, region_ratio, before_confirm,
                      after_confirm, log_fn, action="click", max_retry=3):
    if stop_flag.is_set(): return False, None

    log_fn(f"\n── 校準：{name} ──")
    log_fn(f"  目標：{desc}")

    for attempt in range(1, max_retry + 1):
        if stop_flag.is_set(): return False, None
        if attempt > 1:
            log_fn(f"  [重試] 第 {attempt}/{max_retry} 次")

        # A：最小化視窗後截區域，找目標
        minimize_win()
        img, ox, oy = grab_region(*region_ratio)
        restore_win()
        pos = find_target(img, ox, oy, desc, log_fn)
        if not pos:
            log_fn(f"  ❌ 找不到目標，重試...")
            time.sleep(1.0)
            continue
        log_fn(f"  座標：{pos}")

        # B：滑鼠移到安全位置，截正常狀態
        pyautogui.moveTo(SW // 2, 10)
        time.sleep(0.3)
        normal_img = crop_around(pos[0], pos[1])
        normal_path = os.path.join(TPL_DIR, f"{name}_normal.png")
        normal_img.save(normal_path)
        log_fn(f"  [範本] normal → {os.path.basename(normal_path)}")

        # C：滑鼠移到目標，截 hover 狀態
        pyautogui.moveTo(pos[0], pos[1])
        time.sleep(0.4)
        hover_img = crop_around(pos[0], pos[1])
        hover_path = os.path.join(TPL_DIR, f"{name}_hover.png")
        hover_img.save(hover_path)
        log_fn(f"  [範本] hover  → {os.path.basename(hover_path)}")

        # D：最小化視窗，截圖確認滑鼠位置
        log_fn(f"  [點擊前] 確認位置...")
        minimize_win()
        pre_img = pyautogui.screenshot()
        restore_win()
        q = (f"螢幕截圖中，滑鼠目前停在座標({pos[0]},{pos[1]})附近。\n"
             f"請判斷滑鼠停的位置是否是「{before_confirm}」。\n"
             f"只回傳 JSON：{{\"correct\":true}} 或 {{\"correct\":false,\"reason\":\"原因\"}}")
        answer = ask_gpt4o(pre_img, q)
        log_fn(f"  [點擊前] {answer}")
        d = parse_json(answer)
        if not d.get("correct", False):
            log_fn(f"  ⚠️ 位置不對：{d.get('reason','')}，重試...")
            time.sleep(1.0)
            continue

        # E：執行動作
        if action == "click":
            pyautogui.click(pos[0], pos[1])
            log_fn(f"  ✓ 點擊 {pos}")

        # F：最小化視窗，截圖確認點擊後畫面
        time.sleep(1.5)
        ok = confirm_screen(after_confirm, log_fn)
        if ok:
            log_fn(f"  ✓ 點擊後確認成功")
            return True, pos
        else:
            log_fn(f"  ⚠️ 點擊後畫面未如預期，重試...")
            time.sleep(1.0)

    log_fn(f"  ❌ 重試 {max_retry} 次仍失敗")
    return False, None


# ══════════════════════════════════════════════════════
#  主校準流程
# ══════════════════════════════════════════════════════

def run_calibration(w):
    stop_flag.clear()

    def log_fn(msg):
        w.configure(state="normal")
        w.insert(tk.END, msg + "\n")
        w.see(tk.END)
        w.configure(state="disabled")

    log_fn("="*40)
    log_fn("▶ 校準開始")
    log_fn(f"  螢幕：{SW}x{SH}")

    results = {}

    try:
        # ── 元素 1：Windows 搜尋圖示 ──
        ok, pos = calibrate_element(
            "win_search",
            "Windows 工作列上的放大鏡搜尋圖示",
            (0.0, 0.92, 0.5, 1.0),
            "Windows 放大鏡搜尋圖示",
            "Windows 搜尋選單（有輸入框的彈出視窗）",
            log_fn
        )
        if not ok: log_fn("❌ 校準失敗"); return
        results["win_search"] = pos

        # ── 輸入 chrome ──
        log_fn("\n[輸入] chrome...")
        pyautogui.write("chrome", interval=0.05)
        time.sleep(2.0)

        # ── 元素 2：Chrome 圖示 ──
        ok, pos = calibrate_element(
            "chrome_app",
            "搜尋選單最佳比對中的 Google Chrome 應用程式圖示（紅黃綠藍四色圓形）",
            (0.0, 0.4, 0.6, 0.9),
            "Google Chrome 應用程式圖示",
            "Chrome 瀏覽器視窗（有網址列）",
            log_fn
        )
        if not ok: log_fn("❌ 校準失敗"); return
        results["chrome_app"] = pos
        time.sleep(3.0)

        # ── 元素 3：首頁搜尋列 ──
        ok, pos = calibrate_element(
            "yahoo_bar",
            "瀏覽器頁面中央的白色搜尋輸入框",
            (0.1, 0.05, 0.9, 0.35),
            "白色搜尋輸入框",
            "搜尋結果頁面（有多筆結果列表）",
            log_fn
        )
        if not ok: log_fn("❌ 校準失敗"); return
        results["yahoo_bar"] = pos
        pyautogui.write("yt", interval=0.05)
        pyautogui.press("enter")
        time.sleep(3.5)

        # ── 元素 4：YouTube 連結 ──
        ok, pos = calibrate_element(
            "yahoo_yt",
            "搜尋結果中藍色帶底線的 YouTube 網站標題連結",
            (0.0, 0.1, 0.6, 0.5),
            "YouTube 連結文字",
            "YouTube 網站首頁（有 YouTube logo）",
            log_fn
        )
        if not ok: log_fn("❌ 校準失敗"); return
        results["yahoo_yt"] = pos
        time.sleep(5.5)

        # ── 元素 5：YouTube 搜尋列 ──
        ok, pos = calibrate_element(
            "yt_search",
            "YouTube 頂端中央的長條搜尋框",
            (0.2, 0.0, 0.8, 0.12),
            "YouTube 搜尋框",
            "YouTube 搜尋框已被點擊（游標在框內閃爍）",
            log_fn
        )
        if not ok: log_fn("❌ 校準失敗"); return
        results["yt_search"] = pos

        # ── 儲存結果 ──
        result_path = os.path.join(TPL_DIR, "calibration.json")
        with open(result_path, "w") as f:
            json.dump(results, f, indent=2)

        log_fn(f"\n✅ 校準完成！")
        log_fn(f"   範本存到：templates/")
        log_fn(f"   座標存到：calibration.json")
        log_fn(f"   之後執行 chrome_yt_task.py 直接用範本比對")

    except Exception as e:
        log_fn(f"⚠️ 錯誤：{e}")
    finally:
        stop_flag.clear()


# ══════════════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════════════

class App:
    def __init__(self):
        self.root = tk.Tk()
        _root_ref[0] = self.root
        self.root.title("Miniclaw - 校準模式")
        self.root.geometry("520x460")
        self.root.resizable(False, False)
        self.root.configure(bg="#0d0d1a")
        self.root.attributes("-topmost", True)
        self._build_ui()
        self.task_thread = None

    def _build_ui(self):
        tk.Label(self.root, text="Miniclaw 校準模式",
                 fg="#ff6600", bg="#0d0d1a",
                 font=("Arial", 13, "bold")).pack(pady=(14, 4))
        tk.Label(self.root, text="AI 自動找位置 → 截範本 → 確認 → 存檔",
                 fg="#00f0ff", bg="#0d0d1a",
                 font=("Consolas", 9)).pack(pady=(0, 8))

        bf  = tk.Frame(self.root, bg="#0d0d1a")
        bf.pack(pady=4)
        cfg = dict(font=("Arial", 11, "bold"), width=10, relief="flat", cursor="hand2", pady=6)

        self.btn_start = tk.Button(bf, text="開始校準",
            bg="#1a6e2e", fg="white", activebackground="#27a844",
            command=self.start_task, **cfg)
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_stop = tk.Button(bf, text="停止",
            bg="#6e1a1a", fg="white", activebackground="#a82727",
            command=self.stop_task, state="disabled", **cfg)
        self.btn_stop.grid(row=0, column=1, padx=5)

        tk.Button(bf, text="關閉",
            bg="#2a2a2a", fg="#888888", activebackground="#444444",
            command=self.root.destroy, **cfg).grid(row=0, column=2, padx=5)

        tk.Label(self.root, text="校準日誌",
                 fg="#666688", bg="#0d0d1a",
                 font=("Arial", 9)).pack(anchor="w", padx=16, pady=(10, 2))

        self.log_box = scrolledtext.ScrolledText(
            self.root, height=17, state="disabled",
            bg="#07070f", fg="#c8ffc8",
            font=("Consolas", 9), relief="flat", wrap=tk.WORD, padx=8, pady=6)
        self.log_box.pack(fill=tk.BOTH, padx=14, pady=(0, 14))

        self.log_box.configure(state="normal")
        self.log_box.insert(tk.END, "請確保螢幕顯示桌面，然後按「開始校準」。\n")
        self.log_box.configure(state="disabled")

    def start_task(self):
        if self.task_thread and self.task_thread.is_alive(): return
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.task_thread = threading.Thread(
            target=lambda: [run_calibration(self.log_box),
                            self.root.after(0, self._done)], daemon=True)
        self.task_thread.start()

    def _done(self):
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")

    def stop_task(self):
        stop_flag.set()
        self.log_box.configure(state="normal")
        self.log_box.insert(tk.END, "停止指令已送出...\n")
        self.log_box.configure(state="disabled")
        self.btn_stop.config(state="disabled")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()

