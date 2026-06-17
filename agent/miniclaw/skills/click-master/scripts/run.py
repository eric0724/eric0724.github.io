#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
click-master 技能腳本 — 精準螢幕點擊與座標操作

功能：
1. 接收命令列參數 X 和 Y（座標）
2. 整合 safe_locate.py 防崩潰機制
3. 使用 pyautogui 執行精準移動與點擊
4. 輸出結構化日誌供 server.js 攔截

用法：
    python run.py <X> <Y>
    範例：python run.py 960 540
"""

import sys
import os
import time
from typing import Tuple, Optional

# 加入 safe_locate.py 所在目錄到 Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

try:
    from safe_locate import validate_and_safe, calculate_safe_zone, get_screen_size
except ImportError:
    print("[ERROR] 找不到 safe_locate.py 模組")
    sys.exit(1)

# 嘗試匯入 pyautogui，若無安裝則提供安裝指引
try:
    import pyautogui
    # 設定 pyautogui 安全參數
    pyautogui.FAILSAFE = True  # 啟用失敗保護（滑鼠移到左上角可中止）
    pyautogui.PAUSE = 0.1      # 每次操作間隔 0.1 秒
except ImportError:
    print("[ERROR] 找不到 pyautogui 模組，請執行：pip install pyautogui")
    sys.exit(1)


def parse_coordinates(args: list) -> Optional[Tuple[int, int]]:
    """
    解析命令列參數為座標
    
    Args:
        args: 命令列參數列表
    
    Returns:
        Optional[Tuple[int, int]]: (x, y) 座標，解析失敗回傳 None
    """
    if len(args) < 2:
        return None
    
    try:
        x = int(args[0])
        y = int(args[1])
        return (x, y)
    except (ValueError, IndexError):
        return None


def move_and_click(x: int, y: int, clicks: int = 1, button: str = 'left') -> bool:
    """
    移動滑鼠到指定座標並點擊
    
    Args:
        x: X 座標
        y: Y 座標
        clicks: 點擊次數（預設 1）
        button: 按鈕類型（'left', 'right', 'middle'）
    
    Returns:
        bool: 是否成功
    """
    try:
        # 安全检查
        safe, msg, (safe_x, safe_y) = validate_and_safe(x, y)
        
        if not safe:
            print(f"[WARNING] {msg}")
            if "超出安全範圍" in msg:
                print(f"[INFO] 使用調整後的座標: ({safe_x}, {safe_y})")
                x, y = safe_x, safe_y
            else:
                print("[ERROR] 無法繼續執行點擊操作")
                return False
        
        # 移動滑鼠（動畫時間 0.3 秒，讓使用者看到移動軌跡）
        pyautogui.moveTo(x, y, duration=0.3)
        
        # 執行點擊
        pyautogui.click(x, y, clicks=clicks, button=button)
        
        return True
        
    except pyautogui.FailSafeException:
        print("[EMERGENCY] pyautogui 失敗保護觸發！滑鼠已移到左上角安全區域。")
        return False
    except Exception as e:
        print(f"[ERROR] 點擊操作失敗: {str(e)}")
        return False


def main():
    """主程式"""
    # 讀取命令列參數
    args = sys.argv[1:]
    
    # 解析座標
    coords = parse_coordinates(args)
    if coords is None:
        print("[USAGE] python run.py <X> <Y>")
        print("  範例：python run.py 960 540")
        print("")
        print("[ERROR] 請提供有效的 X 和 Y 座標（整數）")
        sys.exit(1)
    
    x, y = coords
    
    # 輸出開始日誌
    print(f"[START] click-master 開始執行")
    print(f"[INFO] 目標座標: ({x}, {y})")
    
    # 顯示安全區域資訊
    zone = calculate_safe_zone()
    print(f"[INFO] 螢幕尺寸: {zone['width']}x{zone['height']}")
    print(f"[INFO] 安全區域: X({zone['min_x']}-{zone['max_x']}), Y({zone['min_y']}-{zone['max_y']})")
    
    # 檢查座標是否在安全範圍內
    safe, msg, adjusted = validate_and_safe(x, y)
    if not safe and "超出安全範圍" in msg:
        print(f"[WARNING] {msg}")
        x, y = adjusted
        print(f"[INFO] 已自動調整為安全座標: ({x}, {y})")
    
    # 執行點擊
    print(f"[ACTION] 移動滑鼠到 ({x}, {y}) 並點擊...")
    success = move_and_click(x, y)
    
    if success:
        # 成功日誌（server.js 會攔截此輸出）
        print(f"[SUCCESS] 點擊完成")
        print(f"[RESULT] 座標: ({x}, {y})")
        print(f"[TIME] {time.strftime('%Y-%m-%d %H:%M:%S')}")
        sys.exit(0)
    else:
        # 失敗日誌
        print(f"[FAILED] 點擊操作失敗")
        print(f"[ERROR] 座標: ({x}, {y})")
        sys.exit(1)


if __name__ == "__main__":
    main()