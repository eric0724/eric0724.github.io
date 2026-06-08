"""
Chrome + YouTube 自動化搜尋腳本（GPT-4o Vision + 紅點校準版）
=============================================================
啟動時先用紅點校準 GPT 座標偏移
之後每步截全螢幕傳給 GPT，附上螢幕尺寸和錨點資訊
"""

import os, time, threading, base64, json, io
import tkinter as tk
from tkinter import scrolledtext
import pyautogui
from PIL import ImageGrab, ImageTk, ImageDraw
import ctypes
import urllib.request

try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

pyautogui.FAILSAFE = True
pyautogui.PAUSE    = 0.15

stop_flag = threading.Event()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

SW, SH = pyautogui.size()

# 預覽視窗
_preview_win   = [None]
_preview_label = [None]

# GPT 座標校正參數
_offset_x = [0.0]
_offset_y = [0.0]
_scale_x  = [1.0]
_scale_y  = [1.0]

# 停止熱鍵設定
_hotkey = ["F8"]

def _hotkey_listener():
    """背景執行緒監聽停止熱鍵，不需要視窗焦點"""
    import ctypes
    VK_MAP = {
        "F1":0x70,"F2":0x71,"F3":0x72,"F4":0x73,"F5":0x74,
        "F6":0x75,"F7":0x76,"F8":0x77,"F9":0x78,"F10":0x79,
        "F11":0x7A,"F12":0x7B,
    }
    while True:
        vk = VK_MAP.get(_hotkey[0], 0x77)
        if ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000:
            if not stop_flag.is_set():
                stop_flag.set()
                print(f"[{_hotkey[0]}] 停止指令已送出")
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

def img_to_b64(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def parse_json(text):
    try:
        s = text.find("{"); e = text.rfind("}") + 1
        if s >= 0 and e > s:
            return json.loads(text[s:e])
    except Exception:
        pass
    return {}

def ask_gpt4o(img, question):
    payload = json.dumps({
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {
                "url": f"data:image/png;base64,{img_to_b64(img)}", "detail": "high"}}
        ]}],
        "max_tokens": 200
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {OPENAI_API_KEY}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"ERROR:{e}"

def click_at(x, y):
    """點擊指定座標（移動游標）"""
    pyautogui.click(x, y)

def grab_full():
    """截全螢幕前先隱藏預覽視窗，截完再還原"""
    try:
        if _preview_win[0] and _preview_win[0].winfo_exists():
            _preview_win[0].withdraw()
            time.sleep(0.4)
    except Exception:
        pass
    img = pyautogui.screenshot()
    try:
        if _preview_win[0] and _preview_win[0].winfo_exists():
            _preview_win[0].deiconify()
    except Exception:
        pass
    return img, 0, 0
    """截全螢幕前先隱藏預覽視窗，截完再還原"""
    try:
        if _preview_win[0] and _preview_win[0].winfo_exists():
            _preview_win[0].withdraw()
            time.sleep(0.4)  # 等視窗完全消失
    except Exception:
        pass

    img = pyautogui.screenshot()

    try:
        if _preview_win[0] and _preview_win[0].winfo_exists():
            _preview_win[0].deiconify()
    except Exception:
        pass

    return img, 0, 0

def show_preview(img, title="截圖預覽"):
    """把截圖加到歷史紀錄列表（不覆蓋，可往上捲看之前的）"""
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

                # 捲動框架
                canvas = tk.Canvas(win, bg="#0d0d1a", highlightthickness=0)
                sb = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
                canvas.configure(yscrollcommand=sb.set)
                sb.pack(side="right", fill="y")
                canvas.pack(side="left", fill="both", expand=True)

                frame = tk.Frame(canvas, bg="#0d0d1a")
                canvas_win = canvas.create_window((0,0), window=frame, anchor="nw")

                def on_resize(e):
                    canvas.configure(scrollregion=canvas.bbox("all"))
                frame.bind("<Configure>", on_resize)

                _preview_win[0]   = win
                _preview_label[0] = (canvas, frame)

            canvas, frame = _preview_label[0]

            # 加新的截圖到列表底部
            item_frame = tk.Frame(frame, bg="#1a1a2e", bd=1, relief="solid")
            item_frame.pack(fill="x", padx=4, pady=3)

            tk.Label(item_frame, text=title, fg="#00f0ff", bg="#1a1a2e",
                     font=("Consolas", 8), anchor="w").pack(fill="x", padx=4, pady=(3,0))

            lbl = tk.Label(item_frame, image=photo, bg="#1a1a2e")
            lbl.image = photo  # 防止 GC
            lbl.pack(padx=4, pady=(0,4))

            # 捲到最底
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

