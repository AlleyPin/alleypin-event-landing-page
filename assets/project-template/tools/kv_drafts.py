#!/usr/bin/env python3
"""KV 主視覺設計稿：把 assets/kv-drafts/kv-*.png 套進真實 KV 版型，截桌機／手機，拼成一張比較板。

用法：python3 tools/kv_drafts.py [方向設定 json] [輸出檔名]
      預設 assets/kv-drafts/directions.json → out/KV設計稿.html
      方向設定裡 "svg": true 的，會先用 tools/vectorize.py 轉成 SVG，設計稿直接用 SVG（＝上線的樣子）
"""
import base64, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402

DRAFTS = ROOT / "assets" / "kv-drafts"
WORK = ROOT / "out" / "_drafts"
FONTS = f'<link href="https://fonts.googleapis.com/css2?{build.SITE["fonts"]}&display=swap" rel="stylesheet">'


def b64(p, mime):
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def render(key, illus):
    WORK.mkdir(parents=True, exist_ok=True)
    tpl = (build.SRC / "_kv-draft-mock.html").read_text(encoding="utf-8")
    page = build.inline_images(tpl.replace("{{FONTS}}", FONTS).replace("{{ILLUS}}", illus.resolve().as_uri())
                               .replace("/*{{SHARED}}*/", build.css_text()))
    mock = WORK / f"mock-{key}.html"
    mock.write_text(page, encoding="utf-8")
    desk = WORK / f"{key}-desktop.png"
    build.chrome(["--window-size=1440,640", f"--screenshot={desk}", mock.as_uri()])
    wrap = WORK / f"wrap-{key}.html"
    wrap.write_text(f'<!doctype html><body style="margin:0"><iframe src="{mock.name}" '
                    'style="display:block;width:390px;height:780px;border:0"></iframe></body>', encoding="utf-8")
    mob = WORK / f"{key}-mobile.png"
    build.chrome(["--window-size=600,780", "--force-device-scale-factor=2", f"--screenshot={mob}", wrap.as_uri()])
    subprocess.run(["magick", str(mob), "-crop", "780x1560+0+0", "+repage", str(mob)], check=True)
    out = {}
    raw = illus if illus.suffix == ".png" else WORK / f"{key}-svgraster.png"
    if illus.suffix == ".svg":
        view = WORK / f"svgview-{key}.html"
        view.write_text(f'<!doctype html><body style="margin:0;background:#fff"><img src="{illus.name}" style="width:700px;height:700px;display:block"></body>', encoding="utf-8")
        build.chrome(["--window-size=700,700", f"--screenshot={raw}", view.as_uri()])
    for name, p, w in (("desktop", desk, "1440x"), ("mobile", mob, "390x"), ("illus", raw, "700x")):
        jpg = WORK / f"{key}-{name}.jpg"
        subprocess.run(["magick", str(p), "-resize", w, "-quality", "84", str(jpg)], check=True)
        out[name] = b64(jpg, "image/jpeg")
    return out


def main():
    cfg = Path(sys.argv[1]) if len(sys.argv) > 1 else DRAFTS / "directions.json"
    meta = json.loads(cfg.read_text(encoding="utf-8"))
    cards = []
    for d in meta["directions"]:
        illus = DRAFTS / d["file"]
        if not illus.exists():
            continue
        svg_note = ""
        if d.get("svg"):
            svg = WORK / f"{d['key']}.svg"
            r = subprocess.run([str(ROOT / "tools/.venv/bin/python"), str(ROOT / "tools/vectorize.py"), str(illus), str(svg)],
                               check=True, capture_output=True, text=True)
            svg_note = f'<p class="svgnote">已轉 SVG：{r.stdout.strip().split(": ", 1)[-1]}（以下畫面用的就是 SVG）</p>'
            illus = svg
        shots = render(d["key"], illus)
        cards.append(f'''
<section class="dir">
  <header><span class="tag">方向 {d["key"]}</span><h2>{d["name"]}</h2></header>
  <p class="idea">{d["idea"]}</p>{svg_note}
  <ul class="notes">{"".join(f"<li>{n}</li>" for n in d["notes"])}</ul>
  <div class="row">
    <figure class="desk"><img src="{shots["desktop"]}" alt=""><figcaption>桌機 KV（1440 寬）</figcaption></figure>
    <figure class="mob"><img src="{shots["mobile"]}" alt=""><figcaption>手機 KV</figcaption></figure>
  </div>
  <details><summary>看插圖本體</summary><img class="raw" src="{shots["illus"]}" alt=""></details>
</section>''')
    html = f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>KV 設計稿</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{{ --ink:#144E4F; --text:#2A3B3B; --muted:#5F6F6D; --line:#DCE8E5; }}
*{{ box-sizing:border-box; }}
body{{ margin:0; background:#F4F8F7; color:var(--text); font:15px/1.75 "Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif; }}
main{{ max-width:1180px; margin:0 auto; padding:40px 20px 80px; }}
h1{{ margin:0; font-size:28px; color:var(--ink); }}
.lead{{ color:var(--muted); margin:6px 0 0; }}
.dir{{ margin-top:36px; padding:24px; background:#fff; border:1px solid var(--line); border-radius:18px; }}
.dir header{{ display:flex; align-items:center; gap:12px; }}
.dir h2{{ margin:0; font-size:21px; color:var(--ink); }}
.tag{{ padding:2px 12px; border-radius:999px; background:var(--ink); color:#fff; font-weight:700; font-size:13px; }}
.idea{{ margin:10px 0 4px; }} .svgnote{{ margin:0 0 4px; font-size:13px; color:#2F7D6A; }}
.notes{{ margin:0 0 14px; padding-left:20px; color:var(--muted); font-size:14px; }}
.row{{ display:grid; grid-template-columns:1fr 220px; gap:16px; align-items:start; }}
figure{{ margin:0; }} figure img{{ width:100%; display:block; border:1px solid var(--line); border-radius:10px; }}
figcaption{{ font-size:13px; color:var(--muted); margin-top:4px; }}
details{{ margin-top:12px; }} summary{{ cursor:pointer; color:var(--ink); font-weight:700; font-size:14px; }}
.raw{{ margin-top:10px; width:360px; max-width:100%; border:1px solid var(--line); border-radius:10px; }}
@media (max-width:720px){{ .row{{ grid-template-columns:1fr; }} .mob{{ max-width:240px; }} }}
</style></head><body><main>
<h1>{meta.get("title", "KV 主視覺設計稿")}</h1>
<p class="lead">{meta["intro"]}</p>
{"".join(cards)}
</main></body></html>'''
    dest = ROOT / "out" / (sys.argv[2] if len(sys.argv) > 2 else "KV設計稿.html")
    dest.write_text(html, encoding="utf-8")
    print(dest)


if __name__ == "__main__":
    main()
