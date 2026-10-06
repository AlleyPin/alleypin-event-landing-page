# 給同事：用 Claude 做活動報名頁

貼上活動資訊，Claude 會幫你把整套做完：
- 頁面文案（行銷開票中心的格式）
- Notion 開票
- 活動頁與感謝頁的程式碼
- OG 圖、社群圖
- 一份照著做就能上稿的「上稿指南」

上線後跟它說一聲，它會再幫你檢查有沒有漏改的設定。

## 一、安裝（只要做一次）

1. **要用 Claude Code**：Claude 桌面 App 的「Code」分頁，或終端機的 `claude`。claude.ai 網頁版的一般聊天不行，因為要在你的電腦上跑 Chrome 截圖與檢查。
2. **安裝**，兩種擇一：
   - **最簡單**：直接貼這句給 Claude Code：
     > 幫我安裝這個 skill：`git clone https://github.com/AlleyPin/alleypin-event-landing-page.git ~/.claude/skills/alleypin-event-landing-page`，裝好後幫我檢查做活動頁的環境。
   - **或下載安裝包**：https://github.com/AlleyPin/alleypin-event-landing-page/releases/latest/download/alleypin-event-landing-page.zip 。解壓縮後，把 `alleypin-event-landing-page` 資料夾放進 `~/.claude/skills/`。
   - 不要用 GitHub 頁面上綠色的「Code → Download ZIP」：資料夾會多一個 `-main`，跟 skill 名稱對不上。
3. **重開 Claude Code。**
4. **檢查環境**：跟 Claude 說「幫我檢查做活動頁的環境」，它會告訴你缺什麼。通常要裝：
   - **Google Chrome**：一定要。
   - **ImageMagick**：出截圖和社群圖要用。Mac 在終端機貼 `brew install imagemagick`；沒有 brew 就請 Claude 教你裝。
5. **選用的兩個 skill**（沒有也能做頁面，跟 Hsing 拿）：
   - `alleypin-pinfriends`：畫山豆、伊吉這些角色。另外要有 Codex。
   - `frontend-design`：定視覺方向。

**之後要更新**：跟 Claude 說「幫我 git pull 更新 alleypin-event-landing-page skill」；用安裝包裝的，就重新下載一次覆蓋。

## 二、開始做：複製下面這段，填完貼給 Claude

```
幫我做活動報名頁。
活動名稱：
類型：線上說明會／講座／工作坊／小聚（選一個）
日期時間：
地點或平台：（例：Google Meet）
對象：（例：牙醫診所院長、櫃台主管）
主辦／合作方：（合作方 logo 檔一起給）
講者：姓名、職稱、照片、一段介紹（還沒有就寫「待確認」）
議程：時段＋標題＋誰講
報名截止：
是不是審核制？哪天開始寄通知信：
表單：沿用 nova 的欄位就好／要改的地方：
參考資料：（企劃、合作方簡介、舊活動頁網址）
這次要做到：文案＋開票／做出頁面／全部
```

**不用記 skill 名稱。** 直接說「幫我做報名頁」「沿用上次的活動頁改日期」「活動頁手機版跑版幫我修」，Claude 都會用這個 skill。

## 三、你會拿到什麼

1. **先拿到一份「⚠️ 需要你判斷的」清單**，每條都附建議。例如：
   - 講者資料還缺什麼。
   - 哪個標題最後一行只剩一個字，建議刪哪個字。
   - 文案裡哪個數字要先確認。

   看完回覆你的決定。
2. **文案確認後**：Notion 票開好，或給你可以直接貼進去的票內文。
3. **頁面做好後**，專案資料夾的 `out/` 裡會有：
   - `上稿指南.html`：**打開它照著做**。貼哪一格、表單怎麼設、尺寸、驗收清單都在裡面，每段程式碼都有「複製」按鈕。
   - `preview.html`：在自己電腦上先看頁面長怎樣。
   - `上傳用/`：要上傳到 Instapage 的 OG 圖和標題描述文字。
   - `images/`：社群圖 1200×1200（PNG＋向量 PDF，給設計師存 .ai）。

## 四、你自己要做的

1. 在 Instapage 照上稿指南操作：
   - 複製 nova-webinar 頁。
   - 貼三段程式碼。
   - 設表單、接 Zapier、設送出後導向。
   - 換標題、描述與縮圖。
   - 先發布到**測試網址**。

   Claude 不會登入你的 Instapage，也不會幫你按發布。
2. 發布後跟 Claude 說「發布了，網址是 events.alleypin.com/xxx 和 xxx-thankyou」，它會檢查：
   - 有沒有漏換標題、OG。
   - 有沒有接 Zapier。
   - 送出後是不是跳到這次的感謝頁。
   - 手機版有沒有殘留上一檔活動的文字。
3. 自己送一筆測試報名、用手機點一次報名按鈕，確認名單有進來。

## 五、什麼時候要找 Hsing

- 清單上標「需 Hsing 複查」的項目：成效數字、「唯一／最強」這類說法、醫療相關宣稱、金融條件。這些一定要 Hsing 看過才發。
- 要畫 PinFriends 角色、但你的電腦沒有 Codex。
- Instapage 帳號權限、Zapier 要接哪一組。

## 六、常見狀況

| 狀況 | 怎麼辦 |
|---|---|
| 截圖或社群圖出不來 | 沒裝 ImageMagick：`brew install imagemagick` |
| 預覽的字型跟設計不一樣 | 字型從 Google Fonts 抓，要有網路 |
| 改了 Instapage 後台的字，顯示成別的字型 | 跟 Claude 說改了哪些字，它重產程式碼補上字型 |
| 想改頁面上的字 | 跟 Claude 說，它改完會告訴你「要重貼哪幾格」 |