def apply_correction(gpt_x, gpt_y):
    rx = int(gpt_x * _scale_x[0] + _offset_x[0])
    ry = int(gpt_y * _scale_y[0] + _offset_y[0])
    return rx, ry


# ══════════════════════════════════════════════════════
#  紅點校準
# ══════════════════════════════════════════════════════

def calibrate_gpt_offset(log_fn):
    """
    移滑鼠到 4 個已知位置，在截圖上畫紅點
    問 GPT「紅點在哪裡？」計算偏移和縮放
    """
    cal_points = [
        (int(SW * 0.25), int(SH * 0.25)),
        (int(SW * 0.75), int(SH * 0.25)),
        (int(SW * 0.25), int(SH * 0.75)),
        (int(SW * 0.75), int(SH * 0.75)),
    ]
    real_coords = []
    gpt_coords  = []

    log_fn("[校準] 開始 GPT 座標校準（紅點法）...")

    for i, (rx, ry) in enumerate(cal_points):
        if stop_flag.is_set(): return

        # 不移動滑鼠，直接截圖後用 PIL 畫紅點
        img, _, _ = grab_full()

        # 大紅點 + 白色外框 + 十字線
        marked = img.copy()
        draw   = ImageDraw.Draw(marked)
        r = 25
        draw.ellipse([rx-r, ry-r, rx+r, ry+r], fill="red", outline="white", width=4)
        draw.line([rx-40, ry, rx+40, ry], fill="white", width=3)
        draw.line([rx, ry-40, rx, ry+40], fill="white", width=3)
        draw.text((rx+r+5, ry-10), f"({rx},{ry})", fill="yellow")
        show_preview(marked, f"[校準{i+1}] 紅點位置({rx},{ry})")

        q = (
            f"這是一張 {img.size[0]}x{img.size[1]} 像素的截圖。\n"
            f"座標系統說明：\n"
            f"  左上角 = (0, 0)\n"
            f"  右上角 = ({img.size[0]}, 0)\n"
            f"  左下角 = (0, {img.size[1]})\n"
            f"  右下角 = ({img.size[0]}, {img.size[1]})\n"
            f"  水平中央 x = {img.size[0]//2}\n"
            f"  垂直中央 y = {img.size[1]//2}\n\n"
            f"圖片上有一個大紅色圓形標記（帶白色十字線）。\n"
            f"請根據上方座標系統，回傳紅色圓形中心點的 x,y 座標。\n"
            f"直接回傳 JSON：{{\"x\":數字,\"y\":數字}}"
        )
        found = False
        for attempt in range(3):
            if stop_flag.is_set(): return
            log_fn(f"  [校準{i+1}] 真實({rx},{ry}) 第{attempt+1}次詢問GPT...")
            answer = ask_gpt4o(marked, q)
            log_fn(f"  [校準{i+1}] GPT：{answer}")
            d = parse_json(answer)
            if d.get("x") is not None:
                gx, gy = int(d["x"]), int(d["y"])
                real_coords.append((rx, ry))
                gpt_coords.append((gx, gy))
                log_fn(f"  [校準{i+1}] 差距({rx-gx:+d},{ry-gy:+d})")
                found = True
                break
            log_fn(f"  [校準{i+1}] 找不到，重試...")
            time.sleep(1.0)
        if not found:
            log_fn(f"  [校準{i+1}] ❌ 3次仍找不到，繼續下一點")

    if len(real_coords) < 2:
        log_fn("  ⚠️ 校準點不足，不套用校正")
        return

    # 平均偏移
    dx = sum(r[0]-g[0] for r,g in zip(real_coords,gpt_coords)) / len(real_coords)
    dy = sum(r[1]-g[1] for r,g in zip(real_coords,gpt_coords)) / len(real_coords)

    # 縮放比例
    r1,r2 = real_coords[0], real_coords[-1]
    g1,g2 = gpt_coords[0],  gpt_coords[-1]
    sx = (r2[0]-r1[0])/(g2[0]-g1[0]) if (g2[0]-g1[0])!=0 else 1.0
    sy = (r2[1]-r1[1])/(g2[1]-g1[1]) if (g2[1]-g1[1])!=0 else 1.0
    sx = sx if 0.5 < sx < 2.0 else 1.0
    sy = sy if 0.5 < sy < 2.0 else 1.0

    _offset_x[0]=dx; _offset_y[0]=dy
    _scale_x[0]=sx;  _scale_y[0]=sy
    log_fn(f"  [校準完成] 偏移=({dx:.1f},{dy:.1f}) 縮放=({sx:.3f},{sy:.3f})")


