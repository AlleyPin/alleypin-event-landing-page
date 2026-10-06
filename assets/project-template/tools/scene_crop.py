#!/usr/bin/env python3
"""IP 場景圖（3:2 透明底、角色坐在桌後）→ 網頁用 WebP：底部裁到「最低的不透明像素」＝桌子底緣。

用法：python3 tools/scene_crop.py <原圖.png> <輸出名，例 ip_s3-1.webp>
      輸出到 assets/，寬 600、高依比例；CSS 用固定寬度比例＋bottom:0 貼齊框底，同一組圖桌子就會對齊。
為什麼：原圖的桌子畫在不同高度、底下留白不一，整張塞進框裡就會「浮在空中」（2026-10-05 Hsing 指出第 3、4 段都這樣）。
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(src, name):
    w, h, x, y = (int(v) for v in subprocess.run(
        ["magick", src, "-alpha", "extract", "-threshold", "8%", "-format", "%w %h %X %Y", "-trim", "info:"],
        capture_output=True, text=True, check=True).stdout.split()[:4])
    full_w = int(subprocess.run(["magick", src, "-format", "%w", "info:"], capture_output=True, text=True, check=True).stdout)
    bottom = y + h                                     # 不透明內容的最下緣（桌子底）
    out = ROOT / "assets" / name
    subprocess.run(["magick", src, "-crop", f"{full_w}x{bottom}+0+0", "+repage", "-resize", "600x",
                    "-define", "webp:alpha-quality=92", "-quality", "80", str(out)], check=True)
    ow, oh = subprocess.run(["magick", str(out), "-format", "%w %h", "info:"], capture_output=True, text=True, check=True).stdout.split()
    print(f"{out.name}: 原圖 {full_w}×{bottom}（桌底在第 {bottom} 列）→ {ow}×{oh}；img 屬性寫 width=300 height={round(int(oh) / 2)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
