#!/usr/bin/env python3
"""檢查 alleypin-event-landing-page 安裝包（zip）能不能被正常安裝、使用。

用法：python3 tools/verify_package.py <zip> [--max-files 150] [--max-mb 20]
任何一項不通過就印出原因並 exit 1。

檢查項目：
 1. zip 最上層只有一個資料夾，名稱等於 skill 名稱
 2. SKILL.md frontmatter：name 規格、description 長度
 3. 檔案數、未壓縮總大小（skill 安裝功能有 200 檔硬上限，紅線抓 150）
 4. 沒有夾帶維護者檔案（tools/、evals/、MAINTENANCE.md、README.md、.git、.DS_Store、__pycache__）
 5. 沒有寫死某台電腦的絕對路徑（/Users/<名字>/）
 6. SKILL.md 與 references 提到的 references／scripts 檔案都在包裡
 7. 所有 .py 都能編譯
 8. 實際跑一次：解壓縮 → new_project.py 開專案到暫存資料夾 → build.py（不截圖、不開 Chrome）→ 五段貼上用程式碼都產出
"""
import argparse, py_compile, re, subprocess, sys, tempfile, zipfile
from pathlib import Path

NAME = "alleypin-event-landing-page"
ap = argparse.ArgumentParser()
ap.add_argument("zip")
ap.add_argument("--max-files", type=int, default=150)
ap.add_argument("--max-mb", type=float, default=20)
a = ap.parse_args()

errors = []
z = zipfile.ZipFile(a.zip)
infos = [i for i in z.infolist() if not i.is_dir()]
names = [i.filename for i in infos]

# 1
tops = {n.split("/")[0] for n in z.namelist()}
if tops != {NAME}:
    errors.append(f"zip 最上層應該只有 {NAME}/，實際是 {sorted(tops)}")
rel = {n[len(NAME) + 1:]: n for n in names if n.startswith(NAME + "/")}

# 2
skill = z.read(rel["SKILL.md"]).decode("utf-8") if "SKILL.md" in rel else ""
if not skill:
    errors.append("缺少 SKILL.md")
else:
    m = re.match(r"^---\n(.*?)\n---\n", skill, re.S)
    fm = m.group(1) if m else ""
    name = (re.search(r"^name:\s*(.+)$", fm, re.M) or [None, ""])[1].strip()
    desc = (re.search(r"^description:\s*(.+)$", fm, re.M) or [None, ""])[1].strip()
    if name != NAME:
        errors.append(f"frontmatter name「{name}」跟資料夾名稱不一致")
    if not desc or len(desc) > 1024:
        errors.append(f"description 長度 {len(desc)}（要 1–1024）")

# 3
total = sum(i.file_size for i in infos)
if len(infos) > a.max_files:
    errors.append(f"{len(infos)} 個檔，超過紅線 {a.max_files}")
if total > a.max_mb * 1024 * 1024:
    errors.append(f"未壓縮 {total / 1024 / 1024:.1f} MB，超過 {a.max_mb} MB")

# 4
bad = [n for n in rel if re.match(r"(tools|evals)/|MAINTENANCE\.md$|README\.md$", n)
       or re.search(r"(^|/)(\.git|\.DS_Store|__pycache__)(/|$)", n)]
if bad:
    errors.append(f"夾帶維護者或系統檔案：{bad[:5]}")

# 5
for n, full in rel.items():
    if n.endswith((".md", ".py", ".html", ".css", ".json", ".txt")):
        t = z.read(full).decode("utf-8", "replace")
        hit = re.search(r"/Users/[A-Za-z0-9._-]+/", t)
        if hit:
            errors.append(f"{n} 寫死了這台電腦的路徑：{hit.group(0)}")

# 6
docs = skill + "".join(z.read(f).decode("utf-8") for n, f in rel.items() if n.startswith("references/") and n.endswith(".md"))
for ref in sorted(set(re.findall(r"(?:references|scripts)/[\w.-]+\.(?:md|py)", docs))):
    if ref not in rel:
        errors.append(f"文件提到 {ref}，包裡找不到")

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    z.extractall(td)
    root = td / NAME
    # 7
    for py in root.rglob("*.py"):
        try:
            py_compile.compile(str(py), cfile=str(td / "x.pyc"), doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(f"{py.relative_to(root)} 編譯失敗：{e.msg[:100]}")
    # 8（不開 Chrome、不換 HOME）
    if (root / "scripts" / "new_project.py").exists():
        r = subprocess.run([sys.executable, str(root / "scripts" / "new_project.py"), "pkgtest", "--date", "2026-12-08",
                            "--root", str(td / "projects")], capture_output=True, text=True)
        proj = Path(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 and r.stdout.strip() else None
        if not proj or not proj.exists():
            errors.append(f"new_project.py 開專案失敗：{(r.stderr or r.stdout)[-200:]}")
        else:
            b = subprocess.run([sys.executable, "build.py"], cwd=proj, capture_output=True, text=True)
            want = ["1_head.html", "2_body.html", "3_signup-block.html", "4_footer.html", "ty_2_body.html"]
            missing = [w for w in want if not (proj / "out" / "instapage" / w).exists()]
            if b.returncode != 0 or missing:
                errors.append(f"build.py 失敗或缺片段 {missing}：{b.stderr[-200:]}")

print(f"檔案 {len(infos)} 個、未壓縮 {total / 1024:.0f} KB")
if errors:
    print("❌ 沒通過：")
    for e in errors:
        print("  - " + e)
    sys.exit(1)
print("✅ 8 項檢查全過")
