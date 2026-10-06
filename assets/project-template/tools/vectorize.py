#!/usr/bin/env python3
"""把 Codex 產的平塗插圖轉成乾淨的 SVG。

步驟：1) 顏色收斂到品牌色票（去掉反鋸齒雜色）2) 去背 3) vtracer 描邊 4) 移除白底路徑
用法：tools/.venv/bin/python tools/vectorize.py assets/kv-drafts/kv-B-t.png assets/kv-art.svg
"""
import re, subprocess, sys, tempfile
from pathlib import Path

import vtracer

PALETTE = ["#144E4F", "#1D4A82", "#5A92D2", "#DCE7F4", "#49AE86", "#A9DFC6", "#DDF0E7", "#FFFFFF",
           "#F2D3BE", "#2B3A3A"]


def run(*args):
    subprocess.run(["magick", *map(str, args)], check=True)


def vectorize(src, dst, size=1024):
    src, dst = Path(src), Path(dst)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        pal = td / "palette.png"
        run(*[f"xc:{c}" for c in PALETTE], "+append", pal)
        flat = td / "flat.png"
        # 縮到工作尺寸 → 顏色收斂到色票（不抖色）→ 透明度二值化，邊緣乾淨
        run(src, "-resize", f"{size}x{size}", "(", "+clone", "-alpha", "extract", "-threshold", "50%", ")",
            "(", "-clone", "0", "-alpha", "off", "-dither", "None", "-remap", pal, ")",
            "-delete", "0", "+swap", "-compose", "CopyOpacity", "-composite", flat)
        # 注意：vtracer 0.6.15 在 Python 3.14 帶任何數字參數都會 segfault，所以只用預設值；
        # 顏色已先收斂到色票，預設值就夠乾淨
        vtracer.convert_image_to_svg_py(str(flat), str(dst))
    svg = dst.read_text()
    # 去掉 XML 宣告與產生器註解：要內嵌進 HTML，用不到
    svg = re.sub(r"<\?xml[^>]*\?>\s*|<!--.*?-->\s*", "", svg, flags=re.S)
    # 拿掉 vtracer 寫進去的 width/height，改成可縮放；保留 viewBox
    svg = re.sub(r'<svg([^>]*?)width="(\d+)" height="(\d+)"', r'<svg\1viewBox="0 0 \2 \3"', svg, count=1)
    # vtracer 的顏色會飄一點（#49AD86 vs #49AE86），校正回最近的品牌色
    def snap(m):
        c = tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4))
        best = min(PALETTE, key=lambda h: sum((int(h[1 + i * 2:3 + i * 2], 16) - c[i]) ** 2 for i in range(3)))
        return f'fill="{best}"'
    svg = re.sub(r'fill="#([0-9A-Fa-f]{6})"', snap, svg)
    # 座標四捨五入到小數 1 位，檔案小很多、肉眼看不出差別
    # 座標取整數：viewBox 約 1100 單位、畫面顯示約 500px，誤差 < 0.25px 肉眼看不出，檔案小約三成
    def compact(m):
        d = re.sub(r"-?\d+(?:\.\d+)?", lambda n: str(round(float(n.group()))), m.group(1))
        d = re.sub(r"\s*([A-Za-z])\s*", r"\1", d)  # 只在路徑資料裡：指令字母前後的空白不需要
        return f'd="{d}"'
    svg = re.sub(r'd="([^"]+)"', compact, svg)
    dst.write_text(svg)
    paths = svg.count("<path")
    print(f"{dst.name}: {dst.stat().st_size / 1024:.0f} KB, {paths} paths")


if __name__ == "__main__":
    vectorize(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 1024)
