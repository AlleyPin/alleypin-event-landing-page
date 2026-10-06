#!/bin/bash
# 打包給同事安裝的 zip，並做發佈前檢查。
# 用法：bash tools/release.sh [輸出資料夾]
#   預設輸出到 ~/Desktop/AlleyPin/AlleyPin Claude/alleypin-event-landing-page 安裝包/
#   產出兩份內容相同的 zip：留檔用的「_日期」版，以及上傳 GitHub Release 用的固定檔名版。
# 只打包白名單：SKILL.md、QUICKSTART.md、references/、scripts/、assets/。
# tools/、evals/、MAINTENANCE.md、README.md 是維護者或 GitHub 首頁用的，不進安裝包。
# 任何一項檢查失敗：刪掉剛打的 zip、印出原因、exit 1。
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
NAME="alleypin-event-landing-page"
OUT_DIR="${1:-$HOME/Desktop/AlleyPin/AlleyPin Claude/alleypin-event-landing-page 安裝包}"
STAMP="$(date +%Y%m%d)"
ZIP="$OUT_DIR/${NAME}_${STAMP}.zip"

fail() { echo "❌ 發佈中止：$1" >&2; rm -f "$ZIP"; exit 1; }

STAGE="$(mktemp -d)"; trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/$NAME" "$OUT_DIR"
cd "$SKILL_DIR"
for f in SKILL.md QUICKSTART.md; do [ -f "$f" ] || fail "缺少 $f"; cp "$f" "$STAGE/$NAME/"; done
for d in references scripts assets; do [ -d "$d" ] || fail "缺少 $d/"; cp -R "$d" "$STAGE/$NAME/"; done
find "$STAGE" \( -name '.DS_Store' -o -name '__pycache__' \) -prune -exec rm -rf {} +

rm -f "$ZIP"
(cd "$STAGE" && zip -qr -X "$ZIP" "$NAME")

python3 "$SKILL_DIR/tools/verify_package.py" "$ZIP" || fail "verify_package.py 沒通過（原因見上方）"

# GitHub Release 要上傳固定檔名的這份，README 的 releases/latest/download/ 連結才會永遠指到最新版
UPLOAD="$OUT_DIR/${NAME}.zip"
cp "$ZIP" "$UPLOAD"
echo "✅ 打包完成：$ZIP"
echo "   上傳 GitHub Release 用：$UPLOAD（檔名不要改）"
