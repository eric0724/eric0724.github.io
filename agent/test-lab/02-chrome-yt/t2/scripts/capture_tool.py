# -*- coding: utf-8 -*-
"""
capture_tool.py
==================================
視覺化標記與截圖工具
- 提供 tkinter GUI 介面，永遠置頂。
- 讓使用者以「單擊點」或「拖曳區域」標記多個 UI 元素。
- 一鍵隱藏視窗、截取乾淨畫面、自動裁切範本並儲存。
- 自動生成與舊版相容的 templates/ 資料夾與 calibration.json。
"""

import os
import json
import time
import ctypes
import tkinter as tk
from tkinter import messagebox, ttk
import pyautogui
from PIL import Image, ImageGrab, ImageTk, ImageDraw

# 啟用 Windows DPI 感知，避免高解析度螢幕座標縮放偏移
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# 設定資料夾路徑
_DIR = os.path.dirname(os.path.abspath(__file__))
TPL_DIR = os.path.abspath(os.path.join(_DIR, "..", "templates"))
os.makedirs(TPL_DIR, exist_ok=True)
CALIBRATION_PATH = os.path.join(TPL_DIR, "calibration.json")

# 預設元素清單
DEFAULT_ELEMENTS = [
    {"name": "win_search", "label": "Windows 搜尋圖示", "type": "Click"},
    {"name": "chrome_app", "label": "Chrome 應用程式圖示", "type": "Click"},
    {"name": "yahoo_bar", "label": "首頁白色搜尋列", "type": "Region"},
    {"name": "yahoo_yt", "label": "YouTube 網站連結", "type": "Region"},
    {"name": "yt_search", "label": "YouTube 搜尋列", "type": "Click"}
]

class CaptureToolApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Miniclaw Capture Tool")
        self.root.geometry("480x520")
        self.root.configure(bg="#0d0d1a")
        self.root.attributes("-topmost", True)
        
        # 儲存標記資料: {name: {"type": "Click"/"Region", "coords": (x, y) or (x1, y1, x2, y2), "label": label}}
        self.markers = {}
        self.load_existing_calibration()
        
        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # 自訂 ttk 樣式
        self.style.configure("TFrame", background="#0d0d1a")
        self.style.configure("TLabel", background="#0d0d1a", foreground="#ffffff", font=("Microsoft JhengHei", 9))
        self.style.configure("Header.TLabel", background="#0d0d1a", foreground="#ff6600", font=("Microsoft JhengHei", 12, "bold"))
        self.style.configure("Sub.TLabel", background="#0d0d1a", foreground="#00f0ff", font=("Consolas", 8))
        
        # 表格樣式
        self.style.configure("Treeview", 
                             background="#07070f", 
                             foreground="#ffffff", 
                             fieldbackground="#07070f",
                             rowheight=26,
                             font=("Microsoft JhengHei", 9))
        self.style.map("Treeview", background=[("selected", "#ff6600")])
        
        self.style.configure("Treeview.Heading", 
                             background="#1a1a2e", 
                             foreground="#ffffff", 
                             font=("Microsoft JhengHei", 9, "bold"))

    def load_existing_calibration(self):
        # 嘗試載入舊有的 calibration.json 以維持進度
        if os.path.exists(CALIBRATION_PATH):
            try:
                with open(CALIBRATION_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        # v 通常是 [x, y] 坐標
                        # 我們預設讀取為 Click 型態，如果是特定的則保留
                        el_def = next((x for x in DEFAULT_ELEMENTS if x["name"] == k), None)
                        el_type = el_def["type"] if el_def else "Click"
                        el_label = el_def["label"] if el_def else k
                        
                        # 檢查坐標長度
                        if isinstance(v, list):
                            if len(v) == 2:
                                self.markers[k] = {"type": "Click", "coords": tuple(v), "label": el_label}
                            elif len(v) == 4:
                                self.markers[k] = {"type": "Region", "coords": tuple(v), "label": el_label}
            except Exception as e:
                print(f"載入現有 calibration 失敗: {e}")

    def build_ui(self):
        # 標題
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        logo_label = ttk.Label(title_frame, text="🦞 MINICLAW CAPTURE TOOL", style="Header.TLabel")
        logo_label.pack(anchor=tk.W)
        
        desc_label = ttk.Label(title_frame, text="視覺化標記範本裁切工具 (100% 精準免 AI)", style="Sub.TLabel")
        desc_label.pack(anchor=tk.W)

        # 主要內容區域
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # 說明提示
        tip_text = "操作流程：\n1. 選擇下方元素列表\n2. 點擊「標記位置」並在螢幕上進行標記 (單擊點或拖曳區)\n3. 準備好畫面，點擊「📸 一鍵截圖全部」生成乾淨範本"
        tip_box = tk.Text(main_frame, height=4, bg="#1a1a2e", fg="#e0e0e0", 
                          font=("Microsoft JhengHei", 8), relief="flat", padx=8, pady=6)
        tip_box.insert(tk.END, tip_text)
        tip_box.configure(state="disabled")
        tip_box.pack(fill=tk.X, pady=(0, 10))

        # 元素列表表格 (Treeview)
        cols = ("name", "type", "status")
        self.tree = ttk.Treeview(main_frame, columns=cols, show="headings", height=8)
        self.tree.heading("name", text="元素名稱 / 說明")
        self.tree.heading("type", text="標記類型")
        self.tree.heading("status", text="狀態")
        
        self.tree.column("name", width=220, anchor=tk.W)
        self.tree.column("type", width=80, anchor=tk.CENTER)
        self.tree.column("status", width=120, anchor=tk.CENTER)
        
        self.tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 填入預設元素
        self.update_tree_items()

        # 操作按鈕
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_cfg = dict(relief="flat", cursor="hand2", font=("Microsoft JhengHei", 9, "bold"))
        
        self.btn_mark = tk.Button(btn_frame, text="📍 標記選取位置", bg="#00f0ff", fg="#000000",
                                  command=self.start_marking, **btn_cfg)
        self.btn_mark.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.btn_delete = tk.Button(btn_frame, text="🗑️ 清除選取", bg="#3a3a4e", fg="#ffffff",
                                    command=self.delete_selected_marker, **btn_cfg)
        self.btn_delete.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.btn_custom = tk.Button(btn_frame, text="➕ 新增自訂", bg="#1a1a2e", fg="#e0e0e0",
                                    command=self.add_custom_element, **btn_cfg)
        self.btn_custom.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # 底部大按鈕
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.btn_capture = tk.Button(bottom_frame, text="📸 一鍵截圖全部 (自動裁切儲存)", 
                                     bg="#ff6600", fg="#ffffff", font=("Microsoft JhengHei", 10, "bold"),
                                     relief="flat", cursor="hand2", pady=8, command=self.capture_all)
        self.btn_capture.pack(fill=tk.X)

    def update_tree_items(self):
        # 清除現有
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 取得所有已登記的元素
        all_elements = []
        for el in DEFAULT_ELEMENTS:
            all_elements.append(el)
            
        # 加上自訂的元素
        for name, info in self.markers.items():
            if not any(x["name"] == name for x in DEFAULT_ELEMENTS):
                all_elements.append({"name": name, "label": info["label"], "type": info["type"]})
                
        # 渲染到 Treeview
        for el in all_elements:
            name = el["name"]
            label = el["label"]
            el_type = el["type"]
            
            # 判斷狀態
            if name in self.markers and self.markers[name]["coords"]:
                coords = self.markers[name]["coords"]
                status = f"已標記 {coords}"
            else:
                status = "🔴 未標記"
                
            self.tree.insert("", tk.END, iid=name, values=(f"{label} ({name})", el_type, status))

    def delete_selected_marker(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "請先從列表中選擇一個元素！")
            return
        name = selected[0]
        if name in self.markers:
            del self.markers[name]
            self.update_tree_items()
            messagebox.showinfo("成功", f"已清除 {name} 的標記位置")
        else:
            messagebox.showinfo("提示", f"該元素本來就沒有標記")

    def start_marking(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "請先從列表中選擇一個元素！")
            return
        name = selected[0]
        
        # 找出型態
        el_type = "Click"
        el_label = name
        
        # 先從預設清單找
        el_def = next((x for x in DEFAULT_ELEMENTS if x["name"] == name), None)
        if el_def:
            el_type = el_def["type"]
            el_label = el_def["label"]
        elif name in self.markers:
            el_type = self.markers[name]["type"]
            el_label = self.markers[name]["label"]
            
        # 隱藏主視窗，開啟全螢幕遮罩
        self.root.withdraw()
        time.sleep(0.2) # 讓主視窗完全消失
        
        # 擷取當前全螢幕作為遮罩背景
        screen_img = ImageGrab.grab()
        
        OverlayWindow(self, name, el_label, el_type, screen_img)

    def save_marker(self, name, el_label, el_type, coords):
        self.markers[name] = {"type": el_type, "coords": coords, "label": el_label}
        self.root.deiconify() # 恢復主視窗
        self.update_tree_items()
        
        # 選中下一筆未標記的
        children = self.tree.get_children()
        idx = children.index(name)
        if idx + 1 < len(children):
            next_name = children[idx + 1]
            self.tree.selection_set(next_name)
            self.tree.focus(next_name)

    def add_custom_element(self):
        # 彈出小視窗輸入名稱與說明
        dialog = tk.Toplevel(self.root)
        dialog.title("新增自訂元素")
        dialog.geometry("300x240")
        dialog.configure(bg="#0d0d1a")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="新增自訂偵測元素", fg="#ff6600", bg="#0d0d1a", font=("Microsoft JhengHei", 10, "bold")).pack(pady=10)
        
        # 元素程式代號
        tk.Label(dialog, text="程式代號 (例如 custom_btn):", fg="#ffffff", bg="#0d0d1a", font=("Microsoft JhengHei", 8)).pack(anchor=tk.W, padx=20)
        name_entry = tk.Entry(dialog, bg="#1a1a2e", fg="#ffffff", insertbackground="#ffffff", relief="flat")
        name_entry.pack(fill=tk.X, padx=20, pady=(2, 10))
        name_entry.insert(0, "custom_element")
        
        # 元素說明標籤
        tk.Label(dialog, text="中文說明 (例如 購買按鈕):", fg="#ffffff", bg="#0d0d1a", font=("Microsoft JhengHei", 8)).pack(anchor=tk.W, padx=20)
        label_entry = tk.Entry(dialog, bg="#1a1a2e", fg="#ffffff", insertbackground="#ffffff", relief="flat")
        label_entry.pack(fill=tk.X, padx=20, pady=(2, 10))
        label_entry.insert(0, "自訂元素說明")
        
        # 標記型態
        tk.Label(dialog, text="標記型態:", fg="#ffffff", bg="#0d0d1a", font=("Microsoft JhengHei", 8)).pack(anchor=tk.W, padx=20)
        type_var = tk.StringVar(value="Click")
        type_frame = ttk.Frame(dialog)
        type_frame.pack(fill=tk.X, padx=20, pady=(2, 15))
        
        tk.Radiobutton(type_frame, text="單擊點 (Click)", variable=type_var, value="Click", bg="#0d0d1a", fg="#ffffff", selectcolor="#0d0d1a", activebackground="#0d0d1a", activeforeground="#ffffff").pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(type_frame, text="拖曳區域 (Region)", variable=type_var, value="Region", bg="#0d0d1a", fg="#ffffff", selectcolor="#0d0d1a", activebackground="#0d0d1a", activeforeground="#ffffff").pack(side=tk.LEFT)
        
        def save():
            name = name_entry.get().strip()
            label = label_entry.get().strip()
            el_type = type_var.get()
            
            if not name or not label:
                messagebox.showerror("錯誤", "代號與說明皆不能為空！", parent=dialog)
                return
                
            # 檢查是否重複
            if name in self.markers or any(x["name"] == name for x in DEFAULT_ELEMENTS):
                messagebox.showerror("錯誤", f"代號 '{name}' 已存在！", parent=dialog)
                return
                
            self.markers[name] = {"type": el_type, "coords": None, "label": label}
            dialog.destroy()
            self.update_tree_items()
            
            # 選中剛建立的
            self.tree.selection_set(name)
            self.tree.focus(name)
            
        tk.Button(dialog, text="確定新增", bg="#ff6600", fg="#ffffff", relief="flat", cursor="hand2", font=("Microsoft JhengHei", 9, "bold"), command=save).pack(fill=tk.X, padx=20, pady=5)

    def capture_all(self):
        # 檢查是否至少有一個已標記
        active_markers = {k: v for k, v in self.markers.items() if v["coords"]}
        if not active_markers:
            messagebox.showwarning("提示", "請至少完成一個元素的標記再執行截圖！")
            return
            
        # 提示使用者準備畫面
        msg = ("請確認你要截取的畫面（如 Chrome、YouTube、遊戲等）已在背景完全展開且沒有被本視窗擋住。\n\n"
               "點擊確定後，本視窗將會隱藏 0.5 秒並對螢幕進行截圖、自動裁切並儲存。")
        if not messagebox.askokcancel("準備截圖", msg):
            return
            
        # 隱藏主視窗
        self.root.withdraw()
        time.sleep(0.5) # 確保視窗完全隱藏
        
        try:
            # 截取目前乾淨的螢幕畫面
            screenshot = ImageGrab.grab()
            sw, sh = pyautogui.size()
            
            # DPI 檢查與校正 (若 ImageGrab 尺寸與 pyautogui 邏輯解析度不一致，需要做座標映射縮放)
            scale_x = screenshot.size[0] / sw
            scale_y = screenshot.size[1] / sh
            
            calibration_data = {}
            
            for name, info in active_markers.items():
                coords = info["coords"]
                el_type = info["type"]
                
                # 計算實際裁切邊界
                if el_type == "Click":
                    cx, cy = coords
                    # 預設點擊元素裁切 120 x 60 像素
                    w, h = 120, 60
                    x1 = max(0, cx - w // 2)
                    y1 = max(0, cy - h // 2)
                    x2 = min(sw, cx + w // 2)
                    y2 = min(sh, cy + h // 2)
                    
                    # 計算中心點，寫入 calibration.json (用作點擊目標)
                    calibration_data[name] = [int(cx), int(cy)]
                else: # Region
                    x1, y1, x2, y2 = coords
                    # 計算中心點，寫入 calibration.json
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    calibration_data[name] = [int(x1), int(y1), int(x2), int(y2)] # 支援多點/區域格式
                    
                # 套用 DPI 縮放係數，換算為實體像素坐標
                rx1, ry1 = int(x1 * scale_x), int(y1 * scale_y)
                rx2, ry2 = int(x2 * scale_x), int(y2 * scale_y)
                
                # 裁切並儲存
                cropped = screenshot.crop((rx1, ry1, rx2, ry2))
                
                # 儲存 normal 與 hover 檔案 (為了相容性，我們兩者都儲存一樣的圖)
                normal_path = os.path.join(TPL_DIR, f"{name}_normal.png")
                hover_path = os.path.join(TPL_DIR, f"{name}_hover.png")
                
                cropped.save(normal_path)
                cropped.save(hover_path)
                
            # 寫入 calibration.json
            with open(CALIBRATION_PATH, "w", encoding="utf-8") as f:
                json.dump(calibration_data, f, indent=2, ensure_ascii=False)
                
            # 恢復主視窗並提示成功
            self.root.deiconify()
            
            success_msg = (f"🎉 截圖與裁切完成！\n\n"
                           f"已生成 {len(active_markers)} 個元素的範本圖檔。\n"
                           f"儲存目錄：{TPL_DIR}\n"
                           f"座標檔案：{CALIBRATION_PATH}\n\n"
                           f"您可以開啟該資料夾確認圖檔是否乾淨正確！")
            messagebox.showinfo("成功", success_msg)
            
        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("錯誤", f"截圖或儲存時發生錯誤: {e}")

    def run(self):
        self.root.mainloop()

class OverlayWindow:
    def __init__(self, parent_app, name, label, el_type, screen_img):
        self.parent = parent_app
        self.name = name
        self.label = label
        self.el_type = el_type
        
        # 建立全螢幕無邊框置頂視窗
        self.win = tk.Toplevel()
        self.win.attributes("-fullscreen", True)
        self.win.attributes("-topmost", True)
        self.win.configure(cursor="cross")
        
        # 鍵盤監聽
        self.win.bind("<Escape>", self.cancel)
        self.win.bind("<Return>", self.confirm)
        
        # 滑鼠監聽
        self.win.bind("<ButtonPress-1>", self.on_press)
        self.win.bind("<B1-Motion>", self.on_drag)
        self.win.bind("<ButtonRelease-1>", self.on_release)
        
        # 將全螢幕截圖貼到 Canvas 上
        self.screen_width = screen_img.width
        self.screen_height = screen_img.height
        
        # 在記憶體中建立一個加了 30% 半透明黑色遮罩的背景圖
        overlay = Image.new("RGBA", screen_img.size, (0, 0, 0, 75))
        self.bg_image = Image.alpha_composite(screen_img.convert("RGBA"), overlay)
        
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        
        self.canvas = tk.Canvas(self.win, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor=tk.NW)
        
        # 暫存繪圖元件 ID
        self.rect_id = None
        self.dot_id = None
        self.text_id = None
        self.guide_box_id = None
        
        # 紀錄滑鼠起終點
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.coords = None
        
        # 顯示畫面上方的操作指示
        self.draw_instructions()

    def draw_instructions(self):
        mode_text = "單擊標記中心點" if self.el_type == "Click" else "拖曳滑鼠以框選區域"
        instructions = (f"【標記模式】正在標記：{self.label} ({self.name})\n"
                        f"操作說明：請在畫面上 {mode_text}\n"
                        f"確認：按 [Enter] 保存 | 取消：按 [ESC] 退出")
        
        # 畫背景條
        self.canvas.create_rectangle(10, 10, 480, 80, fill="#0d0d1a", outline="#ff6600", width=2)
        # 寫文字
        self.canvas.create_text(25, 45, text=instructions, fill="#ffffff", anchor=tk.W, 
                                font=("Microsoft JhengHei", 9, "bold"))

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        
        if self.el_type == "Click":
            self.draw_click_marker(event.x, event.y)
        else: # Region mode
            # 開始拖曳，先清空舊的
            if self.rect_id:
                self.canvas.delete(self.rect_id)

    def on_drag(self, event):
        if self.el_type == "Region":
            cur_x = event.x
            cur_y = event.y
            
            # 更新或建立虛線矩形
            if self.rect_id:
                self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)
            else:
                self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, cur_x, cur_y, 
                                                             outline="#00f0ff", width=2, dash=(4, 4))

    def on_release(self, event):
        self.end_x = event.x
        self.end_y = event.y
        
        if self.el_type == "Click":
            self.coords = (self.start_x, self.start_y)
        else: # Region
            x1, x2 = sorted([self.start_x, self.end_x])
            y1, y2 = sorted([self.start_y, self.end_y])
            # 避免點太小
            if (x2 - x1) > 3 and (y2 - y1) > 3:
                self.coords = (x1, y1, x2, y2)
                # 將矩形框改為實線
                self.canvas.delete(self.rect_id)
                self.rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline="#00f0ff", width=2)
            else:
                self.coords = None

    def draw_click_marker(self, x, y):
        # 清除舊標記
        if self.dot_id: self.canvas.delete(self.dot_id)
        if self.guide_box_id: self.canvas.delete(self.guide_box_id)
        
        # 1. 畫中心紅點
        r = 5
        self.dot_id = self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="#ff0055", outline="#ffffff", width=1.5)
        
        # 2. 畫預設裁切框（120 x 60）以供使用者預覽
        w, h = 120, 60
        bx1, by1 = x - w//2, y - h//2
        bx2, by2 = x + w//2, y + h//2
        self.guide_box_id = self.canvas.create_rectangle(bx1, by1, bx2, by2, outline="#ff6600", width=1.5, dash=(3, 3))

    def confirm(self, event=None):
        if not self.coords:
            messagebox.showwarning("提示", "您尚未進行任何標記！", parent=self.win)
            return
            
        self.win.destroy()
        self.parent.save_marker(self.name, self.label, self.el_type, self.coords)

    def cancel(self, event=None):
        self.win.destroy()
        self.parent.root.deiconify() # 恢復主視窗

if __name__ == "__main__":
    print(f"啟動視覺化標記工具...")
    print(f"儲存目錄：{TPL_DIR}")
    app = CaptureToolApp()
    app.run()
