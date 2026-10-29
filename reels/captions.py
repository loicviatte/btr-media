"""BTR captions — DOAC-style stacked blocks, word-by-word reveal (validated style, Oct 2026).

usage:
  python3 captions.py words.json blocks.txt out.ass --end 39.3 [--fonts fonts/]

words.json : [[word, start_seconds], ...] for the EDITED video (see transcribe.py)
blocks.txt : the caption script (notation in README.md). Every word in blocks.txt must
             match words.json in order (punctuation and case ignored) — the script stops
             otherwise, so a caption can never contain a word that was not said.
--end      : no caption after this time (end card / last frame)

Canvas is 2160x3840 (PlayRes); libass scales it to any 9:16 output (1080x1920 included).
Effects kept: blur reveal, gold (*), italic (/), letter tracking (~), gold highlighter (#).
Effects removed on purpose (Loïc): landing/slam, word behind the head, counter, camera shake.
"""
import argparse, json, os, re
from PIL import ImageFont

ap = argparse.ArgumentParser()
ap.add_argument("words"); ap.add_argument("blocks"); ap.add_argument("out")
ap.add_argument("--end", type=float, required=True)
ap.add_argument("--fonts", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"))
args = ap.parse_args()

W, H = 2160, 3840
CX = W // 2
CY_DEFAULT = 2380              # block centre: below the face, above the Instagram UI
MARGIN, STEP = 150, 120        # left margin, stair offset per line
REG = ("PP Monument Extended Regular", os.path.join(args.fonts, "PPMonumentExtended-Regular.otf"))
HEV = ("PP Monument Extended Heavy", os.path.join(args.fonts, "PPMonumentExtended-Heavy.otf"))
SMALL, BIG = 165, 300          # linking words / key words
CAP, ADV = 720 / 1360, 1000 / 1360   # libass: cap height = fs*CAP, width = PIL width*ADV
GAP = 60
WHITE, GOLD, INK = "&HFFFFFF&", "&H9ADFFC&", "&H141414&"   # BGR; GOLD = #FCDF9A
REVEAL = 190                   # ms blur-in per word

words = json.load(open(args.words))
norm = lambda t: re.sub(r"[^A-Z0-9]", "", t.upper())
pil = {REG[0]: ImageFont.truetype(REG[1], 100), HEV[0]: ImageFont.truetype(HEV[1], 100)}
def width(text, font, fs):
    return pil[font].getlength(text) * fs / 100 * ADV

# ---------- parse blocks.txt ----------
blocks, cur = [], None
for raw in open(args.blocks):
    l = raw.strip()
    if not l or l.startswith("# "):
        continue
    if l.startswith("@"):
        cur = {"opts": dict(kv.split("=") for kv in l[1:].split()), "lines": []}
        blocks.append(cur); continue
    toks = []
    for tok in l.split():
        m = re.match(r"([*/~#]*)(.+)", tok)
        flags, text = m.group(1), m.group(2)
        toks.append({"text": text.upper().replace("'", "’"), "big": text.upper() == text,
                     "gold": "*" in flags, "ital": "/" in flags, "track": "~" in flags, "hl": "#" in flags})
    cur["lines"].append(toks)

# Match caption words to spoken words in order. Spoken words may be SKIPPED (cutting a
# stutter or a "you know" is allowed), at most MAX_SKIP in a row; a caption word that cannot
# be found stops the script (adding words is never allowed).
ALIASES = {"BALLROOM": {"BALLROOM", "BORN", "BALLROM"}}   # ASR spellings of DanceSport terms
MAX_SKIP = 3
k, skipped = 0, []
for b in blocks:
    for line in b["lines"]:
        for w in line:
            want = ALIASES.get(norm(w["text"]), {norm(w["text"])})
            j = k
            while j < len(words) and j - k <= MAX_SKIP and norm(words[j][0]) not in want:
                j += 1
            assert j < len(words) and norm(words[j][0]) in want, \
                f"caption word {w['text']!r} not found in the audio near {words[k:k + 4]}"
            skipped += [words[x][0] for x in range(k, j)]
            w["t"] = words[j][1]; k = j + 1
if skipped:
    print("spoken words left out of the captions (check these are stutters/fillers):", skipped)
if k < len(words):
    print("spoken words after the last caption (not captioned):", [x[0] for x in words[k:]])

def ts(x):
    x = max(0.0, x); return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"

def word_tags(w, state, shadow):
    font = HEV[0] if w["big"] else REG[0]
    t = f"\\fn{font}\\fs{w['fs']}" + ("\\i1" if w["ital"] else "\\i0") + "\\fsp0\\fscx100\\fscy100"
    if shadow:
        col, on = "\\1c&H000000&", ("&HFF&" if w["hl"] else "&H50&")
    else:
        col, on = "\\1c" + (INK if w["hl"] else GOLD if w["gold"] else WHITE), "&H00&"
    blur0 = "" if shadow else "\\blur0"
    if state == "hidden":
        return "{" + t + col + "\\alpha&HFF&}"
    if state == "said":
        return "{" + t + col + f"\\alpha{on}" + blur0 + "}"
    if w["track"]:
        sp = min(70, int(520 / max(1, len(w["text"]))))
        return "{" + t + col + f"\\alpha&HFF&\\fsp{sp}" + ("" if shadow else "\\blur22") + f"\\t(0,330,\\alpha{on}\\fsp0{blur0})}}"
    if w["hl"]:
        return "{" + t + col + "\\alpha&HFF&" + f"\\t(60,200,\\alpha{on})}}"
    return "{" + t + col + "\\alpha&HFF&" + ("" if shadow else "\\blur26") + f"\\t(0,{REVEAL},\\alpha{on}{blur0})}}"

events = []
for bi, b in enumerate(blocks):
    o = b["opts"]; align = o.get("align", "c"); cy = int(o.get("y", CY_DEFAULT))
    lines = b["lines"]
    geo = []
    for li, line in enumerate(lines):
        for w in line:
            w["fs"] = int(o.get("big", BIG)) if w["big"] else int(o.get("small", SMALL))
        maxw = W - 2 * MARGIN - (li * STEP if align == "stair" else 0)
        line_w = lambda: sum(width(w["text"] + (" " if i < len(line) - 1 else ""), HEV[0] if w["big"] else REG[0], w["fs"])
                             for i, w in enumerate(line))
        if line_w() > maxw:                      # shrink the whole line to fit
            f = maxw / line_w()
            for w in line: w["fs"] = int(w["fs"] * f)
        geo.append({"w": line_w(), "cap": max(w["fs"] for w in line) * CAP})
    total = sum(g["cap"] for g in geo) + GAP * (len(lines) - 1)
    y = cy - total / 2
    for li, g in enumerate(geo):
        g["y"] = round(y + g["cap"] / 2); y += g["cap"] + GAP
        if align == "c":
            g["an"], g["x"], g["x0"] = 5, CX, CX - g["w"] / 2
        else:
            x = MARGIN + (li * STEP if align == "stair" else 0)
            g["an"], g["x"], g["x0"] = 4, x, x

    flat = [(li, wi, w) for li, line in enumerate(lines) for wi, w in enumerate(line)]
    last_t = flat[-1][2]["t"]
    nxt = blocks[bi + 1]["lines"][0][0]["t"] if bi + 1 < len(blocks) else None
    end = float(o["until"]) if "until" in o else max(last_t + 0.5 + 0.05 * len(flat[-1][2]["text"]), last_t + 0.6)
    if nxt is not None:
        end = min(end, nxt)
    end = min(end, args.end)

    for n, (li_a, wi_a, w_a) in enumerate(flat):
        s = w_a["t"]
        e = flat[n + 1][2]["t"] if n + 1 < len(flat) else end
        if e - s < 0.02:
            continue
        dur_ms = int((e - s) * 1000)
        exit_tag = f"\\t({dur_ms - 120},{dur_ms},\\alpha&HFF&\\blur18)" if n == len(flat) - 1 and dur_ms >= 300 else ""
        for li, line in enumerate(lines):
            if li > li_a:
                break                                  # lines not reached yet are not drawn
            g = geo[li]
            for layer, shadow in ((0, True), (2, False)):
                parts = []
                for wi, w in enumerate(line):
                    st = "said" if (li, wi) < (li_a, wi_a) else "active" if (li, wi) == (li_a, wi_a) else "hidden"
                    tg = word_tags(w, st, shadow)
                    if exit_tag and st != "hidden":
                        tg = tg[:-1] + exit_tag + "}"
                    parts.append(tg + w["text"])
                head = f"{{\\an{g['an']}\\pos({g['x']},{g['y'] + (10 if shadow else 0)})\\bord0\\shad0" + \
                       ("\\blur22" if shadow else "") + "}"
                events.append(f"Dialogue: {layer},{ts(s)},{ts(e)},Cap,,0,0,0,,{head}{' '.join(parts)}")

    # gold highlighter bars (#)
    for li, line in enumerate(lines):
        g = geo[li]; x = g["x0"]
        for w in line:
            ww = width(w["text"], HEV[0] if w["big"] else REG[0], w["fs"])
            if w["hl"]:
                pad, capw = 34, w["fs"] * CAP
                x0, x1 = round(x - pad), round(x + ww + pad)
                y0, y1 = round(g["y"] - capw * 0.78), round(g["y"] + capw * 0.78)
                dur_ms = int((end - w["t"]) * 1000)
                events.append(f"Dialogue: 1,{ts(w['t'])},{ts(end)},Cap,,0,0,0,,"
                              f"{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c{GOLD}\\clip({x0},{y0},{x0 + 1},{y1})"
                              f"\\t(0,170,\\clip({x0},{y0},{x1},{y1}))\\t({max(dur_ms - 120, 171)},{dur_ms},\\alpha&HFF&)}}"
                              f"m {x0} {y0} l {x1} {y0} l {x1} {y1} l {x0} {y1}")
            x += ww + width(" ", HEV[0] if w["big"] else REG[0], w["fs"])

HEADER = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{HEV[0]},200,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
open(args.out, "w").write(HEADER + "\n".join(events) + "\n")
n_cap = sum(len(l) for b in blocks for l in b["lines"])
print(f"{len(blocks)} blocks, {n_cap} caption words, {len(events)} events -> {args.out}")
