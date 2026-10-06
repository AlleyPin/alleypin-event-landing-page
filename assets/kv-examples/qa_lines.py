#!/usr/bin/env python3
"""KV 白線線頭驗收：白線過了打勾徽章之後，終點有沒有接在右下藍色圓柱的邊線上。

用法：python3 tools/qa_lines.py 圖1.png [圖2.png ...]
做法：在打勾徽章右側（x 1095–1330、y 600–790）找白線像素，沿著白線往右下追到最遠的那一點＝線頭；
      再看線頭「前方」幾 px 的顏色：是圓柱藍（#5A92D2）＝接上；是墨綠（#144E4F）或透明＝停在半空中。
      另外檢查圓柱藍色範圍裡有沒有白線（線畫到圓柱上面＝層次錯）。
      每張圖輸出一張線頭放大圖（*-lineend.png，放在同資料夾的 _qa/）給人看。
第六輪 kv-r6-1 的線頭停在圓柱內部，這支腳本應該判「沒接上」（鑑別力檢查用）。

第二項（第八輪加）：山豆白袍下緣。在 x 340–480 逐欄往下找白袍（淺色）最後一段，看它下面接的是什麼：
      接深藍主圓柱（#1D4A82）＝白袍平切浮在半空中；接前排墨綠圓柱（#144E4F）＝被前景擋住，正確。
      第七輪三張都應該判「浮空」（鑑別力檢查用）。
"""
import math, subprocess, sys
from pathlib import Path

PILLAR, INK, NAVY = (0x5A, 0x92, 0xD2), (0x14, 0x4E, 0x4F), (0x1D, 0x4A, 0x82)
X0, Y0, X1, Y1 = 1095, 600, 1330, 790


def load(path):
    w, h = map(int, subprocess.run(["magick", path, "-format", "%w %h", "info:"], capture_output=True, text=True, check=True).stdout.split())
    buf = subprocess.run(["magick", path, "-depth", "8", "rgba:-"], capture_output=True, check=True).stdout
    return w, h, buf


def main(path):
    w, h, buf = load(path)
    px = lambda x, y: tuple(buf[(y*w+x)*4:(y*w+x)*4+4])
    def kind(x, y):
        r, g, b, a = px(x, y)
        if a < 128: return "T"
        if min(r, g, b) > 225: return "W"
        if math.dist((r, g, b), PILLAR) < 45: return "P"
        if math.dist((r, g, b), INK) < 45: return "I"
        return "O"
    white = {(x, y) for y in range(Y0, Y1) for x in range(X0, X1) if kind(x, y) == "W"}
    if not white:
        print(f"== {Path(path).name}: 徽章右側找不到白線"); return
    # 從最靠近徽章（最左）的白點開始，取相連的那一條
    start = min(white)
    seen, stack = {start}, [start]
    while stack:
        x, y = stack.pop()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (x+dx, y+dy)
                if q in white and q not in seen:
                    seen.add(q); stack.append(q)
    end = max(seen, key=lambda p: p[0] + p[1])           # 往右下最遠的點＝線頭
    # 線的走向：線頭附近 25px 內白點的平均方向
    near = [p for p in seen if math.dist(p, end) < 25]
    cx = sum(p[0] for p in near) / len(near); cy = sum(p[1] for p in near) / len(near)
    dx, dy = end[0] - cx, end[1] - cy; n = math.hypot(dx, dy) or 1; dx, dy = dx/n, dy/n
    ahead = [kind(int(round(end[0] + dx*k)), int(round(end[1] + dy*k))) for k in range(2, 9)]
    on_pillar = sum(1 for p in seen if all(kind(p[0]+ox, p[1]+oy) in "PW" for ox, oy in ((0, 6), (0, -6), (6, 0), (-6, 0))))
    ok = ahead.count("P") >= 5 and on_pillar < 15
    verdict = "接上圓柱邊線 ✅" if ok else "沒接上 ❌"
    print(f"== {Path(path).name}：白線線頭 {end}，線頭前方 2–8px：{''.join(ahead)}（P＝圓柱藍、I＝墨綠、T＝透明）"
          f"；疊在圓柱上的白點 {on_pillar} → {verdict}")
    qa = Path(path).parent / "_qa"; qa.mkdir(exist_ok=True)
    out = qa / (Path(path).stem + "-lineend.png")
    subprocess.run(["magick", path, "-background", "white", "-alpha", "remove", "-alpha", "off",
                    "-crop", f"240x160+{end[0]-150}+{end[1]-100}", "+repage", "-filter", "point", "-resize", "300%",
                    "-fill", "none", "-stroke", "#FF2D55", "-strokewidth", "3",
                    "-draw", f"circle 450,300 470,300", str(out)], check=True)
    hem(path, w, buf)
    return ok


def hem(path, w, buf):
    px = lambda x, y: buf[(y*w+x)*4:(y*w+x)*4+3]
    light = lambda c: min(c) > 200
    dark = lambda c: max(c) < 60
    float_cols, ok_cols = [], []
    for x in range(340, 481, 2):
        bottom = None
        for y in range(450, 900):
            if light(px(x, y)) and not light(px(x, y+1)):
                run = sum(1 for k in range(0, 20) if light(px(x, y-k)))
                if run >= 15: bottom = y
        if bottom is None: continue
        y = bottom + 1
        while y < bottom + 8 and dark(px(x, y)): y += 1   # 跳過黑色描邊
        c = px(x, y + 3)
        if math.dist(c, NAVY) < 45: float_cols.append(x)
        elif math.dist(c, INK) < 45: ok_cols.append(x)
    n = len(float_cols) + len(ok_cols)
    verdict = "白袍下緣被前景圓柱擋住 ✅" if n and len(float_cols) <= 3 else "白袍下緣浮在深藍圓柱中間 ❌"
    print(f"   山豆白袍下緣（x 340–480 共 {n} 欄）：接深藍 {len(float_cols)} 欄、接前排墨綠 {len(ok_cols)} 欄 → {verdict}")


if __name__ == "__main__":
    for a in sys.argv[1:]:
        main(a)