# ══════════════════════════════════════════════════════
#  GPT 找目標
# ══════════════════════════════════════════════════════

def find_target(img, target_desc, log_fn, retries=2):
    """
    兩輪搜尋，每輪切4塊
    傳給 GPT 的是原始截圖（不放大），放大只用於預覽
    GPT 直接回傳螢幕原始座標
    綠點不對時上下左右各試一次，最多重試3次
    """
    W, H = img.size
    log_fn(f"  ══ 搜尋：{target_desc} ══")
    quadrants = [
        ("左上", 0.0, 0.0, 0.5, 0.5),
        ("右上", 0.5, 0.0, 1.0, 0.5),
        ("左下", 0.0, 0.5, 0.5, 1.0),
        ("右下", 0.5, 0.5, 1.0, 1.0),
    ]

    for round_num in range(1, 11):
        log_fn(f"    [第{round_num}輪] 搜尋...")
        for qname, x1r, y1r, x2r, y2r in [("左下", 0.0, 0.5, 0.5, 1.0)]:
            if stop_flag.is_set(): return None

            x1,y1,x2,y2 = int(x1r*W),int(y1r*H),int(x2r*W),int(y2r*H)
            quad = img.crop((x1,y1,x2,y2))

            # 預覽用放大圖（只給人看）
            qw, qh = quad.size
            zoomed = quad.resize((qw*2, qh*2))
            show_preview(zoomed, f"[第{round_num}輪/{qname}] 搜尋「{target_desc}」")

            # 傳給 GPT 的是原始截圖（不放大），座標直接對應螢幕
            question = (
                f"這是螢幕{qname}區域的截圖（未放大）。\n"
                f"注意：此螢幕使用高對比模式，黑白顏色對調（例如Windows搜尋圖示、工作列等元素顏色與一般相反）。請根據元素的形狀、位置和文字來判斷，必要時可依據你對該UI元素的知識自行判斷。\n"
                f"此區域在螢幕上的範圍：x={x1}~{x2}, y={y1}~{y2}\n"
                f"座標參考：左上({x1},{y1}) 右上({x2},{y1}) 左下({x1},{y2}) 右下({x2},{y2})\n"
                f"校準資訊：GPT座標偏移({_offset_x[0]:+.0f},{_offset_y[0]:+.0f})，縮放({_scale_x[0]:.3f},{_scale_y[0]:.3f})，請自行套用。\n\n"
                f"請找出「{target_desc}」的中心點，直接回傳螢幕座標（x={x1}~{x2}, y={y1}~{y2} 範圍內）。\n"
                f"找到：回傳 JSON {{\"x\":數字,\"y\":數字}}\n"
                f"沒有：回傳 JSON {{\"x\":null}}\n"
                f"只回傳 JSON。"
            )

            answer = ask_gpt4o(quad, question)  # 傳原始截圖            log_fn(f"    [{qname}] GPT：{answer}")
            d = parse_json(answer)

            if d.get("x") is None:
                log_fn(f"    [{qname}] 未找到，跳過")
                continue

            cx, cy = apply_correction(int(d["x"]), int(d["y"]))
            log_fn(f"    [{qname}] 找到({d['x']},{d['y']}) → 校正({cx},{cy})")

            # 綠點確認，最多重試3次（上下左右輪流調整）
            adjust_dirs = [(0,0), (-15,0), (15,0), (0,-15), (0,15)]  # 原位, 左, 右, 上, 下
            for adj_i, (adj_x, adj_y) in enumerate(adjust_dirs[:4]):  # 最多3次調整
                if stop_flag.is_set(): return None

                test_cx = cx + adj_x
                test_cy = cy + adj_y

                # 在放大預覽圖上畫綠點
                gx = int((test_cx - x1) * 2)
                gy = int((test_cy - y1) * 2)
                verify_img = zoomed.copy()
                vdraw = ImageDraw.Draw(verify_img)
                vdraw.ellipse([gx-15, gy-15, gx+15, gy+15], fill="lime", outline="white", width=3)
                vdraw.line([gx-25, gy, gx+25, gy], fill="white", width=2)
                vdraw.line([gx, gy-25, gx, gy+25], fill="white", width=2)
                label = "原位" if adj_i == 0 else ["左移","右移","上移","下移"][adj_i-1]
                show_preview(verify_img, f"[確認/{qname}/{label}] 綠點是「{target_desc}」嗎？")

                verify_q = (
                    f"這是螢幕{qname}區域的放大截圖，上面有一個綠色圓點標記。\n"
                    f"注意：截圖可能因螢幕設定呈現黑白或色差，請根據元素形狀、位置和你對該UI的知識來判斷。\n"
                    f"請判斷綠色圓點是否正好標在「{target_desc}」上。\n"
                    f"正確：回傳 JSON {{\"correct\":true}}\n"
                    f"不對：回傳 JSON {{\"correct\":false}}"
                )
                verify_ans = ask_gpt4o(verify_img, verify_q)
                log_fn(f"    [確認{adj_i+1}] {label} {verify_ans}")
                vd = parse_json(verify_ans)

                if vd.get("correct", False):
                    log_fn(f"    ✓ 確認正確，座標({test_cx},{test_cy})")
                    return (test_cx, test_cy)

            log_fn(f"    ⚠️ 3次調整都不對，繼續找下一塊")

    log_fn(f"    ❌ 兩輪都找不到「{target_desc}」")
    return None

