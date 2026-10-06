#!/usr/bin/env python3
"""產生 KV 的「幾何版面參考圖」：沿用 A-a 的構圖，所有形狀都是數學上的正圓、正半圓頂圓柱。
給 Codex 當參考圖用（角色不畫進來，用文字描述位置）。

用法：python3 tools/kv_geomref.py [輪次資料夾，預設 r7] → assets/kv-drafts/<輪次>/geometry-ref.svg / .png（1536×1024，白底）

第七輪（2026-10-05）：白線改畫在前排圓柱「後面」，終點被右下藍色圓柱（x 1080–1300、頂 660）的圓頂邊線切齊。
第六輪的白線終點 (1230,700) 畫在所有形狀上面、停在圓柱內部半空中，Codex 照抄 → 被 Hsing 退件。
規則：每條線的頭尾都要落在徽章或形狀邊線上，不准停在空中。
第八輪：山豆腰部那裡沒有任何前景形狀（前排墨綠圓柱頂在 780），Codex 只好把白袍下襬平切、浮在藍柱中間。
→ 前排墨綠圓柱（x 260–500）頂端從 780 拉高到 600，山豆的下半身改成藏在它和淺藍圓柱後面。用法：python3 tools/kv_geomref.py r8
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "kv-drafts" / (sys.argv[1] if len(sys.argv) > 1 else "r7")
W, H = 1536, 1024


def pillar(x, w, top, fill, bottom=H):
    """圓角拉到底的圓柱：頂端是直徑＝寬度的正半圓，往下直到 bottom。"""
    r = w / 2
    return f'<path d="M{x} {bottom}V{top + r}A{r} {r} 0 0 1 {x + w} {top + r}V{bottom}Z" fill="{fill}"/>'


def leaf(x1, y1, x2, y2, r, fill):
    return f'<path d="M{x1} {y1}A{r} {r} 0 0 1 {x2} {y2}A{r} {r} 0 0 1 {x1} {y1}Z" fill="{fill}"/>'


def badge(cx, cy, icon):
    ic = {"chat": f'<path d="M{cx-15} {cy-11}h30a6 6 0 0 1 6 6v14a6 6 0 0 1-6 6h-14l-10 8v-8h-6a6 6 0 0 1-6-6v-14a6 6 0 0 1 6-6z" fill="#49AE86"/>',
          "check": f'<path d="M{cx-14} {cy+1}l9 9 19-19" fill="none" stroke="#49AE86" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'}[icon]
    return (f'<circle cx="{cx}" cy="{cy}" r="36" fill="#FFFFFF" stroke="#A9DFC6" stroke-width="5"/>' + ic)


MAIN_X, MAIN_W, MAIN_TOP = 207, 663, 97          # A-a 量到的主圓柱
CX, CY, R = 1059, 471, 313                        # A-a 量到的墨綠圓（改成正圓）


def svg():
    main_path = f"M{MAIN_X} {H}V{MAIN_TOP + MAIN_W / 2}A{MAIN_W / 2} {MAIN_W / 2} 0 0 1 {MAIN_X + MAIN_W} {MAIN_TOP + MAIN_W / 2}V{H}Z"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<rect width="{W}" height="{H}" fill="#FFFFFF"/>
<defs><clipPath id="main"><path d="{main_path}"/></clipPath></defs>
<!-- 後排 -->
{pillar(110, 170, 420, "#DDF0E7")}
{pillar(50, 350, 600, "#5A92D2")}
{pillar(1180, 220, 660, "#DCE7F4")}
<!-- 主圓柱與墨綠正圓、交集 -->
<path d="{main_path}" fill="#1D4A82"/>
<circle cx="{CX}" cy="{CY}" r="{R}" fill="#144E4F"/>
<circle cx="{CX}" cy="{CY}" r="{R}" fill="#A9DFC6" clip-path="url(#main)"/>
<!-- 軌跡線與徽章：畫在前排圓柱之前，終點 (1230,700) 藏在右下藍色圓柱後面，看得到的線頭被圓頂邊線切齊（約在 1192,660） -->
<path d="M524 624C640 624 700 540 800 560S960 640 1054 624C1140 610 1190 650 1230 700" fill="none" stroke="#FFFFFF" stroke-width="7" stroke-linecap="round"/>
{badge(524, 624, "chat")}
{badge(1054, 624, "check")}
<!-- 前排 -->
{pillar(510, 190, 660, "#DCE7F4")}
{pillar(260, 240, 600 if OUT.name >= "r8" else 780, "#144E4F")}
{pillar(880, 160, 720, "#DDF0E7")}
{pillar(920, 80, 790, "#A9DFC6")}
{pillar(1080, 220, 660, "#5A92D2")}
{pillar(1130, 240, 830, "#144E4F")}
{leaf(40, 900, 150, 760, 120, "#49AE86")}
{leaf(90, 1000, 220, 880, 120, "#49AE86")}
{leaf(1350, 760, 1440, 600, 110, "#49AE86")}
{leaf(1380, 880, 1490, 740, 110, "#49AE86")}
{leaf(1420, 990, 1510, 860, 100, "#144E4F")}
</svg>'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "geometry-ref.svg").write_text(svg(), encoding="utf-8")
    html = OUT / "_geom.html"
    html.write_text('<!doctype html><body style="margin:0"><img src="geometry-ref.svg" style="display:block;width:1536px;height:1024px"></body>', encoding="utf-8")
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    subprocess.run([chrome, "--headless=new", "--use-mock-keychain", "--disable-gpu", "--hide-scrollbars", "--timeout=6000", "--window-size=1536,1024",
                    f"--screenshot={OUT / 'geometry-ref.png'}", html.as_uri()], check=True, capture_output=True, timeout=90)
    html.unlink()
    print(OUT / "geometry-ref.png")


if __name__ == "__main__":
    main()
