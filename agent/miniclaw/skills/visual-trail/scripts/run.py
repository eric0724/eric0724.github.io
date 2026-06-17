#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
visual-trail 技能腳本 — 視覺軌跡管理系統

功能：
1. 即時追蹤滑鼠移動軌跡
2. 時間衰減機制（舊軌跡自動淡化）
3. 最大軌跡點限制（LRU 淘汰）
4. 軌跡統計分析
5. 結構化日誌輸出

用法：
    python run.py start              # 開始追蹤
    python run.py stop               # 停止追蹤
    python run.py analyze            # 分析軌跡
    python run.py clear              # 清除軌跡
"""

import sys
import os
import json
import time
import math
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from collections import deque

# 加入腳本目錄到 Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# 嘗試匯入必要模組
try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.01
except ImportError:
    print("[ERROR] 找不到 pyautogui 模組，請執行：pip install pyautogui")
    sys.exit(1)

try:
    from pynput import mouse
except ImportError:
    print("[ERROR] 找不到 pynput 模組，請執行：pip install pynput")
    sys.exit(1)

# 引入 safe_locate 進行安全檢查
try:
    from safe_locate import validate_and_safe
except ImportError:
    print("[WARNING] 找不到 safe_locate.py，將跳過安全檢查")
    validate_and_safe = None

# 軌跡資料儲存目錄
TRAIL_DIR = os.path.join(SCRIPT_DIR, '..', '..', 'data', 'trails')
os.makedirs(TRAIL_DIR, exist_ok=True)

# 軌跡設定
MAX_TRAIL_POINTS = 1000      # 最大軌跡點數
DECAY_TIME_SECONDS = 60      # 衰減時間（秒）
DECAY_FACTOR = 0.95          # 衰減因子（每秒）
MIN_OPACITY = 0.1            # 最小透明度


class TrailPoint:
    """軌跡點"""
    
    def __init__(self, x: int, y: int, timestamp: float):
        self.x = x
        self.y = y
        self.timestamp = timestamp
        self.opacity = 1.0
        self.speed = 0.0
    
    def update_decay(self, current_time: float) -> float:
        """
        更新時間衰減
        
        Args:
            current_time: 當前時間戳
        
        Returns:
            float: 更新後的透明度
        """
        elapsed = current_time - self.timestamp
        
        if elapsed > DECAY_TIME_SECONDS:
            self.opacity = MIN_OPACITY
        else:
            # 指數衰減
            decay = DECAY_FACTOR ** elapsed
            self.opacity = max(MIN_OPACITY, decay)
        
        return self.opacity
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            'x': self.x,
            'y': self.y,
            'timestamp': self.timestamp,
            'opacity': round(self.opacity, 3),
            'speed': round(self.speed, 2)
        }


class VisualTrail:
    """視覺軌跡管理器"""
    
    def __init__(self, max_points: int = MAX_TRAIL_POINTS):
        self.trail_points: deque = deque(maxlen=max_points)
        self.max_points = max_points
        self.tracking = False
        self.mouse_listener = None
        self.last_point: Optional[TrailPoint] = None
        self.start_time = 0
        
    def on_mouse_move(self, x: int, y: int):
        """滑鼠移動事件"""
        if not self.tracking:
            return False
        
        current_time = time.time()
        
        # 安全檢查
        if validate_and_safe:
            safe, msg, (safe_x, safe_y) = validate_and_safe(x, y)
            if not safe and "超出安全範圍" in msg:
                x, y = safe_x, safe_y
        
        # 計算速度
        speed = 0.0
        if self.last_point:
            dx = x - self.last_point.x
            dy = y - self.last_point.y
            distance = math.sqrt(dx**2 + dy**2)
            time_diff = current_time - self.last_point.timestamp
            
            if time_diff > 0:
                speed = distance / time_diff
        
        # 建立軌跡點
        point = TrailPoint(x, y, current_time)
        point.speed = speed
        
        # 加入軌跡（自動 LRU 淘汰）
        self.trail_points.append(point)
        self.last_point = point
        
        # 輸出軌跡資訊（每 10 個點輸出一次，避免過多日誌）
        if len(self.trail_points) % 10 == 0:
            print(f"[ACTION] 軌跡點 #{len(self.trail_points)}: ({x}, {y}) - 速度: {speed:.1f} px/s")
        
        return True
    
    def start_tracking(self):
        """開始追蹤"""
        if self.tracking:
            print("[WARNING] 已經在追蹤中")
            return
        
        self.tracking = True
        self.trail_points.clear()
        self.last_point = None
        self.start_time = time.time()
        
        print("[START] visual-trail 開始追蹤")
        print(f"[INFO] 最大軌跡點：{self.max_points}")
        print(f"[INFO] 衰減時間：{DECAY_TIME_SECONDS} 秒")
        print(f"[INFO] 移動滑鼠來記錄軌跡...")
        print("[INFO] 按 Ctrl+C 停止追蹤")
        print("")
        
        # 啟動滑鼠監聽器
        self.mouse_listener = mouse.Listener(on_move=self.on_mouse_move)
        self.mouse_listener.start()
        
        try:
            while self.tracking:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[INFO] 接收到停止訊號...")
        
        self.stop_tracking()
    
    def stop_tracking(self):
        """停止追蹤"""
        if not self.tracking:
            return
        
        self.tracking = False
        
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        
        duration = time.time() - self.start_time
        point_count = len(self.trail_points)
        
        print("")
        print(f"[SUCCESS] 追蹤已停止")
        print(f"[INFO] 追蹤時長：{duration:.1f} 秒")
        print(f"[INFO] 軌跡點數：{point_count}")
        
        # 儲存軌跡
        if point_count > 0:
            self.save_trail()
    
    def update_decay(self):
        """更新所有軌跡點的衰減狀態"""
        current_time = time.time()
        
        for point in self.trail_points:
            point.update_decay(current_time)
    
    def analyze_trail(self) -> Dict:
        """
        分析軌跡統計
        
        Returns:
            Dict: 分析結果
        """
        if not self.trail_points:
            return {
                'success': False,
                'reason': '沒有軌跡資料'
            }
        
        print("[START] visual-trail 開始分析軌跡")
        print(f"[INFO] 分析 {len(self.trail_points)} 個軌跡點")
        print("")
        
        # 更新衰減
        self.update_decay()
        
        # 計算統計數據
        total_points = len(self.trail_points)
        
        # 計算總移動距離
        total_distance = 0.0
        points_list = list(self.trail_points)
        
        for i in range(1, len(points_list)):
            prev = points_list[i-1]
            curr = points_list[i]
            dx = curr.x - prev.x
            dy = curr.y - prev.y
            distance = math.sqrt(dx**2 + dy**2)
            total_distance += distance
        
        # 計算平均速度
        if total_points > 1:
            time_span = points_list[-1].timestamp - points_list[0].timestamp
            avg_speed = total_distance / time_span if time_span > 0 else 0
        else:
            avg_speed = 0
        
        # 識別熱區（最常出現的區域）
        hotspots = self._find_hotspots(points_list)
        
        # 計算記憶體使用
        memory_usage = self._estimate_memory()
        
        result = {
            'success': True,
            'total_points': total_points,
            'total_distance': round(total_distance, 2),
            'average_speed': round(avg_speed, 2),
            'hotspots': hotspots,
            'memory_usage': memory_usage,
            'time_span': round(points_list[-1].timestamp - points_list[0].timestamp, 2) if total_points > 1 else 0
        }
        
        # 輸出分析結果
        print(f"[SUCCESS] 軌跡分析完成")
        print(f"[TOTAL_POINTS] {result['total_points']}")
        print(f"[TOTAL_DISTANCE] {result['total_distance']} 像素")
        print(f"[AVERAGE_SPEED] {result['average_speed']} 像素/秒")
        print(f"[TIME_SPAN] {result['time_span']} 秒")
        print(f"[MEMORY] 使用 {result['memory_usage']}")
        print("")
        
        if hotspots:
            print("[HOTSPOTS] 最常停留區域：")
            for i, (x, y, count) in enumerate(hotspots[:5], 1):
                print(f"  {i}. ({x}, {y}) - {count} 次")
        
        return result
    
    def _find_hotspots(self, points: List[TrailPoint], grid_size: int = 50) -> List[Tuple[int, int, int]]:
        """
        找出熱區（最常出現的區域）
        
        Args:
            points: 軌跡點列表
            grid_size: 網格大小（像素）
        
        Returns:
            List[Tuple[int, int, int]]: (x, y, 次數) 列表
        """
        grid = {}
        
        for point in points:
            # 將座標四捨五入到網格
            grid_x = (point.x // grid_size) * grid_size
            grid_y = (point.y // grid_size) * grid_size
            key = (grid_x, grid_y)
            
            grid[key] = grid.get(key, 0) + 1
        
        # 排序並回傳前 10 名
        sorted_hotspots = sorted(grid.items(), key=lambda x: x[1], reverse=True)
        
        return [(x, y, count) for (x, y), count in sorted_hotspots[:10]]
    
    def _estimate_memory(self) -> str:
        """估算記憶體使用量"""
        point_count = len(self.trail_points)
        bytes_per_point = 64  # 粗略估算
        total_bytes = point_count * bytes_per_point
        
        if total_bytes < 1024:
            return f"{total_bytes} B"
        elif total_bytes < 1024 * 1024:
            return f"{total_bytes / 1024:.1f} KB"
        else:
            return f"{total_bytes / 1024 / 1024:.1f} MB"
    
    def save_trail(self, filename: Optional[str] = None) -> bool:
        """
        儲存軌跡
        
        Args:
            filename: 檔案名稱（可選）
        
        Returns:
            bool: 是否成功
        """
        if not self.trail_points:
            print("[WARNING] 沒有軌跡資料可儲存")
            return False
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"trail_{timestamp}.json"
        
        filepath = os.path.join(TRAIL_DIR, filename)
        
        try:
            data = {
                'points': [p.to_dict() for p in self.trail_points],
                'total_points': len(self.trail_points),
                'start_time': self.start_time,
                'end_time': time.time(),
                'settings': {
                    'max_points': self.max_points,
                    'decay_time': DECAY_TIME_SECONDS,
                    'decay_factor': DECAY_FACTOR
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"[SUCCESS] 軌跡已儲存: {filepath}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 儲存軌跡失敗: {e}")
            return False
    
    def clear_trail(self):
        """清除軌跡"""
        self.trail_points.clear()
        self.last_point = None
        print("[SUCCESS] 軌跡已清除")


def main():
    """主程式"""
    args = sys.argv[1:]
    
    if len(args) < 1:
        print("[USAGE] python run.py <命令>")
        print("")
        print("命令：")
        print("  start              開始追蹤軌跡")
        print("  stop               停止追蹤")
        print("  analyze            分析軌跡統計")
        print("  clear              清除軌跡")
        print("")
        print("範例：")
        print("  python run.py start")
        print("  python run.py stop")
        print("  python run.py analyze")
        print("")
        print("[ERROR] 請提供命令")
        sys.exit(1)
    
    command = args[0].lower()
    trail = VisualTrail()
    
    print(f"[START] visual-trail 開始執行")
    print(f"[INFO] 命令: {command}")
    print("")
    
    if command == 'start':
        trail.start_tracking()
        sys.exit(0)
    
    elif command == 'stop':
        trail.stop_tracking()
        sys.exit(0)
    
    elif command == 'analyze':
        result = trail.analyze_trail()
        sys.exit(0 if result.get('success') else 1)
    
    elif command == 'clear':
        trail.clear_trail()
        sys.exit(0)
    
    else:
        print(f"[ERROR] 未知命令: {command}")
        print("[USAGE] 支援的命令：start | stop | analyze | clear")
        sys.exit(1)


if __name__ == "__main__":
    main()