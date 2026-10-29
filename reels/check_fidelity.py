"""Check that every caption word was actually said, in order.

usage:  python3 check_fidelity.py edited_words.json blocks.txt
edited_words.json = transcribe.py run on the EDITED reel (not the source).
Allowed: words cut out (stutters, "you know"). Not allowed: any caption word missing from the audio.
"""
import json, re, sys
ALIASES = {"ballroom": {"born", "ballroom"}}   # ASR spellings of DanceSport terms
norm = lambda t: re.sub(r"[^A-Za-z0-9']", "", t).lower()
aud = [norm(w) for w, _ in json.load(open(sys.argv[1]))]
cap = [norm(re.sub(r"^[*/~#]+", "", t)) for l in open(sys.argv[2])
       if l.strip() and not l.startswith("@") and not l.startswith("# ") for t in l.split()]
j = 0
for c in cap:
    ok = ALIASES.get(c, {c})
    while j < len(aud) and aud[j] not in ok:
        j += 1
    if j == len(aud):
        sys.exit(f"NOT SAID (or out of order): {c!r}")
    j += 1
print(f"OK: all {len(cap)} caption words are in the audio, in order")
