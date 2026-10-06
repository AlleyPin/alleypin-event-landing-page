# 踩坑全集（Cofit 線上說明會頁，2026-10-02～10-06）

每一條都來自 Cofit 案：官方文件查證、拆線上原始碼實測，或 Hsing 抓到的問題。格式：**現象** → **原因** → **做法**（出處／日期）。
`qa_page.py`、`check_live.py` 能自動抓的會標 🤖；其餘要靠眼睛或流程。

## 目錄
- A. Instapage 平台
- B. 表單與上線設定
- C. 排版與 CSS
- D. 插圖、KV 與 PinFriends
- E. 工具與環境
- F. 流程與協作

---

## A. Instapage 平台

**A1. 不能上傳 HTML 檔。**
→ Instapage 只收 `.instapage` 格式（官方 help 206024827）。
→ 手寫碼只能貼兩種地方：頁面設定 HTML/CSS 的 Head／Body／Footer 三格，和編輯器左側欄的「HTML 元件」。（2026-10-02 查證）

**A2. Head／Body／Footer 三格整頁共用，不能分區塊貼。**
→ 拆 nova-webinar 上線原始碼：自訂 BODY 碼插在 `<body>` 一開頭、所有區塊（`<main>`）之前；FOOTER 碼在 `</main>` 之後、script 之前（2026-10-05，Hsing 指出）。
→ 頁面結構固定成：**Head（字型＋全部樣式）＋ Body（表單前的所有段落，一般文件流）＋ 編輯器裡唯一一個區塊（報名須知 HTML 元件＋原生表單）＋ Footer（頁尾）**。Body 段落高度由內容撐開，不用在後台設高度；只有報名區塊要量高度、寫進 `layout.json`。

**A3. 自訂碼在編輯器與預覽模式都看不到。**
→ 只在已發布的 live 頁執行。
→ 一定要先發布到測試網址（`<代號>-test`），再用 `check_live.py`＋手機實機驗收。

**A4. 尺寸用 px 會在平板寬度溢出。** 🤖
→ Instapage 依螢幕寬度縮放 `:root` 字級：≤400 是 4vw、401–767 是 16px、768–1200 是 1.33vw。區塊高度與元件框也是 rem。
→ 手寫碼全部用 rem，內容才會跟固定高度的框一起等比縮放。唯一例外：iOS 輸入框保底 `max(1rem,16px)`（見 B7）。（2026-10-02，更正了研究 agent「用 px」的建議）

**A5. HTML 元件設 `height:100%` 沒有用。**
→ 元件外層 `.contents` 沒有高度。
→ 元件高度寫死在 CSS：`build.py` 從 `layout.json` 產生，跟後台設定是同一組數字。

**A6. 某些 class 名稱和寫法會撞到 Instapage。**
→ `.hidden`、`.clearfix`、`.item-*` 是內建 class；自訂碼裡出現 `$(` 會強制載入 jQuery；內建樣式有 `ol,ul{padding-left:2.5rem}`。
→ 所有 class 加前綴（模板用 `ap-`）。列表重置要寫 `.ap :where(ul,ol)`，權重才蓋得過內建樣式。

**A7. 編輯器版面規格。**
→ 經典編輯器：桌機內容欄 960px（響應到 1200）、手機 400px、斷點 768；元件全部絕對定位；區塊高度桌機、手機各寫死。
→ 手機版不要按 **Regenerate**：會清掉手機版所有手動設定。

**A8. Windows 上字型掉到新細明體。**
→ Instapage 頁面的 `<html>` 沒有 `lang`。
→ 字型堆疊要明寫 `"PingFang TC","Microsoft JhengHei"` 當備援。

**A9. 圖片內嵌會讓 Body 變大。**
→ 頁面上的圖全部轉 WebP 後 base64 內嵌（Hsing：「程式寫得出圖就不用上傳」）。Cofit 頁 Body 約 204KB，上線後完整、沒被截斷（2026-10-05）；官方沒寫上限。
→ 唯一要上傳的是社群縮圖（Instapage 設定欄位只收檔案）。被截斷時 `check_live.py` 會報「結尾對不上」🤖，備案是把圖上傳到 Instapage、改用網址。

