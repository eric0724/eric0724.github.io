---
name: gesture-recognizer
description: 手勢識別系統。識別滑鼠或螢幕上的連續軌跡，偵測是否符合特殊的對稱字元手勢（M、W、O、V），並觸發對應的系統指令。用於遊戲輔助、快速指令觸發、手勢控制。
---

# Gesture Recognizer — 手勢識別技能

## 功能概述

此技能提供完整的手勢識別與觸發功能：
1. 讀取視覺軌跡資料（JSON 格式）
2. 分析軌跡特徵（波峰、波谷、方向轉折）
3. 辨識對稱字元手勢（M、W、O、V）
4. 觸發對應的系統指令

## 使用場景

- 遊戲輔助手勢控制（畫 M 開啟地圖、畫 O 確認）
- 快速指令觸發（畫 V 剪貼、畫 W 關閉視窗）
- 無障礙手勢操作
- 創意互動控制

## 支援的手勢

### M 手勢（開啟選單）
```
[gesture-recognizer recognize <軌跡檔案>]
```
- 特徵：兩個波峰，中間一個波谷
- 觸發：開啟遊戲選單或功能表

### W 手勢（關閉/返回）
```
[gesture-recognizer recognize <軌跡檔案>]
```
- 特徵：三個波峰，兩個波谷
- 觸發：關閉視窗或返回上一頁

### O 手勢（確認/圈選）
```
[gesture-recognizer recognize <軌跡檔案>]
```
- 特徵：閉合圓形軌跡
- 觸發：確認操作或圈選區域

### V 手勢（剪貼/特殊功能）
```
[gesture-recognizer recognize <軌跡檔案>]
```
- 特徵：單一尖峰，兩邊對稱下降
- 觸發：剪貼簿操作或特殊功能

## 輸出格式

成功辨識：
```
[START] gesture-recognizer 開始辨識
[INFO] 讀取軌跡：1500 個點
[INFO] 分析特徵點...
[SUCCESS] 手勢辨識完成
[MATCHED] M
[CONFIDENCE] 0.92
[FEATURES] 2個波峰, 1個波谷, 對稱度 0.95
```

辨識失敗：
```
[START] gesture-recognizer 開始辨識
[INFO] 讀取軌跡：1500 個點
[INFO] 分析特徵點...
[FAILED] 無法辨識手勢
[REASON] 軌跡特徵不符合任何已知手勢
```

## 與其他技能的協作

- **visual-trail**：讀取軌跡資料
- **click-master**：手勢觸發後執行點擊
- **calibration-master**：手勢起點校準

## 技術實作

- 特徵點提取（波峰/波谷檢測）
- 方向轉折點分析
- 對稱性計算
- 模板匹配算法
- 信心度評分