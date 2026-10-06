#!/usr/bin/env python3
"""AlleyPin 活動頁（events.alleypin.com，Instapage）：產生上稿片段、本機模擬預覽、上稿指南、OG／社群圖。

頁面結構（2026-10-05 拆 nova-webinar 上線原始碼實證，Cofit 案上線驗證）：
  頁面設定 HTML/CSS → Head   ＝ 1_head.html（字型＋全部樣式，活動頁、感謝頁共用）
  頁面設定 HTML/CSS → Body   ＝ 2_body.html（表單前的所有段落；Instapage 把它插在 <body> 開頭、所有區塊之前）
  編輯器裡唯一的區塊         ＝ 報名須知（HTML 元件，3_signup-block.html）＋原生表單（後台手動建，接 Zapier）
  頁面設定 HTML/CSS → Footer ＝ 4_footer.html（插在所有區塊之後）

用法：python3 build.py            產生片段、預覽、指南
      python3 build.py --shots    另外重截預期畫面＋輸出 OG／社群圖（PNG＋向量 PDF）
      python3 build.py --strict   有「〔待填」佔位字就以錯誤結束（交件前用）
改內容請改 src/ 底下的檔案，不要直接改 out/（會被覆蓋）。
每一檔活動的設定（class 前綴、CSS 檔順序、字型、指南用的活動名稱）在 src/site.json。
"""
import base64, html, json, re, shutil, string, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC, ASSETS, OUT = ROOT / "src", ROOT / "assets", ROOT / "out"
SNIP = OUT / "instapage"
MIME = {".png": "image/png", ".webp": "image/webp", ".svg": "image/svg+xml", ".jpg": "image/jpeg"}
PLACEHOLDER = "〔待填"
SITE = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
P = SITE.get("prefix", "ap")   # class 前綴：避開 Instapage 內建 class（.hidden、.clearfix、.item-* 等）


def find_chrome():
    """找 Chrome／Chromium：先看環境變數 CHROME_PATH，再找 macOS、Linux、Windows 的常見位置。"""
    import os, shutil
    for c in (os.environ.get("CHROME_PATH"),
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium",
              shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chromium-browser"), shutil.which("chrome"),
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"):
        if c and os.path.exists(c):
            return c
    return None


CHROME = find_chrome()


def read(name):
    return (SRC / name).read_text(encoding="utf-8")


def css_text():
    return "\n".join(read(n) for n in SITE["css"])


def fonts_link(texts):
    """Google Fonts 只打包頁面實際用到的字（text= 子集）：三個字重約 400KB，不切的話上限約 3.8MB。
    改了任何文案重跑 build 就會重新計算；不在子集裡的字（例如表單使用者輸入）會退回系統字型。
    CSS 裡 content:"…" 的字（例如表單標題「免費報名」）也要算進來，不然會掉回系統字。"""
    import urllib.parse
    chars = set(string.printable.strip()) | set(SITE.get("extra_chars", "")) | set("×｜：；，。、！？（）「」—–")
    for t in texts:
        t = re.sub(r"<svg.*?</svg>|data:[^\"')]+|\{\{[^}]+\}\}", "", t, flags=re.S)
        chars |= set(html.unescape(re.sub(r"<[^>]+>", " ", t)))
    for s in re.findall(r'"([^"\\]*)"', re.sub(r"/\*.*?\*/", "", css_text(), flags=re.S)):
        if any(ord(c) > 0x2E80 for c in s):
            chars |= set(s)
    q = urllib.parse.quote("".join(sorted(c for c in chars if not c.isspace())))
    return ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            f'<link href="https://fonts.googleapis.com/css2?{SITE["fonts"]}&display=swap&text={q}" rel="stylesheet">')


