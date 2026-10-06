#!/usr/bin/env python3
"""第 3、4 段 IP 插圖新舊對照板：舊圖（assets/ip-scenes/*.png）vs 新圖（assets/ip-scenes/<輪次>/*.png）。

用法：python3 tools/scene_board.py <輪次資料夾，例 r2> <notes.json> → out/IP插圖-對照.html
notes.json：{"intro": "...", "notes": {"s2-clinic": ["..."], ...}}
"""
import base64, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCENES = ROOT / "assets" / "ip-scenes"
NAMES = [("s2-clinic", "第 3 段｜診間"), ("s2-daily", "第 3 段｜日常"),
         ("s3-1", "第 4 段｜1 病人諮詢"), ("s3-2", "第 4 段｜2 團隊討論新服務"), ("s3-3", "第 4 段｜3 輕鬆規劃")]


def jpg(png):
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "a.jpg"
        subprocess.run(["magick", str(png), "-background", "white", "-alpha", "remove", "-alpha", "off",
                        "-resize", "720x", "-quality", "82", str(out)], check=True)
        return "data:image/jpeg;base64," + base64.b64encode(out.read_bytes()).decode()


def main():
    rnd = sys.argv[1]
    meta = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    rows = []
    for key, label in NAMES:
        old, new = SCENES / f"{key}.png", SCENES / rnd / f"{key}.png"
        if not new.exists():
            continue
        notes = "".join(f"<li>{n}</li>" for n in meta["notes"].get(key, []))
        rows.append(f'''<section class="row"><h2>{label}</h2><ul>{notes}</ul>
<div class="pair"><figure><img src="{jpg(old)}" alt=""><figcaption>舊（15:15，skill 建立前）</figcaption></figure>
<figure><img src="{jpg(new)}" alt=""><figcaption>新</figcaption></figure></div></section>''')
    html = f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>IP 插圖新舊對照｜AlleyPin × Cofit</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{{ --ink:#144E4F; --text:#2A3B3B; --muted:#5F6F6D; --line:#DCE8E5; }}
*{{ box-sizing:border-box; }}
body{{ margin:0; background:#F4F8F7; color:var(--text); font:15px/1.75 "Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif; }}
main{{ max-width:1180px; margin:0 auto; padding:40px 16px 80px; }}
h1{{ margin:0; font-size:28px; color:var(--ink); }} .lead{{ color:var(--muted); margin:6px 0 0; }}
.row{{ margin-top:28px; padding:22px; background:#fff; border:1px solid var(--line); border-radius:18px; }}
.row h2{{ margin:0; font-size:20px; color:var(--ink); }} ul{{ margin:6px 0 12px; padding-left:20px; color:var(--muted); font-size:14px; }}
.pair{{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
figure{{ margin:0; }} img{{ width:100%; display:block; border:1px solid var(--line); border-radius:10px; }}
figcaption{{ font-size:13px; color:var(--muted); margin-top:4px; }}
@media (max-width:720px){{ .pair{{ grid-template-columns:1fr; }} }}
</style></head><body><main>
<h1>第 3、4 段 IP 插圖｜新舊對照</h1><p class="lead">{meta["intro"]}</p>
{"".join(rows)}
</main></body></html>'''
    dest = ROOT / "out" / "IP插圖-對照.html"
    dest.write_text(html, encoding="utf-8")
    print(dest)


if __name__ == "__main__":
    main()
