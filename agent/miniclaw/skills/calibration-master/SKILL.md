---
name: calibration-master
description: AI 畫面位置校準系統。支援 GPT-4o Vision 2× 放大偵測、截取 normal/hover 範本、點擊前後確認機制、自動降級手動校準。用於精準定位畫面元素並建立可重複使用的校準資料。
---

# Calibration Master — AI 畫面位置校準技能

## 功能概述

此技能提供完整的 AI 驅動畫面校準流程，讓小龍蝦能夠：
1. 使用 GPT-4o Vision 進行 2× 放大偵測，精準定位畫面元素
2. 自動截取 normal/hover 兩種狀態的範本圖片
3. 點擊前後進行畫面確認，確保操作正確
4. 當 AI 偵測失敗時，自動降級為手動校準模式

## 使用場景

- 遊戲 UI 元素定位（按鈕、圖示、選單）
- 桌面應用程式按鈕校準
- 網頁元素定位與互動
- 需要高精度重複點擊的任務

## 校準模式

### 模式 1：AI 自動校準（推薦）
```
[calibration-master auto <目標名稱>]
```
- 使用 GPT-4o Vision 分析畫面
- 2× 放大截圖提升偵測精度
- 自動尋找並回傳座標

### 模式 2：手動校準（降級）
```
[calibration-master manual <目標名稱>]
```
- 提示使用者移動滑鼠到目標位置
- 記錄當前滑鼠座標
- 建立校準資料檔

### 模式 3：驗證校準
```
[calibration-master verify <目標名稱>]
```
- 使用已儲存的校準資料
- 截圖比對確認位置正確性
- 回傳信心度分數

## 輸出格式

成功時：
```
[SUCCESS] 校準完成
[TARGET] 目標名稱
[COORDINATE] X, Y
[CONFIDENCE] 0.95
[TEMPLATE] normal.png, hover.png
```

失敗時：
```
[FAILED] 校準失敗
[REASON] 無法找到目標元素
[FALLBACK] 建議使用手動校準模式
```

## 與其他技能的協作

- **click-master**：提供精準座標給點擊技能使用
- **safe_locate**：確保校準座標在安全範圍內
- **recorder**：可錄製校準過程建立腳本

## 技術實作

- GPT-4o Vision API 進行圖像分析
- PIL/Pillow 進行圖片處理與 2× 放大
- pyautogui 進行截圖與滑鼠控制
- JSON 格式儲存校準資料（可重複使用）