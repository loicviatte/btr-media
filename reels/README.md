# BTR reels — pipeline

Reels d'environ 30 à 60 s tirés d'un épisode, avec les sous-titres imbriqués style Diary of a CEO validés par Loïc (octobre 2026). Tout tourne dans le cloud : le Mac n'a pas besoin d'être allumé, à condition que YouTube soit dans les domaines autorisés de Claude. Sinon, voir l'étape 1, variante B.

Premier reel fait avec ce pipeline : Oti Mabuse, EP13 Part 2, « TV vs competition » (`examples/oti-p2-tv-vs-competition/`).

## 0. Installation (une fois par session)

```bash
bash reels/setup.sh
```

Le script installe les paquets Python et télécharge les modèles depuis GitHub (Parakeet, Whisper medium.en, Robust Video Matting) dans `reels/models/`. **Les polices ne sont pas dans ce repo public** (PP Monument Extended est sous licence). Il faut récupérer `PPMonumentExtended-Heavy.woff2` et `PPMonumentExtended-Regular.woff2` dans `project/fonts/` du design system BTR (artifact Claude), les mettre dans `reels/fonts/`, puis relancer `setup.sh`, qui les convertit en `.otf`.

## 1. Récupérer l'extrait (jamais l'épisode entier)

**Variante A (cloud, recommandée)** : YouTube est autorisé dans les réglages Claude (Settings → Capabilities → domaines `youtube.com` et `googlevideo.com`).

```bash
pip install -U --break-system-packages yt-dlp
yt-dlp -f 'bv*+ba/b' -S res --download-sections '*1:15:05-1:17:15' --merge-output-format mp4 -o 'work/src.mp4' 'https://www.youtube.com/watch?v=VIDEO_ID'
```

**Variante B (YouTube bloqué)** : Loïc lance la même commande dans son Terminal avec `~/BTR-SHORTS/.venv/bin/yt-dlp`, sortie dans `~/Documents/BTR_reel/`, et on récupère le fichier depuis son Mac. Arguments **entre guillemets simples** : zsh casse le `!` placé entre guillemets doubles. Penser aussi à mettre yt-dlp à jour : une vieille version prend des 403 sur `--download-sections`.

Prendre environ 20 s de marge de chaque côté du moment.

## 2. Choisir le moment

Lire le SRT de l'épisode (Google Drive, dossier de l'épisode) et choisir un moment **absent du teaser**, avec :

- une phrase choc dans les 5 premières secondes ;
- un retournement ou une chute (ex. « And I got a yacht for my husband… ») ;
- un débat qui fait réagir le milieu DanceSport dans les commentaires.

Pour une série de clips, proposer d'un coup la liste des moments à Loïc (citation d'ouverture, durée, pourquoi) avant de monter.

## 3. Transcrire l'extrait et vérifier les passages douteux

```bash
python3 reels/transcribe.py work/src.mp4 work/src_words.json --check 45-62.5 93-107
```

`--check` fait réécouter les fenêtres données par Parakeet **et** Whisper. **Règle absolue : on ne sous-titre que des mots réellement dits.** Couper est permis (bégaiements, « you know », phrases entières), ajouter jamais. Un passage que les deux modèles n'entendent pas pareil est **retiré du montage** (ex. la phrase « …bread » chez Oti).

## 4. Les coupes et le recadrage

```bash
python3 reels/find_heads.py work/src.mp4 46 50 57 63 94 105 114   # position de la tête par plan
```

Ensuite, écrire `cuts.json` (voir l'exemple) : segments `[in, out, "W"|"T", head_cx]`, coupes placées dans les silences (regarder l'énergie audio autour de chaque point), en alternant **W** (large) et **T** (serré) à chaque coupe. Un plan de réaction de Marius en `cutaway` sur la chute. Le dernier segment s'arrête net sur le dernier mot, pour que la boucle reparte.

```bash
python3 reels/edit.py cuts.json work/        # -> work/cut.mp4 (1080x1920, -14 LUFS)
```

## 5. Les sous-titres

```bash
python3 reels/transcribe.py work/cut.mp4 work/words.json           # horodatages exacts sur le MONTAGE
python3 reels/captions.py work/words.json blocks.txt work/reel.ass --end 39.3
python3 reels/check_fidelity.py work/words.json blocks.txt         # doit afficher OK
ffmpeg -i work/cut.mp4 -vf "subtitles=work/reel.ass:fontsdir=reels/fonts" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a copy -movflags +faststart work/reel.mp4
```

### Notation de `blocks.txt`

```
@ align=c|l|stair  y=2380  until=12.5  big=300  small=165
i remember we had a        <- minuscules = petits mots (Regular)
*TRAINER,                  <- MAJUSCULES = mot-choc (Heavy)
```

| Préfixe | Effet |
| --- | --- |
| `*` | or #FCDF9A |
| `/` | italique (sur les chutes) |
| `~` | lettres écartées qui se resserrent |
| `#` | surligneur or, le mot passe en noir |

Un préfixe ne vaut que pour le mot qui le porte. Une ligne vide sépare les blocs ; `@` ouvre un bloc.

- **Alignements** : alterner `c` (centré), `l` (gauche) et `stair` (escalier) d'un bloc à l'autre.
- **Liste qui s'empile** pour les anaphores : mettre plusieurs lignes dans le même bloc, elles s'accumulent.
- Éviter les longues lignes qui mélangent petits et gros mots : la ligne est réduite pour tenir et les petits mots deviennent illisibles. Couper en deux lignes.
- Chaque effet une ou deux fois par reel, pas plus.

### Écarté par Loïc (ne pas réintroduire)

Effet d'atterrissage (mot qui arrive en gros puis rebondit), mot géant derrière la tête de l'invité, secousse ou zoom de caméra, compteur de chiffres.

## Repères techniques

- Source YouTube 4K souvent en AV1 : un seul graphe ffmpeg sur tout l'extrait dépasse la mémoire du sandbox, d'où le rendu par segment dans `edit.py`.
- Vidéo et audio sont rendus séparément avec un nombre d'images exact par segment : un plan de coupe remplace la fin de son segment image pour image. Ne pas utiliser `overlay`, qui laissait passer une image.
- libass : hauteur des capitales = 0,53 × fs, largeur = 0,735 × la largeur mesurée par PIL.
- Livraison : un fichier de plus de 30 Mo ne peut pas être écrit sur le Mac depuis le cloud. Envoyer le reel dans la conversation. Pour Metricool, l'héberger dans `teasers/` de ce repo (pas dans `reels/`, qui ignore les vidéos), en restant sous la limite GitHub de 100 Mo.
