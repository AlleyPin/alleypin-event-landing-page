# AlleyPin 活動報名頁 skill（Instapage）

貼上活動資訊，Claude 就幫你做完一整套 events.alleypin.com 的活動報名頁：
- 頁面文案（行銷開票中心的票格式）、Notion 開票
- 活動頁與感謝頁的程式碼（貼進 Instapage 就能用）
- OG 圖、社群圖、照著做就能上稿的「上稿指南」
- 上線後的設定檢查（表單導向、Zapier、分享預覽、複製頁殘留的舊內容）

**需要 Claude Code**（Claude 桌面 App 的「Code」分頁，或終端機的 `claude`）。claude.ai 網頁版的一般聊天不行：這個 skill 要在你的電腦上跑 Chrome 截圖與檢查。

## 安裝

### 最簡單：直接貼這句給 Claude Code

> 幫我安裝這個 skill：`git clone https://github.com/AlleyPin/alleypin-event-landing-page.git ~/.claude/skills/alleypin-event-landing-page`，裝好後幫我檢查做活動頁的環境。

之後要更新，跟它說「幫我 git pull 更新 alleypin-event-landing-page skill」。

### 或下載安裝包

### 👉 [下載安裝包 alleypin-event-landing-page.zip](https://github.com/AlleyPin/alleypin-event-landing-page/releases/latest/download/alleypin-event-landing-page.zip)

這個連結永遠指向最新版。解壓縮後，把 `alleypin-event-landing-page` 資料夾放進 `~/.claude/skills/`，重開 Claude Code。

⚠️ **不要用綠色的「Code → Download ZIP」**：那樣下載的資料夾會叫 `alleypin-event-landing-page-main`，跟 skill 名稱不一致。請用上面的連結或 git clone。

## 怎麼用

看 [QUICKSTART.md](QUICKSTART.md)：裡面有一份活動資訊填空模板，填完貼給 Claude 就開始。

## 維護

維護者：Hsing。發佈流程見 [MAINTENANCE.md](MAINTENANCE.md)。
