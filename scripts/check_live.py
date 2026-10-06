#!/usr/bin/env python3
"""上線檢查：抓已發布的 Instapage 頁面原始碼，檢查複製頁最容易漏改的地方。只讀不寫，不會送出表單。

用法：python3 check_live.py <活動頁網址> [--thankyou <感謝頁網址>] [--project <專案資料夾>]
      有 --project 時，會拿 src/seo.json、src/_mock_form.html、out/instapage/*.html 當「應該長這樣」來比對；
      沒有就只列出線上現況。有任何 ❌ 以 exit code 1 結束。

檢查項目（每一項都是 Cofit 案上線時真的發生過的）：
  SEO／社群   title、description、og:title、og:description 是不是這次的（複製頁會帶來源頁的舊標題與 OG）；og:image 是 1200×630
  收錄        有沒有 noindex（events.alleypin.com 預設 noindex；要不要開放由 Hsing 決定，這裡只報現況）
  自訂碼      Head／Body／Footer／報名區塊的程式碼有沒有完整出現在線上（Body 被截斷、貼到舊版都會抓到）
  禁用樣式    scroll-behavior:smooth（Cradle.js 錨點卡住）、text-wrap:pretty／balance
  原生表單    有 lpsSubmissionConfig＝原生表單；有 zapier2-integration＝有接 Zapier（複製頁不會帶 Zapier），並比對 Zapier 欄位對應
  送出後導向  照 route 實際跳轉的落點判斷（url= 參數常是舊值，不可信）
  表單欄位    欄位名稱與順序、必填、下拉選項、勾選文字、送出按鈕文字，跟 _mock_form.html 的規格比對
  UTM         5 個 utm 隱藏欄位都在
  區塊        編輯器區塊數量照 layout.json、沒有複製來源頁留下的文字（只在手機顯示的舊區塊）
  元件位置    報名須知 HTML 元件與表單的桌機／手機位置尺寸照 layout.json
"""
import base64, html, json, re, struct, sys, urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129 Safari/537.36"}
FAILS, WARNS = [], []


def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
        return r.status, r.geturl(), (data if binary else data.decode("utf-8", "replace"))


def norm(s):
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def meta(page, attr, key):
    m = re.search(rf'<meta\s+{attr}="{re.escape(key)}"\s+content="([^"]*)"', page, re.S)
    return norm(m.group(1)) if m else None


