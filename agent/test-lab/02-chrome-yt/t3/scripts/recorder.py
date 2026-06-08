"""
Miniclaw Recorder — t3
錄製滑鼠/鍵盤操作，標記說明，產生給 Miniclaw 的 prompt
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading
import time
import json
import base64
import io
import os
import pyautogui
from PIL import Image, ImageDraw, ImageTk
from pynput import mouse, keyboard

# ══════════════════════════════════════════════════════
#  全域狀態
# ══════════════════════════════════════════════════════
records = []          # 所有紀錄 [{type, data, screenshot_b64, label}]
recording = False
stop_hotkey = ["F8"]  # 可自訂
_offset = [0, 0]      # [offset_x, offset_y] 自動校準結果

# pynput listener refs
_mouse_listener  = None
_kb_listener     = None
_kb_buffer       = []   # 暫存連續按鍵，合併成一筆

# 主視窗 ref（給 hotkey thread 用）
_main_app = None

CAPTURE_SIZE = 220   # 截圖範圍 (正方形邊長)

# ══════════════════════════════════════════════════════
#  截圖工具
# ══════════════════════════════════════════════════════
def capture_around(x, y, size=CAPTURE_SIZE):
    """以 (x,y) 為中心截取 size x size 的畫面，回傳 PIL Image"""
    half = size // 2
    left   = max(0, x - half)
    top    = max(0, y - half)
    right  = left + size
    bottom = top  + size
    img = pyautogui.screenshot(region=(left, top, size, size))
    # 畫十字標記點擊位置
    draw = ImageDraw.Draw(img)
    cx = x - left
    cy = y - top
    r = 10
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline="red", width=3)
    draw.line([cx-20, cy, cx+20, cy], fill="red", width=2)
    draw.line([cx, cy-20, cx, cy+20], fill="red", width=2)
    return img

def capture_region(x1, y1, x2, y2):
    """截取指定矩形區域，回傳 (乾淨圖, 預覽圖)"""
    w = abs(x2 - x1)
    h = abs(y2 - y1)
    lx, ly = min(x1,x2), min(y1,y2)
    img = pyautogui.screenshot(region=(lx, ly, w, h))
    # 預覽圖才畫框，原始圖不畫（避免影響比對）
    preview = img.copy()
    draw = ImageDraw.Draw(preview)
    draw.rectangle([1, 1, w-2, h-2], outline="cyan", width=3)
    return img, preview

def img_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

# ══════════════════════════════════════════════════════
#  pynput 事件處理
# ══════════════════════════════════════════════════════
def _flush_kb_buffer():
    """把暫存的按鍵合併成一筆紀錄"""
    global _kb_buffer
    if not _kb_buffer:
        return
    text = _merge_kb_buffer(_kb_buffer)
    _kb_buffer = []
    rec = {"type": "keyboard", "data": text, "screenshot_b64": None, "label": ""}
    records.append(rec)
    # 不在這裡更新 UI，停止後統一 refresh

def _is_recorder_window_active():
    """檢查目前前景視窗是否是 recorder 自己，是的話不記錄"""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
        title = buf.value
        return "Miniclaw Recorder" in title
    except Exception:
        return False

def on_click(x, y, button, pressed):
    if not recording or not pressed:
        return
    # 點到 recorder 視窗本身不記錄
    if _is_recorder_window_active():
        return
    _flush_kb_buffer()
    btn_name = "左鍵" if button == mouse.Button.left else \
               "右鍵" if button == mouse.Button.right else "中鍵"
    # 先記座標，截圖在背景 thread 處理，不阻塞 pynput
    rec = {
        "type": "click",
        "data": {"x": x, "y": y, "button": btn_name},
        "screenshot_b64": None,
        "label": ""
    }
    records.append(rec)
    idx = len(records) - 1

    def _do_capture():
        img = capture_around(x, y)
        records[idx]["screenshot_b64"] = img_to_b64(img)

    threading.Thread(target=_do_capture, daemon=True).start()

def _key_to_str(key):
    try:
        if key.char:
            return key.char
    except AttributeError:
        pass
    return f"[{key.name}]"

def _merge_kb_buffer(buf):
    """字元直接串，特殊鍵前後加空格"""
    result = ""
    for token in buf:
        if token.startswith("["):
            result = result.rstrip() + " " + token + " "
        else:
            result += token
    return result.strip()

def on_press(key):
    if not recording:
        return
    _kb_buffer.append(_key_to_str(key))

# 用 ctypes 輪詢熱鍵，獨立 thread，不依賴 pynput 路徑
VK_MAP = {
    "F5":0x74,"F6":0x75,"F7":0x76,"F8":0x77,
    "F9":0x78,"F10":0x79,"F11":0x7A,"F12":0x7B,
}
_hotkey_prev = [False]   # 上次狀態（防連發）

def _hotkey_thread():
    import ctypes
    while True:
        if recording:
            vk = VK_MAP.get(stop_hotkey[0], 0x77)
            pressed = bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)
            if pressed and not _hotkey_prev[0]:
                # 直接在這裡停止，不經過 tkinter after
                global _mouse_listener, _kb_listener
                _flush_kb_buffer()
                if _mouse_listener:
                    _mouse_listener.stop()
                if _kb_listener:
                    _kb_listener.stop()
                # 再用 after 更新 UI
                if _main_app:
                    _main_app.after(0, _main_app._on_hotkey_stop)
            _hotkey_prev[0] = pressed
        time.sleep(0.05)

threading.Thread(target=_hotkey_thread, daemon=True).start()

# ══════════════════════════════════════════════════════
#  遮罩：手動標記點或區域
# ══════════════════════════════════════════════════════
class OverlayWindow:
    def __init__(self, mode, callback):
        """
        mode: 'point' | 'region'
        callback(data, img): data = (x,y) or (x1,y1,x2,y2), img = PIL Image
        """
        self.mode = mode
        self.callback = callback
        self.start_xy = None

        sw = pyautogui.size().width
        sh = pyautogui.size().height

        self.root = tk.Toplevel()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.35)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")
        self.root.overrideredirect(True)

        self.canvas = tk.Canvas(self.root, bg="black",
                                highlightthickness=0,
                                width=sw, height=sh)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        hint = "點擊確認位置" if mode == "point" else "拖曳框選區域"
        self.canvas.create_text(sw//2, 40, text=f"{hint}  |  ESC 取消",
                                fill="white", font=("Arial", 16, "bold"))

        self.rect_id = None
        self.root.bind("<Escape>", lambda e: self.cancel())
        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def _on_press(self, e):
        self.start_xy = (e.x, e.y)
        if self.rect_id:
            self.canvas.delete(self.rect_id)

    def _on_drag(self, e):
        if self.mode == "region" and self.start_xy:
            if self.rect_id:
                self.canvas.delete(self.rect_id)
            self.rect_id = self.canvas.create_rectangle(
                self.start_xy[0], self.start_xy[1], e.x, e.y,
                outline="cyan", width=2)

    def _on_release(self, e):
        if self.mode == "point":
            x, y = e.x, e.y
            self.root.destroy()
            img = capture_around(x, y)
            self.callback((x, y), img, img)
        else:
            if not self.start_xy:
                return
            x1, y1 = self.start_xy
            x2, y2 = e.x, e.y
            self.root.destroy()
            img, preview = capture_region(x1, y1, x2, y2)
            self.callback((x1, y1, x2, y2), img, preview)

    def cancel(self):
        self.root.destroy()

# ══════════════════════════════════════════════════════
#  主視窗
# ══════════════════════════════════════════════════════
class App:
    def __init__(self):
        global _main_app
        _main_app = self

        self.root = tk.Tk()
        self.root.title("Miniclaw Recorder — t3")
        self.root.configure(bg="#0d0d1a")
        self.root.resizable(True, True)
        self.root.geometry("620x800")
        self.root.attributes("-topmost", True)

        self._build_ui()

    # ── UI 建構 ──────────────────────────────────────
    def _build_ui(self):
        PAD = {"padx": 12, "pady": 4}

        # 標題
        tk.Label(self.root, text="🎬 Miniclaw Recorder",
                 bg="#0d0d1a", fg="#00f0ff",
                 font=("Arial", 14, "bold")).pack(pady=(12, 4))

        # ── 停止按鈕置頂（縮小也看得到）──
        stop_top = tk.Frame(self.root, bg="#0d0d1a")
        stop_top.pack(fill=tk.X, padx=12, pady=(0, 4))
        self.btn_stop = tk.Button(stop_top, text="■ 停止錄製  (F8)",
                                  command=self.stop_recording,
                                  state=tk.DISABLED,
                                  bg="#440000", fg="#ff4444",
                                  relief="flat", font=("Arial", 11, "bold"),
                                  pady=6, activebackground="#660000")
        self.btn_stop.pack(fill=tk.X)

        # ── 主訊息區 ──
        tk.Label(self.root, text="📝 主要訊息（給 AI 的整體說明）",
                 bg="#0d0d1a", fg="#aaaacc",
                 font=("Arial", 9)).pack(anchor="w", **PAD)
        self.main_msg = scrolledtext.ScrolledText(
            self.root, height=4, bg="#1a1a2e", fg="#e0e0ff",
            font=("Arial", 10), relief="flat", wrap=tk.WORD,
            insertbackground="white")
        self.main_msg.pack(fill=tk.X, **PAD)

        # ── 座標偏移校正 ──
        offset_frame = tk.Frame(self.root, bg="#0d0d1a")
        offset_frame.pack(fill=tk.X, **PAD)
        tk.Button(offset_frame, text="🎯 自動校準座標",
                  command=self.start_calibrate,
                  bg="#1a1a2e", fg="#ffcc00", relief="flat",
                  font=("Arial", 9), padx=8, pady=3,
                  activebackground="#2a2a4e").pack(side=tk.LEFT)
        self.calib_label = tk.Label(offset_frame,
                  text="（尚未校準）",
                  bg="#0d0d1a", fg="#555566", font=("Arial", 8))
        self.calib_label.pack(side=tk.LEFT, padx=8)

        # ── 控制列 ──
        ctrl = tk.Frame(self.root, bg="#0d0d1a")
        ctrl.pack(fill=tk.X, **PAD)

        btn_cfg = dict(bg="#1a1a2e", fg="#00f0ff", relief="flat",
                       font=("Arial", 10), padx=10, pady=4,
                       activebackground="#2a2a4e")

        self.btn_rec = tk.Button(ctrl, text="▶ 開始錄製",
                                 command=self.start_recording, **btn_cfg)
        self.btn_rec.pack(side=tk.LEFT, padx=4)

        # 熱鍵選單
        tk.Label(ctrl, text="停止熱鍵：",
                 bg="#0d0d1a", fg="#888888",
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=(12, 2))
        self.hk_var = tk.StringVar(value="F8")
        hk_menu = tk.OptionMenu(ctrl, self.hk_var,
                                 "F5","F6","F7","F8","F9","F10","F11","F12",
                                 command=lambda v: stop_hotkey.__setitem__(0, v))
        hk_menu.configure(bg="#1a1a2e", fg="#00f0ff",
                          activebackground="#2a2a4e",
                          relief="flat", font=("Arial", 9))
        hk_menu.pack(side=tk.LEFT)

        # 錄製狀態燈
        self.rec_label = tk.Label(ctrl, text="⚫ 待機",
                                   bg="#0d0d1a", fg="#666666",
                                   font=("Arial", 9))
        self.rec_label.pack(side=tk.RIGHT, padx=8)

        # ── 手動新增 ──
        add_frame = tk.Frame(self.root, bg="#0d0d1a")
        add_frame.pack(fill=tk.X, **PAD)

        tk.Button(add_frame, text="＋ 新增點",
                  command=self.add_point, **btn_cfg).pack(side=tk.LEFT, padx=4)
        tk.Button(add_frame, text="＋ 新增區域",
                  command=self.add_region, **btn_cfg).pack(side=tk.LEFT, padx=4)
        tk.Button(add_frame, text="🗑 清除全部",
                  command=self.clear_all,
                  bg="#1a1a2e", fg="#ff6666",
                  relief="flat", font=("Arial", 10),
                  padx=10, pady=4,
                  activebackground="#2a2a4e").pack(side=tk.RIGHT, padx=4)

        # ── 分隔 ──
        ttk.Separator(self.root, orient="horizontal").pack(fill=tk.X, pady=6)

        # ── 紀錄清單（可捲動）──
        tk.Label(self.root, text="📋 錄製紀錄",
                 bg="#0d0d1a", fg="#aaaacc",
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=12)

        list_frame = tk.Frame(self.root, bg="#0d0d1a")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        self.canvas_list = tk.Canvas(list_frame, bg="#0d0d1a",
                                     highlightthickness=0)
        sb = tk.Scrollbar(list_frame, orient="vertical",
                          command=self.canvas_list.yview)
        self.canvas_list.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.list_inner = tk.Frame(self.canvas_list, bg="#0d0d1a")
        self._list_window = self.canvas_list.create_window(
            (0, 0), window=self.list_inner, anchor="nw")
        self.list_inner.bind("<Configure>", self._on_inner_configure)
        self.canvas_list.bind("<Configure>", self._on_canvas_configure)
        # 滑鼠滾輪
        self.canvas_list.bind_all("<MouseWheel>",
            lambda e: self.canvas_list.yview_scroll(-1*(e.delta//120), "units"))

        # ── 輸出按鈕 ──
        out_frame = tk.Frame(self.root, bg="#0d0d1a")
        out_frame.pack(fill=tk.X, padx=12, pady=8)

        tk.Button(out_frame, text="✅ 完成，產出並複製給 Miniclaw",
                  command=self.finish_and_copy,
                  bg="#003322", fg="#00ff88", relief="flat",
                  font=("Arial", 11, "bold"), padx=10, pady=6,
                  activebackground="#004433").pack(fill=tk.X, padx=4, pady=(0,4))

        hint_frame = tk.Frame(out_frame, bg="#0d0d1a")
        hint_frame.pack(fill=tk.X, padx=4)
        tk.Label(hint_frame, text="① 自動匯出 JSON 備份",
                 bg="#0d0d1a", fg="#556655", font=("Arial", 8)).pack(side=tk.LEFT)
        tk.Label(hint_frame, text="② 複製文字到剪貼簿",
                 bg="#0d0d1a", fg="#556655", font=("Arial", 8)).pack(side=tk.LEFT, padx=12)
        tk.Label(hint_frame, text="③ 貼到 Miniclaw 說明需求",
                 bg="#0d0d1a", fg="#556655", font=("Arial", 8)).pack(side=tk.LEFT)

        tk.Button(out_frame, text="💾 只匯出 JSON",
                  command=self.export_json,
                  bg="#1a1a2e", fg="#888888", relief="flat",
                  font=("Arial", 9), padx=8, pady=3,
                  activebackground="#2a2a4e").pack(anchor="e", padx=4, pady=(4,0))

        # 儲存 label widget refs
        self._record_widgets = []

    def _on_inner_configure(self, e):
        self.canvas_list.configure(
            scrollregion=self.canvas_list.bbox("all"))

    def _on_canvas_configure(self, e):
        self.canvas_list.itemconfig(self._list_window, width=e.width)

    # ── 錄製控制 ──────────────────────────────────────
    def start_recording(self):
        global recording, _mouse_listener, _kb_listener, _kb_buffer
        if recording:
            return
        recording = True
        _kb_buffer = []
        self.btn_rec.configure(state=tk.DISABLED)
        self.btn_stop.configure(state=tk.NORMAL)
        self.rec_label.configure(text="🔴 錄製中", fg="#ff4444")

        _mouse_listener = mouse.Listener(on_click=on_click)
        _kb_listener    = keyboard.Listener(on_press=on_press)
        _mouse_listener.start()
        _kb_listener.start()

        # 不縮小，改成迷你模式（小浮動條）
        self._switch_to_mini_mode()

    def stop_recording(self):
        global recording, _mouse_listener, _kb_listener
        if not recording:
            return
        recording = False
        _flush_kb_buffer()

        if _mouse_listener:
            _mouse_listener.stop()
        if _kb_listener:
            _kb_listener.stop()

        self.btn_rec.configure(state=tk.NORMAL)
        self.btn_stop.configure(state=tk.NORMAL)
        self.rec_label.configure(text="⚫ 待機", fg="#666666")
        self._switch_to_full_mode()
        self.root.after(500, self.refresh_records)

    def _on_hotkey_stop(self):
        """hotkey thread 觸發，只做 UI 部分（listener 已在 thread 裡停了）"""
        global recording
        recording = False
        self.btn_rec.configure(state=tk.NORMAL)
        self.btn_stop.configure(state=tk.DISABLED)
        self.rec_label.configure(text="⚫ 待機", fg="#666666")
        self._switch_to_full_mode()
        self.root.after(500, self.refresh_records)

    def _switch_to_mini_mode(self):
        """縮成右上角小浮動條，顯示停止按鈕"""
        sw = self.root.winfo_screenwidth()
        self.root.geometry(f"300x80+{sw - 310}+0")
        self.root.attributes("-alpha", 0.9)

    def _switch_to_full_mode(self):
        """還原完整視窗"""
        self.root.geometry("620x800")
        self.root.attributes("-alpha", 1.0)
        self.root.deiconify()
        self.root.lift()

    # ── 手動新增 ──────────────────────────────────────
    def add_point(self):
        self.root.iconify()
        time.sleep(0.4)
        def cb(data, img, preview):
            label = simpledialog.askstring("說明", "請輸入這個點的說明：",
                                            parent=self.root) or ""
            rec = {"type": "manual_point",
                   "data": {"x": data[0], "y": data[1]},
                   "screenshot_b64": img_to_b64(img),
                   "label": label}
            records.append(rec)
            self.root.deiconify()
            self.refresh_records()
        OverlayWindow("point", cb)

    def add_region(self):
        self.root.iconify()
        time.sleep(0.4)
        def cb(data, img, preview):
            label = simpledialog.askstring("說明", "請輸入這個區域的說明：",
                                            parent=self.root) or ""
            rec = {"type": "manual_region",
                   "data": {"x1": data[0], "y1": data[1],
                             "x2": data[2], "y2": data[3]},
                   "screenshot_b64": img_to_b64(img),         # 乾淨圖（比對用）
                   "preview_b64":    img_to_b64(preview),     # 有框圖（顯示用）
                   "label": label}
            records.append(rec)
            self.root.deiconify()
            self.refresh_records()
        OverlayWindow("region", cb)

    # ── 清除 ──────────────────────────────────────────
    def clear_all(self):
        if messagebox.askyesno("確認", "清除所有紀錄？"):
            records.clear()
            # 同時重置按鈕狀態，確保可以重新開始錄製
            self.btn_rec.configure(state=tk.NORMAL)
            self.btn_stop.configure(state=tk.DISABLED)
            self.rec_label.configure(text="⚫ 待機", fg="#666666")
            self.refresh_records()

    # ── 紀錄清單渲染 ─────────────────────────────────
    def refresh_records(self):
        # 清空舊 widget
        for w in self.list_inner.winfo_children():
            w.destroy()
        self._record_widgets = []

        for i, rec in enumerate(records):
            self._render_record(i, rec)

        self.canvas_list.update_idletasks()
        self.canvas_list.yview_moveto(1.0)

    def _render_record(self, idx, rec):
        frame = tk.Frame(self.list_inner, bg="#111128",
                         relief="flat", bd=1)
        frame.pack(fill=tk.X, pady=3, padx=2)

        # ── 標題列 ──
        hf = tk.Frame(frame, bg="#111128")
        hf.pack(fill=tk.X, padx=8, pady=(6, 2))

        icon, title = self._rec_title(rec)
        tk.Label(hf, text=f"{icon} #{idx+1}  {title}",
                 bg="#111128", fg="#ccccff",
                 font=("Consolas", 9)).pack(side=tk.LEFT)

        # 刪除、上移、下移、跳到第N步按鈕
        btn_cfg = dict(bg="#111128", relief="flat",
                       font=("Arial", 9), padx=4, pady=0)
        tk.Button(hf, text="✕", fg="#ff6666",
                  command=lambda i=idx: self._delete_record(i),
                  **btn_cfg).pack(side=tk.RIGHT)
        tk.Button(hf, text="▼", fg="#aaaaaa",
                  command=lambda i=idx: self._move_record(i, 1),
                  **btn_cfg).pack(side=tk.RIGHT)
        tk.Button(hf, text="▲", fg="#aaaaaa",
                  command=lambda i=idx: self._move_record(i, -1),
                  **btn_cfg).pack(side=tk.RIGHT)

        # 跳到第N步
        jump_entry = tk.Entry(hf, width=3, bg="#1e1e3a", fg="#00f0ff",
                              font=("Arial", 9), relief="flat",
                              insertbackground="white", justify="center")
        jump_entry.pack(side=tk.RIGHT, padx=(0, 2))
        tk.Label(hf, text="→", bg="#111128", fg="#aaaaaa",
                 font=("Arial", 9)).pack(side=tk.RIGHT)
        # Enter 或點「→」都觸發
        def _jump(e=None, i=idx, w=jump_entry):
            try:
                target = int(w.get()) - 1  # 玩家輸入 1-based
                self._move_record_to(i, target)
            except ValueError:
                pass
        jump_entry.bind("<Return>", _jump)
        tk.Button(hf, text="移至", fg="#aaaaaa",
                  command=_jump, **btn_cfg).pack(side=tk.RIGHT)

        # ── 截圖縮圖 ──
        if rec.get("screenshot_b64"):
            try:
                data = base64.b64decode(rec["screenshot_b64"])
                img = Image.open(io.BytesIO(data))
                img.thumbnail((200, 120))
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(frame, image=photo, bg="#111128")
                lbl.image = photo  # 防止 GC
                lbl.pack(padx=8, pady=2)
            except Exception:
                pass

        # ── 說明輸入框 ──
        tk.Label(frame, text="說明：",
                 bg="#111128", fg="#888888",
                 font=("Arial", 8)).pack(anchor="w", padx=8)

        entry = tk.Text(frame, height=2, bg="#1e1e3a", fg="#e0e0ff",
                        font=("Arial", 9), relief="flat",
                        insertbackground="white", wrap=tk.WORD)
        entry.insert("1.0", rec.get("label", ""))
        entry.pack(fill=tk.X, padx=8, pady=(0, 6))

        # 同步說明到 records
        def _sync(e, i=idx, w=entry):
            records[i]["label"] = w.get("1.0", tk.END).strip()
        entry.bind("<KeyRelease>", _sync)

    def start_calibrate(self):
        """按下後等玩家在任意地方點一下，同時比對 pynput 和 pyautogui 的座標"""
        self.calib_label.configure(text="請在任意位置點一下...", fg="#ffcc00")
        self.root.update()

        def _run():
            def _on_calib_click(x, y, button, pressed):
                if not pressed:
                    return False
                pg_pos = pyautogui.position()
                _offset[0] = pg_pos.x - x
                _offset[1] = pg_pos.y - y
                self.root.after(0, lambda: self.calib_label.configure(
                    text=f"✓ 偏移 X:{_offset[0]:+d} Y:{_offset[1]:+d}",
                    fg="#00ff88"))
                return False

            cal_listener = mouse.Listener(on_click=_on_calib_click)
            cal_listener.start()
            cal_listener.join()

        threading.Thread(target=_run, daemon=True).start()

    def _get_offset(self):
        return _offset[0], _offset[1]

    def _rec_title(self, rec, apply_offset=False):
        ox, oy = self._get_offset() if apply_offset else (0, 0)
        t = rec["type"]
        if t == "click":
            d = rec["data"]
            return "🖱️", f"點擊 {d['button']}  ({d['x']+ox}, {d['y']+oy})"
        elif t == "keyboard":
            return "⌨️", f"輸入：{rec['data']}"
        elif t == "manual_point":
            d = rec["data"]
            return "📍", f"標記點  ({d['x']+ox}, {d['y']+oy})"
        elif t == "manual_region":
            d = rec["data"]
            return "📦", f"標記區域  ({d['x1']+ox},{d['y1']+oy}) → ({d['x2']+ox},{d['y2']+oy})"
        return "❓", str(rec)

    def _delete_record(self, idx):
        if 0 <= idx < len(records):
            records.pop(idx)
            self.refresh_records()

    def _move_record(self, idx, direction):
        """direction: -1 上移, 1 下移"""
        new_idx = idx + direction
        if 0 <= new_idx < len(records):
            records[idx], records[new_idx] = records[new_idx], records[idx]
            self.refresh_records()

    def _move_record_to(self, idx, target):
        """把第 idx 筆移到第 target 位置（0-based）"""
        if idx == target:
            return
        if not (0 <= target < len(records)):
            return
        rec = records.pop(idx)
        records.insert(target, rec)
        self.refresh_records()

    # ── 輸出 ─────────────────────────────────────────
    def finish_and_copy(self):
        """一鍵完成：匯出 JSON + 複製文字，引導玩家貼到 Miniclaw"""
        if not records:
            messagebox.showwarning("沒有紀錄", "還沒有任何錄製內容。")
            return
        # ① 自動匯出 JSON
        out_dir = os.path.join(os.path.dirname(__file__), "..", "captures")
        os.makedirs(out_dir, exist_ok=True)
        fname = os.path.join(out_dir, f"session_{int(time.time())}.json")
        data = {
            "main_message": self.main_msg.get("1.0", tk.END).strip(),
            "records": records
        }
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # ② 複製文字
        self.copy_for_miniclaw(silent=True)

        # ③ 提示
        messagebox.showinfo("完成",
            f"✅ 已完成！\n\n"
            f"📁 JSON 備份已存到：\n{fname}\n\n"
            f"📋 操作紀錄已複製到剪貼簿\n\n"
            f"➡ 現在貼到 Miniclaw 對話框，\n"
            f"   告訴他你要做什麼就可以了！")

    def copy_for_miniclaw(self, silent=False):
        main_msg = self.main_msg.get("1.0", tk.END).strip()
        lines = []

        if main_msg:
            lines.append("【主要說明】")
            lines.append(main_msg)
            lines.append("")

        lines.append("【操作紀錄】")
        for i, rec in enumerate(records):
            icon, title = self._rec_title(rec, apply_offset=True)
            label = rec.get("label", "").strip()
            line = f"{i+1}. {icon} {title}"
            if label:
                line += f"\n   → {label}"
            lines.append(line)

        lines.append("")
        lines.append("【任務說明】")
        lines.append("（請在此說明你要 Miniclaw 做什麼）")

        text = "\n".join(lines)
        # 用 pyperclip 寫入，關閉視窗後內容不會消失
        import pyperclip
        pyperclip.copy(text)

        if not silent:
            messagebox.showinfo("已複製", "已複製到剪貼簿，貼到 Miniclaw 即可。")

    def export_json(self):
        out_dir = os.path.join(os.path.dirname(__file__), "..", "captures")
        os.makedirs(out_dir, exist_ok=True)
        fname = os.path.join(out_dir,
                             f"session_{int(time.time())}.json")
        data = {
            "main_message": self.main_msg.get("1.0", tk.END).strip(),
            "records": records
        }
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("已匯出", f"存到：\n{fname}")

    # ── 主迴圈 ───────────────────────────────────────
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        self.stop_recording()
        self.root.destroy()


# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    App().run()
