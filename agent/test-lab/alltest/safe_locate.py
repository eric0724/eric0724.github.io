"""
safe_locate.py — 防崩潰圖案比對共用模組
提供 safe_locate(template, opt, log) 介面
- 找不到時自動重試 3 次（半徑 1.5x/2x、原點上下左右微調）
- 內建 FAILSAFE 角落保護（避免 (0,0) 觸發崩潰）
- 3 次全失敗回傳 (-1, None, None)
"""
import pyautogui
import cv2
import numpy as np
import time

# 預設備援信心值（呼叫端可覆寫）
DEFAULT_CONFIDENCE = 0.75
RETRY_ROUNDS = 3
FAILSAFE_CORNER_MARGIN = 5  # 距離螢幕邊緣幾像素內視為危險

def _is_safe_coord(x, y, sw, sh):
    """檢查座標是否會觸發 pyautogui FAILSAFE（螢幕角落）"""
    if x is None or y is None:
        return False
    return not (
        x < FAILSAFE_CORNER_MARGIN or
        y < FAILSAFE_CORNER_MARGIN or
        x > sw - FAILSAFE_CORNER_MARGIN or
        y > sh - FAILSAFE_CORNER_MARGIN
    )

def _match_template(src, tpl, x1, y1):
    """單次 cv2 matchTemplate，回傳 (信心值, 中心 x, 中心 y)"""
    if src.shape[0] < tpl.shape[0] or src.shape[1] < tpl.shape[1]:
        return 0.0, None, None
    res = cv2.matchTemplate(src, tpl, cv2.TM_CCOEFF_NORMED)
    _, mv, _, ml = cv2.minMaxLoc(res)
    th2, tw2 = tpl.shape[:2]
    return mv, x1 + ml[0] + tw2 // 2, y1 + ml[1] + th2 // 2

def _scale_fallback(src, tpl, x1, y1, w, h, log):
    """原始比對信心不足時，縮放比對備援"""
    NORM = 64
    tpl_n = cv2.resize(tpl, (NORM, NORM))
    th, tw = tpl.shape[:2]
    best_val, best_cx, best_cy = 0.0, None, None
    step_px = max(4, min(tw, th) // 4)
    for scale in [1.0, 0.85, 1.15, 0.7, 1.3]:
        sw2, sh2 = int(tw * scale), int(th * scale)
        if sw2 > w or sh2 > h:
            continue
        for wy in range(0, h - sh2, step_px):
            for wx in range(0, w - sw2, step_px):
                crop = src[wy:wy + sh2, wx:wx + sw2]
                crop_n = cv2.resize(crop, (NORM, NORM))
                res = cv2.matchTemplate(crop_n, tpl_n, cv2.TM_CCOEFF_NORMED)
                _, mv, _, _ = cv2.minMaxLoc(res)
                if mv > best_val:
                    best_val = mv
                    best_cx = x1 + wx + sw2 // 2
                    best_cy = y1 + wy + sh2 // 2
    log(f"  縮放備援：{best_val:.2f}")
    return best_val, best_cx, best_cy

def _try_one_round(template, origin, radius, confidence, log, round_idx):
    """單輪搜尋：截圖 + 原始比對 + 縮放備援"""
    sw = pyautogui.size().width
    sh = pyautogui.size().height
    r = radius
    x1 = max(0, origin[0] - r)
    y1 = max(0, origin[1] - r)
    x2 = min(sw, origin[0] + r)
    y2 = min(sh, origin[1] + r)
    w, h = x2 - x1, y2 - y1
    if w <= 0 or h <= 0:
        log(f"  第 {round_idx} 輪：範圍無效")
        return -1, None, None

    region_img = pyautogui.screenshot(region=(x1, y1, w, h))
    tpl = cv2.imread(template)
    if tpl is None:
        log(f"  第 {round_idx} 輪：找不到範本 {template}")
        return -1, None, None
    src = cv2.cvtColor(np.array(region_img), cv2.COLOR_RGB2BGR)

    val, cx, cy = _match_template(src, tpl, x1, y1)
    log(f"  第 {round_idx} 輪 原始：{val:.2f} @ ({cx},{cy}) 半徑={r}")
    if val >= confidence and _is_safe_coord(cx, cy, sw, sh):
        return val, cx, cy

    # 縮放備援
    sval, scx, scy = _scale_fallback(src, tpl, x1, y1, w, h, log)
    if sval >= confidence * 0.85 and _is_safe_coord(scx, scy, sw, sh):
        return sval, scx, scy
    return -1, None, None

def safe_locate(template, opt=None, log=None):
    """
    防崩潰圖案比對。
    template: 範本圖片路徑
    opt: dict，可含 origin (x,y)、radius、mode ('full'|'nearby')、confidence
    log: 輸出函式，預設 print
    回傳: (val, cx, cy) — 失敗回傳 (-1, None, None)
    """
    if log is None:
        log = print
    opt = opt or {}
    origin = opt.get("origin")
    radius = opt.get("radius", 200)
    mode   = opt.get("mode", "nearby")
    confidence = opt.get("confidence", DEFAULT_CONFIDENCE)

    # mode=full 或無原點 → 用整個螢幕
    if mode == "full" or origin is None:
        sw = pyautogui.size().width
        sh = pyautogui.size().height
        origin = (sw // 2, sh // 2)
        radius = max(sw, sh)

    # 3 輪重試：原半徑 → 1.5x 右上 +30,-30 → 2.0x 右下 -30,+30
    rounds = [
        (radius, 0, 0),
        (int(radius * 1.5), 30, -30),
        (int(radius * 2.0), -30, 30),
    ]
    for i, (r, dx, dy) in enumerate(rounds, 1):
        ox = origin[0] + dx
        oy = origin[1] + dy
        val, cx, cy = _try_one_round(template, (ox, oy), r, confidence, log, i)
        if val >= confidence * 0.85 and cx is not None:
            log(f"  ✅ 第 {i} 輪成功 ({cx},{cy}) 信心 {val:.2f}")
            return val, cx, cy
        time.sleep(0.2)  # 兩輪間短暫停

    log("  ❌ 3 輪全失敗，請調低信心值或重新錄製範本")
    return -1, None, None
