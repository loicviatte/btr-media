"""Build Instagram/TikTok captions for World Atlas carousels and merge them into captions.json.
Usage: python3 captions.py [slug ...]      (no slug = every country in countries.json except manual ones)
Needs content/<slug>.json and content/extras-<slug>.json (3 sourced bonus facts)."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
COUNTRIES = json.load(open(os.path.join(HERE, "countries.json")))
OUT = os.path.join(HERE, "captions.json")

TEASE = {"yes": "Spoiler: yes, and it goes back further than you think.",
         "sort of": "The answer is… sort of. And the story is better for it.",
         "barely": "Barely. But the country never stopped dancing.",
         "not really": "Not really. But wait until you see how they dance instead.",
         "growing": "It’s growing. And the story is just getting started."}
HANDLES = {}  # guest name -> "@handle"
EMOJI = [(r"break|b-boy|b-girl|hip-hop|hip hop|freestyle|street dance", "🕺"),
         (r"salsa|ballroom|latin|cha-cha|couple|dancesport|nationals|championship", "💃"),
         (r"manga|anime|film|cinema|screen", "🎬"), (r"mask", "🎭"),
         (r"festival|moussem|celebrat|carnival|guelaguetza", "🎉"),
         (r"drum|music|radio|tape|khaen|accordion|band", "🥁"), (r"unesco|heritage", "🏛️")]
HASHTAGS = "#BreakTheRoutine #DanceSport #Ballroom #LatinDance #WorldAtlas #{tag} #DanceCulture #DancePodcast"

def emoji(t):
    for pat, e in EMOJI:
        if re.search(pat, t, re.I):
            return e
    return "✨"

def clean(s):
    return re.sub(r"\*\*|==", "", s)

def build(slug):
    c = COUNTRIES[slug]
    name, guest, no = c["display"], c["guest"], c["no"]
    content = os.path.join(HERE, "content", f"{slug}.json")
    ans = json.load(open(content))["s2"]["answer"].rstrip(".").lower() if os.path.exists(content) else "yes"
    bonus = json.load(open(os.path.join(HERE, "content", f"extras-{slug}.json")))["bonus"][:3]
    who = HANDLES.get(guest, guest)
    extra = "\n".join(f"{emoji(b['text'])} {clean(b['text'])}" for b in bonus)
    ig = (f"World Atlas No. {no:02d}: {who} opened the atlas and landed on {name}.\n\n"
          f"Is there Latin & Ballroom in {name}? {TEASE.get(ans, '')} Swipe through.\n\n"
          f"{extra}\n\n"
          f"Are you a dancer from {name}, or do you dance there? Tell us what we missed in the comments, "
          f"and tag a dancer from {name} who should see this.\n\n"
          f"Full episode with {who} on YouTube and Spotify, link in bio.")
    return {"instagram": ig, "tiktok": ig + "\n\n" + HASHTAGS.format(tag=c["tag"])}

if __name__ == "__main__":
    slugs = sys.argv[1:] or [s for s, c in COUNTRIES.items() if not c.get("manual")]
    caps = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for s in slugs:
        caps[COUNTRIES[s]["name"]] = build(s)
        print(s, len(caps[COUNTRIES[s]["name"]]["instagram"]))
    json.dump(caps, open(OUT, "w"), ensure_ascii=False, indent=1)
