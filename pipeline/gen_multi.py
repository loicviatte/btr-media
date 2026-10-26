"""BTR World Atlas — data-driven carousel generator.
Usage: python3 gen_multi.py <root> <assetdir> slug [slug...]
Reads content/<slug>.json + COUNTRIES config, writes <root>/project/Atlas-<Name>-NN.dc.html
Text that must fit on one line is sized from real glyph widths measured in Chromium.
"""
import sys, os, json, re, html
from playwright.sync_api import sync_playwright

ROOT, ASSETS = sys.argv[1], sys.argv[2]
SLUGS = sys.argv[3:]
HERE = os.path.dirname(os.path.abspath(__file__))

COUNTRIES = {k: v for k, v in json.load(open(os.path.join(HERE, "countries.json"))).items()}

LOGO = "/_blob/e440a533f995f68292ba052bdcdb1dd8"
F800 = "/_blob/c4d57da8906396cc558640fd45d2719a"
F400 = "/_blob/97d5a4a904e3ab62b8ced0b106499458"
GOLD, NAME_GOLD = "#fecb7a", "#fcdf9a"
HAZE = ("linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0) 40%, rgba(137,118,58,0.10) 55%, "
        "rgba(159,137,69,0.16) 65%, rgba(180,154,79,0.24) 75%, rgba(199,171,88,0.36) 85%, "
        "rgba(217,187,96,0.55) 94%, rgba(223,191,100,0.68) 100%)")
SLATS = "repeating-linear-gradient(90deg, #080403 0px, #080403 30px, #120a06 30px, #120a06 38px)"
ARROW = ('<svg aria-hidden="true" width="44" height="24" viewBox="0 0 44 24" fill="none" stroke="#ffffff" '
         'stroke-width="3" stroke-linecap="square"><path d="M2 12h38"></path><path d="M30 2l10 10-10 10"></path></svg>')
TOTAL = 8
FADE = " -webkit-mask-image: radial-gradient(ellipse 70% 70% at 50% 45%, #000 55%, transparent 100%); mask-image: radial-gradient(ellipse 70% 70% at 50% 45%, #000 55%, transparent 100%);"
AVAIL = 920

# ---------------- measuring ----------------
class Meter:
    def __init__(self):
        self.p = sync_playwright().start()
        self.b = self.p.chromium.launch()
        self.pg = self.b.new_page()
        f800 = f"file://{ASSETS}/c4d57da8906396cc558640fd45d2719a.woff2"
        f400 = f"file://{ASSETS}/97d5a4a904e3ab62b8ced0b106499458.woff2"
        tmp = os.path.join(HERE, "_meter.html")
        open(tmp, "w").write(f"""<html><head><style>@font-face{{font-family:M;src:url('{f800}');font-weight:800}}
        @font-face{{font-family:M;src:url('{f400}');font-weight:400}}</style></head><body><span id=s style="font-family:M;font-weight:800;font-size:100px;white-space:nowrap">x</span></body></html>""")
        self.pg.goto("file://" + tmp)
        self.pg.evaluate("document.fonts.ready")
        self.pg.wait_for_timeout(300)

    def width(self, text, weight=800, size=100):
        return self.pg.evaluate("""([t,w,s]) => {const e=document.getElementById('s'); e.style.fontWeight=w; e.style.fontSize=s+'px'; e.textContent=t; return e.getBoundingClientRect().width;}""", [text, weight, size])

    def fit(self, text, max_size, avail=AVAIL, weight=800):
        w = self.width(text, weight, 100)
        return int(min(max_size, avail * 100 / w)) if w else max_size

    def close(self):
        self.b.close(); self.p.stop()

M = None

def esc(s):
    return html.escape(s, quote=False)

def md(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r'<span style="font-weight: 800;">\1</span>', s)
    s = re.sub(r"==(.+?)==", rf'<span style="font-weight: 800; color: {GOLD};">\1</span>', s)
    return s

def t(size, txt, extra="", weight=800, color="#ffffff"):
    return f'<p style="margin: 0; font-size: {size}px; line-height: 1; font-weight: {weight}; white-space: nowrap; color: {color}; {extra}">{txt}</p>'

