#!/usr/bin/env python3
"""從 skill 的專案模板開一個新的活動頁專案。

用法：python3 new_project.py <代號> --date <活動日 YYYY-MM-DD> [--name "活動名稱"] [--root <上層資料夾>]
      沒給 --root：有 ~/Desktop/AlleyPin/ 就放 ~/Desktop/AlleyPin/landing page/，沒有就要求指定。
例：  python3 new_project.py nova-webinar-2 --date 2026-12-08 --name "AlleyPin Nova 線上說明會"
      → ~/Desktop/AlleyPin/landing page/2026-12-nova-webinar-2/

會建立：build.py、src/（平台層 platform.css、設計層 design.css、各段落骨架、表單規格、上稿指南模板）、
assets/（AlleyPin logo、KV 佔位圖、library/ 段落庫圖片）、src/_library/（Cofit 上線頁的段落範例）、
tools/（scene_crop.py 等）、_ref/（放票上參考圖與合作方素材）、交接.md。
資料夾已存在就停下來，不覆蓋。
"""
import datetime, json, shutil, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL / "assets" / "project-template"
DEFAULT_ROOT = Path.home() / "Desktop" / "AlleyPin" / "landing page"

HANDOFF = """# 交接：{name}

更新：{today}（Asia/Taipei，用 `date` 查過再改這行）

## 任務是什麼
- Notion 票：〔待填：行銷設計開票中心的票網址〕
- 活動：{date}〔待填：時間、形式、受眾〕
- 交件：Instapage 活動頁＋感謝頁、社群圖 1200×1200、OG 1200×630（以票上「規格說明」為準）
- 票上時程：設計第一版〔待填〕、定稿〔待填〕

## 檔案在哪（專案根：`{path}`）
| 路徑 | 內容 |
|---|---|
| `src/` | **唯一要改的地方**。`platform.css` 平台層（沒必要不要動）、`design.css` 設計層、段落 HTML、`layout.json`（段落順序、報名區塊尺寸）、`seo.json`、`site.json`、`_mock_form.html`（表單規格）、`guide_notes.html`（指南裡缺素材與待裁決） |
| `build.py` | `python3 build.py --shots` 重產 `out/`；交件前 `python3 build.py --strict` 確認沒有佔位字 |
| `out/` | 產出物，**不要手改**：`instapage/`（貼上用）、`preview*.html`、`上稿指南.html`、`上傳用/`、`images/` |
| `tools/` | `scene_crop.py`（場景圖裁到桌底）、`close_desk.py`（補櫃子底線，座標要重量）、`kv_drafts.py`（KV 比較板）、`vectorize.py`（PNG→SVG，選用） |
| `assets/` | 圖檔（WebP 為主，build 會轉 base64 內嵌） |
| `_ref/` | 票上參考圖、合作方素材 |

## 上線狀態
- 〔待填：測試網址、正式網址、發布時間、check_live.py 結果〕

## 已定案的決定（含誰、何時）
- 〔待填〕

## 待辦
1. 〔待填〕

## 容易忘的限制
- 讀 skill `alleypin-event-landing-page` 的 references/pitfalls.md；本案特有的坑寫在這裡。
"""


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__); sys.exit(2)
    slug = args[0]
    opt = lambda k: next((args[i + 1] for i, a in enumerate(args) if a == k and i + 1 < len(args)), None)
    date = opt("--date")
    if not date:
        print("要給活動日：--date YYYY-MM-DD（資料夾以活動月份命名，例 2026-11-cofit-webinar）"); sys.exit(2)
    datetime.date.fromisoformat(date)
    if opt("--root"):
        root = Path(opt("--root")).expanduser()
    elif DEFAULT_ROOT.parent.exists():          # Hsing 的機器：~/Desktop/AlleyPin/landing page/
        root = DEFAULT_ROOT
    else:                                        # 同事的機器沒有這個資料夾：不要自己猜位置
        print("這台電腦沒有 ~/Desktop/AlleyPin/，請用 --root 指定要放活動頁專案的資料夾（例：--root ~/Desktop/活動頁）")
        sys.exit(2)
    dest = root / f"{date[:7]}-{slug}"
    if dest.exists():
        print(f"已經有這個資料夾，不覆蓋：{dest}"); sys.exit(1)
    shutil.copytree(TEMPLATE, dest, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "out"))
    (dest / "_ref").mkdir()
    # 段落庫：Cofit 上線頁的段落（ap- 前綴、圖片在 assets/library/），要用就把檔名加進 layout.json 的 body
    lib = SKILL / "assets" / "section-library"
    shutil.copytree(lib, dest / "src" / "_library", ignore=shutil.ignore_patterns(".DS_Store", "img"))
    shutil.copytree(lib / "img", dest / "assets" / "library", ignore=shutil.ignore_patterns(".DS_Store"))
    site = json.loads((dest / "src" / "site.json").read_text(encoding="utf-8"))
    if opt("--name"):
        site["guide"]["EVENT_NAME"] = opt("--name")
        for f in ("layout.json",):
            p = dest / "src" / f
            p.write_text(p.read_text(encoding="utf-8").replace("〔待填：活動名稱〕", opt("--name")), encoding="utf-8")
    site["guide"]["TEST_SLUG"] = f"{slug}-test"
    (dest / "src" / "site.json").write_text(json.dumps(site, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    (dest / "交接.md").write_text(HANDOFF.format(name=opt("--name") or slug, today=today, date=date, path=dest), encoding="utf-8")
    print(dest)


if __name__ == "__main__":
    main()
