"""
safe_locate.py — 滑鼠安全定位模組（防崩潰機制）

功能：
1. 安全角落保護：防止滑鼠移動到螢幕極端位置導致失控
2. 邊界檢查：確保座標在安全範圍內
3. 緊急停止機制：提供快速中止功能
"""

import sys
import time
from typing import Tuple, Optional

# 安全區域設定（百分比，0-100）
SAFE_MARGIN_X = 5  # 左右邊緣保留 5%
SAFE_MARGIN_Y = 5  # 上下邊緣保留 5%

# 緊急停止旗標
emergency_stop = False


def get_screen_size() -> Tuple[int, int]:
    """取得螢幕尺寸"""
    try:
        import tkinter as tk
        root = tk.Tk()
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        root.destroy()
        return (width, height)
    except:
        # 預設 1920x1080
        return (1920, 1080)


def calculate_safe_zone() -> dict:
    """計算安全區域範圍"""
    width, height = get_screen_size()
    return {
        'min_x': int(width * SAFE_MARGIN_X / 100),
        'max_x': int(width * (100 - SAFE_MARGIN_X) / 100),
        'min_y': int(height * SAFE_MARGIN_Y / 100),
        'max_y': int(height * (100 - SAFE_MARGIN_Y) / 100),
        'width': width,
        'height': height
    }


def is_safe_coordinate(x: int, y: int) -> bool:
    """
    檢查座標是否在安全區域內
    
    Args:
        x: X 座標
        y: Y 座標
    
    Returns:
        bool: True 表示安全，False 表示危險
    """
    global emergency_stop
    
    if emergency_stop:
        return False
    
    zone = calculate_safe_zone()
    return (zone['min_x'] <= x <= zone['max_x'] and 
            zone['min_y'] <= y <= zone['max_y'])


def clamp_to_safe_zone(x: int, y: int) -> Tuple[int, int]:
    """
    將座標限制在安全區域內
    
    Args:
        x: 原始 X 座標
        y: 原始 Y 座標
    
    Returns:
        Tuple[int, int]: 調整後的安全座標
    """
    zone = calculate_safe_zone()
    safe_x = max(zone['min_x'], min(x, zone['max_x']))
    safe_y = max(zone['min_y'], min(y, zone['max_y']))
    return (safe_x, safe_y)


def trigger_emergency_stop():
    """觸發緊急停止"""
    global emergency_stop
    emergency_stop = True
    print("[EMERGENCY] 緊急停止已觸發！")


def reset_emergency_stop():
    """重置緊急停止"""
    global emergency_stop
    emergency_stop = False


def validate_and_safe(x: int, y: int) -> Tuple[bool, str, Tuple[int, int]]:
    """
    完整的安全檢查流程
    
    Args:
        x: X 座標
        y: Y 座標
    
    Returns:
        Tuple[bool, str, Tuple[int, int]]: (是否安全, 訊息, 安全座標)
    """
    # 檢查緊急停止
    if emergency_stop:
        return (False, "緊急停止模式啟動中", (x, y))
    
    # 檢查座標範圍
    if not is_safe_coordinate(x, y):
        safe_x, safe_y = clamp_to_safe_zone(x, y)
        return (False, f"座標 ({x}, {y}) 超出安全範圍，已自動調整為 ({safe_x}, {safe_y})", (safe_x, safe_y))
    
    return (True, "座標安全", (x, y))


# 模組測試
if __name__ == "__main__":
    print("=== safe_locate.py 測試 ===")
    zone = calculate_safe_zone()
    print(f"螢幕尺寸: {zone['width']}x{zone['height']}")
    print(f"安全區域: X({zone['min_x']}-{zone['max_x']}), Y({zone['min_y']}-{zone['max_y']})")
    
    # 測試座標
    test_points = [
        (100, 100),      # 左上角（危險）
        (960, 540),      # 中央（安全）
        (1900, 1000),    # 右下角（危險）
        (500, 300)       # 安全區域
    ]
    
    for x, y in test_points:
        safe, msg, adjusted = validate_and_safe(x, y)
        print(f"({x:4d}, {y:4d}) → {msg} → 最終座標: {adjusted}")