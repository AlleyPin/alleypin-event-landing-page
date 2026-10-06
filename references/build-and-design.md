# 第 3 步：頁面設計與程式

完成品參考：Cofit 線上說明會頁（2026-10 上線：events.alleypin.com/cofit、/cofit-thankyou）。它的段落已經改成通用寫法放在段落庫 `assets/section-library/`，開新專案時會複製到 `src/_library/`（圖片在 `assets/library/`）。原始專案只在 Hsing 的電腦上（`~/Desktop/AlleyPin/landing page/2026-11-cofit-webinar/`，前綴 `cf-`），同事不需要它。

## 目錄
1. 開專案
2. 檔案分工
3. 設計方向
4. 寫段落 HTML（元件目錄）
5. 報名區塊與 layout.json
6. KV 主視覺
7. 場景插圖（PinFriends）
8. 照片、logo、OG／社群圖、SEO
9. 建置指令

---

## 1. 開專案

```bash
python3 "<skill>/scripts/new_project.py" <代號> --date <活動日 YYYY-MM-DD> --name "<活動名稱>" [--root <資料夾>]
```

`<skill>` 是這個 skill 的資料夾。專案資料夾以活動月份命名（例 `2026-11-cofit-webinar`）：有 `~/Desktop/AlleyPin/` 的電腦預設建在 `~/Desktop/AlleyPin/landing page/` 底下；沒有的，問使用者要放哪，用 `--root` 指定。資料夾已存在就停下來、不覆蓋。

建完把票上的參考圖、合作方素材放進 `_ref/`，並先填 `交接.md` 的「任務是什麼」。

## 2. 檔案分工

| 檔案 | 放什麼 | 什麼時候改 |
|---|---|---|
| `src/platform.css` | Instapage 平台規矩：rem、橫捲、不寫平滑捲動、換行規則、滿版底色層、文件流段落、原生表單外觀、iOS 16px | 幾乎不改。改之前讀 pitfalls.md |
| `src/design.css` | 色票與字型 token（`:root`）、各段元件樣式 | 每檔重訂。顏色只改 token，不要在元件裡寫死 |
| `src/site.json` | 前綴、CSS 合併順序、Google Fonts 參數、指南用字串、截圖高度 | 換字型、換活動名稱時 |
| `src/layout.json` | Body 段落順序、Footer、報名區塊的區塊高度與元件座標（編輯器 px） | 增刪段落、報名區塊內容變了 |
| `src/kv.html`、`s*.html` | Body 各段 | 寫文案時 |
| `src/_when.html`、`_brand.html`、`_kv-art.html` | KV／感謝頁／OG／社群圖共用的日期時間、品牌列、插圖 | 只改這一處，五個地方同步（pitfalls C6） |
| `src/signup-info.html` | 報名須知（報名區塊的 HTML 元件） | 改了要重量高度 |
| `src/ty-kv.html` | 感謝頁 KV＋報名後須知 | 日期 |
| `src/ty-more.html` | 感謝頁「更多 AlleyPin 資訊」固定模板 | **不改字** |
| `src/footer.html` | 頁尾（兩頁共用） | 很少 |
| `src/_mock_form.html` | 表單規格（上稿指南欄位表、`check_live.py` 比對都從這裡讀）＋本機預覽 | 欄位、選項、按鈕文字定案時 |
| `src/seo.json` | 兩頁的標題、描述 | 文案定稿後 |
| `src/guide_notes.html` | 上稿指南的「還缺的素材」「待裁決的文案」 | 每次交件前 |
| `src/og-1200x630.html`、`social-1200x1200.html` | OG 圖、社群圖版型 | 設計定案後 |
| `assets/icons.html`（skill 內） | 線條圖示庫（currentColor） | 要圖示時複製 |

HTML 片段裡可以寫 `<!-- 註解 -->`：build 會拿掉，不會貼進 Instapage。

佔位字一律寫成 `〔待填：…〕`。`build.py` 會列出還沒填的，`--strict` 有佔位字就失敗，`qa_page.py` 也會抓頁面上的。

## 3. 設計方向

1. **精緻度**：events.alleypin.com 的頁 2026-10-02 起「全部用程式寫」，預設做到可上線的完整視覺。如果這次只要規劃或線框，停在那一層，不要自己做到最精緻。
2. **定方向**：讀票上的「設計參考」（視覺傳達、色彩方向、KV 視覺概念、參考圖），轉成 `design.css` 的 token 與各段版型。有 `frontend-design` skill 就用它（2026-10-02 Hsing 指定）；沒有就照模板預設，只改色票與字型。
3. **色彩**：
   - AlleyPin 單獨主辦：用模板預設（AlleyPin 主要藍 #1D4A82 等，來自 alleypin-slide-design 色盤）。
   - 合作案：照票的色彩方向。Cofit 案是主色 Cofit 深墨綠 #144E4F、輔色醫療藍 #1D4A82 與薄荷綠 #49AE86、背景白與極淺藍綠 #EEF6F4、點綴暖橘 #F5A252。
   - **報名色只給報名按鈕**（pitfalls C6）。淺色不要拿來當小字。
