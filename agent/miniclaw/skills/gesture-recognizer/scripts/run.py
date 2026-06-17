#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gesture-recognizer 技能腳本 — 手勢識別系統

功能：
1. 讀取視覺軌跡資料（JSON 格式）
2. 分析軌跡特徵（波峰、波谷、方向轉折）
3. 辨識對稱字元手勢（M、W、O、V）
4. 觸發對應的系統指令
5. 結構化日誌輸出

用法：
    python run.py recognize <軌跡檔案>     # 辨識手勢
    python run.py test <座標檔案>          # 測試模式（直接輸入座標）
"""

import sys
import os
import json
import math
from typing import List, Tuple, Dict, Optional
from datetime import datetime

# 加入腳本目錄到 Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# 軌跡資料目錄
TRAIL_DIR = os.path.join(SCRIPT_DIR, '..', '..', '..', '..', 'data', 'trails')
os.makedirs(TRAIL_DIR, exist_ok=True)


class GestureRecognizer:
    """手勢識別器"""
    
    def __init__(self):
        # 手勢模板定義
        self.gestures = {
            'M': {
                'name': 'M',
                'description': '開啟選單',
                'peaks': 2,        # 2個波峰
                'valleys': 1,      # 1個波谷
                'min_symmetry': 0.85,
                'min_points': 20
            },
            'W': {
                'name': 'W',
                'description': '關閉/返回',
                'peaks': 3,        # 3個波峰
                'valleys': 2,      # 2個波谷
                'min_symmetry': 0.80,
                'min_points': 30
            },
            'O': {
                'name': 'O',
                'description': '確認/圈選',
                'peaks': 0,        # 圓形（無明顯波峰）
                'valleys': 0,
                'min_symmetry': 0.75,
                'min_points': 30,
                'is_closed': True  # 閉合軌跡
            },
            'V': {
                'name': 'V',
                'description': '剪貼/特殊功能',
                'peaks': 1,        # 1個尖峰
                'valleys': 0,
                'min_symmetry': 0.90,
                'min_points': 15
            }
        }
    
    def load_trajectory(self, filepath: str) -> Optional[List[Dict]]:
        """
        載入軌跡檔案
        
        Args:
            filepath: 軌跡檔案路徑
        
        Returns:
            Optional[List[Dict]]: 軌跡點列表
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            points = data.get('points', [])
            if not points:
                return None
            
            # 轉換為統一格式
            trajectory = []
            for p in points:
                trajectory.append({
                    'x': p['x'],
                    'y': p['y'],
                    'timestamp': p['timestamp']
                })
            
            return trajectory
            
        except Exception as e:
            print(f"[ERROR] 讀取軌跡檔案失敗: {e}")
            return None
    
    def extract_features(self, trajectory: List[Dict]) -> Dict:
        """
        提取軌跡特徵
        
        Args:
            trajectory: 軌跡點列表
        
        Returns:
            Dict: 特徵字典
        """
        if len(trajectory) < 5:
            return {
                'peaks': [],
                'valleys': [],
                'direction_changes': 0,
                'is_closed': False,
                'total_distance': 0,
                'bounding_box': (0, 0, 0, 0)
            }
        
        # 提取座標序列
        x_coords = [p['x'] for p in trajectory]
        y_coords = [p['y'] for p in trajectory]
        
        # 計算移動方向（角度變化）
        directions = []
        for i in range(1, len(trajectory)):
            dx = x_coords[i] - x_coords[i-1]
            dy = y_coords[i] - y_coords[i-1]
            angle = math.atan2(dy, dx)
            directions.append(angle)
        
        # 檢測方向轉折點
        direction_changes = 0
        angle_threshold = math.pi / 4  # 45度視為轉折
        
        for i in range(1, len(directions)):
            angle_diff = abs(directions[i] - directions[i-1])
            if angle_diff > angle_threshold:
                direction_changes += 1
        
        # 檢測波峰和波谷（基於 Y 座標）
        peaks = []
        valleys = []
        
        for i in range(2, len(y_coords) - 2):
            # 波峰：當前點比前後點都高
            if y_coords[i] > y_coords[i-1] and y_coords[i] > y_coords[i+1]:
                if y_coords[i] > y_coords[i-2] and y_coords[i] > y_coords[i+2]:
                    peaks.append(i)
            # 波谷：當前點比前後點都低
            elif y_coords[i] < y_coords[i-1] and y_coords[i] < y_coords[i+1]:
                if y_coords[i] < y_coords[i-2] and y_coords[i] < y_coords[i+2]:
                    valleys.append(i)
        
        # 計算總移動距離
        total_distance = 0
        for i in range(1, len(trajectory)):
            dx = x_coords[i] - x_coords[i-1]
            dy = y_coords[i] - y_coords[i-1]
            total_distance += math.sqrt(dx**2 + dy**2)
        
        # 計算邊界框
        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)
        
        # 檢測是否閉合（起點和終點距離）
        start_x, start_y = x_coords[0], y_coords[0]
        end_x, end_y = x_coords[-1], y_coords[-1]
        close_distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        bbox_diagonal = math.sqrt((max_x - min_x)**2 + (max_y - min_y)**2)
        
        is_closed = close_distance < bbox_diagonal * 0.2 if bbox_diagonal > 0 else False
        
        return {
            'peaks': peaks,
            'valleys': valleys,
            'peak_count': len(peaks),
            'valley_count': len(valleys),
            'direction_changes': direction_changes,
            'is_closed': is_closed,
            'total_distance': total_distance,
            'bounding_box': (min_x, min_y, max_x, max_y),
            'width': max_x - min_x,
            'height': max_y - min_y
        }
    
    def calculate_symmetry(self, trajectory: List[Dict], features: Dict) -> float:
        """
        計算軌跡對稱度
        
        Args:
            trajectory: 軌跡點列表
            features: 特徵字典
        
        Returns:
            float: 對稱度 (0.0 ~ 1.0)
        """
        if len(trajectory) < 10:
            return 0.0
        
        x_coords = [p['x'] for p in trajectory]
        y_coords = [p['y'] for p in trajectory]
        
        # 計算中心線
        min_x = min(x_coords)
        max_x = max(x_coords)
        center_x = (min_x + max_x) / 2
        
        # 計算左右對稱性
        left_points = []
        right_points = []
        
        for i in range(len(trajectory)):
            x = x_coords[i]
            y = y_coords[i]
            
            if x < center_x:
                # 左側點，計算到中心線的距離
                dist = abs(x - center_x)
                left_points.append((y, dist))
            else:
                # 右側點
                dist = abs(x - center_x)
                right_points.append((y, dist))
        
        if not left_points or not right_points:
            return 0.0
        
        # 簡化對稱度計算：比較左右側點的 Y 分佈
        left_y = [p[0] for p in left_points]
        right_y = [p[0] for p in right_points]
        
        # 計算 Y 分佈的相似度
        left_min_y, left_max_y = min(left_y), max(left_y)
        right_min_y, right_max_y = min(right_y), max(right_y)
        
        y_range_diff = abs((left_max_y - left_min_y) - (right_max_y - right_min_y))
        max_range = max(left_max_y - left_min_y, right_max_y - right_min_y)
        
        if max_range == 0:
            return 1.0
        
        symmetry = 1.0 - (y_range_diff / max_range)
        return max(0.0, min(1.0, symmetry))
    
    def recognize_gesture(self, trajectory: List[Dict]) -> Dict:
        """
        辨識手勢
        
        Args:
            trajectory: 軌跡點列表
        
        Returns:
            Dict: 辨識結果
        """
        print("[START] gesture-recognizer 開始辨識")
        print(f"[INFO] 讀取軌跡：{len(trajectory)} 個點")
        print("[INFO] 分析特徵點...")
        print("")
        
        # 檢查軌跡長度
        if len(trajectory) < 10:
            return {
                'success': False,
                'matched': None,
                'reason': '軌跡點數太少，無法辨識'
            }
        
        # 提取特徵
        features = self.extract_features(trajectory)
        symmetry = self.calculate_symmetry(trajectory, features)
        
        print(f"[INFO] 特徵提取完成：")
        print(f"  - 波峰數：{features['peak_count']}")
        print(f"  - 波谷數：{features['valley_count']}")
        print(f"  - 方向轉折：{features['direction_changes']}")
        print(f"  - 對稱度：{symmetry:.2f}")
        print(f"  - 閉合軌跡：{'是' if features['is_closed'] else '否'}")
        print("")
        
        # 匹配手勢模板
        best_match = None
        best_confidence = 0.0
        
        for gesture_key, gesture_template in self.gestures.items():
            confidence = self._match_gesture_template(
                gesture_key,
                gesture_template,
                features,
                symmetry
            )
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = gesture_key
        
        # 判斷是否匹配成功
        if best_match and best_confidence >= 0.6:
            gesture_info = self.gestures[best_match]
            
            print(f"[SUCCESS] 手勢辨識完成")
            print(f"[MATCHED] {best_match}")
            print(f"[CONFIDENCE] {best_confidence:.2f}")
            print(f"[FEATURES] {gesture_info['peak_count']}個波峰, {gesture_info['valley_count']}個波谷, 對稱度 {symmetry:.2f}")
            print(f"[ACTION] 觸發指令：{gesture_info['description']}")
            
            return {
                'success': True,
                'matched': best_match,
                'confidence': best_confidence,
                'description': gesture_info['description'],
                'features': {
                    'peaks': features['peak_count'],
                    'valleys': features['valley_count'],
                    'symmetry': symmetry,
                    'is_closed': features['is_closed']
                }
            }
        else:
            print(f"[FAILED] 無法辨識手勢")
            print(f"[REASON] 軌跡特徵不符合任何已知手勢（最高信心度：{best_confidence:.2f}）")
            
            return {
                'success': False,
                'matched': None,
                'reason': '軌跡特徵不符合任何已知手勢',
                'best_confidence': best_confidence
            }
    
    def _match_gesture_template(self, gesture_key: str, template: Dict, 
                                features: Dict, symmetry: float) -> float:
        """
        匹配單個手勢模板
        
        Args:
            gesture_key: 手勢名稱
            template: 手勢模板
            features: 軌跡特徵
            symmetry: 對稱度
        
        Returns:
            float: 信心度 (0.0 ~ 1.0)
        """
        confidence = 0.0
        
        # 1. 檢查波峰波谷數量
        if template['peaks'] > 0:
            peak_match = 1.0 - abs(features['peak_count'] - template['peaks']) / max(template['peaks'], 1)
            confidence += peak_match * 0.3
        else:
            # 無波峰要求（O 手勢）
            confidence += 0.3
        
        if template['valleys'] > 0:
            valley_match = 1.0 - abs(features['valley_count'] - template['valleys']) / max(template['valleys'], 1)
            confidence += valley_match * 0.3
        else:
            # 無波谷要求
            confidence += 0.3
        
        # 2. 檢查閉合性（O 手勢）
        if template.get('is_closed', False):
            if features['is_closed']:
                confidence += 0.2
            else:
                confidence -= 0.2
        else:
            confidence += 0.2
        
        # 3. 檢查對稱度
        if symmetry >= template['min_symmetry']:
            confidence += 0.2
        else:
            confidence += symmetry * 0.2
        
        # 4. 檢查軌跡長度
        if features['total_distance'] > 100:  # 至少移動 100 像素
            confidence += 0.1
        else:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))