def confirm_screen(desc, log_fn):
    img, _, _ = grab_full()
    q = (f"這是螢幕截圖。畫面上是否出現「{desc}」？\n"
         f"只回傳 JSON：{{\"found\":true}} 或 {{\"found\":false}}")
    log_fn(f"    [確認] {desc}")
    answer = ask_gpt4o(img, q)
    log_fn(f"    [確認] {answer}")
    return parse_json(answer).get("found", False)


# ══════════════════════════════════════════════════════
#  主任務
# ══════════════════════════════════════════════════════

def run_task(w):
    stop_flag.clear()
    log("="*40, w)
    log(f"▶ 任務開始  螢幕:{SW}x{SH}", w)

    try:
        # ── 紅點校準 ──
        calibrate_gpt_offset(lambda m: log(m, w))
        time.sleep(0.5)
        if stop_flag.is_set(): return

        # ── Step 1：找 Windows 搜尋圖示 ──
        log("─"*40, w)
        log("[1] 找 Windows 搜尋圖示...", w)
        img, ox, oy = grab_full()
        show_preview(img, "[1] 全螢幕")
        pos = find_target(img, "Windows 工作列上的放大鏡搜尋圖示（此螢幕為高對比模式，黑白顏色對調，放大鏡圖示為白色背景黑色圖示或黑色背景白色圖示）", lambda m: log(m,w))
        if not pos:
            log("❌ 找不到搜尋圖示", w); return
        click_at(pos[0], pos[1])
        log(f"    點擊 {pos}，等待選單...", w)
        time.sleep(1.5)
        if not confirm_screen("Windows 搜尋選單（有輸入框的彈出視窗）", lambda m: log(m,w)):
            log("    選單未出現，再點一次...", w)
            click_at(pos[0], pos[1])
            time.sleep(2.0)
            if not confirm_screen("Windows 搜尋選單（有輸入框的彈出視窗）", lambda m: log(m,w)):
                log("❌ 搜尋選單未打開", w); return
        log("    ✓ 搜尋選單已打開", w)

        # ── Step 2：輸入 chrome ──
        log("[2] 輸入 chrome...", w)
        pyautogui.write("chrome", interval=0.05)
        time.sleep(2.0)

        # ── Step 3：找 Chrome 圖示 ──
        log("[3] 找 Chrome 圖示...", w)
        img, ox, oy = grab_full()
        show_preview(img, "[3] 全螢幕")
        pos = find_target(img,
            "搜尋選單最佳比對中的 Google Chrome 應用程式圖示（紅黃綠藍四色圓形）",
            lambda m: log(m,w))
        if not pos:
            log("❌ 找不到 Chrome 圖示", w); return
        click_at(pos[0], pos[1])
        log(f"    點擊 {pos}，等待 Chrome...", w)
        time.sleep(4.0)
        if not confirm_screen("Chrome 瀏覽器視窗（有網址列）", lambda m: log(m,w)):
            log("❌ Chrome 未打開", w); return
        log("    ✓ Chrome 已打開", w)

        # ── Step 4：找 Chrome 網址列，輸入 yt ──
        log("[4] 找 Chrome 網址列...", w)
        img, ox, oy = grab_full()
        show_preview(img, "[4] 全螢幕")
        pos = find_target(img,
            "Chrome 瀏覽器頂端的網址列輸入框（長條白色框）",
            lambda m: log(m,w))
        if not pos:
            log("❌ 找不到網址列", w); return
        click_at(pos[0], pos[1])
        time.sleep(0.3)
        pyautogui.hotkey("ctrl", "a")
        pyautogui.write("yt", interval=0.05)
        pyautogui.press("enter")
        log("    等待搜尋結果...", w)
        time.sleep(3.5)
        if not confirm_screen("搜尋結果頁面（有多筆結果列表）", lambda m: log(m,w)):
            log("❌ 搜尋結果未出現", w); return
        log("    ✓ 搜尋結果已出現", w)

        # ── Step 5：找 YouTube 連結 ──
        log("[5] 找 YouTube 連結...", w)
        img, ox, oy = grab_full()
        show_preview(img, "[5] 全螢幕")
        pos = find_target(img,
            "搜尋結果中藍色帶底線的 YouTube 網站標題連結文字",
            lambda m: log(m,w))
        if not pos:
            log("❌ 找不到 YouTube 連結", w); return
        click_at(pos[0], pos[1])
        log(f"    點擊 {pos}，等待 YouTube...", w)
        time.sleep(5.5)
        if not confirm_screen("YouTube 網站首頁（有 YouTube logo）", lambda m: log(m,w)):
            log("❌ YouTube 未載入", w); return
        log("    ✓ YouTube 已載入", w)

        # ── Step 6：找 YT 搜尋列，輸入 agent ──
        log("[6] 找 YouTube 搜尋列...", w)
        img, ox, oy = grab_full()
        show_preview(img, "[6] 全螢幕")
        pos = find_target(img,
            "YouTube 網頁頂端中央的長條搜尋框",
            lambda m: log(m,w))
        if not pos:
            log("❌ 找不到 YouTube 搜尋列", w); return
        click_at(pos[0], pos[1])
        time.sleep(0.5)
        pyautogui.write("agent", interval=0.05)
        pyautogui.press("enter")
        time.sleep(3.0)
        if confirm_screen("YouTube 搜尋結果頁面（有影片列表）", lambda m: log(m,w)):
            log("\n✅ 任務完成！", w)
        else:
            log("\n⚠️ 已輸入搜尋，請手動確認", w)

    except Exception as e:
        log(f"⚠️ 錯誤：{e}", w)
    finally:
        stop_flag.clear()


