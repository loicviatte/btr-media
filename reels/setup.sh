#!/bin/bash
# One-time setup in a fresh cloud session (models are NOT committed: too big).
set -e
cd "$(dirname "$0")"
pip install -q --break-system-packages sherpa-onnx soundfile onnxruntime fonttools brotli pillow numpy 2>&1 | grep -v WARNING || true
mkdir -p models && cd models
R=https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models
[ -d sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8 ] || curl -sL "$R/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2" | tar xj
[ -d sherpa-onnx-whisper-medium.en ] || curl -sL "$R/sherpa-onnx-whisper-medium.en.tar.bz2" | tar xj
[ -f rvm_mobilenetv3_fp32.onnx ] || curl -sLO https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx
cd ..
# Fonts: PP Monument Extended is a licensed font -> NOT in this public repo.
# Fetch PPMonumentExtended-Heavy.woff2 and -Regular.woff2 from the BTR design system artifact
# (project/fonts/), save them in reels/fonts/, then run:
if ls fonts/*.woff2 >/dev/null 2>&1; then
  python3 - <<'PY'
from fontTools.ttLib import TTFont
import glob
for f in glob.glob("fonts/*.woff2"):
    t = TTFont(f); t.flavor = None; t.save(f[:-6] + ".otf"); print("font ->", f[:-6] + ".otf")
PY
fi
ls fonts/*.otf >/dev/null 2>&1 && echo "fonts OK" || echo "!! fonts missing: see comment above"
echo "setup done"