**A10. 搜尋收錄。**
→ events.alleypin.com 的活動頁預設 `noindex,nofollow`，複製來源頁就會帶過來（2026-10-06 查 nova 兩頁）。所以 SEO 標題與描述實際上主要用在 LINE／FB 分享預覽：標題＝分享標題、描述＝分享說明，重點放前面。
→ 要不要開放收錄由 Hsing 決定，`check_live.py` 只報現況 🤖。

## B. 表單與上線設定

**B1. 程式寫的表單收不到名單。**
→ 嵌入式表單不進 Leads、不觸發整合、不寄通知、不算轉換（官方 help 205221768、360012028512）。
→ 原生表單送出時帶 Instapage 簽章的 `lpsSubmissionConfig`，以及 `zapier2-integration` 欄位對應。
→ **表單一律用原生的**：欄位、必填、Zapier、導向由 Hsing 在後台設，外觀由 Head 的 CSS 接管。`check_live.py` 會檢查簽章 🤖。

**B2. 改了欄位樣式，送出鈕跟最後一欄重疊。**
→ 原生送出鈕是絕對定位（`.form-btn-geometry` 寫死 top）。
→ 改成 `position:relative` 跟著欄位排（`platform.css` 已處理）。覆寫原生表單的規則要用 `body#landing-page form.email-form …` 起頭，才蓋得過 `#element-xxx`。

**B3. 複製頁不會帶 Zapier。** 🤖
→ 2026-10-05 實測：複製 nova-webinar 出來的 cofit 頁，原始碼裡沒有 `zapier2-integration`。
→ 到表單 Integrations 重新接；欄位改過名，Zapier 對應也要跟著改。

**B4. 複製頁會帶來源頁的舊設定。** 🤖
→ 會帶：頁面標題、描述、社群縮圖、送出後導向、欄位文字與選項、送出按鈕文字。
→ **2026-10-06 13:5x 線上實測 cofit 活動頁**：標題與 OG 已換成 Cofit，但表單仍是 nova 原版（第 8 欄、科別 9 項、勾選文字、按鈕「完成送出」、送出後跳 nova-webinar-thankyou、沒有 Zapier）。同日另查到 B11、B12、B13。
→ 上稿指南第二節逐項列出，上線後一定跑 `check_live.py --project`。

**B5. 送出後導向不能看 `url=` 參數判斷。** 🤖
→ 原始碼裡的導向值是 `app.instapage.com/route/<id>/?url=…`，`url=` 後面常是舊值。
→ 2026-10-06 實測：`url=` 寫 `kaitest_ty`（那個網址是 404），但 route 實際跳到 nova-webinar-thankyou。之前「nova 表單導向 404」的判斷是錯的。
→ 一律跟著 route 轉址看最後落點，`check_live.py` 就是這樣做。

**B6. 感謝頁沒發布，導向清單裡選不到。**
→ 先發布感謝頁，再回活動頁設送出後導向。
→ 感謝頁能不能一個區塊都沒有，還沒實測；不行就留一個最小高度的白色空區塊。

**B7. iPhone 點輸入框，整頁自動放大。**
→ iOS Safari 遇到字級 < 16px 的輸入框會放大；手機根字級是 4vw（390 寬時 15.6px）。
→ 手機版輸入框 `font-size:max(1rem,16px)`。

**B8. 下拉選單出現英文「-- Select one --」。**
→ 這是 Instapage 預設的空選項文字。
→ 未選時 `color:transparent`，選了（`aria-invalid="false"`）才顯示，跟 Instapage 預設行為一致。

**B9. 測試名單污染下游。**
→ 測試資料會進 Leads，也會經 Zapier 流進試算表或 CRM。
→ 驗收完清掉或標註。

**B11. 複製來的頁面留下只在手機顯示的舊區塊。** 🤖
→ 2026-10-06 抓 cofit-thankyou 線上原始碼：留著一個 nova 感謝頁的編輯器區塊，內容是 Nova「裕利醫藥」刷卡回饋文案與「活動細則」連結。這個區塊桌機隱藏、手機顯示，在桌機編輯器裡看不到。
→ 刪區塊時，桌機與 Mobile 兩個檢視都要看。`check_live.py --project` 會比對區塊數量（照 layout.json）並列出不是這次程式碼的文字。