# ══════════════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════════════

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Miniclaw - Vision Mode")
        self.root.geometry("520x460")
        self.root.resizable(False, False)
        self.root.configure(bg="#0d0d1a")
        self.root.attributes("-topmost", True)
        self._build_ui()
        self.task_thread = None

    def _build_ui(self):
        tk.Label(self.root, text="Chrome → YouTube → agent  [Vision]",
                 fg="#ff6600", bg="#0d0d1a",
                 font=("Arial", 12, "bold")).pack(pady=(14, 4))
        tk.Label(self.root, text="GPT-4o 紅點校準 + 全螢幕定位",
                 fg="#00f0ff", bg="#0d0d1a",
                 font=("Consolas", 9)).pack(pady=(0, 8))

        bf  = tk.Frame(self.root, bg="#0d0d1a")
        bf.pack(pady=4)
        cfg = dict(font=("Arial", 11, "bold"), width=10, relief="flat", cursor="hand2", pady=6)

        self.btn_start = tk.Button(bf, text="Start",
            bg="#1a6e2e", fg="white", activebackground="#27a844",
            command=self.start_task, **cfg)
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_stop = tk.Button(bf, text="Stop",
            bg="#6e1a1a", fg="white", activebackground="#a82727",
            command=self.stop_task, state="disabled", **cfg)
        self.btn_stop.grid(row=0, column=1, padx=5)

        tk.Button(bf, text="Close",
            bg="#2a2a2a", fg="#888888", activebackground="#444444",
            command=self.root.destroy, **cfg).grid(row=0, column=2, padx=5)

        tk.Label(self.root, text="⚠ 執行中請勿移動滑鼠",
                 fg="#ffaa00", bg="#0d0d1a",
                 font=("Arial", 9)).pack(pady=(0,4))

        # 熱鍵設定
        hk_frame = tk.Frame(self.root, bg="#0d0d1a")
        hk_frame.pack(pady=(0,4))
        tk.Label(hk_frame, text="停止熱鍵：",
                 fg="#888888", bg="#0d0d1a", font=("Arial",9)).pack(side="left")
        self.hk_var = tk.StringVar(value="F8")
        hk_options = ["F5","F6","F7","F8","F9","F10","F11","F12"]
        hk_menu = tk.OptionMenu(hk_frame, self.hk_var, *hk_options,
                                command=lambda v: _hotkey.__setitem__(0, v))
        hk_menu.configure(bg="#1a1a2e", fg="#00f0ff", activebackground="#2a2a4e",
                          relief="flat", font=("Arial",9))
        hk_menu.pack(side="left")
        tk.Label(hk_frame, text="（執行中按下可停止）",
                 fg="#666666", bg="#0d0d1a", font=("Arial",8)).pack(side="left")

        tk.Label(self.root, text="Log",
                 fg="#666688", bg="#0d0d1a",
                 font=("Arial", 9)).pack(anchor="w", padx=16, pady=(10, 2))

        self.log_box = scrolledtext.ScrolledText(
            self.root, height=17, state="disabled",
            bg="#07070f", fg="#c8ffc8",
            font=("Consolas", 9), relief="flat", wrap=tk.WORD, padx=8, pady=6)
        self.log_box.pack(fill=tk.BOTH, padx=14, pady=(0, 14))

        # 右鍵選單：複製全部 / 複製選取
        def _copy_all():
            self.root.clipboard_clear()
            self.root.clipboard_append(self.log_box.get("1.0", tk.END))
        def _copy_sel():
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(self.log_box.get(tk.SEL_FIRST, tk.SEL_LAST))
            except tk.TclError:
                pass
        def _enable_select(e):
            self.log_box.configure(state="normal")
        def _disable_select(e):
            self.log_box.configure(state="disabled")

        ctx = tk.Menu(self.log_box, tearoff=0)
        ctx.add_command(label="複製選取", command=_copy_sel)
        ctx.add_command(label="複製全部", command=_copy_all)

        def _show_ctx(e):
            self.log_box.configure(state="normal")
            ctx.tk_popup(e.x_root, e.y_root)
            self.log_box.configure(state="disabled")

        self.log_box.bind("<Button-3>", _show_ctx)
        self.log_box.bind("<Button-1>", _enable_select)
        self.log_box.bind("<ButtonRelease-1>", _disable_select)
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

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()



