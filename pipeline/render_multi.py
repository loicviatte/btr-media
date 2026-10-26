"""Render every Atlas-<Name>-NN artboard under <root>/project and build one contact sheet per country.
Reports text overflowing the 80 px side margins or running into the footer zone (y > 1240).
Usage: python3 render_multi.py <root> <assetdir> <outdir> [Name ...]"""
import sys, re, glob, os, collections
from playwright.sync_api import sync_playwright
from PIL import Image

root, assets, out = sys.argv[1:4]
only = set(sys.argv[4:])
os.makedirs(out, exist_ok=True)
files = sorted(glob.glob(f"{root}/project/Atlas-*-0[1-8].dc.html"))

def local(html):
    inner = re.search(r"<x-dc>(.*)</x-dc>", html, re.S).group(1).replace("<helmet>", "").replace("</helmet>", "")
    def rep(m):
        hits = glob.glob(f"{assets}/{m.group(1)}.*")
        return "file://" + hits[0] if hits else m.group(0)
    inner = re.sub(r"/_blob/([0-9a-f]{32})", rep, inner)
    return f"<!doctype html><html><head><meta charset='utf-8'></head><body style='margin:0'>{inner}</body></html>"

groups = collections.defaultdict(list)
problems = []
with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1080, "height": 1350})
    for f in files:
        name = re.match(r"Atlas-(.+)-\d\d\.dc\.html", os.path.basename(f)).group(1)
        if only and name not in only:
            continue
        tmp = f"{out}/_tmp.html"
        open(tmp, "w").write(local(open(f).read()))
        pg.goto("file://" + tmp)
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(250)
        bad = pg.evaluate("""() => {
          const out = [];
          for (const e of document.querySelectorAll('p')) {
            if (e.closest('[aria-hidden]')) continue;
            const r = e.getBoundingClientRect(); if (!r.width) continue;
            const txt = e.textContent.trim().slice(0, 28);
            // content width of nowrap text
            const sw = e.scrollWidth > e.clientWidth + 2;
            if (r.right > 1002 || r.left < 78) out.push(txt + ' x:' + Math.round(r.left) + '-' + Math.round(r.right));
            if (sw) out.push(txt + ' clipped');
            const isFoot = r.top > 1240;
            if (!isFoot && r.bottom > 1240) out.push(txt + ' bottom:' + Math.round(r.bottom));
          }
          return out;
        }""")
        png = f"{out}/{os.path.basename(f).replace('.dc.html', '.png')}"
        pg.screenshot(path=png)
        groups[name].append(png)
        if bad:
            problems.append((os.path.basename(f), bad))
    br.close()

for name, shots in groups.items():
    w, h = 405, 506
    sheet = Image.new("RGB", (w * 4 + 30, h * 2 + 10), "white")
    for i, s in enumerate(sorted(shots)):
        sheet.paste(Image.open(s).resize((w, h)), ((i % 4) * (w + 10), (i // 4) * (h + 10)))
    sheet.save(f"{out}/sheet-{name}.png")
for f, b in problems:
    print("PROBLEM", f, b)
print("rendered", sum(len(v) for v in groups.values()), "slides;", len(problems), "with problems")
