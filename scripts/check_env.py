#!/usr/bin/env python3
"""開工前的環境檢查：這台電腦能不能跑這個 skill 的腳本。缺什麼就印出怎麼裝。

用法：python3 check_env.py
必要：Python 3.8+、Google Chrome（量頁面、截圖、OG 圖）。
做截圖與社群圖才需要：ImageMagick（magick 指令）。
選用：網路（Google Fonts）、Codex（產 KV／角色插圖）、alleypin-pinfriends 與 frontend-design 兩個 skill。
"""
import os, shutil, subprocess, sys, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qa_page import find_chrome  # noqa: E402

MAC = sys.platform == "darwin"
rows = []


def add(ok, name, msg):
    rows.append((ok, name, msg))


add(sys.version_info >= (3, 8), "Python", f"{sys.version.split()[0]}" + ("" if sys.version_info >= (3, 8) else "（要 3.8 以上）"))
c = find_chrome()
add(bool(c), "Google Chrome", c or ("沒找到 → 到 https://www.google.com/chrome/ 下載安裝；裝在別的位置就設環境變數 CHROME_PATH"))
m = shutil.which("magick")
add(bool(m), "ImageMagick（截圖、OG 圖、場景圖裁切）", m or ("沒找到 → " + ("brew install imagemagick" if MAC else "到 https://imagemagick.org 下載") + "；沒有它只能產程式碼與預覽，不能出截圖和社群圖"))
try:
    urllib.request.urlopen("https://fonts.googleapis.com/css2?family=Noto+Sans+TC&text=AB", timeout=8)
    add(True, "網路／Google Fonts", "連得到")
except Exception as e:
    add(False, "網路／Google Fonts", f"連不到（{e.__class__.__name__}）→ 字型會退回系統字，孤字與對齊的量測可能跟線上不同")
cx = shutil.which("codex")
add(None if not cx else True, "Codex（選用：產 KV、PinFriends 插圖）", cx or "沒有 → KV 先用幾何插圖或佔位圖，角色插圖請有 Codex 的人產")
skills = Path.home() / ".claude" / "skills"
for s, why in (("alleypin-pinfriends", "畫 PinFriends 角色"), ("frontend-design", "定視覺方向")):
    ok = (skills / s).exists()
    add(True if ok else None, f"skill：{s}（選用：{why}）", "已安裝" if ok else "沒裝 → 不影響做頁面；要用時跟 Hsing 拿")

for ok, name, msg in rows:
    mark = "✅" if ok else ("➖" if ok is None else "❌")
    print(f"{mark} {name}：{msg}")
need = [n for ok, n, _ in rows if ok is False and (n.startswith("Python") or n.startswith("Google Chrome"))]
print("\n" + ("可以開工。" if not need else f"先處理 ❌ 的必要項目：{'、'.join(need)}"))
sys.exit(1 if need else 0)
