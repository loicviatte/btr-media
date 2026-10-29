"""Cut list -> 9:16 reel (no captions), frame-accurate.

usage:  python3 edit.py cuts.json work_dir/   ->  work_dir/cut.mp4

cuts.json:
{
  "src": "oti_p2_moment.mp4",                 # 16:9 source (4K from YouTube)
  "fps": 25,
  "segments": [ [in, out, "W"|"T", head_cx], ... ],   # seconds in the source
  "cutaway":  {"over_segment": 3, "src_in": 68.4, "dur": 1.0, "head_cx": 1702}   # optional
}
W = wide crop 1215x2160, T = tight crop 900x1600 (punch-in). Alternate W/T at each cut so
jump cuts read as camera changes. head_cx comes from find_heads.py.

Why it is built this way:
- each segment is rendered on its own (one ffmpeg graph on 4K AV1 runs out of memory);
- video and audio are rendered separately with an exact frame count per segment, then joined:
  a cutaway therefore REPLACES the end of its segment frame for frame (an overlay used to leave
  one stray frame of the speaker before the next cut);
- 12 ms / 15 ms audio fades at every cut, loudnorm -14 LUFS (social standard).
"""
import json, os, subprocess, sys

cfg = json.load(open(sys.argv[1]))
work = sys.argv[2]; os.makedirs(work, exist_ok=True)
base = os.path.dirname(os.path.abspath(sys.argv[1]))
SRC = cfg["src"] if os.path.isabs(cfg["src"]) else os.path.join(base, cfg["src"])
FPS = cfg.get("fps", 25)
CROPS = {"W": (1215, 2160, 0), "T": (900, 1600, 100)}   # w, h, y0 in a 3840x2160 source

def crop(kind, cx):
    w, h, y0 = CROPS[kind]
    x = max(0, min(3840 - w, int(cx) - w // 2))
    return f"crop={w}:{h}:{x}:{y0},scale=1080:1920:flags=lanczos,setsar=1"

def render_v(a, n, kind, cx, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", SRC, "-frames:v", str(n), "-an",
                    "-vf", crop(kind, cx), "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "12",
                    "-pix_fmt", "yuv420p", out], check=True)

def render_a(a, n, out):
    d = n / FPS
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", SRC, "-t", f"{d:.3f}", "-vn",
                    "-af", f"afade=t=in:d=0.012,afade=t=out:st={d - 0.015:.3f}:d=0.015,apad,atrim=0:{d:.3f}",
                    "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", out], check=True)

cut = cfg.get("cutaway")
vclips, aclips, total = [], [], 0
for i, (a, b, kind, cx) in enumerate(cfg["segments"]):
    a = round(a * FPS) / FPS
    n = round((b - a) * FPS)
    if cut and i == cut["over_segment"]:
        nc = round(cut["dur"] * FPS)
        render_v(a, n - nc, kind, cx, f"{work}/v{i:02d}a.mov"); vclips.append(f"{work}/v{i:02d}a.mov")
        render_v(cut["src_in"], nc, "W", cut["head_cx"], f"{work}/v{i:02d}b.mov"); vclips.append(f"{work}/v{i:02d}b.mov")
    else:
        render_v(a, n, kind, cx, f"{work}/v{i:02d}.mov"); vclips.append(f"{work}/v{i:02d}.mov")
    render_a(a, n, f"{work}/a{i:02d}.wav"); aclips.append(f"{work}/a{i:02d}.wav")
    total += n
open(f"{work}/vlist.txt", "w").write("".join(f"file '{os.path.abspath(c)}'\n" for c in vclips))
open(f"{work}/alist.txt", "w").write("".join(f"file '{os.path.abspath(c)}'\n" for c in aclips))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{work}/vlist.txt",
                "-f", "concat", "-safe", "0", "-i", f"{work}/alist.txt",
                "-map", "0:v", "-map", "1:a", "-af", "loudnorm=I=-14:TP=-1.0:LRA=11,aresample=48000",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "256k", "-shortest", f"{work}/cut.mp4"], check=True)
print(f"{work}/cut.mp4  {total} frames = {total / FPS:.2f} s")
