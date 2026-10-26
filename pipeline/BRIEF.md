# Brief: BTR "World Atlas" Instagram carousel — research one country

Break The Routine (BTR) is a DanceSport (competitive Latin & Ballroom) podcast. Each episode, the guest opens a world atlas and lands on a country. We publish an 8-slide Instagram carousel: "How does <COUNTRY> dance?". Audience: ballroom/Latin dancers and fans. Tone: curious, warm, punchy, respectful. Public copy is in ENGLISH. No emoji.

Your job: research ONE country and write the slide copy as a JSON file. Every fact must come from a source you actually opened this session (WebSearch then WebFetch). Never write a number, date or name from memory. Prefer authoritative sources: UNESCO Intangible Cultural Heritage pages, national/world dance federations (WDSF worlddancesport.org member list, national dancesport federations), government/tourism boards, reputable press, Wikipedia only as a last resort (and cross-check its key claims). If something cannot be verified, leave it out. Accuracy beats sparkle.

Be honest on slide 2: if the country has little or no Latin & Ballroom scene, say so ("NOT REALLY.", "BARELY.", "GROWING.", "SORT OF.") and explain what exists instead (e.g. salsa clubs, a small federation, a single studio, diaspora dancers). Check whether the country has a WDSF member federation. Respectful: no stereotypes, no mockery, no political or religious judgement; if dance is socially sensitive somewhere, state facts neutrally.

## Hard length limits (the font is extremely wide: ~1 em per capital letter)
- Any field marked LINE: max 12 characters (incl. spaces/punctuation).
- KEY words: max 9 characters, ideally 4–7. They are auto-sized, shorter = bigger.
- Paragraphs ("p…"): max 170 characters each. Short sentences.
- "meta": max 34 characters, CAPITALS, parts separated by " · ".
- Dance "name": max 12 characters, CAPITALS (if longer, use the common short name).
- "number": max 7 characters (e.g. "13,000", "1.3M", "62", "400+").
- Inline markup in paragraphs: **bold** for 1–3 key words, ==gold== for at most one highlight per slide.

## JSON shape (write exactly these keys)
{
  "country": "JAPAN",                 // CAPITALS, the English name as it should appear huge on the cover (max 12 chars; e.g. "PNG" is NOT ok, write "PAPUA NEW GUINEA" only if you put it in "country_lines")
  "country_lines": ["JAPAN"],         // 1 or 2 lines for the cover title, each max 10 chars (e.g. ["PAPUA NEW","GUINEA"] or ["SÃO TOMÉ &","PRÍNCIPE"])
  "s2": { "answer": "YES.", "p1": "...", "p2": "..." },          // Latin & Ballroom? + history/what exists
  "s3": { "number": "13,000", "line1": "ballroom", "line2": "coaches", "p": "..." },   // one big striking number about dance there (LINE fields lowercase ok)
  "s4": { "top": "Shall We", "key": "DANCE?", "bottom": "1996", "p1": "...", "p2": "..." },   // the pop/iconic moment: a film, a star dancer, a famous troupe, a viral moment, a world champion. top/bottom are LINEs, key is a KEY
  "s5": [ { "name": "BON ODORI", "meta": "≈ 600 YEARS · EVERY SUMMER", "p": "..." },
          { "name": "AWA ODORI", "meta": "400+ YEARS · TOKUSHIMA", "p": "..." } ],   // exactly 2 typical/traditional dances
  "s6": { "top": "No", "key": "DANCING", "bottom": "after midnight", "y1": "1948", "y2": "2015", "p": "..." },  // the surprising cultural fact. y1/y2 optional (omit or "" if no date span fits); top/bottom LINEs
  "s7": { "year": "2012", "line1": "Dance becomes", "line2": "compulsory", "p": "...", "tag": "PARIS 2024", "p2": "..." },  // a key date + a recent news item (tag max 16 chars). line1/line2 max 13 chars each
  "sources": [ { "claim": "short description", "url": "https://..." } ]   // one entry per fact used
}

## Reference example (Japan, already published)
{"country":"JAPAN","country_lines":["JAPAN"],
 "s2":{"answer":"YES.","p1":"Ballroom arrived in **1883**, at Tokyo’s **Rokumeikan**: a Western-style hall built to impress foreign diplomats.","p2":"Waltz, polka, quadrille and mazurka, taught by foreigners living in Tokyo."},
 "s3":{"number":"13,000","line1":"ballroom","line2":"coaches","p":"are registered with the **Japan Ballroom Dance Federation** (JBDF), across **46 branches** from Hokkaido to Kyushu."},
 "s4":{"top":"Shall We","key":"DANCE?","bottom":"1996","p1":"A Tokyo salaryman takes ballroom lessons **in secret**, because in Japan it was seen as embarrassing.","p2":"The film won ==13 Japanese Academy Awards==. Hollywood remade it in **2004** with Richard Gere and Jennifer Lopez."},
 "s5":[{"name":"BON ODORI","meta":"≈ 600 YEARS · EVERY SUMMER","p":"Everyone dances in a **circle** around the yagura tower, to welcome the spirits of the ancestors during Obon."},
       {"name":"AWA ODORI","meta":"400+ YEARS · TOKUSHIMA · 12–15 AUG","p":"A street dance parade watched by **1.3 million** people. Its song says: if you’re a fool watching, you might as well be a fool dancing."}],
 "s6":{"top":"No","key":"DANCING","bottom":"after midnight","y1":"1948","y2":"2015","p":"For **67 years**, a post-war law banned dancing in Japanese clubs after midnight. It was only lifted in 2015, ahead of the Tokyo Olympics."},
 "s7":{"year":"2012","line1":"Dance becomes","line2":"compulsory","p":"Every junior high school in Japan now teaches dance in PE: **creative, folk and modern rhythm** dance.","tag":"PARIS 2024","p2":"B-Girl **Ami Yuasa** becomes the first women’s Olympic champion in breaking."},
 "sources":[...]}

Notes: s4 top/key/bottom read as one phrase in quote marks (“Shall We DANCE? 1996”), so make them read naturally together, e.g. top "The", key "GNAWA", bottom "on stage". s6 also reads as one phrase in quotes (“No DANCING after midnight”). Use real curly apostrophes (’). Do not invent a fact to fill a slot: pick a different true angle instead.

Write the file with the Write tool, then reply with just: the file path, and one line per slide flagging anything you were unsure about.
