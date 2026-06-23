#!/usr/bin/env python3
# Generates a self-contained code-browser page (code.html) from the bundled
# code/ package. Every file is embedded as base64 and rendered inline (no
# out-links to raw files).
import base64, json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))  # repo root (folder containing this script)
CODE = os.path.join(ROOT, "code")
OUT  = os.path.join(ROOT, "code.html")
DRIVE = "https://drive.google.com/drive/folders/1C_Oe4YrnoQ_YkCjxdLaRgnmEOLm1c8Au?usp=share_link"

# group order + labels
GROUPS = [
    ("overview", "套件總覽"),
    ("alpha",    "α · ALPHA"),
    ("beta",     "β · BETA（exp 03）"),
    ("gamma",    "γ · GAMMA（exp 04–08）"),
    ("beta_prime","β′ · BETA′（exp 12）"),
    ("theta",    "θ · THETA（exp 15 / 15A）"),
    ("tools",    "共用工具 TOOLS"),
    ("validation","驗證 VALIDATION"),
    ("specs",    "設計規格 SPECS"),
]

# explicit file order + descriptions (path relative to code/)
FILES_ORDER = [
    ("README.md", "overview", "套件總覽與閱讀順序"),
    ("requirements.txt", "overview", "Python 套件需求"),

    ("alpha/README.md", "alpha", "Alpha 模型說明（自寫 TD3 起點）"),
    ("alpha/train_alpha.py", "alpha", "Alpha 訓練腳本（自寫 PyTorch TD3）"),
    ("alpha/test_alpha.py", "alpha", "Alpha 測試／錄影腳本"),

    ("beta/README.md", "beta", "Beta 模型說明（SB3 TD3 + 步態 wrapper）"),
    ("beta/train_beta.py", "beta", "Beta 訓練腳本（exp 03 自然步態）"),
    ("beta/test_beta.py", "beta", "Beta 測試／評估腳本"),

    ("gamma/README.md", "gamma", "Gamma reward 搜尋線說明（04–08）"),
    ("gamma/gamma_progress_base.py", "gamma", "progress 基礎 reward（04）"),
    ("gamma/gamma_tent_speed.py", "gamma", "tent 速度閘（06）"),
    ("gamma/gamma_speed_balanced.py", "gamma", "速度平衡（07）"),
    ("gamma/gamma_proxy_best.py", "gamma", "步態代理指標最佳（08）"),
    ("gamma/gamma_fusion.py", "gamma", "gamma 融合設定"),

    ("beta_prime/README.md", "beta_prime", "Beta Prime 說明（gate 微調）"),
    ("beta_prime/finetune_beta_prime.py", "beta_prime", "載入 03 後 gait gate 微調（exp 12）"),

    ("theta/README.md", "theta", "Theta 說明（ctrl curriculum）"),
    ("theta/train_theta.py", "theta", "Theta 訓練腳本（exp 15／15A）"),

    ("tools/README.md", "tools", "共用工具說明"),
    ("tools/td3_agent.py", "tools", "TD3 agent（actor／critic 更新）"),
    ("tools/networks.py", "tools", "Actor / Critic 網路定義"),
    ("tools/replay_buffer.py", "tools", "Replay buffer"),
    ("tools/gait_wrapper_03.py", "tools", "步態 reward wrapper（核心 reward shaping）"),
    ("tools/gait_metrics.py", "tools", "九大指標計算"),
    ("tools/gait_train.py", "tools", "共用訓練骨架"),
    ("tools/__init__.py", "tools", "套件初始化"),

    ("validation/README.md", "validation", "驗證腳本說明"),
    ("validation/eval_scorecard.py", "validation", "九大指標 scorecard 評估"),
    ("validation/multiseed_validation.py", "validation", "multi-seed 重現性驗證（exp 13）"),

    ("specs/README.md", "specs", "設計規格索引"),
    ("specs/beta_original_spec.md", "specs", "Beta 原始設計規格"),
    ("specs/alpha_reward_modifications.md", "specs", "Alpha reward 修改"),
    ("specs/alpha_reward_attractor_fix.md", "specs", "Alpha reward attractor 修正"),
    ("specs/gamma_reward_search_spec.md", "specs", "Gamma reward 搜尋規格"),
    ("specs/beta_prime_followup_failed_spec.md", "specs", "Beta Prime 後續（失敗）實驗規格"),
]

