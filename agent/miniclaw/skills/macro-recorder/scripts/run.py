#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macro-recorder 技能腳本 — 巨集錄製與執行系統

功能：
1. 錄製滑鼠移動、點擊、鍵盤輸入
2. 儲存為可重複執行的巨集腳本
3. 支援單次或循環執行
4. 結構化日誌輸出

用法：
    python run.py record <巨集名稱>      # 開始錄製
    python run.py play <巨集名稱>        # 執行巨集
    python run.py list                   # 列出所有巨集
    python run.py stop                   # 停止錄製
"""

import sys
import os
import json
import time
import threading
from typing import List, Dict, Optional
from datetime import datetime

# 加入腳本目錄到 Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# 嘗試匯入必要模組
try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
except ImportError:
    print("[ERROR] 找不到 pyautogui 模組，請執行：pip install pyautogui")
    sys.exit(1)

try:
    from pynput import mouse, keyboard
except ImportError:
    print("[ERROR] 找不到 pynput 模組，請執行：pip install pynput")
    sys.exit(1)

# 引入 safe_locate 進行安全檢查
try:
    from safe_locate import validate_and_safe
except ImportError:
    print("[WARNING] 找不到 safe_locate.py，將跳過安全檢查")
    validate_and_safe = None

# 巨集儲存目錄
MACRO_DIR = os.path.join(SCRIPT_DIR, '..', '..', 'data', 'macros')
os.makedirs(MACRO_DIR, exist_ok=True)

# 全域變數
recording = False
current_macro: List[Dict] = []
start_time = 0


class MacroRecorder:
    """巨集錄製器"""
    
    def __init__(self):
        self.mouse_listener = None
        self.keyboard_listener = None
        self.actions: List[Dict] = []
        self.start_time = 0
        
    def on_mouse_move(self, x, y):
        """滑鼠移動事件"""
        if not recording:
            return False
        
        elapsed = time.time() - self.start_time
        self.actions.append({
            'type': 'mouse_move',
            'x': x,
            'y': y,
            'time': elapsed
        })
        return True
    
    def on_mouse_click(self, x, y, button, pressed):
        """滑鼠點擊事件"""
        if not recording:
            return False
        
        if pressed:
            elapsed = time.time() - self.start_time
            button_name = 'left'
            if button == mouse.Button.right:
                button_name = 'right'
            elif button == mouse.Button.middle:
                button_name = 'middle'
            
            self.actions.append({
                'type': 'mouse_click',
                'x': x,
                'y': y,
                'button': button_name,
                'time': elapsed
            })
        return True
    
    def on_key_press(self, key):
        """鍵盤按下事件"""
        if not recording:
            return False
        
        try:
            elapsed = time.time() - self.start_time
            
            # 處理特殊鍵
            if hasattr(key, 'char'):
                key_char = key.char
            elif hasattr(key, 'name'):
                key_char = f'[{key.name}]'
            else:
                key_char = str(key)
            
            self.actions.append({
                'type': 'key_press',
                'key': key_char,
                'time': elapsed
            })
        except Exception as e:
            print(f"[WARNING] 鍵盤記錄錯誤: {e}")
        
        return True
    
    def start_recording(self):
        """開始錄製"""
        global recording, current_macro, start_time
        
        recording = True
        self.actions = []
        self.start_time = time.time()
        start_time = self.start_time
        
        print("[START] macro-recorder 開始錄製")
        print("[INFO] 移動滑鼠、點擊或按鍵盤來記錄操作...")
        print("[INFO] 按 Ctrl+C 停止錄製")
        print("")
        
        # 啟動監聽器
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click
        )
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        try:
            while recording:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[INFO] 接收到停止訊號...")
        
        self.stop_recording()
        return self.actions
    
    def stop_recording(self):
        """停止錄製"""
        global recording
        
        recording = False
        
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        
        current_macro = self.actions
        print(f"[SUCCESS] 錄製完成，共記錄 {len(self.actions)} 個動作")


class MacroPlayer:
    """巨集播放器"""
    
    def __init__(self, macro_data: List[Dict], loop: bool = False, speed: float = 1.0):
        self.actions = macro_data
        self.loop = loop
        self.speed = speed
        self.running = False
        
    def play(self):
        """執行巨集"""
        print(f"[START] macro-recorder 開始執行巨集")
        print(f"[INFO] 總共 {len(self.actions)} 個動作")
        print(f"[INFO] 執行速度: {self.speed}x")
        print(f"[INFO] 循環模式: {'開啟' if self.loop else '關閉'}")
        print("")
        
        self.running = True
        execution_count = 0
        
        try:
            while self.running:
                execution_count += 1
                print(f"[INFO] 執行次數: {execution_count}")
                
                for i, action in enumerate(self.actions, 1):
                    if not self.running:
                        break
                    
                    # 計算延遲（根據速度調整）
                    if i > 1:
                        delay = action['time'] / self.speed
                        time.sleep(delay)
                    
                    # 執行動作
                    self.execute_action(action, i)
                
                if not self.loop:
                    break
                
                print(f"[INFO] 循環執行中... (第 {execution_count} 次)")
                time.sleep(1)
            
            print("")
            print(f"[SUCCESS] 巨集執行完成")
            print(f"[COUNT] 總共執行 {execution_count} 次")
            return True
            
        except KeyboardInterrupt:
            print("\n[INFO] 接收到停止訊號...")
            self.running = False
            print(f"[SUCCESS] 巨集已停止")
            print(f"[COUNT] 執行 {execution_count} 次後停止")
            return False
        except Exception as e:
            print(f"[FAILED] 巨集執行失敗: {e}")
            return False
    
    def execute_action(self, action: Dict, index: int):
        """執行單個動作"""
        try:
            action_type = action['type']
            
            if action_type == 'mouse_move':
                x, y = action['x'], action['y']
                
                # 安全檢查
                if validate_and_safe:
                    safe, msg, (safe_x, safe_y) = validate_and_safe(x, y)
                    if not safe and "超出安全範圍" in msg:
                        x, y = safe_x, safe_y
                        print(f"[WARNING] 座標已調整為安全範圍: ({x}, {y})")
                
                pyautogui.moveTo(x, y, duration=0.1)
                print(f"[ACTION] 步驟 {index}: 移動滑鼠到 ({x}, {y})")
            
            elif action_type == 'mouse_click':
                x, y = action['x'], action['y']
                button = action.get('button', 'left')
                
                # 安全檢查
                if validate_and_safe:
                    safe, msg, (safe_x, safe_y) = validate_and_safe(x, y)
                    if not safe and "超出安全範圍" in msg:
                        x, y = safe_x, safe_y
                
                pyautogui.click(x, y, button=button)
                print(f"[ACTION] 步驟 {index}: {button} 鍵點擊 ({x}, {y})")
            
            elif action_type == 'key_press':
                key = action['key']
                
                # 處理特殊鍵
                if key.startswith('[') and key.endswith(']'):
                    key_name = key[1:-1]
                    pyautogui.press(key_name)
                    print(f"[ACTION] 步驟 {index}: 按下 {key}")
                else:
                    pyautogui.press(key)
                    print(f"[ACTION] 步驟 {index}: 按下按鍵 {key}")
        
        except Exception as e:
            print(f"[ERROR] 執行動作失敗 (步驟 {index}): {e}")


def save_macro(name: str, actions: List[Dict]) -> bool:
    """儲存巨集"""
    macro_file = os.path.join(MACRO_DIR, f"{name}.json")
    try:
        data = {
            'name': name,
            'actions': actions,
            'created_at': datetime.now().isoformat(),
            'action_count': len(actions)
        }
        with open(macro_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[SUCCESS] 巨集已儲存: {macro_file}")
        return True
    except Exception as e:
        print(f"[ERROR] 儲存巨集失敗: {e}")
        return False


def load_macro(name: str) -> Optional[List[Dict]]:
    """載入巨集"""
    macro_file = os.path.join(MACRO_DIR, f"{name}.json")
    if not os.path.exists(macro_file):
        return None
    
    try:
        with open(macro_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('actions', [])
    except Exception as e:
        print(f"[ERROR] 載入巨集失敗: {e}")
        return None


def list_macros():
    """列出所有巨集"""
    if not os.path.exists(MACRO_DIR):
        print("[INFO] 巨集目錄不存在")
        return []
    
    macros = []
    for file in os.listdir(MACRO_DIR):
        if file.endswith('.json'):
            macro_file = os.path.join(MACRO_DIR, file)
            try:
                with open(macro_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                macros.append({
                    'name': data.get('name', file[:-5]),
                    'actions': data.get('action_count', 0),
                    'created': data.get('created_at', 'unknown')
                })
            except:
                continue
    
    return macros


def main():
    """主程式"""
    args = sys.argv[1:]
    
    if len(args) < 1:
        print("[USAGE] python run.py <命令> [參數]")
        print("")
        print("命令：")
        print("  record <巨集名稱>    開始錄製巨集")
        print("  play <巨集名稱>      執行巨集")
        print("  list                列出所有巨集")
        print("  stop                停止錄製")
        print("")
        print("範例：")
        print("  python run.py record 每日登入")
        print("  python run.py play 每日登入")
        print("  python run.py play 每日登入 --loop")
        print("  python run.py play 每日登入 --speed 2.0")
        print("")
        print("[ERROR] 請提供命令")
        sys.exit(1)
    
    command = args[0].lower()
    
    print(f"[START] macro-recorder 開始執行")
    print(f"[INFO] 命令: {command}")
    print("")
    
    # 錄製模式
    if command == 'record':
        if len(args) < 2:
            print("[ERROR] 請提供巨集名稱")
            print("範例：python run.py record 每日登入")
            sys.exit(1)
        
        macro_name = args[1]
        recorder = MacroRecorder()
        actions = recorder.start_recording()
        
        if actions:
            save_macro(macro_name, actions)
            sys.exit(0)
        else:
            print("[FAILED] 沒有錄製到任何動作")
            sys.exit(1)
    
    # 執行模式
    elif command == 'play':
        if len(args) < 2:
            print("[ERROR] 請提供巨集名稱")
            print("範例：python run.py play 每日登入")
            sys.exit(1)
        
        macro_name = args[1]
        actions = load_macro(macro_name)
        
        if not actions:
            print(f"[FAILED] 找不到巨集: {macro_name}")
            print(f"[INFO] 使用 'python run.py list' 查看所有巨集")
            sys.exit(1)
        
        # 解析參數
        loop = '--loop' in args
        speed = 1.0
        
        for i, arg in enumerate(args):
            if arg == '--speed' and i + 1 < len(args):
                try:
                    speed = float(args[i + 1])
                except:
                    print("[WARNING] 速度參數無效，使用預設值 1.0")
        
        player = MacroPlayer(actions, loop=loop, speed=speed)
        success = player.play()
        
        sys.exit(0 if success else 1)
    
    # 列出巨集
    elif command == 'list':
        print("[INFO] 列出所有巨集：")
        print("")
        
        macros = list_macros()
        if not macros:
            print("（尚無巨集）")
        else:
            print(f"{'名稱':<20} {'動作數':<10} {'建立時間'}")
            print("-" * 60)
            for m in macros:
                name = m['name']
                count = m['actions']
                created = m['created'][:19] if m['created'] != 'unknown' else 'unknown'
                print(f"{name:<20} {count:<10} {created}")
        
        sys.exit(0)
    
    # 停止錄製
    elif command == 'stop':
        global recording
        if recording:
            recording = False
            print("[SUCCESS] 已發送停止訊號")
        else:
            print("[INFO] 目前沒有正在錄製的巨集")
        sys.exit(0)
    
    else:
        print(f"[ERROR] 未知命令: {command}")
        print("[USAGE] 支援的命令：record | play | list | stop")
        sys.exit(1)


if __name__ == "__main__":
    main()