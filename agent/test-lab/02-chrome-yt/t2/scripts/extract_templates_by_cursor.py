"""
extract_templates_by_cursor.py
==================================
自動游標比對裁切工具（PoC）
- 支援 Manual Mode: 直接傳入 --click_seconds 秒數（免 API Key）
- 支援 Auto Mode: 上傳影片至 Gemini API 進行點擊動作時間點分析
- 在記憶體中生成標準 Windows 游標及遮罩，執行 OpenCV 遮罩樣板比對定位
- 倒帶擷取乾淨的正常狀態（Normal）與滑鼠停靠時的懸停狀態（Hover）範本
"""

import os
import sys
import json
import argparse
import time
import cv2
import numpy as np
from PIL import Image

# 解決 Windows 終端機 Unicode 編碼輸出報錯問題
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

_DIR = os.path.dirname(os.path.abspath(__file__))
TPL_DIR = os.path.abspath(os.path.join(_DIR, "..", "templates"))
os.makedirs(TPL_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════
#  1. 多類型游標與遮罩生成（記憶體內生成）
# ══════════════════════════════════════════════════════

def generate_cursor_templates():
    """
    在記憶體中繪製多種標準 Windows 游標 (箭頭、手掌、I型文字輸入) 及其遮罩。
    回傳: 包含各類型游標樣板、遮罩與點擊熱點偏移 (offset) 的字典。
    """
    templates = {}
    h, w = 24, 24

    # A. 標準白色箭頭游標 (Arrow)
    arrow_tpl = np.zeros((h, w), dtype=np.uint8)
    arrow_mask = np.zeros((h, w), dtype=np.uint8)
    arrow_poly = np.array([
        [0, 0], [0, 17], [4, 13], [8, 21], [10, 20], [6, 12], [11, 12]
    ], dtype=np.int32)
    cv2.fillConvexPoly(arrow_tpl, arrow_poly, 255)
    cv2.fillConvexPoly(arrow_mask, arrow_poly, 255)
    cv2.polylines(arrow_tpl, [arrow_poly], isClosed=True, color=0, thickness=1)
    
    templates["arrow"] = {
        "tpl": arrow_tpl,
        "mask": arrow_mask,
        "offset": (0, 0)  # 點擊點在左上角
    }

    # B. 點選連結小手 (Hand)
    hand_tpl = np.zeros((h, w), dtype=np.uint8)
    hand_mask = np.zeros((h, w), dtype=np.uint8)
    # 簡化手掌多邊形，食指尖端在 (9, 0)
    hand_poly = np.array([
        [9, 0], [11, 0], [11, 8], [14, 9], [15, 12], [15, 17], [12, 21],
        [6, 21], [4, 16], [4, 11], [7, 10], [7, 8], [9, 8]
    ], dtype=np.int32)
    cv2.fillConvexPoly(hand_tpl, hand_poly, 255)
    cv2.fillConvexPoly(hand_mask, hand_poly, 255)
    cv2.polylines(hand_tpl, [hand_poly], isClosed=True, color=0, thickness=1)

    templates["hand"] = {
        "tpl": hand_tpl,
        "mask": hand_mask,
        "offset": (9, 0)  # 點擊點在食指指尖 (9, 0)
    }

    # C. 文字輸入游標 (I-Beam)
    # 設計包含背景的 I-Beam 以提供足夠的色彩對比，防止純色背景誤判
    ih, iw = 20, 12
    
    # 1. 淺色背景上的黑色 I-Beam (主體為 0，背景為 255)
    ibeam_black_tpl = np.ones((ih, iw), dtype=np.uint8) * 255
    ibeam_black_mask = np.ones((ih, iw), dtype=np.uint8) * 255 # 覆蓋整張以強制比對背景對比
    cv2.line(ibeam_black_tpl, (2, 2), (9, 2), 0, 1)
    cv2.line(ibeam_black_tpl, (2, 17), (9, 17), 0, 1)
    cv2.line(ibeam_black_tpl, (6, 2), (6, 17), 0, 2)
    
    templates["ibeam_black_on_light"] = {
        "tpl": ibeam_black_tpl,
        "mask": ibeam_black_mask,
        "offset": (6, 9)
    }

    # 2. 深色背景上的白色 I-Beam (主體為 255，背景為 0)
    ibeam_white_tpl = np.zeros((ih, iw), dtype=np.uint8)
    ibeam_white_mask = np.ones((ih, iw), dtype=np.uint8) * 255
    cv2.line(ibeam_white_tpl, (2, 2), (9, 2), 255, 1)
    cv2.line(ibeam_white_tpl, (2, 17), (9, 17), 255, 1)
    cv2.line(ibeam_white_tpl, (6, 2), (6, 17), 255, 2)
    
    templates["ibeam_white_on_dark"] = {
        "tpl": ibeam_white_tpl,
        "mask": ibeam_white_mask,
        "offset": (6, 9)
    }

    return templates

# ══════════════════════════════════════════════════════
#  2. 精準影格擷取
# ══════════════════════════════════════════════════════

def extract_frame_at_second(video_path, target_sec):
    """
    使用 OpenCV 精準定位並讀取影片特定秒數的影格
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERR] 無法開啟影片：{video_path}")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    target_frame = int(target_sec * fps)

    seek_frame = max(0, target_frame - 15)
    cap.set(cv2.CAP_PROP_POS_FRAMES, seek_frame)

    current_frame = seek_frame
    frame = None
    while current_frame <= target_frame:
        ret, f = cap.read()
        if not ret:
            break
        frame = f
        current_frame += 1

    cap.release()
    return frame

# ══════════════════════════════════════════════════════
#  3. 遮罩樣板比對定位多類型滑鼠游標
# ══════════════════════════════════════════════════════

def find_cursor(frame_bgr, search_scales=[1.0, 1.25, 1.5, 1.75, 2.0]):
    """
    使用多重比例 (Multi-scale) 在畫面上尋找各種游標類型。
    限制最小比例為 1.0x 避免比對到 OBS 等預覽視窗中的微小遞迴游標。
    """
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    cursor_templates = generate_cursor_templates()

    best_val = float('inf')
    best_loc = None
    best_scale = 1.0
    best_type = None
    best_offset = (0, 0)

    for type_name, info in cursor_templates.items():
        tpl_base = info["tpl"]
        mask_base = info["mask"]
        offset_base = info["offset"]

        for scale in search_scales:
            th = int(tpl_base.shape[0] * scale)
            tw = int(tpl_base.shape[1] * scale)
            if th < 6 or tw < 6:
                continue

            tpl = cv2.resize(tpl_base, (tw, th), interpolation=cv2.INTER_AREA)
            mask = cv2.resize(mask_base, (tw, th), interpolation=cv2.INTER_AREA)

            _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

            res = cv2.matchTemplate(gray, tpl, cv2.TM_SQDIFF, mask=mask)
            min_val, _, min_loc, _ = cv2.minMaxLoc(res)

            mask_pixels = np.sum(mask > 0)
            norm_val = min_val / (255.0 * mask_pixels) if mask_pixels > 0 else float('inf')

            if norm_val < best_val:
                best_val = norm_val
                best_loc = min_loc
                best_scale = scale
                best_type = type_name
                best_offset = (int(offset_base[0] * scale), int(offset_base[1] * scale))

    if best_loc is not None and best_val < 100.0:  # 經驗閥值
        cx = best_loc[0] + best_offset[0]
        cy = best_loc[1] + best_offset[1]
        print(f"    [比對資訊] 匹配類型: {best_type}，縮放比: {best_scale:.2f}，分數: {best_val:.2f}")
        return (cx, cy), best_scale, best_val

    return None, None, best_val

# ══════════════════════════════════════════════════════
#  4. 裁切與儲存
# ══════════════════════════════════════════════════════

def crop_and_save_templates(video_path, item_name, label, click_sec, crop_w=120, crop_h=60):
    """
    在 click_sec (點擊瞬間) 與 click_sec - 0.8秒 (點擊前) 擷取畫面，
    進行游標尋找與裁切，產出 hover 與 normal 範本。
    """
    print(f"\n[處理] 開始處理元素：{label} ({item_name}) - 目標時間: {click_sec}秒")

    # A. 取得點擊瞬間的影格 (Hover)
    hover_frame = extract_frame_at_second(video_path, click_sec)
    if hover_frame is None:
        print("  [FAIL] 無法取得點擊瞬間的影格")
        return False

    # B. 在 Hover 影格中尋找滑鼠游標
    pos, scale, score = find_cursor(hover_frame)
    if pos is None:
        print(f"  [FAIL] 無法定位滑鼠游標 (最佳比對分數: {score:.2f}，超出安全限制)")
        return False

    cx, cy = pos
    print(f"  [OK] 定位游標：({cx}, {cy})，縮放比: {scale:.2f}，分數: {score:.2f}")

    # C. 取得點擊前的影格 (Normal)
    normal_sec = max(0.0, click_sec - 0.8)
    normal_frame = extract_frame_at_second(video_path, normal_sec)
    if normal_frame is None:
        print("  [FAIL] 無法取得點擊前影格")
        return False

    # D. 換算並執行裁切
    fh, fw, _ = hover_frame.shape
    x1 = max(0, cx - crop_w // 2)
    y1 = max(0, cy - crop_h // 2)
    x2 = min(fw, cx + crop_w // 2)
    y2 = min(fh, cy + crop_h // 2)

    if x2 <= x1 or y2 <= y1:
        print("  [FAIL] 裁切邊界計算錯誤")
        return False

    hover_crop = hover_frame[y1:y2, x1:x2]
    normal_crop = normal_frame[y1:y2, x1:x2]

    # E. 儲存範本圖片
    hover_filename = f"template_{item_name}_hover.png"
    normal_filename = f"template_{item_name}_normal.png"
    hover_path = os.path.join(TPL_DIR, hover_filename)
    normal_path = os.path.join(TPL_DIR, normal_filename)

    cv2.imwrite(hover_path, hover_crop)
    cv2.imwrite(normal_path, normal_crop)

    print(f"  [儲存] Hover  範本已存至：{os.path.basename(hover_path)} ({hover_crop.shape[1]}x{hover_crop.shape[0]}px)")
    print(f"  [儲存] Normal 範本已存至：{os.path.basename(normal_path)} ({normal_crop.shape[1]}x{normal_crop.shape[0]}px)")

    # 畫框框以利除錯
    debug_img = hover_frame.copy()
    cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.circle(debug_img, (cx, cy), 4, (0, 0, 255), -1)
    debug_path = os.path.join(TPL_DIR, f"debug_{item_name}_click.png")
    cv2.imwrite(debug_path, debug_img)
    print(f"  [儲存] 除錯用定位截圖已存至：{os.path.basename(debug_path)}")

    return True

# ══════════════════════════════════════════════════════
#  5. Auto Mode (Gemini API 分析秒數)
# ══════════════════════════════════════════════════════

def run_gemini_analysis(video_path, task_desc, api_key):
    """
    呼叫 Gemini API 進行點擊秒數分析
    """
    print("[Gemini] 上傳影片並分析中...")
    try:
        import google.generativeai as genai
    except ImportError:
        print("[ERR] 請先安裝 google-generativeai：pip install google-generativeai")
        return []

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    # 上傳影片
    video_file = genai.upload_file(path=video_path)
    print(f"  檔案已上傳，名稱: {video_file.name}，正在進行轉碼與快取...")

    while video_file.state.name == "PROCESSING":
        time.sleep(2)
        video_file = genai.get_file(video_file.name)
        print("  等待中...")

    if video_file.state.name == "FAILED":
        print("  [FAIL] 影片處理失敗")
        return []

    print("  [OK] 影片處理完成，開始呼叫模型分析點擊動作...")

    prompt = (
        f"你是自動化腳本助手。使用者的任務是：{task_desc}\n"
        f"這是一段螢幕操作影片。請仔細分析這段影片，找出使用者點擊 UI 元素的關鍵時間點（秒數）。\n"
        f"請只回傳一個 JSON 陣列，每個元素格式如下：\n"
        f"[\n"
        f"  {{\n"
        f"    \"name\": \"按鈕英文變數名（例如 chrome_btn）\",\n"
        f"    \"label\": \"按鈕中文說明（例如 Chrome 圖示）\",\n"
        f"    \"second\": 點擊發生的精確秒數（浮點數）\n"
        f"  }}\n"
        f"]\n"
        f"注意：只回傳純 JSON，不要任何 Markdown 標記或額外說明文字。"
    )

    try:
        response = model.generate_content([video_file, prompt])
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        genai.delete_file(video_file.name)
        return data
    except Exception as e:
        print(f"  [FAIL] Gemini API 執行失敗或回傳格式有誤：{e}")
        try:
            genai.delete_file(video_file.name)
        except:
            pass
    return []

# ══════════════════════════════════════════════════════
#  主程式入口
# ══════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="二代自動游標比對裁切工具（PoC）")
    parser.add_argument("--video", required=True, help="錄影檔案路徑 (.mp4 / .avi / .mov)")
    parser.add_argument("--click_seconds", default="", help="手動指定的點擊時間秒數，逗號分隔 (例如: 3.2,8.5)")
    parser.add_argument("--task", default="網頁自動化", help="任務描述 (Auto Mode 使用)")
    parser.add_argument("--crop_w", type=int, default=120, help="裁切寬度 (預設: 120)")
    parser.add_argument("--crop_h", type=int, default=60, help="裁切高度 (預設: 60)")
    args = parser.parse_args()

    video_path = os.path.abspath(args.video)
    if not os.path.exists(video_path):
        print(f"[ERR] 找不到影片：{video_path}")
        sys.exit(1)

    elements_to_process = []

    if args.click_seconds:
        print("[模式] 手動輸入秒數模式")
        seconds = [float(s.strip()) for s in args.click_seconds.split(",") if s.strip()]
        for i, sec in enumerate(seconds):
            elements_to_process.append({
                "name": f"element_{i+1}",
                "label": f"步驟 {i+1} 按鈕",
                "second": sec
            })
    else:
        print("[模式] AI 自動分析模式")
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            print("[ERR] 自動模式需要設定 GEMINI_API_KEY 環境變數，或請改用 --click_seconds 手動指定秒數")
            sys.exit(1)
        elements_to_process = run_gemini_analysis(video_path, args.task, api_key)

    if not elements_to_process:
        print("[ERR] 無任何點擊事件需要處理，程式結束。")
        sys.exit(1)

    print(f"\n[開始] 共需要分析裁切 {len(elements_to_process)} 個元素。")

    success_count = 0
    saved_snippets = []

    for el in elements_to_process:
        name = el.get("name", "unnamed")
        label = el.get("label", "未命名元素")
        sec = float(el.get("second", 0.0))

        ok = crop_and_save_templates(
            video_path=video_path,
            item_name=name,
            label=label,
            click_sec=sec,
            crop_w=args.crop_w,
            crop_h=args.crop_h
        )
        if ok:
            success_count += 1
            saved_snippets.append({
                "name": name,
                "label": label,
                "hover": f"template_{name}_hover.png",
                "normal": f"template_{name}_normal.png"
            })

    print("\n" + "="*50)
    print(f"裁切作業結束！成功數: {success_count}/{len(elements_to_process)}")
    print(f"範本已存至：{TPL_DIR}")

    if saved_snippets:
        print("\n[腳本片段] 您可以直接將以下範本定義複製到自動化執行腳本 (chrome_yt_task.py)：")
        for s in saved_snippets:
            var_name = s['name'].upper()
            print(f"  # {s['label']}")
            print(f"  TPL_{var_name}_NORMAL = os.path.join(_TPL_DIR, \"{s['normal']}\")")
            print(f"  TPL_{var_name}_HOVER  = os.path.join(_TPL_DIR, \"{s['hover']}\")")
        
        print("\n[腳本片段] 點擊與比對邏輯範例：")
        for s in saved_snippets:
            var_name = s['name'].upper()
            print(f"""  # 尋找並點擊 {s['label']}
  pos = locate_template(TPL_{var_name}_NORMAL, confidence=0.7)
  if not pos:
      pos = locate_template(TPL_{var_name}_HOVER, confidence=0.7)
  if pos:
      pyautogui.click(pos[0], pos[1])
      log("OK: 點擊 {s['label']} {{pos}}")
  else:
      log("ERR: 找不到 {s['label']}")""")


if __name__ == "__main__":
    main()
