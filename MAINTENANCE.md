---
最後更新: 2026-10-06
用途: 給 Hsing 的維護說明（同事看 QUICKSTART.md）
---

# 維護

## 這個 skill 的來源

- **流程與坑**：2026-10-02～10-06 Cofit 線上說明會頁（events.alleypin.com/cofit）。原始專案在 `~/Desktop/AlleyPin/landing page/2026-11-cofit-webinar/`，只在這台電腦上。
- **模板** `assets/project-template/`：從 Cofit 專案抽出來的，前綴 `cf-` 改 `ap-`，`shared.css` 拆成 `platform.css`（平台規矩）＋`design.css`（每檔重訂）。
- **段落庫** `assets/section-library/`：Cofit 的五個段落改成 `ap-` 寫法，附圖。
- **KV 範例** `assets/kv-examples/`：幾何參考圖產生器、線頭驗收腳本、提示詞範本（座標都是 Cofit 那張構圖的）。

## 文案規則：vault 是源頭，copy-rules.md 是萃取版

`references/copy-rules.md` 萃取自 vault 的以下四處，**單向萃取，不反向**：
- `05_常用句型與禁忌/`
- `06_日常文案改稿/04_AI改稿前必讀包/01_阿幸改稿判斷流程.md`
- `06_日常文案改稿/03_各類文案判斷標準/00_各類文案判斷標準.md`（活動文案）
- `04_對外文稿/活動頁（LP）結構判準.md`

**敏感題總表、公司口徑與數字刻意沒萃取**：同事碰到只會被要求「標出來給 Hsing 複查」。

改了上面任何一份，就同步 `copy-rules.md`，並更新它開頭的同步日期。

## 改了模板之後要跑的檢查

1. **Cofit 重現**：把模板的 `build.py` 放進 Cofit 專案的複本，加 `src/site.json`：
   ```json
   {"prefix":"cf","css":["shared.css"],"fonts":"family=Chiron+GoRound+TC:wght@700&family=Noto+Sans+TC:wght@400;700","extra_chars":"免費報名照片待補"}
   ```
   跑 `python3 build.py`，五段 `out/instapage/*.html` 要跟 Cofit 專案現有的逐位元組相同（2026-10-06 通過）。

2. **QA 鑑別力**：`scripts/qa_page.py` 用 Cofit 現行版要 0 個 ❌。
   - 加 `--prefix cf --cta-var --cf-orange`。
   - 新增任何檢查，都要做一個「應該不過」的版本確認抓得到。
   - 2026-10-06 驗過：平滑捲動、pretty、subgrid、插圖浮空、孤字、時間橘色膠囊、錨點、佔位字、溢出、手機貼邊、表單標籤孤字。

3. **新專案冒煙測試**：`new_project.py` 開一個到暫存資料夾 → `build.py --shots` → `qa_page.py`。只應該剩佔位字相關的 ❌。

4. **上線檢查**：`scripts/check_live.py` 對任何一個已上線的活動頁跑一次，確認沒有誤報。
   - 2026-10-06 修過一次誤報：模板註解裡寫了「不要加 text-wrap:pretty」被當成違規。

## 踩到新坑時

1. 寫進 `references/pitfalls.md`：現象／原因／做法／日期，能自動抓的標 🤖。
2. 平台層的修正同步到 `assets/project-template/src/platform.css`。
3. 能自動檢查的加進 `qa_page.py` 或 `check_live.py`，照上面第 2 點驗鑑別力。
4. SKILL.md 的「踩坑速查」表加一行。

## 發佈（GitHub：`AlleyPin/alleypin-event-landing-page`）

| 路徑 | 給誰 | 進安裝包？ |
|---|---|---|
| `SKILL.md`、`references/`、`scripts/`、`assets/` | AI 讀與執行 | ✅ |
| `QUICKSTART.md` | 同事的安裝與使用說明 | ✅ |
| `README.md` | GitHub 首頁：安裝方式、下載連結、「不要用 Download ZIP」 | ❌ |
| `MAINTENANCE.md`、`tools/`、`evals/` | 維護者 | ❌ |

改了東西之後：
1. 改檔，跑上面「改了模板之後要跑的檢查」。
2. 打包並檢查：`bash tools/release.sh`，輸出到 `~/Desktop/AlleyPin/AlleyPin Claude/alleypin-event-landing-page 安裝包/`。
   - `tools/verify_package.py` 的 8 項檢查，包括實際解壓縮、開專案、建置。
   - 任何一項不過就刪掉壞包並 exit 1。
   - 這一步不開 Chrome、不換 HOME。
3. commit → push（SSH，`Hsing-Ju-Chi` 身分）。
4. 發 Release：https://github.com/AlleyPin/alleypin-event-landing-page/releases/new
   - tag 用 `v日期`（例 `v2026.10.06`）。
   - 附件上傳 `alleypin-event-landing-page.zip`（固定檔名，不帶日期）。
   - 勾 Set as the latest release。
5. **驗收三條下載路**（每次都要）：
   - Release 固定連結：下載後跑 `verify_package.py` 全過。
   - `git clone`：資料夾名是 `alleypin-event-landing-page`，SKILL.md 的 name 一致。
   - 綠色 Download ZIP：資料夾一定叫 `-main`，只能靠 README 的提醒擋，確認提醒還在。

2026-10-06 模擬全新安裝的實測：
- 照 QUICKSTART 解壓縮、`cp -R` 進一個沒有 `~/Desktop/AlleyPin/`、沒有其他 skill 的 HOME：
  - 環境檢查正確標出缺的 skill。
  - 沒給 `--root` 會停下來要求指定。
  - 開專案、`build.py --shots`、QA 都能跑（截圖與 QA 是用真的 HOME 跑）。
- 沒有測過：真的同事電腦、Windows。
- **模擬時只能替「安裝」那一步換 HOME，不要讓 Chrome 在假 HOME 底下跑**：會一直跳鑰匙圈視窗（pitfalls E6）。

## 還沒驗證的

- 感謝頁能不能一個區塊都沒有（目前上稿指南寫「不行就留一個最小高度的白色空區塊」）。
- 活動頁的 `twitter:description` 是 Instapage 後台哪一格產生的。
- skill 描述的真實自動觸發測試：2026-10-06 `run_eval`／`run_loop` 都沒跑成，終端機版 `claude` 一直回 401（重新 /login 後，app 內的終端機分頁也一樣）。改做代理小測（subagent 判斷會選哪個 skill）20/20 正確，紀錄在 `alleypin-event-landing-page-workspace/description-opt/proxy_results.md`。