**B12. X（Twitter）卡片的描述跟 og 不一樣。** 🤖
→ 2026-10-06 cofit 活動頁：og:description 正確，但 `twitter:description` 是感謝頁的描述。
→ 後台是哪一格產生這個標籤，還沒查證。`check_live.py` 會比對 twitter:title／twitter:description。

**B13. 報名區塊的元件位置沒照尺寸表設。** 🤖
→ 2026-10-06 cofit 活動頁線上 CSS：報名須知 HTML 元件桌機在 left 52／top 47／寬 360（規格 0／0／380），表單也偏了，「報名須知」比上面各段右偏 52px（驗收清單第 3 項沒過）。
→ 元件拖進來後的預設位置不會剛好是規格值，要照上稿指南第五節逐格輸入桌機與手機的 X／Y／寬／高。`check_live.py --project` 會拿線上 CSS 跟 layout.json 比。

**B10. 感謝頁是固定模板。**
→ 以 `nova-webinar-thankyou` 為準（2026-10-06 Hsing）：KV 沿用活動頁視覺，加上感謝與報名後須知；第二段「更多 AlleyPin 資訊」固定三列點（線上學習不費力／交流成長不停歇／服務專業不間斷）＋敘述＋CTA（部落格、LINE、顧問諮詢，`utm_source=thankyou`），**文字與連結一字不改**，樣式跟這次活動頁同一套；頁尾同活動頁。
→ 模板的 `src/ty-more.html` 就是這段，不要改字。

## C. 排版與 CSS

**C1. 錨點按鈕捲到報名區時卡住、拖很久、期間滑不動。** 🤖
→ Instapage 上線頁的 Cradle.js 會攔截所有 `href="#…"`，自己用 300ms 的 requestAnimationFrame 迴圈捲到差 ≤1px 才停。再疊 CSS `scroll-behavior:smooth`，每一格的 `window.scroll()` 都變成非同步動畫、永遠追不上。
→ 2026-10-05 Hsing 手機實測卡住；本機重現 1769ms → 拿掉後 308–315ms。
→ **永遠不要寫 `scroll-behavior:smooth`**。

**C2. 手機上內文每一行都提早換行。** 🤖
→ `text-wrap:pretty` 會讓 Safari（WebKit）對整段重排來修右緣（WebKit 官方部落格）。
→ 內文不加 pretty，排滿固定寬度才換行（2026-10-05 Hsing 手機實測）。

**C3. 標題只在逗點後換行，右邊留一大塊空白。** 🤖
→ `word-break:keep-all`（加 `text-wrap:balance`）會讓中文只在標點換行。
→ **標題也齊寬換行**：不加 keep-all、不加 balance（2026-10-06 12:13 Hsing：「不要逗點後換行」）。
→ 要刻意分行就在 HTML 寫 `<br>`（KV 主標、「Cofit ——<br>診所的外掛健康管理團隊」）。
→ 只想在桌機分行的（例：置中引言照語意在逗點後分兩行），用 `<br class="ap-br-desk">`，手機會隱藏，因為手機一行只放得下約 20 字，硬斷會留下孤字或短行（2026-10-06 12:34）。
→ 2026-10-02 一度定過「中文標題要 keep-all」，已被這條取代。

**C4. 孤字：最後一行只剩一個字。** 🤖
→ 齊寬換行的副作用：桌機「…管理需／求」；手機「…庫存限／制」「…容易中／斷」「…健康管理的新機／會」。
→ **用刪字解，不用 CSS**。Hsing 2026-10-06 12:19 同意刪「在」「需」「結束」「的」。
→ 刪字是改文案：列給使用者確認，不要自己決定刪哪個字。1440 與 390 都要量。
→ 內文段落的孤字 `qa_page.py` 只給 ⚠️，要不要處理問使用者。

**C5. 並排卡片的說明文字高低不一。** 🤖
→ 標題折行數不同，說明就被推到不同高度。
→ 每張卡佔 N 列、共用外層的列：`grid-row:span N; grid-template-rows:subgrid; row-gap:0`（2026-10-06 12:09，「適合對象」「三優勢」）。
→ 感謝頁三張卡同理（四列）。間距照舊用 margin，不要用 row-gap。