def main():
    """主程式"""
    args = sys.argv[1:]
    
    if len(args) < 1:
        print("[USAGE] python run.py <命令> [參數]")
        print("")
        print("命令：")
        print("  recognize <軌跡檔案>    辨識手勢")
        print("  test <座標JSON>         測試模式")
        print("")
        print("範例：")
        print("  python run.py recognize trail_20260617_094322.json")
        print("  python run.py test '{\"points\": [...]}'")
        print("")
        print("[ERROR] 請提供命令")
        sys.exit(1)
    
    command = args[0].lower()
    recognizer = GestureRecognizer()
    
    print(f"[START] gesture-recognizer 開始執行")
    print(f"[INFO] 命令: {command}")
    print("")
    
    # 辨識模式
    if command == 'recognize':
        if len(args) < 2:
            print("[ERROR] 請提供軌跡檔案路徑")
            print("範例：python run.py recognize trail_20260617_094322.json")
            sys.exit(1)
        
        trajectory_file = args[1]
        
        # 嘗試完整路徑
        if not os.path.exists(trajectory_file):
            # 嘗試在軌跡目錄中尋找
            trajectory_file = os.path.join(TRAIL_DIR, trajectory_file)
        
        if not os.path.exists(trajectory_file):
            print(f"[FAILED] 找不到軌跡檔案: {args[1]}")
            sys.exit(1)
        
        trajectory = recognizer.load_trajectory(trajectory_file)
        if not trajectory:
            print(f"[FAILED] 讀取軌跡失敗")
            sys.exit(1)
        
        result = recognizer.recognize_gesture(trajectory)
        sys.exit(0 if result['success'] else 1)
    
    # 測試模式
    elif command == 'test':
        if len(args) < 2:
            print("[ERROR] 請提供座標 JSON")
            print("範例：python run.py test '{\"points\": [{\"x\": 100, \"y\": 200, \"timestamp\": 1234567890}, ...]}'")
            sys.exit(1)
        
        try:
            test_data = json.loads(args[1])
            points = test_data.get('points', [])
            
            if not points:
                print("[FAILED] JSON 中沒有 points 資料")
                sys.exit(1)
            
            # 轉換為軌跡格式
            trajectory = []
            for p in points:
                trajectory.append({
                    'x': p['x'],
                    'y': p['y'],
                    'timestamp': p.get('timestamp', time.time())
                })
            
            result = recognizer.recognize_gesture(trajectory)
            sys.exit(0 if result['success'] else 1)
            
        except json.JSONDecodeError as e:
            print(f"[FAILED] JSON 解析失敗: {e}")
            sys.exit(1)
    
    else:
        print(f"[ERROR] 未知命令: {command}")
        print("[USAGE] 支援的命令：recognize | test")
        sys.exit(1)


if __name__ == "__main__":
    import time
    main()