#!/usr/bin/env python3
"""Atlas v8 -> v9: the same content, re-set. Light 'chart paper' report: Public Sans headings, Source Serif 4 body, one
chart-blue accent, rules instead of cards, a sticky contents rail, ruled data tables with the best value marked, captions with
provenance, a reading-progress hairline, and a dark scheme that follows the viewer. No number is retyped: every figure comes
through the v2..v8 builders; this step only touches markup and style.  -> churchill_atlas_v9.html"""
import re, html
src = open("churchill_atlas_v8.html", encoding="utf-8").read()

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=IBM+Plex+Mono:wght@400;500&display=swap">'
CSS = r"""
<style>
:root{
  --paper:#f8f8f6; --paper-2:#f1f2ef; --ink:#15191d; --ink-2:#3b434b; --ink-3:#6b7480; --rule:#d9dcd8; --rule-2:#c3c7c2;
  --accent:#1f5f8b; --accent-ink:#174a6d; --accent-soft:#e3edf4;
  --good:#2e7d5b; --bad:#b3492b; --warn:#a2681c;
  --line:#c9cdc9; --muted:#6b7480; --blue:#1f5f8b; --amber:#a2681c; --hazard:#b3492b; --text:#15191d; --panel:#ffffff; --sigma:#6b4c9a;
  --sans:'Public Sans',system-ui,-apple-system,sans-serif; --serif:'Source Serif 4',Georgia,'Times New Roman',serif; --mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;
  --measure:66ch; --wide:940px; --rail:232px;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --paper:#121417; --paper-2:#191c20; --ink:#e6e8e6; --ink-2:#c3c8cc; --ink-3:#8d959d; --rule:#2a2f35; --rule-2:#3a4149;
  --accent:#7fb2d8; --accent-ink:#9cc4e3; --accent-soft:#1a2733; --good:#5fb08c; --bad:#d9775a; --warn:#d1a052;
  --line:#3a4149; --muted:#8d959d; --blue:#7fb2d8; --amber:#d1a052; --hazard:#d9775a; --text:#e6e8e6; --panel:#191c20; --sigma:#b39ddb;
}}
:root[data-theme="dark"]{
  --paper:#121417; --paper-2:#191c20; --ink:#e6e8e6; --ink-2:#c3c8cc; --ink-3:#8d959d; --rule:#2a2f35; --rule-2:#3a4149;
  --accent:#7fb2d8; --accent-ink:#9cc4e3; --accent-soft:#1a2733; --good:#5fb08c; --bad:#d9775a; --warn:#d1a052;
  --line:#3a4149; --muted:#8d959d; --blue:#7fb2d8; --amber:#d1a052; --hazard:#d9775a; --text:#e6e8e6; --panel:#191c20; --sigma:#b39ddb;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
@media (prefers-reduced-motion: reduce){ html{scroll-behavior:auto} }
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--serif);font-size:17.5px;line-height:1.58;font-variant-numeric:oldstyle-nums proportional-nums;text-rendering:optimizeLegibility}
a{color:var(--accent-ink);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:2px}
a:hover{color:var(--accent)}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
code{font-family:var(--mono);font-size:.86em;background:var(--paper-2);padding:.05em .3em;border-radius:3px;word-break:break-all}
#progress{position:fixed;top:0;left:0;height:2px;width:0;background:var(--accent);z-index:50}
.page{max-width:1240px;margin:0 auto;padding:0 28px}
/* masthead */
.mast{display:flex;justify-content:space-between;align-items:baseline;gap:20px;padding:18px 0 14px;border-bottom:1px solid var(--rule);font-family:var(--sans);font-size:13px;color:var(--ink-3);letter-spacing:.01em}
.mast b{color:var(--ink);font-weight:600}
.mast .links a{margin-left:18px;text-decoration:none;color:var(--ink-2)}
.mast .links a:hover{color:var(--accent)}
/* hero */
.hero{padding:56px 0 34px;max-width:var(--wide)}
.hero h1{font-family:var(--sans);font-weight:700;font-size:clamp(34px,4.4vw,52px);line-height:1.06;letter-spacing:-.018em;margin:0 0 14px;text-wrap:balance;color:var(--ink)}
.hero .deck{font-size:21px;line-height:1.42;color:var(--ink-2);max-width:60ch;margin:0 0 22px;text-wrap:pretty}
.hero .intro{max-width:var(--measure);color:var(--ink-2);font-size:17px;margin:0 0 26px}
.hero .cta{display:inline-flex;align-items:center;gap:10px;font-family:var(--sans);font-weight:600;font-size:14.5px;color:var(--accent-ink);text-decoration:none;border:1px solid var(--rule-2);padding:10px 16px;border-radius:4px;background:var(--panel)}
.hero .cta:hover{border-color:var(--accent);color:var(--accent)}
.hero .cta i{width:8px;height:8px;border-radius:50%;background:var(--accent);display:inline-block}
.keys{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border-top:1px solid var(--ink);border-bottom:1px solid var(--rule);margin:30px 0 0;max-width:var(--wide)}
.keys .k{padding:18px 22px 18px 0;border-left:1px solid var(--rule);padding-left:18px}
.keys .k:first-child{border-left:none;padding-left:0}
.keys b{display:block;font-family:var(--sans);font-weight:600;font-size:30px;line-height:1.05;letter-spacing:-.02em;font-variant-numeric:tabular-nums lining-nums;color:var(--ink)}
.keys b.bad{color:var(--bad)}.keys b.warn{color:var(--warn)}.keys b.accent{color:var(--accent)}
.keys span{display:block;font-family:var(--sans);font-size:13px;color:var(--ink-3);margin-top:6px;line-height:1.35}
.keys2{display:flex;flex-wrap:wrap;gap:6px 28px;font-family:var(--sans);font-size:13.5px;color:var(--ink-3);padding:12px 0 0;max-width:var(--wide)}
.keys2 b{font-weight:600;color:var(--ink-2);font-variant-numeric:tabular-nums lining-nums;margin-right:6px}
/* layout */
.layout{display:grid;grid-template-columns:var(--rail) minmax(0,1fr);gap:56px;align-items:start;padding-top:8px}
.rail{position:sticky;top:22px;font-family:var(--sans);font-size:13px;line-height:1.35;max-height:calc(100vh - 44px);overflow:auto;padding-right:8px;scrollbar-width:thin}
.rail h4{font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);margin:12px 0 10px;font-weight:600}
.rail ol{list-style:none;margin:0;padding:0}
.rail li{margin:0}
.rail a{display:grid;grid-template-columns:22px 1fr;gap:8px;padding:6px 8px 6px 0;color:var(--ink-2);text-decoration:none;border-left:2px solid transparent;padding-left:10px;margin-left:-12px}
.rail a em{font-style:normal;color:var(--ink-3);font-variant-numeric:tabular-nums;font-size:12px}
.rail a:hover{color:var(--accent)}
.rail a.on{color:var(--ink);border-left-color:var(--accent);font-weight:600}
.rail a.on em{color:var(--accent)}
.toc-mobile{display:none}
main{min-width:0}
section{padding:40px 0 18px;border-top:1px solid var(--rule)}
section:first-child{border-top:none;padding-top:8px}
section .label{font-family:var(--sans);font-size:12.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);font-weight:600;margin:0 0 10px}
section .label b{color:var(--accent);font-weight:700;margin-right:10px}
h2{font-family:var(--sans);font-weight:700;font-size:clamp(24px,2.6vw,31px);line-height:1.15;letter-spacing:-.015em;margin:0 0 14px;text-wrap:balance;max-width:var(--wide)}
h3{font-family:var(--sans);font-weight:600;font-size:19px;line-height:1.3;margin:30px 0 8px;letter-spacing:-.005em}
p{max-width:var(--measure);margin:0 0 16px;text-wrap:pretty}
.lede{color:var(--ink);max-width:var(--measure)}
.lede.note{font-size:15.5px;color:var(--ink-2);line-height:1.55}
p b{font-weight:600;color:var(--ink)}
/* figures */
.exh{margin:22px 0 10px;max-width:var(--wide);background:transparent;border:none;border-radius:0}
.exh img{display:block;width:100%;height:auto;border:1px solid var(--rule)}
.cap{font-family:var(--sans);font-size:13.5px;line-height:1.45;color:var(--ink-3);padding:10px 0 0;border-top:none;max-width:var(--wide)}
.cap b{color:var(--ink);font-weight:600}
#profwrap{border:1px solid var(--rule);background:var(--panel);border-radius:4px;padding:14px 14px 6px;margin:18px 0;max-width:var(--wide)}
#prof{width:100%;height:340px;display:block;cursor:crosshair;touch-action:pan-y}
#read{display:flex;gap:26px;flex-wrap:wrap;font-family:var(--sans);font-size:13px;padding:10px 4px 6px;color:var(--ink-3);font-variant-numeric:tabular-nums lining-nums}
#read b{color:var(--ink);font-weight:600}
.chip{display:inline-block;padding:1px 8px;border-radius:3px;font-family:var(--sans);font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;font-weight:600}
.chip.surveyed{background:var(--accent-soft);color:var(--accent-ink)}
.chip.inferred{background:#f4ead6;color:var(--warn)}
.chip.none{background:#f6e3dc;color:var(--bad)}
:root[data-theme="dark"] .chip.inferred,:root[data-theme="dark"] .chip.none{background:var(--paper-2)}
.legend{display:flex;gap:22px;flex-wrap:wrap;font-family:var(--sans);font-size:12.5px;color:var(--ink-3);padding:6px 4px 8px}
.legend i{display:inline-block;width:22px;height:4px;border-radius:2px;margin-right:7px;vertical-align:middle}
/* tables */
.tblwrap{overflow-x:auto;border:none;border-radius:0;margin:18px 0 22px;max-width:var(--wide);-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;min-width:640px;margin:0;font-family:var(--sans);font-size:14px;line-height:1.35}
.tblwrap table td:first-child{min-width:150px;max-width:280px}
thead th{position:sticky;top:0;background:var(--paper);font-weight:600;font-size:12.5px;letter-spacing:.01em;text-transform:none;color:var(--ink-2);text-align:right;padding:8px 12px 9px;border-bottom:1.5px solid var(--ink);vertical-align:bottom}
th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--paper);z-index:1}
td{padding:8px 12px;border-bottom:1px solid var(--rule);text-align:right;font-variant-numeric:tabular-nums lining-nums;color:var(--ink);vertical-align:top}
tbody tr:hover td{background:var(--paper-2)}
tbody tr:hover td:first-child{background:var(--paper-2)}
td.hot{color:var(--bad);font-weight:600}
td.best{font-weight:700;color:var(--accent-ink);box-shadow:inset 3px 0 0 var(--accent)}
td small,th small{font-size:11.5px;color:var(--ink-3)}
/* claim lists */
.claims{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:0 28px;margin:14px 0 8px;max-width:var(--wide)}
.claim{border:none;background:transparent;border-radius:0;border-top:1px solid var(--rule);padding:14px 0 16px}
.claim h3{font-family:var(--sans);font-weight:600;font-size:15px;margin:0 0 4px;line-height:1.3}
.claim p{font-family:var(--sans);font-size:13.5px;color:var(--ink-3);margin:0;line-height:1.45}
.claim .num{font-family:var(--sans);font-weight:600;color:var(--accent);font-size:22px;display:block;margin-bottom:2px;font-variant-numeric:tabular-nums lining-nums;letter-spacing:-.01em}
.stamp{display:inline-block;border:1px solid var(--bad);color:var(--bad);font-family:var(--sans);font-weight:600;letter-spacing:.06em;font-size:11.5px;text-transform:uppercase;padding:5px 10px;border-radius:3px;transform:none;margin:18px 0 6px}
/* footer */
footer{font-family:var(--sans);color:var(--ink-3);font-size:13px;line-height:1.55;padding:30px 0 70px;border-top:1px solid var(--ink);margin-top:56px}
footer p{max-width:86ch;margin:8px 0}
.kicker{font-family:var(--sans);font-size:12.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);font-weight:600}
@media (max-width:1100px){
  .layout{grid-template-columns:1fr;gap:0}
  .rail{display:none}
  .toc-mobile{display:block;margin:10px 0 0;border:1px solid var(--rule);border-radius:4px;font-family:var(--sans);font-size:14px;background:var(--panel)}
  .toc-mobile summary{padding:10px 14px;cursor:pointer;font-weight:600;color:var(--ink-2);list-style:none}
  .toc-mobile summary::-webkit-details-marker{display:none}
  .toc-mobile ol{list-style:none;margin:0;padding:0 14px 10px;columns:2;column-gap:24px}
  .toc-mobile li{padding:5px 0;break-inside:avoid}
  .toc-mobile a{text-decoration:none;color:var(--ink-2)}
  .toc-mobile em{font-style:normal;color:var(--ink-3);margin-right:8px;font-variant-numeric:tabular-nums}
}
@media (max-width:760px){
  .page{padding:0 18px}
  .hero{padding:34px 0 22px}
  .hero .deck{font-size:18.5px}
  .keys{grid-template-columns:1fr 1fr}
  .keys .k{border-left:none;padding-left:0;border-top:1px solid var(--rule)}
  .keys .k:nth-child(-n+2){border-top:none}
  .keys b{font-size:26px}
  .mast{flex-direction:column;gap:6px;align-items:flex-start}
  .mast .links a{margin:0 16px 0 0}
  .toc-mobile ol{columns:1}
  body{font-size:16.5px}
  h2{font-size:24px}
}
@media print{ #progress,.rail,.toc-mobile,.mast .links{display:none} body{background:#fff;color:#000;font-size:11pt} section{break-inside:avoid-page} }
</style>
"""