def line(txt, extra="", maxs=72, color="#ffffff", quote_open=False, quote_close=False):
    plain = ("“" if quote_open else "") + txt + ("”" if quote_close else "")
    size = M.fit(plain, maxs)
    body = esc(txt)
    if quote_open: body = f'<span style="color: {GOLD};">“</span>' + body
    if quote_close: body = body + f'<span style="color: {GOLD};">”</span>'
    return t(size, body, extra, color=color), size

def body(txt, size=36, extra=""):
    return f'<p style="margin: 0; font-size: {size}px; line-height: 1.32; font-weight: 400; color: #ffffff; {extra}">{md(txt)}</p>'

def stamp(size, center, sub, rot, pos, uid):
    return f'''<div aria-hidden="true" style="position: absolute; {pos} width: {size}px; height: {size}px; transform: rotate({rot}deg);">
    <svg width="{size}" height="{size}" viewBox="0 0 200 200" style="position: absolute; left: 0; top: 0;">
      <circle cx="100" cy="100" r="96" fill="none" stroke="{GOLD}" stroke-width="4"></circle>
      <circle cx="100" cy="100" r="68" fill="none" stroke="{GOLD}" stroke-width="2"></circle>
      <path id="ring{uid}" d="M100,100 m-77,0 a77,77 0 1,1 154,0 a77,77 0 1,1 -154,0" fill="none"></path>
      <text font-size="12" font-weight="800" fill="{GOLD}"><textPath href="#ring{uid}" textLength="483" lengthAdjust="spacing">WORLD ATLAS · BREAK THE ROUTINE · </textPath></text>
    </svg>
    <div style="position: absolute; left: 0; top: 0; width: {size}px; height: {size}px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 5px;">
      <p style="margin: 0; font-size: {size*0.06:.0f}px; line-height: 1; font-weight: 400; letter-spacing: 0.12em; color: {GOLD};">No.</p>
      <p style="margin: 0; font-size: {size*0.2:.0f}px; line-height: 1; font-weight: 800; color: {GOLD};">{center}</p>
      <p style="margin: 0; font-size: {min(18, M.fit(sub, 18, size*0.44) - 1)}px; line-height: 1; font-weight: 800; letter-spacing: 0.06em; color: {GOLD};">{esc(sub)}</p>
    </div>
  </div>'''

