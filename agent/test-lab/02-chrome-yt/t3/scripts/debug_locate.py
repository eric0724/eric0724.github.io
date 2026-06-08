"""
debug_locate.py — 除錯用：顯示範本圖並嘗試在螢幕上找到它
"""
import pyautogui
import cv2
import numpy as np
import os
import time

TEMPLATE = r"c:\Users\fff\Downloads\TT\antigravity\antigravity\_github_clone\agent\test-lab\02-chrome-yt\t3\captures\s4_region.png"

# 1. 確認檔案存在
print(f"範本路徑：{TEMPLATE}")
print(f"檔案存在：{os.path.exists(TEMPLATE)}")

tpl = cv2.imread(TEMPLATE)
if tpl is None:
    print("ERROR: 無法讀取圖片")
    input("按 Enter 結束")
    exit()

print(f"範本大小：{tpl.shape[1]}x{tpl.shape[0]} px")

# 2. 用 Windows 開啟圖片讓你看
os.startfile(TEMPLATE)
print("\n已開啟圖片，請確認內容...")
time.sleep(2)

# 3. 截全螢幕並比對
print("\n截圖比對中...")
screen = pyautogui.screenshot()
src = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)

result = cv2.matchTemplate(src, tpl, cv2.TM_CCOEFF_NORMED)
_, max_val, _, max_loc = cv2.minMaxLoc(result)
th, tw = tpl.shape[:2]
cx = max_loc[0] + tw // 2
cy = max_loc[1] + th // 2

print(f"最高比對分數：{max_val:.4f}")
print(f"找到位置：({cx}, {cy})")

# 4. 移動滑鼠到找到的位置
if max_val > 0.5:
    print(f"\n移動滑鼠到 ({cx}, {cy})...")
    time.sleep(1)
    pyautogui.moveTo(cx, cy, duration=0.8)
    print("完成，請確認滑鼠是否在正確位置")
else:
    print(f"\n分數太低（{max_val:.4f}），找不到圖案")
    print("可能原因：範本截圖和現在的畫面不一樣")

input("\n按 Enter 結束")