4. **字型**：Cofit 案標題用 Chiron GoRound TC（圓角黑體，配 Cofit 的親和感）、內文 Noto Sans TC。換字型要同時改 `design.css` 的 `--ap-font-*` 與 `site.json` 的 `fonts`。
5. **一次只做一個方向**：要給 Hsing 選方向時，做比較板（KV 用 `tools/kv_drafts.py`），不要做三個完整頁面。

## 4. 寫段落 HTML（元件目錄）

每一段的根元素是 `<div class="ap ap-<段名>">`。build 會自動補 `ap-flow`（置中 960／400 內容欄、高度由內容撐開）。

滿版底色：在段內第一個子元素放 `<div class="ap-bleed <底色 class>" aria-hidden="true"></div>`，內容包在 `.ap-layer` 裡。

| 元件 | class | 用在 | 段落庫範例 |
|---|---|---|---|
| KV 左字右圖 | `.ap-kv`、`.ap-kv__illus`、`.ap-kv__content`、`.ap-brand`、`.ap-when` | 首屏 | `kv.html`（模板） |
| 段落標題／引言／置中段 | `.ap-sec`、`.ap-h2`、`.ap-intro`、`.ap-sec--center`、`.ap-no` | 每段 | 痛點、適合對象置中 |
| 問題卡（圖示＋標題＋說明＋價值條） | `.ap-cards`、`.ap-card*` | 痛點→價值 | `_library/pain-cards.html` |
| 重點列表（三欄，subgrid） | `.ap-points` | 優勢、特色 | `_library/split-journey-points.html` |
| 兩場景＋弧線 | `.ap-journey`、`.ap-scene*`、`.ap-journey__arc／__dot` | 服務延伸、前後對照 | `_library/split-journey-points.html` |
| 插圖卡（3:2 插圖＋標題＋說明，subgrid） | `.ap-fits`、`.ap-fit*` | 適合對象、情境 | `_library/fit-cards.html` |
| 議程（深色段） | `.ap-bg--ink`、`.ap-agenda`、`.ap-slot*` | webinar | `_library/agenda-dark.html` |
| 講者卡 | `.ap-speakers`、`.ap-speaker*` | 講者 | `_library/speakers.html` |
| 報名須知 | `.ap-info`、`.ap-notes`、`.ap-note` | 報名區塊 | `signup-info.html`（模板） |
| 感謝頁 | `.ap-kv--ty`、`.ap-kv__note`、`.ap-more*` | 感謝頁 | `ty-kv.html`、`ty-more.html`（模板） |
| 頁尾 | `.ap-footer*` | 兩頁 | `footer.html`（模板） |

模板附了問題卡、議程、講者三段骨架（佔位字版）；段落庫 `src/_library/` 有五種完整段落（Cofit 文案版）：`pain-cards`、`split-journey-points`、`fit-cards`、`agenda-dark`、`speakers`。要用就把檔名（例 `_library/fit-cards.html`）加進 `layout.json` 的 body，改寫文案、換圖，最後刪掉根元素的 `data-example`。

寫的時候守住這幾條（理由見 pitfalls）：
- 並排卡片一律 subgrid（C5）。
- 編號獨立一行（C7）。
- 標題齊寬換行：要分行寫 `<br>`，只桌機分行用 `<br class="ap-br-desk">`（C3）。
- 報名按鈕連到 `#ap-signup`（報名須知的 id）。
- 圖片一律 `{{img:檔名}}`（build 轉 base64），`width`／`height` 屬性寫顯示尺寸。

## 5. 報名區塊與 layout.json

報名區塊是頁面上唯一要在 Instapage 編輯器建的區塊：左邊 HTML 元件（`signup-info.html`）＋右邊原生表單。

- 座標單位是**編輯器 px**：桌機內容欄 960 寬、手機 400 寬，x／y 從內容欄左上角算。
- Cofit 的值：
  - 桌機：區塊高 880；HTML 元件 0,0,380,880；表單 420,64,540,740。
  - 手機：區塊高 1776；HTML 元件 0,0,400,632；表單 16,640,368,1090。
  - 表單欄位數不同就要重量。
- **量法**：`qa_page.py` 的 ℹ️ 那行會印出每個元件的內容高與區塊留白（已換算成編輯器 px），並給建議區塊高。內容底到區塊底，桌機留約 96、手機約 64。
- 改了 `layout.json` 要重跑 build：元件高度會寫進 CSS（Instapage 的 HTML 元件外層沒有高度，pitfalls A5）。上稿指南第五節的表也會跟著更新。
- Hsing 在後台改了任何座標，要同步回 `layout.json`。

## 6. KV 主視覺

Cofit 案走過的路（2026-10-02～10-05，八輪），結論：

