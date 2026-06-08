"""
analyze_video.py
================
從影片抽幀 → 傳給 GPT-4o 分析目標位置 → 裁切範本存到 templates/

執行：
  py scripts/analyze_video.py
"""

import os, json, base64, io, urllib.request
import cv2
from PIL import Image

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

_DIR     = os.path.dirname(os.path.abspath(__file__))
VIDEO    = os.path.join(_DIR, "..", "gotest", "2026-06-01 17-04-09.mp4")
TPL_DIR  = os.path.join(_DIR, "..", "templates")
os.makedirs(TPL_DIR, exist_ok=True)

# 每個要分析的目標：秒數 + 描述 + 存檔名
TARGETS = [
    {"second": 5,  "name": "win_search",
     "desc": "Windows 工作列上的放大鏡搜尋圖示（不含旁邊的天氣或其他圖示）"},
    {"second": 9,  "name": "chrome_app",
     "desc": "Windows 搜尋選單最佳比對區塊中的 Google Chrome 應用程式圖示（紅黃綠藍四色圓形）"},
    {"second": 15, "name": "yahoo_bar",
     "desc": "瀏覽器頁面中央的白色搜尋輸入框"},
    {"second": 21, "name": "yahoo_yt",
     "desc": "搜尋結果第一項藍色帶底線的 YouTube 網站標題連結文字"},
    {"second": 28, "name": "yt_search",
     "desc": "YouTube 網頁頂端中央的長條搜尋框"},
]


# ══════════════════════════════════════════════════════
#  工具函數
# ══════════════════════════════════════════════════════

def grab_frame(video_path, second):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(second * fps))
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

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
        "max_tokens": 200
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

def crop_template(img, cx, cy, pad=15):
    """以中心點裁切範本，加 pad 邊距"""
    w, h = img.size
    # 裁切範圍加大，讓 AI 有更多上下文判斷
    tw, th = 300, 150
    x1 = max(0, cx - tw//2 - pad)
    y1 = max(0, cy - th//2 - pad)
    x2 = min(w, cx + tw//2 + pad)
    y2 = min(h, cy + th//2 + pad)
    return img.crop((x1, y1, x2, y2))


# ══════════════════════════════════════════════════════
#  主流程
# ══════════════════════════════════════════════════════

def main():
    if not os.path.exists(VIDEO):
        print(f"[錯誤] 找不到影片：{VIDEO}")
        return

    print(f"影片：{VIDEO}")
    print(f"輸出：{TPL_DIR}")
    print()

    results = {}

    for t in TARGETS:
        print(f"── {t['name']} （第 {t['second']} 秒）──")

        # 抽幀
        img = grab_frame(VIDEO, t["second"])
        if img is None:
            print(f"  ❌ 無法讀取第 {t['second']} 秒")
            continue
        w, h = img.size
        print(f"  幀尺寸：{w}x{h}")

        # 存整幀供對照
        frames_dir = os.path.join(_DIR, "..", "gotest", "frames")
        os.makedirs(frames_dir, exist_ok=True)
        frame_path = os.path.join(frames_dir, f"{t['name']}_frame_{t['second']}s.png")
        img.save(frame_path)
        print(f"  [整幀] → gotest/frames/{os.path.basename(frame_path)}")

        # 問 GPT-4o
        question = (
            f"這是影片第 {t['second']} 秒的截圖。\n"
            f"請找出「{t['desc']}」的中心點座標。\n"
            f"找到：只回傳 JSON {{\"x\":數字,\"y\":數字}}（像素座標，整數）\n"
            f"找不到：只回傳 JSON {{\"x\":null}}\n"
            f"不要其他文字。"
        )
        print(f"  [GPT] 詢問中...")
        answer = ask_gpt4o(img, question)
        print(f"  [GPT] {answer}")

        d = parse_json(answer)
        if d.get("x") is None:
            print(f"  ❌ 找不到目標")
            continue

        cx, cy = int(d["x"]), int(d["y"])
        # 確認座標在影片幀範圍內
        cx = max(0, min(cx, w-1))
        cy = max(0, min(cy, h-1))
        print(f"  座標：({cx}, {cy})  幀尺寸：{w}x{h}")

        # 裁切範本
        tpl = crop_template(img, cx, cy)
        tpl_path = os.path.join(TPL_DIR, f"{t['name']}_normal.png")
        tpl.save(tpl_path)
        print(f"  [範本] → {os.path.basename(tpl_path)}  ({tpl.size[0]}x{tpl.size[1]}px)")

        results[t["name"]] = {
            "x": cx, "y": cy,
            "second": t["second"],
            "frame_w": w, "frame_h": h
        }
        print()

    # 存座標
    result_path = os.path.join(TPL_DIR, "video_analysis.json")
    with open(result_path, "w") as f:
        json.dump(results, f, indent=2)

    print("="*40)
    print(f"完成！共分析 {len(results)}/{len(TARGETS)} 個元素")
    print(f"座標存到：{result_path}")
    print()
    print("請開啟 templates/ 確認每張範本圖是否正確。")
    print("確認後執行 calibrate.py 進行實際校準。")


if __name__ == "__main__":
    main()