# ---- head: fonts + style
src = re.sub(r'<link rel="stylesheet" href="https://fonts.googleapis.com[^>]*>', FONTS, src, count=1)
i = src.find("<style>"); j = src.find("</style>") + len("</style>"); src = src[:i] + CSS.strip() + src[j:]

# ---- header -> masthead + hero + key numbers
i = src.find("<header>"); j = src.find("</header>") + len("</header>"); head = src[i:j]
intro = re.search(r'<p class="lede">(.*?)</p>', head, re.S).group(1).strip()
stats = re.findall(r'<div class="stat([^"]*)"><b>(.*?)</b><span>(.*?)</span></div>', head, re.S)
stats = [(c.strip(), b, s) for c, b, s in stats if "GLOBE" not in b]
tone = {"": "", "blue": "accent", "amber": "warn", "red": "bad"}
prim = stats[:4]; rest = stats[4:]
keys = "".join(f'<div class="k"><b class="{tone.get(c, "")}">{b}</b><span>{s}</span></div>' for c, b, s in prim)
keys2 = "".join(f'<div><b>{b}</b>{s}</div>' for c, b, s in rest)
hero = f'''<div class="mast"><div><b>Churchill Corridor Atlas</b> &middot; SeabedNet &middot; CHS NONNA archive, completed by model &middot; September 2026</div><div class="links"><a href="map/">Interactive globe</a><a href="report/">Technical report</a><a href="https://github.com/girardemilio3-svg/seabednet-validation">Code &amp; validation</a></div></div>
<div class="hero">
  <h1>The seabed under Canada&rsquo;s Arctic trade route, completed by model and tested against the soundings it never saw.</h1>
  <p class="deck">Only 17% of the 2,327 km Churchill route has a published sounding. This atlas fills the rest with depth, uncertainty and provenance for every kilometre, then puts every claim in front of a test it can fail.</p>
  <p class="intro">{intro}</p>
  <a class="cta" href="map/"><i></i>Open the interactive globe: every sealed claim on the planet</a>
  <div class="keys">{keys}</div>
  <div class="keys2">{keys2}</div>
</div>'''
src = src[:i] + hero + src[j:]

