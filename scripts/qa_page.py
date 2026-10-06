#!/usr/bin/env python3
"""活動頁本機 QA：在 1440／1024／390 三個寬度量 out/preview*.html，把 Hsing 曾經用眼睛抓出來的問題變成自動檢查。

用法：python3 qa_page.py <專案資料夾> [--widths 1440,1024,390] [--pages campaign,thankyou] [--prefix ap] [--cta-var --ap-cta]
      class 前綴預設讀 src/site.json 的 prefix（沒有 site.json 的舊專案，例如 Cofit，要帶 --prefix cf --cta-var --cf-orange）。
      先跑 build.py 產生 out/preview.html。報告印在終端機，另存 out/qa_report.json。
      有任何 ❌ 就以 exit code 1 結束。⚠️ 是要人看一眼的提醒，不擋交件。

檢查項目（每一項都是一次真實退件）：
  橫向溢出   內容超出視窗（html 設了 overflow-x:clip，捲軸不會出現，但字會被切掉）
  禁用樣式   scroll-behavior:smooth（Instapage Cradle.js 錨點卡住）、text-wrap:pretty/balance、標題 word-break:keep-all
  孤字       標題、表單欄位標籤最後一行只剩一個字（❌）；內文段落（⚠️）。用刪字解，不用 CSS
  手機貼邊   390 寬時文字或卡片離螢幕邊緣 < 8px
  並排對齊   同一列的卡片，標題、說明的起始高度要在同一條線（subgrid）
  插圖浮空   場景圖底部的透明留白＋圖框底距 > 3px＝浮在空中（scene_crop.py 裁到桌底）；同組插圖寬度比例要一樣
  報名色     CTA 色（--ap-cta）只能出現在連結／按鈕上（時間膠囊撞造型那次）
  錨點       href="#…" 的目標都存在
  內容欄     Body／Footer 段落與報名區塊左右對齊同一條內容欄
  報名區塊   HTML 元件內容有沒有超出 layout.json 的高度；表單底部到區塊底的留白；換算成編輯器 px 給建議值
  其他       佔位字「〔待填」、字型是否載入、PNG 內嵌過大
鑑別力：2026-10-06 用 Cofit 上線版（應全過）與故意弄壞的版本（加平滑捲動、pretty、拿掉 subgrid、換回未裁的場景圖、
製造孤字、時間改橘色膠囊）驗過，弄壞的每一項都會被抓到。
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

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

QA_JS = r"""
(function(){
var PUNCT = /[\s，。、！？；：「」『』（）《》〈〉…—–\-,.!?;:()'"’”“‘·・｜|／/]/;
function desc(el){
  if(!el||!el.tagName) return '?';
  var c=(el.getAttribute('class')||'').trim().split(/\s+/).filter(Boolean).slice(0,2).join('.');
  var t=(el.textContent||'').replace(/\s+/g,' ').trim().slice(0,18);
  return el.tagName.toLowerCase()+(c?'.'+c:'')+(t?'「'+t+'」':'');
}
function hidden(el){ return !!el.closest('[aria-hidden="true"]'); }
function visible(el){ var r=el.getBoundingClientRect(); var cs=getComputedStyle(el); return r.width>0&&r.height>0&&cs.visibility!=='hidden'&&cs.display!=='none'; }
function rgb(color){ var d=document.createElement('div'); d.style.color=color; document.body.appendChild(d); var c=getComputedStyle(d).color; d.remove(); return c; }
function lines(el){
  // 每個字的位置 → 依 top 分行；回傳 [[字,...],...]
  var out=[], walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,null), n, range=document.createRange();
  var rows={};
  while((n=walker.nextNode())){
    if(n.parentElement.closest('[aria-hidden="true"]')) continue;
    if(n.parentElement.closest('.ap-no')) continue;   // 獨立一行的編號不算
    var s=n.textContent;
    for(var i=0;i<s.length;i++){
      var ch=s[i]; if(/\s/.test(ch)) continue;
      range.setStart(n,i); range.setEnd(n,i+1);
      var rs=range.getClientRects(); if(!rs.length) continue;
      var top=Math.round(rs[0].top+rs[0].height/2);
      var key=Object.keys(rows).find(function(k){return Math.abs(k-top)<6;});
      if(key===undefined){ key=top; rows[key]=[]; }
      rows[key].push(ch);
    }
  }
  return Object.keys(rows).map(Number).sort(function(a,b){return a-b;}).map(function(k){return rows[k];});
}
function run(){
  var R={width:innerWidth, root_px:parseFloat(getComputedStyle(document.documentElement).fontSize), fails:[], warns:[], info:{}};
  var F=function(k,m){R.fails.push([k,m]);}, W=function(k,m){R.warns.push([k,m]);};
  var all=[].slice.call(document.querySelectorAll('.ap *, form.email-form *, form.email-form, .ap'));

  // 1) 橫向溢出（排除滿版底色層與裝飾）
  all.forEach(function(el){
    if(el.closest('.ap-bleed')||hidden(el)||!visible(el)) return;
    var r=el.getBoundingClientRect();
    if(r.right>innerWidth+1.5||r.left<-1.5) F('橫向溢出', desc(el)+' 超出視窗 '+Math.round(Math.max(r.right-innerWidth,-r.left))+'px');
  });

  // 1b) 手機貼邊：文字或有框／有底色的卡片離螢幕邊緣 < 8px（段落少了 .ap-sec 的左右內距就會這樣）
  if(innerWidth<768){ var edge={};
    all.forEach(function(el){
      if(el.closest('.ap-bleed')||hidden(el)||!visible(el)) return;
      var cs=getComputedStyle(el), boxy=(cs.borderLeftStyle!=='none'&&parseFloat(cs.borderLeftWidth)>0)||(cs.backgroundColor!=='rgba(0, 0, 0, 0)'&&cs.backgroundColor!=='transparent');
      var texty=/^(H[1-4]|P|DD|DT|LI|A|LABEL)$/.test(el.tagName);
      if(!boxy&&!texty) return;
      var r=el.getBoundingClientRect();
      if(r.left<8||r.right>innerWidth-8){ var k=desc(el).split('「')[0]; if(!edge[k]){ edge[k]=1; F('手機貼邊', desc(el)+' 左 '+Math.round(r.left)+'／右 '+Math.round(innerWidth-r.right)+'px，離螢幕邊緣太近（放進 .ap-sec 或補左右內距）'); } }
    });
  }

  // 2) 禁用樣式
  if(getComputedStyle(document.documentElement).scrollBehavior==='smooth'||getComputedStyle(document.body).scrollBehavior==='smooth')
    F('禁用樣式','html/body 有 scroll-behavior:smooth（Instapage 錨點捲動會卡住）');
  var tw={};   // 同一個 class 只報一次（附數量），只看直接有文字的元素（br、svg 會繼承，不算）
  all.forEach(function(el){
    if(!/^(H[1-6]|P|DD|DT|LI|SPAN|A|B|STRONG|FIGCAPTION|LABEL)$/.test(el.tagName)) return;
    var cs=getComputedStyle(el), w=cs.textWrapStyle||cs.textWrap||'';
    var key=el.tagName.toLowerCase()+'.'+((el.getAttribute('class')||'').split(/\s+/)[0]||'');
    if(/pretty|balance/.test(w)){ (tw[key+' text-wrap:'+w]=tw[key+' text-wrap:'+w]||[]).push(el); }
    if(/^H[1-4]$/.test(el.tagName)&&cs.wordBreak==='keep-all'){ (tw[key+' word-break:keep-all（標題要齊寬換行）']=tw[key+' word-break:keep-all（標題要齊寬換行）']||[]).push(el); }
  });
  Object.keys(tw).forEach(function(k){ F('禁用樣式', k+' ×'+tw[k].length+'（例：'+desc(tw[k][0])+'）'); });

  // 3) 孤字
  // 原生表單的欄位標籤也算標題級：桌機兩欄時標籤折行、最後一行剩一個字，右欄輸入框還會因此低一截
  var heads=[].slice.call(document.querySelectorAll('.ap h1,.ap h2,.ap h3,.ap h4,.ap [class*="title"],.ap [class*="__name"],form.email-form .form-label-title:not(.form-label-checkbox)'));
  var paras=[].slice.call(document.querySelectorAll('.ap p,.ap dd,.ap li > p'));
  function orphan(el,isHead){
    if(hidden(el)||!visible(el)) return;
    var L=lines(el); if(L.length<2) return;
    var last=L[L.length-1].filter(function(c){return !PUNCT.test(c);});
    if(last.length<=1){ var msg=desc(el)+' 最後一行「'+L[L.length-1].join('')+'」（共 '+L.length+' 行）'; isHead?F('孤字',msg):W('孤字（內文）',msg); }
  }
  heads.forEach(function(el){ orphan(el,true); });
  paras.forEach(function(el){ if(!heads.some(function(h){return h.contains(el)||el.contains(h);})) orphan(el,false); });

  // 4) 並排對齊：grid 容器裡同一列的子項，第 k 個文字區塊的 top 要一致
  [].slice.call(document.querySelectorAll('.ap ul, .ap ol, .ap div')).forEach(function(box){
    var cs=getComputedStyle(box); if(cs.display!=='grid') return;
    var kids=[].slice.call(box.children).filter(visible); if(kids.length<2) return;
    var rows={}; kids.forEach(function(k){ var t=Math.round(k.getBoundingClientRect().top/4); (rows[t]=rows[t]||[]).push(k); });
    Object.keys(rows).forEach(function(t){
      var row=rows[t]; if(row.length<2) return;
      var parts=row.map(function(k){ return [].slice.call(k.querySelectorAll('h3,h4,p')).filter(function(e){return !hidden(e)&&visible(e)&&!e.closest('.ap-card__value');}); });
      var n=Math.min.apply(null,parts.map(function(p){return p.length;}));
      for(var i=0;i<n;i++){
        var tops=parts.map(function(p){return p[i].getBoundingClientRect().top;});
        var spread=Math.max.apply(null,tops)-Math.min.apply(null,tops);
        if(spread>2) F('並排對齊', desc(box)+' 同一列第 '+(i+1)+' 個文字區塊高低差 '+Math.round(spread)+'px（'+desc(parts[0][i])+'）→ 用 subgrid');
      }
    });
  });

  // 5) 插圖浮空與同組比例
  var groups={};
  [].slice.call(document.querySelectorAll('.ap [class*="__art"] img')).forEach(function(img){
    var frame=img.closest('[class*="__art"]'), fr=frame.getBoundingClientRect(), ir=img.getBoundingClientRect();
    var c=document.createElement('canvas'); c.width=img.naturalWidth; c.height=img.naturalHeight;
    var x=c.getContext('2d'); x.drawImage(img,0,0); var last=-1;
    try{
      var d=x.getImageData(0,0,c.width,c.height).data;
      for(var y=c.height-1;y>=0&&last<0;y--){ for(var xx=0;xx<c.width;xx++){ if(d[(y*c.width+xx)*4+3]>20){ last=y; break; } } }
    }catch(e){ W('插圖', desc(img)+' 讀不到像素（不是內嵌圖？）'); return; }
    var transparentBottom=(c.height-1-last)/c.height*ir.height;
    var gap=transparentBottom+(fr.bottom-ir.bottom);
    if(gap>3) F('插圖浮空', desc(frame.parentElement)+' 圖的內容底部離框底 '+Math.round(gap)+'px（用 tools/scene_crop.py 裁到桌底、CSS bottom:0）');
    var g=frame.parentElement.parentElement; var key=Array.prototype.indexOf.call(document.querySelectorAll('*'),g);
    (groups[key]=groups[key]||[]).push([desc(frame.parentElement), ir.width/fr.width]);
  });
  Object.keys(groups).forEach(function(k){ var g=groups[k]; if(g.length<2) return;
    var rs=g.map(function(a){return a[1];}); if(Math.max.apply(null,rs)-Math.min.apply(null,rs)>0.01)
      W('插圖比例','同一組插圖寬度比例不一致：'+g.map(function(a){return a[0]+' '+(a[1]*100).toFixed(1)+'%';}).join('；'));
  });

  // 6) 報名色只給按鈕
  var cta=getComputedStyle(document.documentElement).getPropertyValue('--ap-cta').trim();
  if(cta){ var ctaRgb=rgb(cta);
    all.forEach(function(el){ if(!visible(el)) return; var cs=getComputedStyle(el);
      if(cs.backgroundColor===ctaRgb && !el.closest('a,button')) F('報名色', desc(el)+' 不是按鈕卻用了報名色（橘色只留給報名按鈕）');
    });
  }

  // 7) 錨點
  [].slice.call(document.querySelectorAll('a[href^="#"]')).forEach(function(a){
    var id=a.getAttribute('href').slice(1); if(id&&!document.getElementById(id)) F('錨點', desc(a)+' 指向 #'+id+'，頁面上找不到');
  });

  // 8) 內容欄對齊
  var cols=[].slice.call(document.querySelectorAll('.ap-flow')).map(function(e){var r=e.getBoundingClientRect();return [desc(e),r.left,r.width];});
  var block=document.querySelector('.section-block .section-inner');
  if(block){ var br=block.getBoundingClientRect(); cols.push(['報名區塊內容欄',br.left,br.width]); }
  if(cols.length>1){ var l0=cols[0][1], w0=cols[0][2];
    cols.forEach(function(c){ if(Math.abs(c[1]-l0)>1||Math.abs(c[2]-w0)>1) F('內容欄', c[0]+' 左緣 '+Math.round(c[1])+'／寬 '+Math.round(c[2])+'，跟第一段（'+Math.round(l0)+'／'+Math.round(w0)+'）不同'); });
  }

  // 9) 報名區塊：內容高度 vs layout.json
  var scale=R.root_px/16, blocks=[];
  [].slice.call(document.querySelectorAll('section[id^="page-block-"]')).forEach(function(sec){
    var sr=sec.getBoundingClientRect(), info={id:sec.id, block_h:Math.round(sr.height/scale), elements:[]};
    [].slice.call(sec.querySelectorAll('.widget')).forEach(function(w){
      var wr=w.getBoundingClientRect(), bottom=wr.top;
      // 只量「內容」元素：元件根節點的高度是 layout.json 寫死的，量它等於量自己
      [].slice.call(w.querySelectorAll('h1,h2,h3,h4,p,dt,dd,li,img,svg,a,button,input,select,label,form,figure')).forEach(function(e){ if(e.closest('.ap-bleed')||hidden(e)||!visible(e)) return; bottom=Math.max(bottom,e.getBoundingClientRect().bottom); });
      var el={id:w.id, box_h:Math.round(wr.height/scale), content_h:Math.round((bottom-wr.top)/scale), content_bottom_in_block:Math.round((bottom-sr.top)/scale)};
      info.elements.push(el);
      if(w.id!=='element-form' && bottom>wr.bottom+1) F('報名區塊', w.id+' 內容高 '+el.content_h+' 超出元件高 '+el.box_h+'（編輯器 px），更新 layout.json');
    });
    var lowest=Math.max.apply(null,info.elements.map(function(e){return e.content_bottom_in_block;}));
    info.slack=info.block_h-lowest;
    var want=innerWidth>=768?96:64;
    info.suggest_block_h=lowest+want;
    if(info.slack<0) F('報名區塊', sec.id+' 內容超出區塊底 '+(-info.slack)+'（編輯器 px）→ 區塊高建議 '+info.suggest_block_h);
    else if(Math.abs(info.slack-want)>40) W('報名區塊', sec.id+' 內容底到區塊底留白 '+info.slack+'（建議約 '+want+'，區塊高可設 '+info.suggest_block_h+'）');
    blocks.push(info);
  });
  R.info.blocks=blocks;

  // 10) 其他
  var txt=document.body.innerText;
  if(txt.indexOf('〔待填')>=0) F('佔位字','頁面上還有「〔待填」：'+(txt.match(/〔待填[^〕]*〕/g)||[]).slice(0,5).join('、'));
  var fams={}; document.fonts.forEach(function(f){ if(f.status==='loaded') fams[f.family.replace(/["']/g,'')]=1; });
  R.info.fonts_loaded=Object.keys(fams);
  var disp=getComputedStyle(document.documentElement).getPropertyValue('--ap-font-display').split(',')[0].replace(/["'\s]/g,'');
  if(disp && !Object.keys(fams).some(function(f){return f.replace(/\s/g,'')===disp;})) W('字型', '標題字型 '+disp+' 沒載入（沒網路，或 site.json 的 fonts 參數不對）；孤字與對齊結果可能跟線上不同');
  [].slice.call(document.querySelectorAll('img')).forEach(function(img){ var s=img.getAttribute('src')||''; if(/^data:image\/png/.test(s)&&s.length>200000) W('圖片', desc(img)+' 是 '+Math.round(s.length/1370)+'KB 的 PNG，轉 WebP 會小很多'); });
  parent.postMessage(JSON.stringify(R),'*');
}
window.addEventListener('load',function(){ document.fonts.ready.then(function(){ setTimeout(run,400); }); });
})();
"""


def js_for(prefix: str, cta_var: str) -> str:
    js = re.sub(r"\.ap\b", "." + prefix, QA_JS).replace("--ap-font-display", f"--{prefix}-font-display")
    return js.replace("'--ap-cta'", repr(cta_var))


def measure(preview: Path, width: int, js: str) -> dict:
    with tempfile.TemporaryDirectory(dir=preview.parent) as td:
        td = Path(td)
        page = td / "page.html"
        page.write_text(preview.read_text(encoding="utf-8").replace("</body>", f"<script>{js}</script></body>"), encoding="utf-8")
        wrap = td / "wrap.html"
        wrap.write_text(f'<!doctype html><body style="margin:0"><pre id="qa">pending</pre>'
                        f'<iframe src="page.html" style="display:block;width:{width}px;height:1000px;border:0"></iframe>'
                        "<script>addEventListener('message',function(e){document.getElementById('qa').textContent=e.data;});</script></body>",
                        encoding="utf-8")
        # 無頭 Chrome 視窗最小寬約 500px，所以 390 寬用 iframe 包；量測結果用 postMessage 回到外層、--dump-dom 印出來
        # --use-mock-keychain：不碰 macOS 鑰匙圈。不要加 --user-data-dir（實測 Chrome 寫完結果不會結束、卡到逾時）
        cmd = [CHROME, "--headless=new", "--use-mock-keychain", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=15000",
               f"--window-size={max(width, 600)},1100", "--dump-dom", wrap.as_uri()]
        for attempt in (1, 2):
            try:
                out = subprocess.run(cmd, capture_output=True, text=True, timeout=90).stdout
                break
            except subprocess.TimeoutExpired:   # 無頭 Chrome 偶爾會卡死：subprocess 已砍掉這個 Chrome，重試一次
                out = ""
        m = re.search(r'<pre id="qa">(.*?)</pre>', out, re.S)
        if not m or m.group(1) == "pending":
            return {"width": width, "fails": [["量測", "量測沒有回來（頁面載入逾時或 JS 錯誤）"]], "warns": [], "info": {}}
        import html as _h
        return json.loads(_h.unescape(m.group(1)))


def main():
    if not CHROME:
        sys.exit("找不到 Google Chrome：QA 要用它量頁面。裝好 Chrome，或用環境變數 CHROME_PATH 指到執行檔。")
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(2)
    proj = Path(args[0]).expanduser().resolve()
    opt = lambda k, d: next((args[i + 1] for i, a in enumerate(args) if a == k and i + 1 < len(args)), d)
    widths = [int(w) for w in opt("--widths", "1440,1024,390").split(",")]
    layout = json.loads((proj / "src" / "layout.json").read_text(encoding="utf-8"))
    want = opt("--pages", ",".join(p["id"] for p in layout["pages"])).split(",")
    site = proj / "src" / "site.json"
    prefix = opt("--prefix", json.loads(site.read_text(encoding="utf-8")).get("prefix", "ap") if site.exists() else "ap")
    js = js_for(prefix, opt("--cta-var", f"--{prefix}-cta"))
    report, n_fail, n_warn = {}, 0, 0
    for page in layout["pages"]:
        if page["id"] not in want:
            continue
        prev = proj / "out" / page["preview"]
        if not prev.exists():
            print(f"找不到 {prev}，先跑 build.py"); sys.exit(2)
        report[page["id"]] = {}
        for w in widths:
            r = measure(prev, w, js)
            report[page["id"]][w] = r
            print(f"\n== {page['short']}｜{w} 寬（根字級 {r.get('root_px', '?')}px）")
            for k, m in r["fails"]:
                print(f"  ❌ {k}：{m}")
            for k, m in r["warns"]:
                print(f"  ⚠️ {k}：{m}")
            for b in r.get("info", {}).get("blocks", []):
                els = "；".join(f"{e['id']} 內容高 {e['content_h']}／元件高 {e['box_h']}" for e in b["elements"])
                print(f"  ℹ️ {b['id']}：區塊高 {b['block_h']}、內容底留白 {b['slack']}（{els}）")
            if not r["fails"] and not r["warns"]:
                print("  ✅ 全部通過")
            n_fail += len(r["fails"]); n_warn += len(r["warns"])
    (proj / "out" / "qa_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n合計：❌ {n_fail}　⚠️ {n_warn}　（報告：{proj / 'out' / 'qa_report.json'}）")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
