#!/usr/bin/env python3
"""舊版場景圖的櫃子沒有畫底邊（兩側直線畫到底直接截掉）→ 用同一組線寬、線色、圓角補上底邊。

用法：python3 tools/close_desk.py <原圖.png> <輸出.png>
數字是量 assets/ip-scenes/s3-1.png 得到的（2026-10-06）：左右邊線外緣 x 45／1490、線寬 5px、
上方圓角外緣半徑約 47px、櫃子最下緣在第 926 列、填色約 (208,229,245)。換別張圖要重量。
為什麼：第 4 段三張並排時，只有這張（舊圖）的櫃子沒有黑色底線，Hsing 指出不統一。
"""
import subprocess, sys

LEFT, RIGHT, BOTTOM = 47, 1488, 923.5      # 線條中心線（外緣 45／1490、下緣 926，線寬 5）
R = 44.5                                   # 中心線半徑（外緣 47 − 線寬一半）
TOP = 872                                  # 從這一列以下重畫（以上維持原圖）
FILL, STROKE, WIDTH = "rgb(208,229,245)", "rgb(8,8,8)", 5


def main(src, dst):
    shape = (f"M {LEFT},{TOP} L {LEFT},{BOTTOM - R} A {R},{R} 0 0 0 {LEFT + R},{BOTTOM} "
             f"L {RIGHT - R},{BOTTOM} A {R},{R} 0 0 0 {RIGHT},{BOTTOM - R} L {RIGHT},{TOP}")
    subprocess.run([
        "magick", src,
        # 1) 把要重畫的那一段清成透明
        "-region", f"1536x{1024 - TOP}+0+{TOP}", "-alpha", "set", "-channel", "A", "-evaluate", "set", "0", "+channel", "+region",
        # 2) 填櫃子底色（封閉形狀、不描邊）
        "-fill", FILL, "-stroke", "none", "-draw", f"path '{shape} Z'",
        # 3) 描兩側與底邊（開放路徑、不填色）
        "-fill", "none", "-stroke", STROKE, "-strokewidth", str(WIDTH), "-draw", f"path '{shape}'",
        dst], check=True)
    print(dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