**C6. 活動時間看起來像第二顆按鈕。** 🤖
→ 時間做成橘色膠囊，跟「立即免費報名」撞造型。
→ **報名色（橘）只給報名按鈕**。時間改成獨立一行＋時鐘圖示、跟日期同字樣（2026-10-06 12:09）。
→ 那次要同步改五處（活動頁 KV、感謝頁 KV、OG、社群圖、KV 設計稿版型）。模板把日期時間做成共用片段 `_when.html` 就是為了只改一處。

**C7. 編號跟標題同一行，折行後左緣不齊。**
→ 「01｜標題」折到第二行，字會對不齊。
→ 編號做成標題裡獨立一行的小字（`.ap-no`），標題每一行、內文都從同一條左緣開始（2026-10-05）。

**C8. 出現左右捲軸，或字被切掉。** 🤖
→ 滿版底色層 `.ap-bleed` 是 100vw，會比有捲軸的視窗多出捲軸寬。
→ `html,body{overflow-x:clip}`。但 clip 也會把真的溢出的內容默默切掉、捲軸不會出現，所以 `qa_page.py` 是逐元素量有沒有超出視窗。

**C8b. 手機上卡片貼齊螢幕邊緣。** 🤖
→ 手機的左右內距是 `.ap-sec` 給的；卡片清單寫在 `.ap-sec` 外面，390 寬時就貼著螢幕邊（2026-10-06 skill 測試時抓到，模板已修）。
→ 段落內容都包在 `.ap-sec` 裡。`qa_page.py` 會量文字與卡片離邊緣是否 < 8px。

**C4b. 表單欄位標籤也會有孤字。** 🤖
→ 桌機表單兩欄，長的欄位標籤（例「( 選填 ) 目前預約流程最困擾的地方」）會折行、最後一行剩一個字，右欄輸入框還會因此低一截（2026-10-06 skill 測試時抓到）。
→ 解法同 C4：提刪字方案給 Hsing。欄位名稱改了，Zapier 對應也要改（B3）。

**C9. 換 KV 插圖後，手機版標題壓到插圖。**
→ 手機 KV 是插圖絕對定位在上、標題用 margin-top 推到插圖下方。
→ 插圖比例變了（1000/593 → 1000/629）就要重算 `.ap-kv__illus` 的 aspect-ratio、手機標題 margin-top（16 → 16.75rem），感謝頁 KV 同步。

**C10. 改文案後出現系統字。**
→ Google Fonts 用 `text=` 子集只打包頁面用到的字（Cofit 三個字重約 392KB；全字集約 3.8MB）。新字不在子集裡就退回系統字。
→ 改任何文案都要重跑 `build.py`。Hsing 在 Instapage 後台改的字（例如表單欄位名稱）要回 `src/` 同步。CSS `content:"…"` 裡的字 build 會自動算進去。

**C11. 動態太多。**
→ 只留一個：KV 插圖載入時往上浮一次；系統設定「減少動態」就不動。

## D. 插圖、KV 與 PinFriends

**D1. 角色走樣。**
→ 只要畫面有 PinFriends，**先呼叫 `alleypin-pinfriends` skill**，照它的四面圖、英文區塊、QA 三點產圖。
→ skill 建立前的舊圖：伊吉耳機變亮寶藍、吐司缺單邊斜眉、山豆 M 記號變大帶漸層。

**D2. 同一組插圖不一致。**
→ Hsing 的標準：**同一組插圖的大小、情境、角色取用部位要一致**（2026-10-05）。
→ 開工先定三件事：
  - 角色分工：Cofit 案是山豆醫師＝醫師、伊吉＝病人、吐司＝診所夥伴。
  - 鏡頭：腰部以上、坐在桌後、3:2、透明底。
  - 服裝：附定稿 KV 當 Image 1，寫明「ONLY for Shandou's outfit, character look and line weight; do NOT copy its background shapes」。
→ **同一組要在同一輪產**：Cofit 第 4 段混用舊圖與新圖，結果第 1 張角色大一號、山豆沒領帶（到 10-06 都還沒解）。

