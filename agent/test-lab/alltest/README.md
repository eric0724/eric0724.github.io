# Miniclaw 操作錄製工具

## 安裝

```
py -m pip install pyautogui Pillow pynput opencv-python
```

## 使用步驟

### 1. 錄製操作
```
py recorder.py
```
- 在「主要訊息」欄寫整體說明
- 按「▶ 開始錄製」→ 視窗縮小，開始操作
- 按 **F8** 停止錄製
- 填寫每個步驟的說明
- 按「✅ 完成，產出並複製給 Miniclaw」

### 2. 存出截圖（有標記區域時才需要）
```
py extract_screenshots.py
```
截圖存在 `captures/` 資料夾

### 3. 把複製的文字貼給 Miniclaw
告訴 Miniclaw：「幫我做一個自動執行這些步驟的腳本」

### 4. 執行產出的腳本
```
py auto_run_xxx.py
```

## 檔案說明

| 檔案 | 說明 |
|------|------|
| `recorder.py` | 錄製工具主程式 |
| `extract_screenshots.py` | 從 JSON 存出截圖 |
| `auto_run_template.py` | Miniclaw 產出腳本的範本 |
| `alltest.md` | 開發過程與技術說明 |
| `captures/` | 錄製的 JSON 和截圖 |