# ---- sections: ids, labels, contents rail
secs = [m.start() for m in re.finditer(r"<section>", src)]
entries = []; out = []; last = 0; n = 0
for st in secs:
    n += 1; sid = f"s{n:02d}"
    seg_end = src.find("</section>", st)
    seg = src[st:seg_end]
    m = re.search(r'<div class="eyebrow">(.*?)</div>', seg, re.S); eb = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""
    h2 = re.search(r"<h2>(.*?)</h2>", seg, re.S); title = re.sub(r"<[^>]+>", "", h2.group(1)).strip() if h2 else eb
    mm = re.match(r"Exhibit\s+([A-Z])\s*[—–-]\s*(.*)", eb)
    if mm: short, tag = mm.group(1), f"Exhibit {mm.group(1)}"; labelhtml = f'<p class="label"><b>{tag}</b>{html.escape(mm.group(2))}</p>'; railtxt = mm.group(2).strip()
    else: short, tag = "", eb; labelhtml = f'<p class="label">{html.escape(eb)}</p>' if eb else ""; railtxt = eb or title
    railtxt = railtxt[0].upper() + railtxt[1:] if railtxt else railtxt
    entries.append((sid, short, railtxt))
    seg = re.sub(r'<div class="eyebrow">.*?</div>', labelhtml, seg, count=1, flags=re.S)
    seg = seg.replace("<section>", f'<section id="{sid}">', 1)
    out.append(src[last:st]); out.append(seg); last = seg_end