def png_size(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":  # JPEG：找 SOF
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1; continue
            marker, length = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", data[i + 5:i + 9]); return w, h
            i += 2 + length
    return None


def ok(msg): print(f"  ✅ {msg}")
def fail(msg): FAILS.append(msg); print(f"  ❌ {msg}")
def warn(msg): WARNS.append(msg); print(f"  ⚠️ {msg}")
def info(msg): print(f"  ℹ️ {msg}")


def check_seo(page, expect):
    title = norm(m.group(1)) if (m := re.search(r"<title>(.*?)</title>", page, re.S)) else None
    got = {"title": title, "description": meta(page, "name", "description"),
           "og:title": meta(page, "property", "og:title"), "og:description": meta(page, "property", "og:description"),
           # X（Twitter）卡片是另一組標籤：2026-10-06 cofit 活動頁的 twitter:description 被設成感謝頁的描述，og 卻是對的
           "twitter:title": meta(page, "name", "twitter:title"), "twitter:description": meta(page, "name", "twitter:description")}
    for k, v in got.items():
        want = None
        if expect:
            want = norm(expect["title" if "title" in k else "description"])
        if v is None:
            (warn if k.startswith("twitter:") else fail)(f"{k} 沒有設定")
        elif want and v != want:
            fail(f"{k} 跟 seo.json 不同：線上「{v[:60]}」／應為「{want[:60]}」（複製頁帶來的舊值？）")
        elif want:
            ok(f"{k} 正確")
        else:
            info(f"{k}：{v[:80]}")
    img = meta(page, "property", "og:image")
    if not img:
        fail("og:image（社群縮圖）沒有設定")
    else:
        try:
            st, _, data = get(img if img.startswith("http") else "https:" + img, binary=True)
            size = png_size(data)
            if size == (1200, 630):
                ok(f"og:image 1200×630（{img.rsplit('/', 1)[-1]}）")
            else:
                warn(f"og:image 尺寸 {size}，應為 1200×630（{img}）")
        except Exception as e:
            fail(f"og:image 打不開：{img}（{e}）")
    robots = re.search(r'<meta\s+name="robots"\s+content="([^"]*)"', page)
    info(f"收錄設定：{robots.group(1) if robots else '沒有 robots meta（可被搜尋引擎收錄）'}（要不要收錄由 Hsing 決定）")


def check_code(page, snippets):
    flat = norm(page)
    # 禁用樣式只看真正生效的碼：模板註解裡會寫「不要加 xxx」，不能算違規
    code = re.sub(r"/\*.*?\*/|<!--.*?-->", "", page, flags=re.S)
    if re.search(r"scroll-behavior\s*:\s*smooth", code):
        fail("頁面有 scroll-behavior:smooth：Instapage 錨點捲動會卡住（Head 是舊版？）")
    else:
        ok("沒有 CSS 平滑捲動")
    if re.search(r"text-wrap\s*:\s*(pretty|balance)", code):
        fail("頁面有 text-wrap:pretty／balance（內文會提早換行、標題不齊寬）")
    for name, code in snippets.items():
        c = norm(code)
        if c in flat:
            ok(f"{name} 完整出現在線上（{len(code.encode()) // 1000}KB）")
            continue
        lines = [norm(l) for l in code.splitlines() if norm(l)]
        missing = [l for l in lines if l not in flat]
        tail_ok = c[-300:] in flat   # 結尾 300 字（只看最後幾行會被 </div> 這種到處都有的行騙過）
        if len(missing) == len(lines):
            fail(f"{name} 不在線上 → 沒貼、或貼錯欄位")
            continue
        sample = "；".join(("Google Fonts 字型子集（改過文案）" if "fonts.googleapis.com" in l else l[:50]) for l in missing[:3])
        if tail_ok:
            # 結尾在、只缺中間幾行＝線上是較舊的版本。是否影響這一頁要看缺的是什麼（例：只缺感謝頁用的樣式就不影響活動頁）
            warn(f"{name} 線上是舊版：缺 {len(missing)}/{len(lines)} 行（{sample}）→ 看缺的內容會不會影響這一頁，會的話重貼 out/instapage/{name}")
        else:
            fail(f"{name} 結尾對不上、缺 {len(missing)}/{len(lines)} 行 → 可能被截斷（{sample}）")


def check_blocks(page, expected_blocks, own_texts):
    """編輯器區塊（<main> 裡的 section#page-block-*）：數量要跟 layout.json 一樣，而且不能有我們以外的文字。
    2026-10-06 cofit 感謝頁：複製 nova 感謝頁後留下一個區塊，裡面是 Nova「裕利醫藥」刷卡回饋文案——桌機隱藏、手機顯示，
    桌機編輯器裡看不到，所以要在手機檢視也刪。"""
    i, j = page.find("<main"), page.find("</main>")
    if i < 0:
        return
    main = page[i:j]
    secs = list(re.finditer(r'<section[^>]*id="(page-block-[^"]+)"', main))
    own = norm(" ".join(own_texts))
    leftovers = []
    for k, m in enumerate(secs):
        body = main[m.start(): secs[k + 1].start() if k + 1 < len(secs) else len(main)]
        body = re.sub(r"<(script|style|textarea|select)[^>]*>.*?</\1>", " ", body, flags=re.S)
        body = re.sub(r"<form.*?</form>", " ", body, flags=re.S)       # 原生表單另外檢查
        text = norm(re.sub(r"<[^>]+>", " ", body))
        extra = " ".join(w for w in text.split(" ") if w and w not in own)
        if extra:
            leftovers.append((m.group(1), extra))
    if len(secs) != expected_blocks:
        (fail if len(secs) > expected_blocks else warn)(f"編輯器區塊有 {len(secs)} 個，layout.json 是 {expected_blocks} 個（多的可能是複製來源頁留下、只在手機顯示的區塊）")
    for sid, extra in leftovers:
        fail(f"區塊 {sid} 有不是這次程式碼的文字：「{extra[:80]}」→ 複製來源頁留下的內容，桌機與手機檢視都要檢查、刪掉")
    if len(secs) == expected_blocks and not leftovers:
        ok(f"編輯器區塊 {len(secs)} 個，沒有殘留的來源頁內容")


def check_positions(page, block, snippet):
    """報名區塊兩個元件（HTML 元件、原生表單）在線上的位置尺寸，跟 layout.json 比（編輯器 px，1px 容差）。
    2026-10-06 cofit 活動頁：HTML 元件桌機在 left 52／top 47／寬 360（規格 0／0／380），「報名須知」比上面各段右偏 52px。"""
    css = "".join(re.findall(r"<style[^>]*>(.*?)</style>", page, re.S))
    def box(eid):
        rules = [r for r in re.findall(r"#" + eid + r"\s*\{([^}]*)\}", css) if "left" in r and "top" in r]
        out = []
        for r in rules[:1] + rules[-1:]:   # Instapage 先寫手機、再在 media query 裡寫桌機
            v = {k: float(m.group(1)) * (16 if m.group(2) == "rem" else 1)
                 for k in ("left", "top", "width", "height") if (m := re.search(rf"(?<![-\w]){k}:\s*([\d.]+)(rem|px)", r))}
            out.append(v)
        return out
    anchor = norm(re.sub(r"<[^>]+>", " ", snippet))[:30] if snippet else None
    ids = {}
    if snippet:
        root = re.search(r'id="([\w-]+)"', snippet)
        k = page.find(f'id="{root.group(1)}"') if root else -1
        if k > 0:
            ids["html"] = re.findall(r'id="(element-\d+)"', page[:k])[-1]
    fk = page.find("<form")
    if fk > 0:
        ids["form"] = re.findall(r'id="(element-\d+)"', page[:fk])[-1]
    for e in block["elements"]:
        eid = ids.get(e["type"])
        if not eid:
            continue
        got = box(eid)
        if len(got) < 2:
            continue
        for label, want, have in (("手機", e["mobile"], got[0]), ("桌機", e["desktop"], got[1])):
            want = dict(zip(("left", "top", "width", "height"), want))
            diff = {k: (round(have.get(k, -1)), v) for k, v in want.items() if abs(have.get(k, -1) - v) > 1}
            if diff:
                fail(f"{e['name']}（{eid}）{label}位置尺寸跟 layout.json 不同：" + "、".join(f"{k} 線上 {a}／規格 {b}" for k, (a, b) in diff.items()) + "（照上稿指南第五節重設）")
            else:
                ok(f"{e['name']}{label}位置尺寸正確")


def live_form(page):
    m = re.search(r"<form[^>]*email-form.*?</form>", page, re.S)
    if not m:
        return None
    f = m.group(0)
    fields, hidden = [], {}
    for tag in re.finditer(r"<(input|select|textarea)\b([^>]*)>", f, re.S):
        a = tag.group(2)
        name = html.unescape(m2.group(1)) if (m2 := re.search(r'\bname="([^"]*)"', a)) else ""
        typ = m3.group(1) if (m3 := re.search(r'\btype="([^"]*)"', a)) else tag.group(1)
        if typ == "hidden":
            hidden[name] = html.unescape(m4.group(1)) if (m4 := re.search(r'\bvalue="([^"]*)"', a)) else ""
            continue
        req = bool(re.search(r"(^|\s)required(\s|=|$)", a))
        opts = []
        if tag.group(1) == "select":
            body = f[tag.end(): f.find("</select>", tag.end())]
            opts = [html.unescape(o) for o in re.findall(r'<option[^>]*value="([^"]+)"', body)]
        fields.append({"label": name, "type": typ, "required": req, "options": opts})
    for k in list(hidden):
        if "::INSTAPAGE_BOX::" in k:   # 勾選框的勾選文字藏在隱藏欄位名稱裡
            label, box = k.split("::INSTAPAGE_BOX::", 1)
            for fl in fields:
                if fl["label"] == label:
                    fl["options"] = [box]
    btn = re.search(r"<button[^>]*form-btn[^>]*>(.*?)</button>", f, re.S)
    return {"fields": fields, "hidden": hidden, "button": norm(re.sub(r"<[^>]+>", "", btn.group(1))) if btn else None, "raw": f}


def spec_form(proj):
    """表單規格直接從 src/_mock_form.html 讀（跟 build.py 的 form_fields 同一套解析），不依賴 out/，舊專案也能比。"""
    p = proj / "src" / "_mock_form.html"
    if not p.exists():
        return [], None
    mock = p.read_text(encoding="utf-8")
    spec = []
    for m in re.finditer(r'<label[^>]*class="form-label-title[^"]*"[^>]*for="([^"]+)"[^>]*>(.*?)</label>', mock, re.S):
        fid, label = m.group(1), norm(re.sub(r"<[^>]+>", "", m.group(2)))
        el = re.search(rf'<(input|select)[^>]*id="{fid}"[^>]*>', mock)
        if not el:
            continue
        tag = el.group(0)
        if el.group(1) == "select":
            body = re.search(rf'id="{fid}".*?</select>', mock, re.S).group(0)
            opts = [html.unescape(o) for o in re.findall(r'class="form-select-option" value="([^"]+)"', body)]
        else:
            t = re.search(r'type="([^"]+)"', tag).group(1)
            opts = [html.unescape(v) for v in re.findall(r'value="([^"]+)"', tag)] if t == "checkbox" else []
        spec.append({"label": label, "required": " required" in tag, "options": opts})
    btn = re.search(r"<button[^>]*form-btn[^>]*>(.*?)</button>", mock, re.S)
    return spec, norm(btn.group(1)) if btn else None


def check_form(page, url, proj, thankyou):
    lf = live_form(page)
    if not lf:
        fail("找不到 Instapage 原生表單（form.email-form）"); return
    if "lpsSubmissionConfig" in lf["hidden"]:
        ok("原生表單（有 Instapage 簽章 lpsSubmissionConfig）")
    else:
        fail("表單沒有 lpsSubmissionConfig：不是原生表單，名單進不了 Leads、不觸發 Zapier")
    z = lf["hidden"].get("zapier2-integration")
    labels = [f["label"] for f in lf["fields"]]
    if not z:
        fail("沒有接 Zapier（zapier2-integration 不在表單裡）：複製頁不會帶 Zapier，要到表單 Integrations 重新接")
    else:
        try:
            cfg = json.loads(base64.b64decode(z + "=" * (-len(z) % 4)))
            for i, acc in enumerate(cfg.get("accounts", []), 1):
                mapped = [fm.get("instapage") for fm in acc.get("fieldmap", [])]
                missing = [l for l in labels if l not in mapped]
                (warn if missing else ok)(f"Zapier 第 {i} 組：對應 {len(mapped)} 欄" + (f"；表單有、Zapier 沒對應：{missing}" if missing else ""))
        except Exception:
            ok("有接 Zapier（欄位對應解不開，請到後台看）")
    red = lf["hidden"].get("redirect")
    if not red:
        warn("表單沒有設送出後導向（會停在原頁顯示感謝訊息）")
    else:
        try:
            _, final, _ = get(red)
        except Exception as e:
            final = f"（跟轉失敗：{e}）"
        info(f"送出後導向：{red}")
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        if thankyou:
            (ok if final.rstrip("/") == thankyou.rstrip("/") else fail)(f"送出後實際落點：{final}" + ("" if final.rstrip("/") == thankyou.rstrip("/") else f"（應為 {thankyou}）"))
        elif slug not in final:
            warn(f"送出後實際落點 {final} 看起來不是這檔活動的感謝頁（網址不含「{slug}」）")
        else:
            ok(f"送出後實際落點：{final}")
    utm = [k for k in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term") if k not in lf["hidden"]]
    (warn(f"少了 UTM 隱藏欄位：{utm}") if utm else ok("5 個 UTM 隱藏欄位都在"))
    if not proj:
        for f in lf["fields"]:
            info(f"欄位：{f['label']}｜{f['type']}｜{'必填' if f['required'] else '選填'}" + (f"｜{'／'.join(f['options'])}" if f["options"] else ""))
        info(f"送出按鈕：{lf['button']}")
        return
    spec, btn = spec_form(proj)
    if not spec:
        warn("專案沒有 src/_mock_form.html，跳過欄位比對"); return
    want = [s["label"] for s in spec]
    if labels == want:
        ok(f"欄位名稱與順序一致（{len(want)} 欄）")
    else:
        for i in range(max(len(labels), len(want))):
            a = labels[i] if i < len(labels) else "（無）"
            b = want[i] if i < len(want) else "（無）"
            if a != b:
                fail(f"第 {i + 1} 欄：線上「{a}」／規格「{b}」")
    by = {f["label"]: f for f in lf["fields"]}
    for s in spec:
        f = by.get(s["label"])
        if not f:
            continue
        if f["required"] != s["required"]:
            fail(f"「{s['label']}」必填設定不同：線上{'必填' if f['required'] else '選填'}／規格{'必填' if s['required'] else '選填'}")
        if s["options"] and f["options"] != s["options"]:
            fail(f"「{s['label'][:20]}」選項不同：線上 {f['options']}／規格 {s['options']}")
    if btn and lf["button"] != btn:
        fail(f"送出按鈕文字：線上「{lf['button']}」／規格「{btn}」")
    elif btn:
        ok(f"送出按鈕文字「{btn}」")


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__); sys.exit(2)
    url = args[0] if args[0].startswith("http") else "https://" + args[0]
    opt = lambda k: next((args[i + 1] for i, a in enumerate(args) if a == k and i + 1 < len(args)), None)
    ty = opt("--thankyou")
    ty = ty if not ty or ty.startswith("http") else "https://" + ty
    proj = Path(opt("--project")).expanduser().resolve() if opt("--project") else None
    seo = json.loads((proj / "src" / "seo.json").read_text(encoding="utf-8")) if proj else None
    snip = lambda n: (proj / "out" / "instapage" / n).read_text(encoding="utf-8") if proj and (proj / "out" / "instapage" / n).exists() else None

    print(f"== 活動頁 {url}")
    st, final, page = get(url)
    (ok if st == 200 else fail)(f"HTTP {st}")
    check_seo(page, seo["campaign"] if seo else None)
    check_code(page, {n: s for n in ("1_head.html", "2_body.html", "3_signup-block.html", "4_footer.html") if (s := snip(n))})
    check_form(page, url, proj, ty)
    if proj:
        lay = json.loads((proj / "src" / "layout.json").read_text(encoding="utf-8"))
        n = {p["id"]: len(p["blocks"]) for p in lay["pages"]}
        check_blocks(page, n.get("campaign", 1), [re.sub(r"<[^>]+>", " ", s) for s in [snip("3_signup-block.html") or ""]])
        camp = next((p for p in lay["pages"] if p["id"] == "campaign"), None)
        if camp and camp["blocks"]:
            check_positions(page, camp["blocks"][0], snip("3_signup-block.html"))

    if ty:
        print(f"\n== 感謝頁 {ty}")
        st, _, tpage = get(ty)
        (ok if st == 200 else fail)(f"HTTP {st}")
        check_seo(tpage, seo["thankyou"] if seo else None)
        check_code(tpage, {n: s for n in ("1_head.html", "ty_2_body.html", "4_footer.html") if (s := snip(n))})
        if proj:
            check_blocks(tpage, n.get("thankyou", 0), [])

    print(f"\n合計：❌ {len(FAILS)}　⚠️ {len(WARNS)}")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
