# ngrok Update Guide

If ngrok is too old or fails to start, do this:

## Method 1: Using ngrok update (Recommended)

1. Press `Win + R`
2. Type `cmd`
3. Run:

```bat
ngrok update
```

4. Close the old `openminiclaw.bat` window
5. Run `openminiclaw.bat` again

**Note:** If you get `'ngrok' is not recognized` error, it means ngrok is not in your system PATH. Use Method 2 instead.

## Method 2: Manual Download & Install

1. Download ngrok from: https://ngrok.com/download
2. Extract the zip file to a folder (e.g., `C:\ngrok\`)
3. **Important:** Add ngrok to system PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" variable
   - Add the folder path (e.g., `C:\ngrok\`)
4. Close and reopen command prompt
5. Run `openminiclaw.bat` again

## Method 3: Quick Fix (No PATH needed)

If you don't want to modify PATH, you can:
1. Extract ngrok to a known location
2. When `openminiclaw.bat` asks "Installed? Press Y", press Y
3. If it still says "ngrok not found", manually copy `ngrok.exe` to:
   - `C:\Windows\System32\` (requires admin)
   - Or the same folder as `openminiclaw.bat`

---

# ngrok 更新說明

如果 ngrok 版本太舊，或啟動失敗，請這樣做：

## 方法一：使用 ngrok update（推薦）

1. 按 `Win + R`
2. 輸入 `cmd`
3. 執行：

```bat
ngrok update
```

4. 關閉原本的 `openminiclaw.bat` 視窗
5. 再次執行 `openminiclaw.bat`

**注意：** 如果出現 `'ngrok' 不是內部或外部命令` 錯誤，表示 ngrok 沒有在系統 PATH 中。請使用方法二。

## 方法二：手動下載安裝

1. 前往 https://ngrok.com/download 下載 ngrok
2. 解壓縮 zip 到資料夾（例如 `C:\ngrok\`）
3. **重要：** 將 ngrok 加入系統 PATH：
   - 在 Windows 搜尋「環境變數」
   - 編輯「Path」變數
   - 新增資料夾路徑（例如 `C:\ngrok\`）
4. 關閉並重新開啟命令提示字元
5. 再次執行 `openminiclaw.bat`

## 方法三：快速修正（不需要設定 PATH）

如果不想修改 PATH，可以：
1. 解壓縮 ngrok 到任意位置
2. 當 `openminiclaw.bat` 詢問 "Installed? Press Y" 時，按 Y
3. 如果仍然顯示 "ngrok not found"，手動複製 `ngrok.exe` 到：
   - `C:\Windows\System32\`（需要系統管理員權限）
   - 或與 `openminiclaw.bat` 相同的資料夾

---

# ngrok 更新ガイド

ngrok のバージョンが古い、または起動に失敗する場合は、次の手順で更新してください。

1. `Win + R` を押す
2. `cmd` と入力する
3. 次を実行する：

```bat
ngrok update
```

4. 以前の `openminiclaw.bat` ウィンドウを閉じる
5. `openminiclaw.bat` をもう一度実行する

`ngrok update` が失敗した場合は、以下から新しい ngrok をダウンロードしてください。

https://ngrok.com/download