out.append(src[last:]); src = "".join(out)
def navlist(): return "".join(f'<li><a href="#{sid}"><em>{html.escape(short)}</em><span>{html.escape(t)}</span></a></li>' for sid, short, t in entries)
rail = f'<aside class="rail"><h4>Contents</h4><ol>{navlist()}</ol></aside>'
tocm = f'<details class="toc-mobile"><summary>On this page ({len(entries)} sections)</summary><ol>{navlist()}</ol></details>'
# wrap: page > mast/hero, then layout(rail + main(sections...)) , footer
first_sec = src.find("<section id="); foot = src.find("<footer>")
body_open = src.find(">", src.find("<body")) + 1
pre = src[body_open:first_sec]; mid = src[first_sec:foot]; post = src[foot:]
pre = pre.replace('<div class="wrap">', "", 1)   # old wrapper opened here; its close sits before </body>
post = post.replace("</div>\n</body>", "</body>").replace("</div></body>", "</body>")
src = src[:body_open] + '\n<div id="progress"></div>\n<div class="page">' + pre + tocm + '<div class="layout">' + rail + "<main>" + mid + "</main></div>" + post
if src.count("<div") > src.count("</div>"): src = src.replace("</body>", "</div>\n</body>", 1)   # close .page only if the old wrapper close is gone

