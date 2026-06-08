"""
extract_templates.py
====================
上傳遊戲影片 → Gemini 分析每幀 → 自動裁切範本圖片存到 templates/

使用方式：
  py scripts/extract_templates.py --video <影片路徑> --task "每隔3秒點攻擊按鈕"

需要：
  pip install google-genai opencv-python Pillow

環境變數：
  GEMINI_API_KEY=你的金鑰
"""

import os, sys, json, argparse, time
import cv2
from PIL import Image
import google.generativeai as genai

_DIR     = os.path.dirname(os.path.abspath(__file__))
TPL_DIR  = os.path.join(_DIR, "..", "templates")
os.makedirs(TPL_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════
#  Step 1：影片切幀
# ══════════════════════════════════════════════════════

def extract_frames(video_path, fps=1, max_frames=30):
    """
    從影片每秒取 fps 張，最多取 max_frames 張
    回傳 list of (frame_index, PIL.Image)
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"無法開啟影片：{video_path}")

    video_fps  = cap.get(cv2.CAP_PROP_FPS) or 30
    interval   = max(1, int(video_fps / fps))
    frames     = []
    frame_idx  = 0

    print(f"[影片] FPS={video_fps:.1f}，每 {interval} 幀取一張")

    while len(frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % interval == 0:
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img   = Image.fromarray(rgb)
            frames.append((frame_idx, img))
            print(f"  取幀 #{frame_idx}（共 {len(frames)} 張）")
        frame_idx += 1

    cap.release()
    print(f"[影片] 共取 {len(frames)} 張幀")
    return frames


# ══════════════════════════════════════════════════════
#  Step 2：Gemini 分析幀，回傳 bounding box
# ══════════════════════════════════════════════════════

BBOX_PROMPT = """
你是遊戲自動化助手。使用者的任務是：{task}

請分析這張遊戲截圖，找出執行此任務需要偵測或點擊的 UI 元素。

回傳 JSON 陣列，每個元素格式：
{{
  "name": "英文變數名（例如 attack_btn）",
  "label": "中文說明（例如 攻擊按鈕）",
  "box": [y_min, x_min, y_max, x_max],
  "confidence": 0.0~1.0,
  "action": "click / hover / wait / read"
}}

box 的值是 0~1000 的正規化座標（相對於圖片寬高）。
只回傳 JSON，不要其他文字。
如果畫面中沒有相關元素，回傳空陣列 []。
"""

def analyze_frame(model, img: Image.Image, task: str):
    """送一張幀給 Gemini，回傳 list of element dict"""
    prompt = BBOX_PROMPT.format(task=task)
    try:
        response = model.generate_content([prompt, img])
        text = response.text.strip()
        # 移除可能的 markdown code block
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except Exception as e:
        print(f"  [Gemini] 解析失敗：{e}")
    return []


# ══════════════════════════════════════════════════════
#  Step 3：裁切並存範本圖片
# ══════════════════════════════════════════════════════

def crop_and_save(img: Image.Image, element: dict, frame_idx: int):
    """
    根據 bounding box 裁切圖片，存到 templates/
    box 格式：[y_min, x_min, y_max, x_max]，值 0~1000
    """
    w, h  = img.size
    box   = element.get("box", [])
    if len(box) != 4:
        return None

    y_min, x_min, y_max, x_max = box
    # 正規化座標轉像素，加 5px 邊距
    pad  = 5
    left  = max(0, int(x_min / 1000 * w) - pad)
    top   = max(0, int(y_min / 1000 * h) - pad)
    right = min(w, int(x_max / 1000 * w) + pad)
    bottom= min(h, int(y_max / 1000 * h) + pad)

    if right <= left or bottom <= top:
        return None

    cropped   = img.crop((left, top, right, bottom))
    name      = element.get("name", f"element_{frame_idx}")
    save_path = os.path.join(TPL_DIR, f"template_{name}.png")

    # 若已存在，不覆蓋（保留信心度較高的）
    if not os.path.exists(save_path):
        cropped.save(save_path)
        print(f"  [存檔] {save_path}  ({right-left}x{bottom-top}px)")
        return save_path
    else:
        print(f"  [跳過] {save_path} 已存在")
        return save_path


# ══════════════════════════════════════════════════════
#  主流程
# ══════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="從遊戲影片自動裁切範本圖片")
    parser.add_argument("--video", required=True, help="影片路徑（mp4/avi/mov）")
    parser.add_argument("--task",  required=True, help="任務描述，例如：每隔3秒點攻擊按鈕")
    parser.add_argument("--fps",   type=float, default=0.5, help="每秒取幾幀（預設 0.5，即每2秒一張）")
    parser.add_argument("--max",   type=int,   default=20,  help="最多分析幾幀（預設 20）")
    parser.add_argument("--key",   default=os.environ.get("GEMINI_API_KEY",""), help="Gemini API Key")
    args = parser.parse_args()

    if not args.key:
        print("[錯誤] 請設定 GEMINI_API_KEY 環境變數，或用 --key 傳入")
        sys.exit(1)

    if not os.path.exists(args.video):
        print(f"[錯誤] 找不到影片：{args.video}")
        sys.exit(1)

    # 初始化 Gemini
    genai.configure(api_key=args.key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    print(f"[Gemini] 模型已初始化")

    # 切幀
    frames = extract_frames(args.video, fps=args.fps, max_frames=args.max)

    # 分析每幀
    all_elements = {}  # name -> element（去重，保留最高信心度）
    for frame_idx, img in frames:
        print(f"\n[分析] 幀 #{frame_idx}...")
        elements = analyze_frame(model, img, args.task)
        print(f"  找到 {len(elements)} 個元素")

        for el in elements:
            name = el.get("name","")
            conf = el.get("confidence", 0)
            if name and (name not in all_elements or conf > all_elements[name]["confidence"]):
                all_elements[name] = {"element": el, "img": img, "confidence": conf}

        time.sleep(0.5)  # 避免 API rate limit

    # 裁切存檔
    print(f"\n[裁切] 共 {len(all_elements)} 個唯一元素")
    saved = []
    for name, data in all_elements.items():
        path = crop_and_save(data["img"], data["element"], 0)
        if path:
            saved.append({"name": name, "label": data["element"].get("label",""), "path": path})

    # 輸出摘要
    print("\n" + "="*40)
    print(f"完成！共存 {len(saved)} 個範本：")
    for s in saved:
        print(f"  {s['label']}（{s['name']}）→ {os.path.basename(s['path'])}")

    # 產出腳本片段供參考
    print("\n[腳本片段] 複製到 run_task.py 的範本路徑區：")
    for s in saved:
        var = s['name'].upper()
        print(f"  TPL_{var} = os.path.join(_TPL_DIR, \"{os.path.basename(s['path'])}\")")

    print("\n[腳本片段] 主任務範例：")
    for s in saved:
        var  = s['name'].upper()
        act  = all_elements[s['name']]["element"].get("action","click")
        if act == "click":
            print(f"""
    pos = locate_retry(TPL_{var}, lambda m: log(m,w), label="{s['label']}", timeout=5.0)
    if pos:
        pyautogui.click(pos[0], pos[1])
        log(f"點擊 {s['label']} {{pos}}", w)""")


if __name__ == "__main__":
    main()
