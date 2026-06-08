# 給 Gemini 的提示詞（要求精確裁切座標）

把這段提示詞連同影片一起貼到 Google AI Studio。

---

```
我要用 Python cv2 從這段影片裁切 UI 元素作為圖案比對範本。

請針對以下 5 個元素，分析影片對應秒數的畫面，給我精確的裁切座標。

元素清單：
1. Windows 工作列搜尋圖示（影片約第 5 秒）
2. 搜尋結果中的 Chrome 應用程式圖示（影片約第 9 秒）
3. 首頁搜尋列輸入框（影片約第 15 秒）
4. Yahoo 搜尋結果中的 YouTube 連結文字（影片約第 21 秒）
5. YouTube 頂端搜尋列（影片約第 28 秒）

請用畫面比例（0.0 ~ 1.0）表示裁切區域，左上角為 (0,0)，右下角為 (1,1)。
裁切範圍只要包住元素本身，不要裁太大。

請只回傳以下 JSON 格式，不要其他說明文字：

[
  {
    "name": "template_win_search",
    "second": 5,
    "x1": 0.00, "y1": 0.00, "x2": 0.00, "y2": 0.00,
    "color": "元素主要顏色",
    "shape": "形狀描述",
    "text": "文字內容（沒有就填空字串）"
  },
  {
    "name": "template_chrome_app",
    "second": 9,
    "x1": 0.00, "y1": 0.00, "x2": 0.00, "y2": 0.00,
    "color": "",
    "shape": "",
    "text": ""
  },
  {
    "name": "template_yahoo_bar",
    "second": 15,
    "x1": 0.00, "y1": 0.00, "x2": 0.00, "y2": 0.00,
    "color": "",
    "shape": "",
    "text": ""
  },
  {
    "name": "template_yahoo_yt",
    "second": 21,
    "x1": 0.00, "y1": 0.00, "x2": 0.00, "y2": 0.00,
    "color": "",
    "shape": "",
    "text": ""
  },
  {
    "name": "template_yt_search",
    "second": 28,
    "x1": 0.00, "y1": 0.00, "x2": 0.00, "y2": 0.00,
    "color": "",
    "shape": "",
    "text": ""
  }
]
```