def lang_of(path):
    if path.endswith(".py"): return "py"
    if path.endswith(".md"): return "md"
    if path.endswith(".html"): return "html"
    if path.endswith(".csv"): return "csv"
    return "txt"

# scrub the personal folder names from displayed content (display-only; original files untouched)
def scrub(txt):
    return (txt.replace("RLAP_TD3_for_teacher", "電腦與物理_TD3")
               .replace("RLAP_TD3_TB_analysis", "電腦與物理_TB分析")
               .replace("RLAP_AI_usage_report", "電腦與物理_AI紀錄")
               .replace("RLAP", "電腦與物理"))

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__PAGE_TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&family=Noto+Serif+TC:wght@600;700;900&display=swap" rel="stylesheet">
<style>
  :root{
    --ink:#1a2520; --muted:#5f6f68; --paper:#f5f3ec; --panel:#fffdf8;
    --sage:#e8efe5; --sage-line:#cdddc8; --deep:#1f4e5a; --deep-2:#2b5f6c;
    --coral-ink:#b5482e; --green:#2f8f4e; --line:#ddd7c8; --sand:#e7c9a3;
    --serif:"Noto Serif TC","Songti TC",serif;
    --sans:"Noto Sans TC",-apple-system,BlinkMacSystemFont,"PingFang TC","Microsoft JhengHei","Segoe UI",Roboto,sans-serif;
    --mono:ui-monospace,"SF Mono",Menlo,Consolas,"Roboto Mono",monospace;
    --topbar:58px; --side:300px;
  }
  *{box-sizing:border-box}
  body{margin:0;font-family:var(--sans);color:var(--ink);background:var(--paper);-webkit-font-smoothing:antialiased}
  a{color:var(--deep);text-decoration:none}
  /* top bar */
  .top{position:fixed;inset:0 0 auto 0;height:var(--topbar);z-index:30;display:flex;align-items:center;gap:14px;padding:0 18px;background:rgba(31,78,90,.97);backdrop-filter:blur(8px);color:#fff;box-shadow:0 4px 16px rgba(0,0,0,.16)}
  .top .back{color:#cfe1e4;font-size:13.5px;font-weight:600;padding:7px 12px;border-radius:8px;border:1px solid rgba(255,255,255,.18)}
  .top .back:hover{background:rgba(255,255,255,.12);color:#fff}
  .top .tt{font-family:var(--serif);font-weight:700;font-size:16px}
  .top .tt small{font-family:var(--sans);font-weight:400;color:#bcd3d8;font-size:11.5px;margin-left:8px;letter-spacing:.04em}
  .top .gdrive{margin-left:auto;color:#cfe1e4;font-size:13px;font-weight:600;padding:7px 13px;border-radius:8px;border:1px solid rgba(255,255,255,.20)}
  .top .gdrive:hover{background:rgba(255,255,255,.12);color:#fff;text-decoration:none}
  .top .menu{margin-left:8px;display:none;background:none;border:1px solid rgba(255,255,255,.25);color:#fff;border-radius:8px;width:38px;height:34px;font-size:18px;cursor:pointer}
  /* layout */
  .layout{display:flex;padding-top:var(--topbar);min-height:100vh}
  .side{width:var(--side);flex:none;border-right:1px solid var(--line);background:#fbfaf4;position:sticky;top:var(--topbar);align-self:flex-start;height:calc(100vh - var(--topbar));overflow-y:auto;padding:14px 10px 40px}
  .grp{margin:6px 0 2px}
  .grp>summary{list-style:none;cursor:pointer;padding:8px 10px;font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--coral-ink);display:flex;align-items:center;gap:8px;border-radius:8px}
  .grp>summary::-webkit-details-marker{display:none}
  .grp>summary::before{content:"▸";color:var(--muted);font-size:10px;transition:.15s}
  .grp[open]>summary::before{transform:rotate(90deg)}
  .grp>summary:hover{background:#f0efe6}
  .file{display:block;padding:7px 10px 7px 26px;border-radius:8px;font-size:13.5px;color:#33433d;cursor:pointer;font-family:var(--mono);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .file:hover{background:#eef2ec}
  .file.active{background:var(--deep);color:#fff}
  .file .ext{opacity:.55;font-size:11px}
  .file.active .ext{opacity:.8}
  /* main */
  .main{flex:1;min-width:0;padding:26px clamp(16px,3vw,40px) 80px}
  .crumb{font-family:var(--mono);font-size:13px;color:var(--muted);margin:0 0 4px}
  .crumb b{color:var(--ink)}
  .fdesc{font-size:14px;color:var(--muted);margin:0 0 18px}
  .viewer{background:var(--panel);border:1px solid var(--line);border-radius:14px;box-shadow:0 6px 22px rgba(31,78,90,.07);overflow:hidden}
  /* code view */
  .codewrap{display:flex;font-family:var(--mono);font-size:13px;line-height:1.7;overflow-x:auto;background:#15201d}
  .gutter{flex:none;text-align:right;padding:16px 12px 16px 16px;color:#52645d;user-select:none;background:#111a18;white-space:pre}
  .code{flex:1;padding:16px 18px;color:#dfeae3;white-space:pre;min-width:0}
  .code .k{color:#e0a978}.code .s{color:#9ec98a}.code .c{color:#6f877f;font-style:italic}.code .n{color:#d6b06a}.code .d{color:#86b2bb}
  /* markdown view */
  .md{padding:30px clamp(20px,3vw,46px);max-width:900px;line-height:1.8;color:var(--ink)}
  .md h2{font-family:var(--serif);font-size:25px;margin:30px 0 12px;border-bottom:2px solid var(--sage-line);padding-bottom:8px}
  .md h2:first-child{margin-top:0}
  .md h3{font-family:var(--serif);font-size:20px;margin:24px 0 10px}
  .md h4{font-family:var(--serif);font-size:16.5px;margin:18px 0 8px;color:var(--deep)}
  .md h5{font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--coral-ink);margin:16px 0 6px}
  .md p{margin:10px 0}
  .md ul,.md ol{margin:10px 0;padding-left:24px}
  .md li{margin:4px 0}
  .md code{font-family:var(--mono);font-size:12.5px;background:#eef2ec;border:1px solid var(--line);border-radius:5px;padding:1px 6px}
  .md pre{background:#15201d;border-radius:10px;padding:14px 16px;overflow-x:auto;margin:14px 0}
  .md pre code{background:none;border:none;color:#dfeae3;padding:0;font-size:12.5px;line-height:1.7;display:block;white-space:pre}
  .md blockquote{margin:14px 0;padding:8px 16px;border-left:4px solid var(--sage-line);background:var(--sage);border-radius:0 8px 8px 0;color:#33433d}
  .md hr{border:none;border-top:1px solid var(--line);margin:24px 0}
  .md a{color:var(--deep);text-decoration:underline}
  .md table{border-collapse:collapse;width:100%;margin:14px 0;font-size:13.5px;display:block;overflow-x:auto}
  .md th,.md td{border:1px solid var(--line);padding:8px 12px;text-align:left;vertical-align:top}
  .md thead th{background:var(--deep);color:#fff;white-space:nowrap}
  .md tbody tr:nth-child(even){background:#faf9f3}
  /* csv table */
  .csv{padding:24px;overflow-x:auto}
  .csv table{border-collapse:collapse;font-family:var(--mono);font-size:12.5px}
  .csv th,.csv td{border:1px solid var(--line);padding:6px 12px;text-align:right;white-space:nowrap}
  .csv thead th{background:var(--deep);color:#fff;position:sticky;top:0}
  .csv td:first-child,.csv th:first-child{text-align:left}
  /* html report iframe */
  .iframewrap{padding:0}
  .iframewrap .bar{display:flex;align-items:center;gap:10px;padding:12px 18px;background:var(--sage);border-bottom:1px solid var(--sage-line);font-size:13px;color:#33433d}
  .iframewrap iframe{display:block;width:100%;height:78vh;border:0;background:#fff}
  /* welcome */
  .welcome{padding:40px clamp(20px,3vw,46px);max-width:820px}
  .welcome h1{font-family:var(--serif);font-size:30px;margin:0 0 10px}
  .welcome p{color:var(--muted);line-height:1.8}
  .welcome .hint{margin-top:18px;background:var(--sage);border:1px solid var(--sage-line);border-radius:12px;padding:16px 20px;font-size:14px;color:#33433d}
  .scrim{display:none}
  @media(max-width:820px){
    :root{--side:80vw}
    .top .menu{display:block}
    .side{position:fixed;top:var(--topbar);left:0;height:calc(100vh - var(--topbar));z-index:25;transform:translateX(-105%);transition:.22s;box-shadow:6px 0 24px rgba(0,0,0,.2)}
    .side.open{transform:none}
    .scrim.show{display:block;position:fixed;inset:var(--topbar) 0 0 0;background:rgba(0,0,0,.35);z-index:20}
  }
</style>
</head>
<body>
<div class="top">
  <a class="back" href="index.html">← 返回數據總覽</a>
  <span class="tt">__BAR_TITLE__<small>__SUBTITLE__</small></span>
  <a class="gdrive" href="__DRIVE__" target="_blank" rel="noopener">☁ 雲端硬碟</a>
  <button class="menu" id="menuBtn" aria-label="檔案列表">☰</button>
</div>
<div class="layout">
  <aside class="side" id="side"></aside>
  <div class="scrim" id="scrim"></div>
  <main class="main" id="main">
    <div class="welcome">
      <h1>__W_H1__</h1>
      <p>__W_BODY__</p>
      <div class="hint">__W_HINT__</div>
    </div>
  </main>
</div>

<script id="manifest" type="application/json">__MANIFEST__</script>
<script id="files" type="application/json">__FILES__</script>
<script>
const MANIFEST = JSON.parse(document.getElementById('manifest').textContent);
const FILES = JSON.parse(document.getElementById('files').textContent);
const GROUPS = __GROUPS__;

function decode(id){
  const b = FILES[id]; if(b==null) return '';
  const bytes = Uint8Array.from(atob(b), c => c.charCodeAt(0));
  return new TextDecoder('utf-8').decode(bytes);
}
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

/* ---- python highlight (operates on escaped text) ---- */
const PY_KW = "False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield|self|print";
const PY_RE = new RegExp(
  "(#[^\\n]*)" +
  "|((?:[rRbBfFuU]{0,2})(?:\"\"\"[\\s\\S]*?\"\"\"|'''[\\s\\S]*?'''|\"(?:\\\\.|[^\"\\\\\\n])*\"|'(?:\\\\.|[^'\\\\\\n])*'))" +
  "|(@[\\w.]+)" +
  "|(\\b\\d[\\w.]*\\b)" +
  "|(\\b(?:" + PY_KW + ")\\b)", "g");
function highlightPy(text){
  const e = esc(text);
  return e.replace(PY_RE, (m,c,s,d,n,k)=>{
    if(c!=null) return '<span class="c">'+c+'</span>';
    if(s!=null) return '<span class="s">'+s+'</span>';
    if(d!=null) return '<span class="d">'+d+'</span>';
    if(n!=null) return '<span class="n">'+n+'</span>';
    if(k!=null) return '<span class="k">'+k+'</span>';
    return m;
  });
}
/* ---- inline markdown ---- */
function mdInline(s){
  // s is already HTML-escaped
  let out='', i=0;
  // protect inline code first
  const parts = s.split('`');
  for(let p=0;p<parts.length;p++){
    if(p%2===1){ out += '<code>'+parts[p]+'</code>'; }
    else{
      let t = parts[p];
      t = t.replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>');
      t = t.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
      t = t.replace(/__([^_]+)__/g,'<strong>$1</strong>');
      t = t.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g,'$1<em>$2</em>');
      out += t;
    }
  }
  return out;
}
/* ---- block markdown ---- */
function renderMarkdown(src){
  const lines = src.replace(/\r\n/g,'\n').split('\n');
  let html='', i=0;
  const isTableSep = l => /^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$/.test(l) && l.includes('-');
  const cells = l => { let s=l.trim(); if(s.startsWith('|'))s=s.slice(1); if(s.endsWith('|'))s=s.slice(0,-1); return s.split('|').map(c=>c.trim()); };
  while(i<lines.length){
    let l = lines[i];
    if(/^```/.test(l)){           // fenced code
      i++; let buf=[];
      while(i<lines.length && !/^```/.test(lines[i])){ buf.push(lines[i]); i++; }
      i++; html += '<pre><code>'+esc(buf.join('\n'))+'</code></pre>'; continue;
    }
    if(/^\s*$/.test(l)){ i++; continue; }
    let h = l.match(/^(#{1,6})\s+(.*)$/);
    if(h){ const lv=Math.min(h[1].length+1,5); html += '<h'+lv+'>'+mdInline(esc(h[2]))+'</h'+lv+'>'; i++; continue; }
    if(/^(-{3,}|\*{3,}|_{3,})\s*$/.test(l)){ html += '<hr>'; i++; continue; }
    if(l.includes('|') && i+1<lines.length && isTableSep(lines[i+1])){   // table
      const head=cells(l); i+=2; let rows=[];
      while(i<lines.length && lines[i].includes('|') && !/^\s*$/.test(lines[i])){ rows.push(cells(lines[i])); i++; }
      html += '<table><thead><tr>'+head.map(c=>'<th>'+mdInline(esc(c))+'</th>').join('')+'</tr></thead><tbody>'
            + rows.map(r=>'<tr>'+r.map(c=>'<td>'+mdInline(esc(c))+'</td>').join('')+'</tr>').join('')+'</tbody></table>';
      continue;
    }
    if(/^>\s?/.test(l)){          // blockquote
      let buf=[];
      while(i<lines.length && /^>\s?/.test(lines[i])){ buf.push(lines[i].replace(/^>\s?/,'')); i++; }
      html += '<blockquote>'+mdInline(esc(buf.join(' ')))+'</blockquote>'; continue;
    }
    if(/^\s*[-*+]\s+/.test(l)){   // ul
      let buf=[];
      while(i<lines.length && /^\s*[-*+]\s+/.test(lines[i])){ buf.push(lines[i].replace(/^\s*[-*+]\s+/,'')); i++; }
      html += '<ul>'+buf.map(x=>'<li>'+mdInline(esc(x))+'</li>').join('')+'</ul>'; continue;
    }
    if(/^\s*\d+\.\s+/.test(l)){   // ol
      let buf=[];
      while(i<lines.length && /^\s*\d+\.\s+/.test(lines[i])){ buf.push(lines[i].replace(/^\s*\d+\.\s+/,'')); i++; }
      html += '<ol>'+buf.map(x=>'<li>'+mdInline(esc(x))+'</li>').join('')+'</ol>'; continue;
    }
    let buf=[];                    // paragraph
    while(i<lines.length && !/^\s*$/.test(lines[i]) && !/^(#{1,6}\s|```|>\s?|\s*[-*+]\s|\s*\d+\.\s)/.test(lines[i])
          && !(lines[i].includes('|') && i+1<lines.length && isTableSep(lines[i+1]))){ buf.push(lines[i]); i++; }
    html += '<p>'+mdInline(esc(buf.join(' ')))+'</p>';
  }
  return html;
}
/* ---- csv ---- */
function renderCSV(src){
  const rows = src.replace(/\r\n/g,'\n').trim().split('\n').map(r=>r.split(','));
  const head = rows.shift()||[];
  return '<div class="csv"><table><thead><tr>'+head.map(c=>'<th>'+esc(c)+'</th>').join('')
       + '</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(c=>'<td>'+esc(c)+'</td>').join('')+'</tr>').join('')
       + '</tbody></table></div>';
}

let blobUrl=null;
function show(entry){
  const main = document.getElementById('main');
  document.querySelectorAll('.file').forEach(f=>f.classList.toggle('active', f.dataset.id===entry.id));
  if(blobUrl){ URL.revokeObjectURL(blobUrl); blobUrl=null; }
  let body='';
  if(entry.lang==='py' || entry.lang==='txt'){
    const text = decode(entry.id);
    const n = text.split('\n').length;
    let gutter=''; for(let j=1;j<=n;j++) gutter += j+'\n';
    const code = entry.lang==='py' ? highlightPy(text) : esc(text);
    body = '<div class="viewer"><div class="codewrap"><div class="gutter">'+gutter+'</div><div class="code">'+code+'</div></div></div>';
  } else if(entry.lang==='md'){
    body = '<div class="viewer"><div class="md">'+renderMarkdown(decode(entry.id))+'</div></div>';
  } else if(entry.lang==='csv'){
    body = '<div class="viewer">'+renderCSV(decode(entry.id))+'</div>';
  } else if(entry.lang==='html'){
    const blob = new Blob([decode(entry.id)], {type:'text/html'});
    blobUrl = URL.createObjectURL(blob);
    body = '<div class="viewer iframewrap"><div class="bar">📄 網頁報告於下方內嵌顯示</div><iframe src="'+blobUrl+'"></iframe></div>';
  }
  main.innerHTML = '<p class="crumb">__CRUMB__ / <b>'+esc(entry.path)+'</b></p><p class="fdesc">'+esc(entry.desc||'')+'</p>'+body;
  main.scrollTop=0; window.scrollTo(0,0);
  if(window.innerWidth<=820) closeSide();
  location.hash = entry.id;
}

/* sidebar */
function buildTree(){
  const side = document.getElementById('side');
  GROUPS.forEach(([gid,label],idx)=>{
    const items = MANIFEST.filter(m=>m.group===gid);
    if(!items.length) return;
    const det = document.createElement('details'); det.className='grp'; if(idx<6) det.open=true;
    const sum = document.createElement('summary'); sum.textContent=label; det.appendChild(sum);
    items.forEach(m=>{
      const a=document.createElement('div'); a.className='file'; a.dataset.id=m.id;
      const dot=m.name.lastIndexOf('.');
      const base=dot>0?m.name.slice(0,dot):m.name, ext=dot>0?m.name.slice(dot):'';
      a.innerHTML = esc(base)+'<span class="ext">'+esc(ext)+'</span>';
      a.title = m.path+(m.desc?'  —  '+m.desc:'');
      a.addEventListener('click',()=>show(m));
      det.appendChild(a);
    });
    side.appendChild(det);
  });
}
buildTree();

/* mobile menu */
const side=document.getElementById('side'), scrim=document.getElementById('scrim');
function openSide(){side.classList.add('open');scrim.classList.add('show');}
function closeSide(){side.classList.remove('open');scrim.classList.remove('show');}
document.getElementById('menuBtn').addEventListener('click',openSide);
scrim.addEventListener('click',closeSide);

/* deep link */
const start = MANIFEST.find(m=>m.id===location.hash.slice(1));
if(start) show(start);
</script>
</body>
</html>
"""

def build(src_dir, out, page_title, bar_title, subtitle, w_h1, w_body, w_hint, crumb, groups, files_order):
    manifest, files = [], {}
    for path, group, desc in files_order:
        full = os.path.join(src_dir, path)
        if not os.path.exists(full):
            print("WARN missing:", out, path); continue
        with open(full, "rb") as f:
            raw = f.read()
        try:
            raw = scrub(raw.decode("utf-8")).encode("utf-8")
        except UnicodeDecodeError:
            pass
        fid = re.sub(r"[^a-zA-Z0-9]", "_", path)
        files[fid] = base64.b64encode(raw).decode("ascii")
        manifest.append({"id": fid, "path": path, "name": os.path.basename(path),
                         "group": group, "lang": lang_of(path), "desc": desc})
    html = (TEMPLATE
            .replace("__PAGE_TITLE__", page_title)
            .replace("__BAR_TITLE__", bar_title)
            .replace("__SUBTITLE__", subtitle)
            .replace("__W_H1__", w_h1)
            .replace("__W_BODY__", w_body)
            .replace("__W_HINT__", w_hint)
            .replace("__CRUMB__", crumb)
            .replace("__DRIVE__", DRIVE)
            .replace("__MANIFEST__", json.dumps(manifest, ensure_ascii=False))
            .replace("__FILES__", json.dumps(files, ensure_ascii=False))
            .replace("__GROUPS__", json.dumps(groups, ensure_ascii=False)))
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote %s | files: %d | %.1f KB" % (out, len(files), len(html) / 1024))


# ---------------- code.html ----------------
build(os.path.join(ROOT, "code"), os.path.join(ROOT, "code.html"),
      "程式碼專區 · 電腦與物理 · TD3 × Ant-v5", "程式碼專區",
      "電腦與物理 · TD3 × Ant-v5 期末專題",
      "TD3 × Ant-v5 程式碼套件",
      "這裡收錄期末專題完整的訓練程式碼、共用工具與 reward 設計規格。左側依模型分組，點選任一檔案即可<strong>直接在本頁閱讀</strong>，不會下載或跳出原始檔。",
      "建議閱讀順序：<b>套件總覽 README</b> → 各模型訓練腳本（α → β → γ → β′ → θ）→ <b>共用工具</b> 與 <b>驗證</b>。",
      "code", GROUPS, FILES_ORDER)

# ---------------- ai.html ----------------
AI_GROUPS = [
    ("overview", "總覽 OVERVIEW"),
    ("rules",    "AI 協作規範 RULES"),
    ("handoff",  "Prompt／交接 HANDOFF"),
    ("debug",    "Debug 日誌 LOGS"),
    ("specs",    "任務規格 SPECS"),
    ("tb",       "TensorBoard 分析"),
]
AI_FILES = [
    ("README.md", "overview", "本紀錄包導覽與閱讀順序"),
    ("AI_USAGE_REPORT.md", "overview", "AI 使用總報告：角色、貢獻、限制、人工決策"),
    ("DEBUG_JOURNAL.md", "overview", "Debug 日誌：九個主要 bug／failure mode"),
    ("AI_HANDOFF_RECORDS.md", "overview", "Claude／Codex／prompt／changelog 如何接力"),
    ("EVIDENCE_INDEX.md", "overview", "所有原始證據檔位置對照"),

    ("01_ai_rules/CLAUDE.md", "rules", "AI agent 協作規範與專案約束"),

    ("02_prompt_handoff/initial_project_prompt_and_plan.md", "handoff", "初期專案 prompt 與規劃"),
    ("02_prompt_handoff/project_context_summary.md", "handoff", "專案 context 摘要"),

    ("03_debug_logs/CHANGELOG_experiment_log.md", "debug", "多輪實驗 changelog（問題→修改→結果→下一步）"),
    ("03_debug_logs/alpha_training_run.log", "debug", "Alpha 訓練 log"),
    ("03_debug_logs/beta_training_run.log", "debug", "Beta 訓練 log"),

    ("04_specs_and_design/alpha_reward_modification_spec.md", "specs", "Alpha reward 修改規格"),
    ("04_specs_and_design/alpha_standing_attractor_debug.md", "specs", "Alpha 站著不動 attractor debug"),
    ("04_specs_and_design/beta_claude_task_spec.md", "specs", "Beta：Claude Code 任務規格"),
    ("04_specs_and_design/gamma_claude_task_spec.md", "specs", "Gamma：Claude Code 任務規格"),
    ("04_specs_and_design/beta_prime_followup_ai_spec.md", "specs", "BetaPrime 後續 AI 規格"),

    ("05_tb_analysis/model_analysis_from_tb.md", "tb", "從 TensorBoard 整理的模型分析"),
    ("05_tb_analysis/build_tb_analysis.py", "tb", "TensorBoard 分析產生器"),
    ("05_tb_analysis/data/final_scorecard.csv", "tb", "最終 scorecard 數據"),
]
build(os.path.join(ROOT, "ai_report"), os.path.join(ROOT, "ai.html"),
      "AI 協作與工作日誌 · 電腦與物理 · TD3 × Ant-v5", "AI 協作 · 工作日誌",
      "電腦與物理 · TD3 × Ant-v5 期末專題",
      "AI 協作與除錯紀錄",
      "本專題把 AI 當「協作研究助理」：AI 使用總報告、Debug 日誌、prompt／agent 交接、任務規格與 TensorBoard 分析。左側分組，點任一檔案即可<strong>直接在本頁閱讀</strong>。",
      "建議閱讀順序：<b>AI 使用總報告</b> → <b>Debug 日誌</b> → <b>交接紀錄</b> → 任務規格與訓練 log。",
      "ai", AI_GROUPS, AI_FILES)