def inline_images(text):
    """{{include:檔名}} 插入 src 片段；{{img:檔名}} 轉成 base64（圖不用上傳 Instapage）；{{svg:檔名}} 直接內嵌 SVG。
    HTML 註解（給自己看的說明、註解掉的備用寫法）一律拿掉：不貼進 Instapage，也不算進字型子集。"""
    text = re.sub(r"\{\{include:([^}]+)\}\}", lambda m: read(m.group(1)), text)
    text = re.sub(r"<!--.*?-->\n?", "", text, flags=re.S)
    text = re.sub(r"\{\{svg:([^}]+)\}\}", lambda m: (ASSETS / m.group(1)).read_text(encoding="utf-8").strip().replace(
        "<svg ", f'<svg class="{P}-kv__illus" aria-hidden="true" focusable="false" ', 1), text)
    def repl(m):
        p = ASSETS / m.group(1)
        return f"data:{MIME[p.suffix]};base64," + base64.b64encode(p.read_bytes()).decode()
    return re.sub(r"\{\{img:([^}]+)\}\}", repl, text)


def rem(px):
    return f"{px / 16:g}rem"


def html_elements(page):
    for b in page["blocks"]:
        for e in b["elements"]:
            if e["type"] == "html":
                yield b, e


def layout_css(page):
    """模擬 Instapage 的區塊與元件定位：手機為預設、桌機寫在 min-width:768px。"""
    mob, desk = [], []
    for b in page["blocks"]:
        sel = f"#page-block-{b['id']}"
        mob.append(f"{sel},{sel} .section-block{{height:{rem(b['mobile_h'])};}}{sel} .section-block{{background:{b['bg']};}}")
        desk.append(f"{sel},{sel} .section-block{{height:{rem(b['desktop_h'])};}}")
        for e in b["elements"]:
            eid = "element-form" if e["type"] == "form" else f"element-{e['id']}"
            x, y, w, h = e["mobile"]
            mob.append(f"#{eid}{{left:{rem(x)};top:{rem(y)};width:{rem(w)};height:{rem(h)};z-index:{70 if e['type'] == 'form' else 10};}}")
            x, y, w, h = e["desktop"]
            desk.append(f"#{eid}{{left:{rem(x)};top:{rem(y)};width:{rem(w)};height:{rem(h)};}}")
    return "\n".join(mob) + "\n@media screen and (min-width:768px){\n" + "\n".join(desk) + "\n}"


def element_heights_css(pages):
    """HTML 元件外層 .contents 沒有高度（height:100% 會失效），所以把元件高度寫進 CSS（跟編輯器裡設定的同一組數字）。"""
    mob, desk = [], []
    for page in pages:
        for _, e in html_elements(page):
            mob.append(f".{e['root']}{{height:{rem(e['mobile'][3])};}}")
            desk.append(f".{e['root']}{{height:{rem(e['desktop'][3])};}}")
    if not mob:
        return ""
    return ("/* ---- 元件高度：由 src/layout.json 產生，請勿手改 ---- */\n"
            "@media (min-width:768px){ " + " ".join(desk) + " }\n"
            "@media (max-width:767px){ " + " ".join(mob) + " }\n")


def flow(src):
    """Body／Footer 段落：根元素加 -flow（置中內容欄、高度由內容撐開），圖片內嵌。"""
    text = inline_images(read(src))
    return re.sub(rf'class="{P} ', f'class="{P} {P}-flow ', text, count=1)


def page_snippets(page):
    """回傳這頁要貼的片段：{檔名: 內容}（Head 另外處理，兩頁共用）。"""
    pre = "ty_" if page["id"] == "thankyou" else ""
    out = {}
    if page["body"]:
        out[f"{pre}2_body.html"] = "\n".join(flow(s) for s in page["body"])
    for _, e in html_elements(page):
        out[e["snippet"]] = inline_images(read(e["src"]))
    if page["footer"]:
        out["4_footer.html"] = "\n".join(flow(s) for s in page["footer"])   # 頁尾兩頁共用
    return out


