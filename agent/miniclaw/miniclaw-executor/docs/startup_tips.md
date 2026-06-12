# Miniclaw 啟動提示

如果在啟動過程中出現以下情況：

## 問題一：出現「請按任意鍵繼續」
表示某個步驟失敗了（例如 Node.js 未安裝、ngrok 找不到等）。
請先關閉當前視窗，然後**重新打開 openminiclaw.bat**。
重試前建議確認：
- 網路是否連線
- 防火牆/防毒是否阻擋

如果重複失敗，請截圖錯誤訊息回報。

## 問題二：瀏覽器打開後無法連線
1. 確認 ngrok 視窗有沒有顯示 `ERROR` 或 `Session failed`
2. 如果有錯誤，按 `Win + R` → 輸入 `cmd` → 執行 `ngrok update`
3. 關閉所有視窗，重新打開 `openminiclaw.bat`

## 問題三：Node.js 錯誤
- `npm install` 失敗 → 檢查網路，重新執行 `.bat`
- `port 3000` 被占用 → 關閉佔用程式（如另一個 Node.js），重新執行

---

**最簡單的解決方法：關掉所有視窗，重新打開 openminiclaw.bat。**