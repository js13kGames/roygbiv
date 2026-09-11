#!/usr/bin/env bash
# Extract the entire silent Wavedash clip as a looping GIF.
set -euo pipefail
cd "$(dirname "$0")/.."
ffmpeg -y -v error -i media/gameplay-wavedash.mp4 \
  -filter_complex '[0:v]fps=15,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=none' \
  -an -loop 0 media/gameplay.gif
