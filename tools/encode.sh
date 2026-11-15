#!/bin/bash
# SX-8 — final 20 s cut (1.5x), 1920x1080 60 fps, H.264 CRF 16, original score at -23 LUFS
set -e
cd "$(dirname "$0")/.."

N=$(ls video/c/*.jpg | wc -l)
echo "frames: $N"
if [ "$N" -lt 1200 ]; then echo "not enough frames"; exit 1; fi

# ---- video pass (no audio)
ffmpeg -hide_banner -loglevel error -y \
  -framerate 60 -start_number 0 -i video/c/%05d.jpg \
  -vf "scale=1920:1080:flags=lanczos,format=yuv420p" \
  -c:v libx264 -crf 16 -preset slow -profile:v high -level 4.2 \
  -movflags +faststart -an video/_v.mp4

# ---- audio pass: two-pass loudnorm to -23 LUFS (linear)
ffmpeg -hide_banner -loglevel error -y -i media/score.wav \
  -af "loudnorm=I=-23:TP=-2:LRA=11:measured_I=-14.31:measured_TP=0.23:measured_LRA=3.50:measured_thresh=-24.31:offset=-0.40:linear=true" \
  -ar 48000 -ac 2 video/_score_norm.wav

ffmpeg -hide_banner -loglevel error -y -i video/_v.mp4 -i video/_score_norm.wav \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest \
  -movflags +faststart "media/SX8_field_simulator_20s_1080p60.mp4"

rm -f video/_v.mp4 video/_score_norm.wav
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,r_frame_rate,sample_rate -of default=nw=1 "media/SX8_field_simulator_20s_1080p60.mp4"
