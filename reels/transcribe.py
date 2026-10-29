"""Word-level transcription (Parakeet TDT 0.6b v2) + optional Whisper cross-check.

usage:
  python3 transcribe.py video_or_audio out_words.json [--check 45.0-62.5 93-107 ...]

- out_words.json : [[word, start_seconds], ...]
- --check        : windows (seconds) re-transcribed by BOTH Parakeet and Whisper medium.en and
                   printed side by side. A line the two models do not hear the same way is
                   left out of the reel (rule: never subtitle a word we are not sure was said).
Models are downloaded by setup.sh into ./models.
"""
import argparse, json, os, subprocess, tempfile
import sherpa_onnx, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
M = os.path.join(HERE, "models")
PK = os.path.join(M, "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8") + "/"
WH = os.path.join(M, "sherpa-onnx-whisper-medium.en") + "/"

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--check", nargs="*", default=[])
ap.add_argument("--threads", type=int, default=os.cpu_count() or 2)
args = ap.parse_args()

wav = tempfile.mktemp(suffix=".wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.src, "-ac", "1", "-ar", "16000", wav], check=True)
audio, sr = sf.read(wav, dtype="float32")

pk = sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=PK + "encoder.int8.onnx", decoder=PK + "decoder.int8.onnx", joiner=PK + "joiner.int8.onnx",
    tokens=PK + "tokens.txt", model_type="nemo_transducer", num_threads=args.threads)

def words_of(rec, seg, off):
    s = rec.create_stream(); s.accept_waveform(sr, seg); rec.decode_stream(s)
    out, cur = [], None
    for t, ts in zip(s.result.tokens, s.result.timestamps):
        if t.startswith(" ") or t.startswith("▁") or cur is None:
            if cur and cur[0]: out.append(cur)
            cur = [t.strip(" ▁"), round(ts + off, 2)]
        else:
            cur[0] += t
    if cur and cur[0]: out.append(cur)
    return out

# Short clips (a reel, an extract) in one pass. Longer audio in ~30 s windows whose
# boundaries are snapped to the quietest point nearby, so no word is cut in half.
import numpy as np
dur = len(audio) / sr
if dur <= 180:
    bounds = [0.0, dur]
else:
    bounds, t = [0.0], 30.0
    while t < dur - 5:
        cands = np.arange(t - 2.0, t + 2.0, 0.05)
        q = min(cands, key=lambda x: float(np.sqrt(np.mean(audio[int(x * sr):int((x + 0.2) * sr)] ** 2))))
        bounds.append(float(q) + 0.1); t = bounds[-1] + 30.0
    bounds.append(dur)
words = []
for a, b in zip(bounds[:-1], bounds[1:]):
    words += words_of(pk, audio[int(a * sr):int(b * sr)], a)
json.dump(words, open(args.out, "w"))
print(" ".join(f"{w}@{t:.1f}" for w, t in words))

if args.check:
    wh = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=WH + "medium.en-encoder.onnx", decoder=WH + "medium.en-decoder.onnx",
        tokens=WH + "medium.en-tokens.txt", language="en", task="transcribe", num_threads=args.threads)
    for win in args.check:
        a, b = map(float, win.split("-"))
        seg = audio[int(a * sr):int(b * sr)]
        for name, rec in (("parakeet", pk), ("whisper ", wh)):
            s = rec.create_stream(); s.accept_waveform(sr, seg); rec.decode_stream(s)
            print(f"[{name} {a}-{b}] {s.result.text}")
os.remove(wav)