def page(cfg, title, inner, n, footer=True, bg=None, label=True):
    MAP = "/_blob/" + cfg["blob"]
    mw, mh = cfg["wh"]
    counter = f'<p style="position: absolute; right: 80px; top: 64px; margin: 0; font-size: 24px; line-height: 1; font-weight: 400; letter-spacing: 0.18em; color: #ffffff;">{n:02d} / {TOTAL:02d}</p>'
    lab = f'<p style="position: absolute; left: 80px; top: 64px; margin: 0; font-size: 24px; line-height: 1; font-weight: 400; letter-spacing: 0.18em; color: {GOLD};">WORLD ATLAS</p>'
    bgimg = ""
    if bg is not None:
        if mh >= mw:
            h = 1900; w = round(h * mw / mh)
        else:
            w = 2100; h = round(w * mh / mw)
        bgimg = f'<img src="{MAP}" alt="" aria-hidden="true" style="position: absolute; left: {bg[0]}px; top: {bg[1]}px; width: {w}px; height: {h}px; opacity: 0.09;">'
    foot = ""
    if footer:
        ih = 40; iw = round(ih * mw / mh)
        if iw > 60: iw = 60; ih = round(iw * mh / mw)
        foot = f'''<div style="position: absolute; left: 80px; bottom: 64px; display: flex; align-items: center; gap: 16px;">
    <img src="{MAP}" alt="" aria-hidden="true" style="width: {iw}px; height: {ih}px;">
    <p style="margin: 0; font-size: 24px; line-height: 1; font-weight: 800; letter-spacing: 0.18em; color: #ffffff;">{esc(cfg["label"])}</p>
  </div>
  <div style="position: absolute; right: 80px; bottom: 64px; display: flex; align-items: center; gap: 16px;">
    <p style="margin: 0; font-size: 24px; line-height: 1; font-weight: 400; letter-spacing: 0.18em; color: #ffffff;">SWIPE</p>
    {ARROW}
  </div>'''
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{esc(title)}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<style>
@font-face{{font-family:"PP Monument Extended";src:url("{F800}") format("woff2");font-weight:800 900;font-style:normal}}
@font-face{{font-family:"PP Monument Extended";src:url("{F400}") format("woff2");font-weight:400;font-style:normal}}
body{{margin:0}}
a{{color:#fecb7a}}a:hover{{color:#ffffff}}
</style>
</helmet>
<div style="position: relative; width: 1080px; height: 1350px; overflow: hidden; background: {SLATS}; font-family: 'PP Monument Extended', 'Arial Black', sans-serif; color: #ffffff;">
  {bgimg}
  <div aria-hidden="true" style="position: absolute; left: 0; top: 0; width: 1080px; height: 1350px; background: {HAZE};"></div>
  {lab if label else ""}
  {counter if label else ""}
  {inner}
  {foot}
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":1080,"height":1350}}}}'>
class Component extends DCLogic {{
  renderVals() {{
    return {{}};
  }}
}}
</script>
</body>
</html>
'''

def build(slug):
    cfg = dict(COUNTRIES[slug]); cfg["wh"] = tuple(cfg["wh"])
    raw = open(os.path.join(HERE, "content", f"{slug}.json")).read().replace("&amp;", "&")
    c = json.loads(raw)
    MAP = "/_blob/" + cfg["blob"]
    mw, mh = cfg["wh"]
    no = f'{cfg["no"]:02d}'
    nxt = f'{cfg["no"] + 1:02d}'
    lines = c.get("country_lines") or [c["country"]]
    cfg["label"] = c["country"] if len(c["country"]) <= 22 else cfg.get("short", lines[0])
    stamp_sub = cfg.get("short") or (c["country"] if len(c["country"]) <= 12 else lines[0])
    first, *rest = cfg["guest"].upper().split(" ", 1)
    last = rest[0] if rest else ""
    out = []

    # ---- 1 cover ----
    csize = min(M.fit(l, 172, 900) for l in lines)
    title_bottom = 250 + 72 + 14 + len(lines) * csize + 18 + 72
    name_w = max(M.width(first, 800, 56), M.width(last, 800, 56))
    name_right = 80 + name_w
    # map: try tall box down to 1290 right-aligned; keep clear of the name block
    title_right = 80 + max(M.width("“How does", 800, 72), max(M.width(l, 800, csize) for l in lines))
    box_l, box_r = 420, 1040

    def place(top):
        bottom = 1230
        while True:
            s = min((box_r - box_l) / mw, (bottom - top) / mh)
            w, h = mw * s, mh * s
            left = box_r - w
            if bottom <= 1080 or left > name_right + 30 or top + h < 1090:
                return left, w, h
            bottom -= 20

    top = max(470, title_bottom - 60) if mh >= mw else title_bottom + 30
    left, w, h = place(top)
    if top < title_bottom + 20 and left < title_right + 30:
        top = title_bottom + 20
        left, w, h = place(top)
    mapimg = f'<img src="{MAP}" alt="Map of {esc(c["country"].title())}" style="position: absolute; left: {left:.0f}px; top: {top:.0f}px; width: {w:.0f}px; height: {h:.0f}px;{FADE if cfg.get('fade') else ''}">'
    title_ps = "\n    ".join(t(csize, esc(l), "margin: 14px 0 18px;" if (len(lines) == 1) else ("margin-top: 14px;" if i == 0 else "margin: 6px 0 18px;")) for i, l in enumerate(lines))
    cover = f'''
  <img src="{LOGO}" alt="BTR — The Dancesport Podcast" style="position: absolute; left: 40px; top: 30px; width: 240px; height: 152.5px;">
  <p style="position: absolute; right: 80px; top: 64px; margin: 0; font-size: 24px; line-height: 1; font-weight: 400; letter-spacing: 0.18em; color: {GOLD};">WORLD ATLAS</p>
  {mapimg}
  <div style="position: absolute; left: 80px; top: 250px; display: flex; flex-direction: column; align-items: stretch;">
    {t(72, f'<span style="color: {GOLD};">“</span>How does')}
    {title_ps}
    {t(72, f'dance?<span style="color: {GOLD};">”</span>', "text-align: right;")}
  </div>
  {stamp(250, no, stamp_sub, -12, "left: 90px; top: 760px;", f"{cfg['name']}{no}")}
  <div style="position: absolute; left: 80px; top: 1110px; display: flex; flex-direction: column; gap: 14px;">
    <p style="margin: 0; font-size: 24px; line-height: 1; font-weight: 400; letter-spacing: 0.18em; color: #ffffff;">DRAWN BY</p>
    <p style="margin: 0; font-size: 56px; line-height: 1.1; font-weight: 800; white-space: nowrap; color: {NAME_GOLD}; mix-blend-mode: hard-light;">{esc(first)}<br>{esc(last)}</p>
  </div>
  <div style="position: absolute; right: 80px; bottom: 64px; display: flex; align-items: center; gap: 16px;">
    <p style="margin: 0; font-size: 24px; line-height: 1; font-weight: 400; letter-spacing: 0.18em; color: #ffffff;">SWIPE</p>
    {ARROW}
  </div>'''
    out.append(("Cover", cover, None, False, False))

    # ---- 2 Latin & Ballroom ----
    s2 = c["s2"]
    asz = M.fit(s2["answer"], 300)
    out.append(("Latin and Ballroom", f'''
  <div style="position: absolute; left: 80px; top: 220px; width: 920px; display: flex; flex-direction: column;">
    {t(72, "Latin &amp;")}
    {t(72, "Ballroom?", "margin-top: 10px;")}
    {t(asz, esc(s2["answer"]), f"margin: 40px 0 70px; color: {GOLD};")}
    {body(s2["p1"])}
    {body(s2["p2"], extra="margin-top: 28px;") if s2.get("p2") else ""}
  </div>''', (300, -250), True, True))

    # ---- 3 big number ----
    s3 = c["s3"]
    nsz = M.fit(s3["number"], 220)
    l1, _ = line(s3["line1"], "margin-top: 40px;")
    l2, _ = line(s3["line2"], "margin-top: 10px;") if s3.get("line2") else ("", 0)
    out.append(("Big number", f'''
  <div style="position: absolute; left: 80px; top: 260px; width: 920px; display: flex; flex-direction: column;">
    {t(nsz, esc(s3["number"]), f"color: {GOLD};")}
    {l1}
    {l2}
    {body(s3["p"], 40, "margin-top: 70px;")}
  </div>''', (0, -350), True, True))

    # ---- 4 pop moment ----
    s4 = c["s4"]
    top4, _ = line(s4["top"], quote_open=True)
    ksz = M.fit(s4["key"], 150)
    bot4, _ = line(s4["bottom"], f"margin-top: 18px; text-align: right;", color=GOLD, quote_close=True)
    out.append(("Pop moment", f'''
  <div style="position: absolute; left: 80px; top: 220px; width: 920px; display: flex; flex-direction: column;">
    {top4}
    {t(ksz, esc(s4["key"]), "margin: 14px 0 0;")}
    {bot4}
    {body(s4["p1"], extra="margin-top: 70px;")}
    {body(s4["p2"], extra="margin-top: 28px;") if s4.get("p2") else ""}
  </div>''', (-300, -500), True, True))

    # ---- 5 typical dances ----
    blocks = []
    for d in c["s5"][:2]:
        dsz = M.fit(d["name"], 110)
        blocks.append(f'''<div style="display: flex; flex-direction: column; gap: 22px;">
      {t(dsz, esc(d["name"]))}
      <p style="margin: 0; font-size: 26px; line-height: 1.2; font-weight: 800; letter-spacing: 0.14em; color: {GOLD};">{esc(d["meta"])}</p>
      {body(d["p"], 34)}
    </div>''')
    out.append(("Typical dances", f'''
  <div style="position: absolute; left: 80px; top: 190px; width: 920px; display: flex; flex-direction: column; gap: 44px;">
    {t(72, "Typical dances")}
    {blocks[0]}
    <div aria-hidden="true" style="width: 920px; height: 3px; background: {GOLD};"></div>
    {blocks[1]}
  </div>''', (-650, -650), True, True))

    # ---- 6 surprising fact ----
    s6 = c["s6"]
    top6, _ = line(s6["top"], quote_open=True)
    k6 = M.fit(s6["key"], 158)
    bot6, _ = line(s6["bottom"], "text-align: right;", quote_close=True)
    span = ""
    if s6.get("y1") and s6.get("y2"):
        ysz = min(96, M.fit(s6["y1"] + s6["y2"], 96, 700))
        span = f'''<div style="display: flex; align-items: center; gap: 28px; margin-top: 80px;">
      {t(ysz, esc(s6["y1"]), f"color: {GOLD};")}
      <div aria-hidden="true" style="flex: 1; height: 4px; background: {GOLD};"></div>
      {t(ysz, esc(s6["y2"]), f"color: {GOLD};")}
    </div>'''
    out.append(("Surprising fact", f'''
  <div style="position: absolute; left: 80px; top: 220px; width: 920px; display: flex; flex-direction: column;">
    {top6}
    {t(k6, esc(s6["key"]), "margin: 14px 0 18px;")}
    {bot6}
    {span}
    {body(s6["p"], extra="margin-top: 60px;" if span else "margin-top: 80px;")}
  </div>''', (-150, -900), True, True))

    # ---- 7 key date + news ----
    s7 = c["s7"]
    ysz7 = M.fit(s7["year"], 200)
    a7, _ = line(s7["line1"], "margin-top: 28px;")
    b7, _ = line(s7["line2"], "margin-top: 10px;") if s7.get("line2") else ("", 0)
    news = ""
    if s7.get("tag") and s7.get("p2"):
        news = f'''<div aria-hidden="true" style="width: 920px; height: 3px; background: {GOLD}; margin: 44px 0 36px;"></div>
    <p style="margin: 0; font-size: 26px; line-height: 1; font-weight: 800; letter-spacing: 0.14em; color: {GOLD};">{esc(s7["tag"])}</p>
    {body(s7["p2"], 34, "margin-top: 20px;")}'''
    out.append(("Key date", f'''
  <div style="position: absolute; left: 80px; top: 180px; width: 920px; display: flex; flex-direction: column;">
    {t(ysz7, esc(s7["year"]), f"color: {GOLD};")}
    {a7}
    {b7}
    {body(s7["p"], 34, "margin-top: 40px;")}
    {news}
  </div>''', (250, -500), True, True))

    # ---- 8 CTA ----
    out.append(("Next country", f'''
  <img src="{LOGO}" alt="BTR — The Dancesport Podcast" style="position: absolute; left: 420px; top: 120px; width: 240px; height: 152.5px;">
  <div style="position: absolute; left: 80px; top: 380px; width: 920px; display: flex; flex-direction: column; align-items: stretch;">
    {t(72, "Where will the", "text-align: left;")}
    {t(184, "ATLAS", "margin: 14px 0 18px; text-align: center;")}
    {t(72, f'land next<span style="color: {GOLD};">?</span>', "text-align: right;")}
  </div>
  {stamp(230, nxt, "???", 10, "left: 425px; top: 790px;", f"{cfg['name']}{nxt}")}
  <div style="position: absolute; left: 80px; top: 1080px; width: 920px; display: flex; flex-direction: column; align-items: center; gap: 16px;">
    <p style="margin: 0; font-size: 34px; line-height: 1.3; font-weight: 800; text-align: center; color: #ffffff;">Drop your guess in the comments</p>
    <p style="margin: 0; font-size: 26px; line-height: 1.3; font-weight: 400; letter-spacing: 0.08em; text-align: center; color: #ffffff;">FULL EPISODE ON YOUTUBE &amp; SPOTIFY</p>
  </div>''', None, False, True))

    names = []
    os.makedirs(f"{ROOT}/project", exist_ok=True)
    for i, (title, inner, bg, foot, lab) in enumerate(out, 1):
        fn = f"Atlas-{cfg['name']}-{i:02d}.dc.html"
        names.append(fn)
        open(f"{ROOT}/project/{fn}", "w").write(page(cfg, f"World Atlas {cfg['name']} {i:02d} · {title}", inner, i, foot, bg, lab))
    return names

if __name__ == "__main__":
    M = Meter()
    try:
        for s in SLUGS:
            print(s, build(s))
    finally:
        M.close()