1. **定方向**：先出 2–3 個方向的比較板（`tools/kv_drafts.py <directions.json> <輸出檔名>`，把插圖套進真實 KV 版型、截桌機＋手機）。
   - Hsing 的選法：「C 最清楚、B 有質感」→ 要求「B 的質感＋看得懂」→ 再出一輪。
   - 方向必須讓人「單憑畫面就看懂」服務內容（純抽象新芽被打回，pitfalls D12）。
2. **產圖**：
   - 有角色就先用 `alleypin-pinfriends` skill。
   - 背景幾何要精確時，用程式畫一張幾何參考圖附給 Codex。Cofit 的產生器與成品在 `<skill>/assets/kv-examples/`（`kv_geomref.py`、`kv-geometry-ref-r8.png`），提示詞範本 `kv-prompt-r8.txt`。
   - 參考圖先自驗線頭與遮擋（pitfalls D5、D6）。
   - 要改就調提示詞重生，不修圖（D9）。
3. **驗收**：
   - 照 pinfriends 的 QA 三點。
   - 跑線頭／遮擋腳本（`<skill>/assets/kv-examples/qa_lines.py`，座標是那張構圖的，換構圖要改）。
   - 眼看全圖找漸層、光暈、白條（D7）。
4. **上頁**：
   - 透明底 PNG 轉 WebP，約 1000px 寬。Cofit 定稿 1000×629、約 40KB：`magick in.png -resize 1000x -quality 82 assets/kv-art.webp`。
   - 改 `_kv-art.html` 的檔名與寬高、`design.css` 的 `aspect-ratio`、手機標題 `margin-top`、感謝頁 KV 同步（C9）。
5. 定案前的每一輪設計稿都留在 `assets/kv-drafts/<輪次>/`（prompt、log、原圖），比較板 HTML 放 `out/`。

`directions.json` 格式（`kv_drafts.py` 讀）：

```json
{"title": "KV 設計稿｜第 N 輪", "intro": "這輪改了什麼、推薦哪張",
 "directions": [{"key": "r8-1", "name": "第八輪 1", "file": "r8/kv-r8-1.png", "idea": "一句構想", "notes": ["優點或問題"], "svg": false}]}
```

## 7. 場景插圖（PinFriends）

1. **整組先定規格**：角色分工、鏡頭、比例、透明底、服裝參考（pitfalls D2）。同一組在同一輪產。
2. 產圖照 `alleypin-pinfriends` skill：四面圖、英文區塊、QA 三點。
3. 每張過 `tools/scene_crop.py <原圖.png> <輸出名.webp>`：裁到桌底、600 寬 WebP，並印出 `<img>` 要寫的 width／height。
4. 線條缺口（例：櫃子沒底線）用 `tools/close_desk.py` 補。它的座標是量 Cofit 那張的，換圖要重量；另存新檔，原圖不動。
5. CSS 已經是「框寬 92%＋貼底」，同組插圖不用個別調。
6. 有新舊兩版要選時，做對照板（範例腳本 `<skill>/assets/kv-examples/scene_board.py`，路徑寫死 Cofit 的檔名，用時改 NAMES），不要只描述。

## 8. 照片、logo、OG／社群圖、SEO

- **講者照片**：裁正方形轉 WebP，Cofit 用 320×320（顯示 120px）。Cofit 的 Kenneth 照片取自 `saleskit & deck & intro final/Introduction/AlleyPin_Introduction_TW_2026.08.31.pdf` 第 3 頁。沒有照片就留「照片待補」色塊。
- **logo**：顯示高 32px，檔案用 2 倍以上的 PNG（模板裡的 AlleyPin 藍、白兩版是 72px 高）。合作方 logo 先從票上素材抽，交件時在 guide_notes 註明「正式上線前要官方 SVG／AI」。
- **OG 1200×630**：KV 縮排（票寫「KV resize 即可」）。**社群圖 1200×1200**：KV 元素重排，可加活動類型標籤與報名膠囊，文字只能取自票上。
  - `build.py --shots` 會輸出 PNG＋向量 PDF。原生 .ai 產不出來，請設計師用 Illustrator 開 PDF 另存。
- **SEO**（`seo.json`）：
  - 活動頁：標題＝KV 主標｜活動名稱；描述＝副標＋這場會得到什麼＋日期時間地點＋免費報名。
  - 感謝頁：標題＝KV 主標｜感謝您的報名；描述＝感謝＋審核制與寄信日期。
  - 預設 noindex，主要用在分享預覽，重點放前面（pitfalls A10）。

## 9. 建置指令

```bash
python3 build.py              # 片段、預覽、上稿指南、form_spec.json、上傳用資料夾
python3 build.py --shots      # 另外截預期畫面、輸出 OG／社群圖（PNG＋PDF），再把截圖嵌進指南
python3 build.py --strict     # 有「〔待填」就失敗（交件前）
```

需要：macOS 的 Google Chrome（無頭截圖）、ImageMagick `magick`、Python 3。字型從 Google Fonts 抓，要有網路。