**D3. 插圖浮在半空中。** 🤖
→ 原圖的桌子畫在不同高度、底下留白不一，整張塞進框裡就浮起來。
→ `tools/scene_crop.py` 把底部裁到「最低的不透明像素＝桌子底緣」（600 寬 WebP）。CSS 用同一個寬度比例（框寬 92%）＋ `bottom:0` 貼齊框底，同組桌子對齊、角色同比例。
→ 2026-10-05 先修第 3 段兩張，隔天 Hsing 又抓到第 4 段三張一樣（見 F1）。

**D4. 櫃子沒有底線。**
→ 舊圖的櫃子兩側直線畫到底就截掉，跟其他張有黑色底線的不統一（2026-10-06 13:24）。
→ `tools/close_desk.py` 照原圖的線寬 5px、圓角外緣 47px 補上底邊，另存新檔、原圖不動，再過 `scene_crop.py`。腳本裡的座標是量那一張圖的，換圖要重量。

**D5. KV 幾何參考圖的線頭停在半空中。**
→ 附了參考圖，Codex 會連錯誤一起照抄：第六輪白線終點畫在所有形狀上面、落在圓柱內部，三張全中（2026-10-05 18:48 退件）。
→ 參考圖出圖前先自己驗：每條線的頭尾要落在徽章或形狀邊線上，或藏在前景形狀後面。
→ 最穩的做法：線畫在那根圓柱**後面**，讓圓柱邊線把線切齊；提示詞寫「pillar is in FRONT of the path」「a line end may never stop in empty space」。
→ 驗收腳本見 `<skill>/assets/kv-examples/qa_lines.py`（線頭前方顏色；座標是 Cofit 那張構圖的）。

**D6. 角色下半身平切、浮在背景中間。**
→ 第七輪山豆白袍下襬平切浮在深藍主圓柱中間：參考圖在腰部沒有任何前景形狀，模型只能平切。
→ 前排圓柱拉高到角色腰線，提示詞寫「a character's body may only be cut off by a shape in front of it」（第八輪三張都藏好）。

**D7. 漸層、光暈、細白條。**
→ 第八輪第 2 張白袍右緣拖出細白條、第 3 張有模糊白色光暈。
→ 腳本量不到，每張都要眼看全圖。

**D8. 寬身形角色被窄形狀擠變形。**
→ 山豆身形偏寬，搭配的幾何寬度要拉開（2026-10-05 15:4x Hsing 指出窄拱門把山豆醫師擠變形）。

**D9. 修圖修到不符效益。**
→ Hsing 否決過兩種做法：「程式畫幾何＋Codex 角色去背合成」（「超爛」）、「逐像素修正圓」（「太久，不符合效益」）。
→ 要改圖就**調提示詞重生、不要用改的**。細工先估時間，超過兩三輪先問要不要繼續。

**D10. Codex 叫法。**
→ 指令：`codex exec --skip-git-repo-check -s workspace-write -C <圖片資料夾> "<prompt>" -i <ref1> -i <ref2> … < /dev/null`。
  - prompt 放在 `-i` 前面。
  - 背景跑一定要接 `< /dev/null`，否則卡在讀 stdin。
  - prompt 第一行寫「pure image-generation task, do not read any files or notes」，否則它可能去掃 Obsidian vault。
→ 速度：一張約 1–2 分鐘、1254×1254；一次指令可以產多張，每張寫清楚檔名。
→ 背景幾何要精確時，附一張程式畫的幾何參考圖，比只用文字有效：圓的邊緣偏離從 2.4px 降到 0.5px。

**D11. 要轉 SVG（選用）。**
→ `tools/vectorize.py`（vtracer）。先把顏色收斂到品牌色票，事後再 snap 顏色、座標取整數。
→ vtracer 0.6.15 在 Python 3.14 帶任何數字參數都會 segfault，只能用預設值。
→ 需要的話自建 venv：`python3 -m venv tools/.venv && tools/.venv/bin/pip install vtracer`。
→ Cofit 最後 KV 用的是 WebP，不是 SVG。

**D12. KV 的主題約束來自票。**
→ Cofit 票寫「不需直接使用藥丸、十字等醫療符號」「避免呈現成保健品銷售頁」：B 方向「單憑新芽看不出營養師照護」被打回，改成醫師→營養師＋客製保健組合盒，不畫藥丸。
→ 每次先把票上的 KV 視覺概念讀成可檢查的條件。

