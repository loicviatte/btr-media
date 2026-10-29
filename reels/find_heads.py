"""Where is the speaker's head? (for 9:16 reframing)

usage:  python3 find_heads.py source.mp4 45.5 50 57 63 ...
prints, for each time: head centre x and top y in SOURCE pixels (3840x2160 assumed scale).
Uses Robust Video Matting (person matte) — the head is the top of the matte.
"""
import subprocess, sys, os, json
import numpy as np, onnxruntime as ort

HERE = os.path.dirname(os.path.abspath(__file__))
sess = ort.InferenceSession(os.path.join(HERE, "models", "rvm_mobilenetv3_fp32.onnx"))
src = sys.argv[1]
probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip().split(",")
SW, SH = int(probe[0]), int(probe[1])
w, h = 960, 540
out = {}
for t in map(float, sys.argv[2:]):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", src, "-frames:v", "1", "-vf", f"scale={w}:{h}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.uint8).reshape(h, w, 3).transpose(2, 0, 1)[None].astype(np.float32) / 255
    z = np.zeros([1, 1, 1, 1], np.float32); rec = [z] * 4
    for _ in range(3):   # a few passes let the recurrent state settle on a still frame
        fgr, pha, *rec = sess.run(None, {"src": x, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3],
                                         "downsample_ratio": np.array([0.5], np.float32)})
    a = pha[0, 0] > 0.5
    rows = np.where(a.sum(1) > 8)[0]
    if not len(rows):
        print(t, "no person"); continue
    top = rows.min(); xs = np.where(a[top:top + 60].any(0))[0]
    cx = (xs.min() + xs.max()) / 2
    out[t] = (round(cx * SW / w), round(top * SH / h))
    print(f"{t:7.2f}  head_cx={out[t][0]}  head_top={out[t][1]}")