# ---- prose sizes: inline lede sizes -> note class
src = re.sub(r'<p class="lede" style="font-size:1[34](?:\.5)?px">', '<p class="lede note">', src)
src = src.replace('<p class="lede" style="font-size:14.5px">', '<p class="lede note">')
# ---- canvas: hard-coded light-on-dark colour -> ink
src = src.replace("'rgba(216,224,238,0.45)'", "'rgba(21,25,29,0.45)'").replace("'rgba(232,178,74,0.16)'", "'rgba(162,104,28,0.14)'")
# ---- scripts: progress bar, rail scroll-spy, best-in-column marks
JS = r"""
<script>
(function(){
  var bar=document.getElementById('progress');
  function prog(){var h=document.documentElement;var s=h.scrollTop||document.body.scrollTop;var m=h.scrollHeight-h.clientHeight;bar.style.width=(m>0?100*s/m:0)+'%';}
  addEventListener('scroll',prog,{passive:true});prog();
  var links=[].slice.call(document.querySelectorAll('.rail a'));var map={};links.forEach(function(a){map[a.getAttribute('href').slice(1)]=a;});
  if('IntersectionObserver' in window){var cur=null;var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){if(cur)cur.classList.remove('on');cur=map[e.target.id];if(cur){cur.classList.add('on');}}});},{rootMargin:'-18% 0px -70% 0px',threshold:0});
    document.querySelectorAll('main section[id]').forEach(function(s){io.observe(s);});}
  document.querySelectorAll('table').forEach(function(t){var ths=[].slice.call(t.querySelectorAll('thead th'));
    ths.forEach(function(th,ci){var txt=th.textContent.toLowerCase();if(!(/mae|\(m\)/.test(txt)))return;var best=null,bv=Infinity;
      t.querySelectorAll('tbody tr').forEach(function(tr){var td=tr.children[ci];if(!td)return;var v=parseFloat((td.textContent||'').replace(/[^0-9.\-]/g,''));if(isFinite(v)&&v<bv){bv=v;best=td;}});
      if(best&&t.querySelectorAll('tbody tr').length>=3)best.classList.add('best');});});
})();
</script>
"""
src = src.replace("</body>", JS + "</body>", 1)
src = src.replace("atlas v8.0", "atlas v9.0").replace("atlas v8.2", "atlas v9.0")
open("churchill_atlas_v9.html", "w", encoding="utf-8").write(src)
print("ATLAS_V9_DONE", len(src)//1024, "KB; sections", len(entries), "| keys", len(prim), "+", len(rest))