## E. 工具與環境

**E1. 手機截圖寬度被撐開。**
→ 無頭 Chrome 視窗最小寬約 500px。
→ 手機截圖與量測用 390 寬的 iframe 包一層（`build.py`、`qa_page.py` 都這樣做）。

**E2. 無頭 Chrome 隨機卡死。**
→ `build.chrome()` 有逾時重試；自己叫 Chrome 也要設 timeout。macOS 沒有 `timeout` 指令，用 Python 的 `subprocess.run(timeout=…)`。

**E3. 列印 PDF 卡死。**
→ `--print-to-pdf` 搭 `--virtual-time-budget` 會卡死，PDF 改用 `--timeout`。

**E4. 長頁截圖被截斷。**
→ Chrome 截圖高度上限約 16,000px。
→ 手機截圖用 1.5 倍解析度，`site.json` 的 `shot_heights` 手機高度 ×1.5 不要超過上限。

**E6. Mac 一直跳「找不到鑰匙圈來儲存『Chrome』」視窗。**
→ 2026-10-06 為了模擬同事的電腦，在換過 HOME 的環境裡跑截圖。macOS 版 Chrome 每次啟動都要把「Chrome Safe Storage」金鑰存進鑰匙圈，假 HOME 底下找不到 login 鑰匙圈，就跳系統視窗。每截一張圖跳一次，連「取消」都按不掉（PinFriends session 抓到）。
→ 所有無頭 Chrome 都加 `--use-mock-keychain`（模板與腳本已加），而且**永遠不要替 Chrome 換 HOME**。視窗跳出來時按「取消」，不要按「重置為預設值」：那會換掉整個 login 鑰匙圈。
→ 不要加 `--user-data-dir`：實測截圖寫完後 Chrome 不會結束，每次都卡到逾時。
→ 不要用 `pkill` 砍 headless Chrome：會誤殺別的工作開的 Chrome。subprocess 逾時時已經會砍掉自己開的那個。

**E5. 原生 .ai 產不出來。**
→ 社群圖與 OG 輸出 PNG（上架用）＋向量 PDF。設計師用 Illustrator 開 PDF 另存 .ai。

## F. 流程與協作

**F1. Hsing 點出一個問題，代表的是一類。**
→ 第 3 段插圖浮空只修兩張，隔天 Hsing 又抓到第 4 段三張（「你有發現嗎」）。
→ 修之前先問病因在哪一層（原圖、共用 CSS、產生器），把同層影響到的實例全部列出、一起修、一起在 1440／390 驗收，回報時寫明掃過哪些地方。`qa_page.py` 就是把這幾類變成全頁掃描。

**F2. 改了 out/ 的檔案，下次 build 就被蓋掉。**
→ `out/` 全部由 `build.py` 產生。改 `src/`，重跑 build。

**F3. 票上的「上稿提醒」是寫給拖拉設計師的。**
→ 舊票的上稿提醒（物件分開上傳、用群組、Chrome／Safari 各自測）是 Instapage 拖拉編輯器的做法，套到手寫 HTML 會誤導。
→ 開新票時照 `plan-copy-ticket.md` 第 4 節的手寫版上稿提醒寫。

**F4. 給 Hsing 看規劃與版面時給錯格式。**
→ Hsing 不想開 .md。
→ 版面、指南給 HTML（`上稿指南.html`、比較板），文案給 Notion 票。

**F5. 交接靠記憶會漏。**
→ 每做完一批修正，就更新專案根目錄的 `交接.md`：時間用 `date` 查、寫明哪幾段程式碼要重貼。
→ 2026-10-05、10-06 的每一批修正，交接裡都寫明「要重貼 Head＋Body」這類指示；少了這句就不知道該重貼哪幾格。

**F6. Hsing 說「已上稿」不等於上線設定都對了。**
→ 2026-10-06 上稿完成後抓線上原始碼，表單仍是來源頁的（B4）。
→ 上稿後一律跑 `check_live.py`，結果列給使用者。後台設定是使用者的權限，Claude 不代改。