def preview_html(page, head_snip, snips):
    """照 Instapage 上線頁的真實順序組：<body> → 自訂 BODY 碼 → <main>（編輯器建的區塊）→ 自訂 FOOTER 碼。"""
    base = read("_instapage_base_from_nova.css").replace("element-312", "element-form")
    mock_form = read("_mock_form.html")
    pre = "ty_" if page["id"] == "thankyou" else ""
    sections = []
    for b in page["blocks"]:
        widgets = []
        for e in b["elements"]:
            if e["type"] == "html":
                widgets.append(f'<div class="widget item-absolute" id="element-{e["id"]}" data-at="html">'
                               f'<div class="contents">{snips[e["snippet"]]}</div></div>')
            else:
                widgets.append(f'<div class="widget item-absolute" id="element-form">{mock_form}</div>')
        sections.append(
            f'<section class="section section-relative" id="page-block-{b["id"]}" data-at="section">'
            '<div class="section-holder-border item-block item-absolute"></div>'
            '<div class="section-holder-overlay item-block item-absolute"></div>'
            '<div class="section-block"><div class="section-inner section-fit section-relative">'
            + "".join(widgets) + "</div></div></section>")
    script = ""
    if any(e["type"] == "form" for b in page["blocks"] for e in b["elements"]):
        script = """<script>
/* 模擬 Instapage：下拉選完才顯示文字、送出時標示未填欄位 */
document.querySelectorAll('.form-select').forEach(function(s){s.addEventListener('change',function(){s.setAttribute('aria-invalid','false');});});
document.querySelector('form.email-form').addEventListener('submit',function(ev){ev.preventDefault();
  this.querySelectorAll('[required]').forEach(function(f){var bad=f.type==='checkbox'?!f.checked:!f.value;f.classList.toggle('user-invalid',bad);});});
</script>"""
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[本機預覽] {page['name']}</title>
<!-- 1) Instapage 實際的基礎 CSS（拆自 events.alleypin.com/nova-webinar），含 :root 字級縮放與原生表單樣式 -->
<style>{base}</style>
<!-- 2) 模擬 Instapage 編輯器裡設定的區塊高度與元件位置（數字來自 src/layout.json） -->
<style>{layout_css(page)}</style>
<!-- 3) 自訂 HEAD 碼 -->
{head_snip}
</head>
<body id="landing-page">
<!-- custom BODY code-->
{snips.get(pre + "2_body.html", "")}
<!-- end custom BODY code-->
<main>
{"".join(sections)}
</main>
<!-- custom FOOTER code-->
{snips.get("4_footer.html", "")}
<!-- end custom FOOTER code-->
{script}
</body></html>"""


def upload_kit():
    """out/上傳用/：Instapage 頁面設定要用的東西放同一個資料夾——兩頁的 OG 圖＋可直接複製的 SEO 文字（來源 src/seo.json）。"""
    kit = OUT / "上傳用"; kit.mkdir(parents=True, exist_ok=True)
    og = OUT / "images" / "og-1200x630.png"
    if og.exists():
        for name in ("活動頁_OG_1200x630.png", "感謝頁_OG_1200x630.png"):
            shutil.copyfile(og, kit / name)
    seo = json.loads(read("seo.json"))
    lines = ["Instapage 頁面設定（右側 Page Settings）要填的內容", "社群縮圖：活動頁、感謝頁都上傳同一張 OG 圖（本資料夾內）", ""]
    for key, label in (("campaign", "活動頁"), ("thankyou", "感謝頁")):
        lines += [f"【{label}】", "頁面標題（Title）：", seo[key]["title"], "", "頁面描述（Description）：", seo[key]["description"], ""]
    (kit / "SEO與社群設定.txt").write_text("\n".join(lines), encoding="utf-8")


def form_fields():
    """從 src/_mock_form.html（＝這次表單的規格）讀出欄位表：給上稿指南與 check_live.py 用。"""
    mock = read("_mock_form.html")
    rows = []
    for m in re.finditer(r'<label[^>]*class="form-label-title[^"]*"[^>]*for="([^"]+)"[^>]*>(.*?)</label>', mock, re.S):
        fid, label = m.group(1), html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        el = re.search(rf'<(input|select)[^>]*id="{fid}"[^>]*>', mock)
        if not el:
            continue
        tag = el.group(0)
        if el.group(1) == "select":
            kind = "Dropdown"
            body = re.search(rf'id="{fid}".*?</select>', mock, re.S).group(0)
            opts = [html.unescape(o) for o in re.findall(r'class="form-select-option" value="([^"]+)"', body)]
        else:
            t = re.search(r'type="([^"]+)"', tag).group(1)
            kind = {"email": "Email", "checkbox": "Checkbox"}.get(t, "Text")
            opts = [html.unescape(v) for v in re.findall(r'value="([^"]+)"', tag)] if t == "checkbox" else []
        rows.append({"label": label, "type": kind, "required": " required" in tag, "options": opts})
    return rows


def build():
    data = json.loads(read("layout.json"))
    pages = data["pages"]
    per_page = {page["id"]: page_snippets(page) for page in pages}
    bodies = {k: v for snips in per_page.values() for k, v in snips.items()}
    font_texts = list(bodies.values()) + [read("_mock_form.html")]
    head_snip = f"{fonts_link(font_texts)}\n<style>\n{css_text()}\n{element_heights_css(pages)}</style>\n"
    snippets = {"1_head.html": head_snip, **bodies}

    shutil.rmtree(SNIP, ignore_errors=True)  # 清掉舊檔名，避免貼到過期片段
    for name, body in snippets.items():
        path = SNIP / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    for page in pages:
        (OUT / page["preview"]).write_text(preview_html(page, head_snip, per_page[page["id"]]), encoding="utf-8")

    (OUT / "上稿指南.html").write_text(guide(pages, snippets), encoding="utf-8")
    (OUT / "form_spec.json").write_text(json.dumps(form_fields(), ensure_ascii=False, indent=1), encoding="utf-8")
    upload_kit()
    for n, s in snippets.items():
        print(f"{n:30s} {len(s.encode()):>7,} bytes")
    print("預覽與上稿指南已更新")
    return snippets


def placeholder_report(snippets):
    """佔位字守門：「〔待填」出現在任何要貼上的片段、SEO 或表單規格裡都列出來。回傳筆數。"""
    hits = []
    for name, s in list(snippets.items()) + [("seo.json", read("seo.json")), ("_mock_form.html", read("_mock_form.html")),
                                              ("site.json", read("site.json"))] + [(n, read(n)) for n in ("guide_notes.html",) if (SRC / n).exists()]:
        text = re.sub(r"<[^>]+>", " ", s) if name.endswith(".html") else s
        for m in re.finditer(re.escape(PLACEHOLDER) + r"[^〕]*〕?", text):
            hits.append(f"  {name}: {m.group(0)}")
    for name, s in snippets.items():   # 段落庫的範例段落（Cofit 文案）要改成這次的內容，改完把 data-example 拿掉
        for ex in sorted(set(re.findall(r'data-example="([^"]+)"', s))):
            hits.append(f"  {name}: 還有沒改寫的範例段落（data-example=\"{ex}\"）→ 換成這次的文案後刪掉 data-example")
    hits = list(dict.fromkeys(hits))
    if hits:
        print(f"\n⚠️ 還有 {len(hits)} 種佔位字沒填（上線前一定要清掉）：")
        print("\n".join(hits))
    return len(hits)


def guide(pages, snippets):
    def box(v):
        x, y, w, h = v
        return f"X {x}・Y {y}・寬 {w}・高 {h}"
    sections = {}
    for page in pages:
        rows = []
        for b in page["blocks"]:
            rows.append(f'<tr class="blk"><th colspan="3">{b["name"]}</th></tr>'
                        f'<tr><td>區塊設定</td><td>背景色 <code>{b["bg"]}</code>・高 {b["desktop_h"]}</td>'
                        f'<td>高 {b["mobile_h"]}</td></tr>')
            for e in b["elements"]:
                label = e["name"] + (f'<br><span class="muted">貼 <code>{e["snippet"]}</code></span>' if e["type"] == "html" else "")
                rows.append(f'<tr><td>{label}</td><td>{box(e["desktop"])}</td><td>{box(e["mobile"])}</td></tr>')
        sections[page["id"]] = "\n".join(rows)
    where = {"1_head.html": "活動頁、感謝頁都貼：右側 Page Settings → HTML/CSS → Head",
             "2_body.html": "活動頁：右側 Page Settings → HTML/CSS → Body",
             "4_footer.html": "活動頁、感謝頁都貼：右側 Page Settings → HTML/CSS → Footer",
             "ty_2_body.html": "感謝頁：右側 Page Settings → HTML/CSS → Body（KV＋更多 AlleyPin 資訊）"}
    for page in pages:
        for b, e in html_elements(page):
            where[e["snippet"]] = f'{page["short"]}：{b["name"]}的 HTML 元件（左側欄拖進來）→ Edit'
    copy_blocks = []
    for n, s in snippets.items():
        copy_blocks.append(
            f'<div class="snip"><div class="snip__head"><div><b>{n}</b><span>{where.get(n, "")}</span></div>'
            f'<button type="button" data-copy="{n}">複製</button></div>'
            f'<textarea id="{n}" readonly spellcheck="false">{html.escape(s)}</textarea></div>')
    field_rows = []
    for i, f in enumerate(form_fields(), 1):
        req = "是" if f["required"] else "<b>否</b>"
        field_rows.append(f'<tr><td>{i}</td><td>{html.escape(f["label"])}</td><td>{f["type"]}</td><td>{req}</td>'
                          f'<td>{"／".join(html.escape(o) for o in f["options"])}</td></tr>')
    names = []   # Body 段落清單（驗收清單用）：KV＋各段第一個 h2；沒有 h2 的段落用檔名
    for src in next(p for p in pages if p["id"] == "campaign")["body"]:
        text = re.sub(rf'<span class="{P}-no">.*?</span>', "", re.sub(r"<!--.*?-->", "", read(src), flags=re.S))
        m = re.search(r"<h([12])[^>]*>(.*?)</h\1>", text, re.S)
        if m:
            names.append("KV" if m.group(1) == "1" else html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip())
        else:
            names.append(Path(src).stem)
    out = read("guide_template.html")
    out = re.sub(r"\{\{include:([^}]+)\}\}", lambda m: read(m.group(1)), out)
    out = out.replace("{{BODY_LIST}}", f"{'、'.join(html.escape(n) for n in names)} 共 {len(names)} 段")
    for pid, rows in sections.items():
        out = out.replace("{{LAYOUT_ROWS:%s}}" % pid, rows)
    out = out.replace("{{SNIPPETS}}", "\n".join(copy_blocks)).replace("{{FORM_ROWS}}", "\n".join(field_rows))
    for key, val in SITE.get("guide", {}).items():
        out = out.replace("{{%s}}" % key, html.escape(val))
    seo = json.loads(read("seo.json"))
    for key in re.findall(r"\{\{SEO:([a-z]+)\.([a-z]+)\}\}", out):
        out = out.replace("{{SEO:%s.%s}}" % key, html.escape(seo[key[0]][key[1]]))
    for key in re.findall(r"\{\{SIZE:([^}]+)\}\}", out):
        out = out.replace("{{SIZE:%s}}" % key, f"{len(snippets.get(key, '').encode()) / 1000:.0f}KB")
    for key in re.findall(r"\{\{SHOT:([^}]+)\}\}", out):
        p = OUT / "_shots" / key
        out = out.replace("{{SHOT:%s}}" % key, "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode() if p.exists() else "")
    return out


def chrome(args, pdf=False):
    """截圖用 virtual-time 等字型與動畫跑完；PDF 用一般逾時（virtual-time 搭配 --print-to-pdf 會卡死）。
    無頭 Chrome 偶爾會卡死或失敗：重試一次。逾時時 subprocess 會砍掉自己開的那個 Chrome，不用 pkill（會誤殺別的工作開的 Chrome）。
    --use-mock-keychain：不碰 macOS 鑰匙圈。2026-10-06 在換過 HOME 的環境啟動 Chrome，系統一直跳「找不到鑰匙圈」視窗。
    不要加 --user-data-dir：實測截圖寫完後 Chrome 不會結束，每次都卡到逾時。"""
    if not CHROME:
        sys.exit("找不到 Google Chrome：截圖與 OG 圖需要它。裝好 Chrome，或用環境變數 CHROME_PATH 指到執行檔。")
    base = [CHROME, "--headless=new", "--use-mock-keychain", "--disable-gpu", "--hide-scrollbars"]
    timing = ["--timeout=8000"] if pdf else ["--virtual-time-budget=6000"]
    try:
        subprocess.run([*base, *timing, *args], check=True, capture_output=True, timeout=60)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        subprocess.run([*base, "--timeout=8000", "--run-all-compositor-stages-before-draw", *args],
                       check=True, capture_output=True, timeout=90)


def render_shots():
    """預期畫面（放進上稿指南）＋ OG／社群圖。"""
    data = json.loads(read("layout.json"))
    shots = OUT / "_shots"; shots.mkdir(parents=True, exist_ok=True)
    # Body／Footer 段落高度由內容決定，事先不知道整頁多高：先用夠高的視窗截，再把底部空白裁掉。
    # 手機截圖用 1.5 倍解析度，Chrome 截圖高度上限約 16,000px → 手機高度不要超過約 10,600。
    tall = SITE.get("shot_heights", {})
    for page in data["pages"]:
        dh, mh = tall.get(page["id"], (6000, 9000))
        url = (OUT / page["preview"]).resolve().as_uri()
        trim = ["-background", "white", "-define", "trim:edges=south", "-trim", "+repage"]
        png = shots / f"{page['id']}-desktop.png"
        chrome([f"--window-size=1440,{dh}", f"--screenshot={png}", url])
        subprocess.run(["magick", str(png), *trim, str(png)], check=True)
        subprocess.run(["magick", str(png), "-resize", "1200x", "-quality", "82", str(shots / f"{page['id']}-desktop.jpg")], check=True)
        # 手機：無頭 Chrome 視窗有最小寬度（約 500px），設 390 會被撐寬，所以用固定 390 寬的 iframe 包一層再截
        wrap = OUT / "_mobile_wrap.html"
        wrap.write_text(f'<!doctype html><body style="margin:0;background:#fff"><iframe src="{page["preview"]}" '
                        f'style="display:block;width:390px;height:{mh}px;border:0"></iframe></body>', encoding="utf-8")
        png = shots / f"{page['id']}-mobile.png"
        chrome([f"--window-size=600,{mh}", "--force-device-scale-factor=1.5", f"--screenshot={png}", wrap.resolve().as_uri()])
        subprocess.run(["magick", str(png), "-crop", f"585x{round(mh * 1.5)}+0+0", "+repage", *trim, str(png)], check=True)
        subprocess.run(["magick", str(png), "-quality", "82", str(shots / f"{page['id']}-mobile.jpg")], check=True)
        wrap.unlink()
    # 社群圖：PNG 給上架用、PDF（向量）給設計師開 Illustrator 存 .ai（產不出原生 .ai）
    img = OUT / "images"; img.mkdir(exist_ok=True)
    for name, w, h in (("og-1200x630", 1200, 630), ("social-1200x1200", 1200, 1200)):
        src = SRC / f"{name}.html"
        if not src.exists():
            continue
        tmp = OUT / f"_{name}.html"
        tmp.write_text(inline_images(src.read_text(encoding="utf-8")).replace("/*{{SHARED}}*/", css_text()), encoding="utf-8")
        chrome([f"--window-size={w},{h}", f"--screenshot={img / (name + '.png')}", tmp.resolve().as_uri()])
        chrome(["--no-pdf-header-footer", f"--print-to-pdf={img / (name + '.pdf')}", tmp.resolve().as_uri()], pdf=True)
        subprocess.run(["magick", str(img / (name + ".png")), "-resize", "900x", "-quality", "82",
                        str(shots / (name.split("-")[0] + ".jpg"))], check=True)
        tmp.unlink()


if __name__ == "__main__":
    snips = build()
    if "--shots" in sys.argv:
        render_shots()
        snips = build()  # 把新截圖嵌進上稿指南
    n = placeholder_report(snips)
    if n and "--strict" in sys.argv:
        sys.exit(1)
