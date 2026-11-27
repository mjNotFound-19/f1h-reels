#!/usr/bin/env bash
# Reels generated from the published site's data (web/scripts/render-video.mjs), frame by frame, drawn natively at
# 4K, cut on the beat of an original soundtrack with a synthesized F1 engine. Plan: web/scripts/video/PLAN.md.
#   bash web/scripts/make-video.sh forecast [url] [name]     before a race: lights, the favourite's car, the top five, circuit, plan
#   bash web/scripts/make-video.sh sprint   [url] [name]     sprint weekend: the same, from the sprint forecast
#   bash web/scripts/make-video.sh result   [url] [name]     after a race: lights out on the winner's car, podium, verdicts, season
# Writes docs/video/:
#   <name>-4k.mp4            master: 3840 x 2160, 120 fps, with sound
#   <name>-linkedin.mp4      3840 x 2160, 60 fps (LinkedIn takes up to 60)
#   <name>.mp4               1920 x 1080, 60 fps
#   <name>-story.mp4         Instagram story: 1080 x 1920, 60 fps (Instagram's limits), drawn at 4K and downscaled
#   <name>-story-4k.mp4      the story at 2160 x 3840, 60 fps
#   <name>-thumbnail.jpg     the poster frame (also frame 0 of each video)
# Cloud settings (env): REEL_ONLY=story|wide, REEL_FPS (16:9 frame rate, default 120), REEL_STORY_DPR (story pixel density, default 2)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
KIND="${1:?forecast, sprint or result}"
URL="${2:-https://manasjha.online/f1/}"
NAME="${3:-f1h-$KIND}"
[ "$KIND" = forecast ] || [ "$KIND" = sprint ] || [ "$KIND" = result ] || { echo "kind must be forecast, sprint or result"; exit 1; }
OUT="$ROOT/docs/video"
cd "$ROOT"
mkdir -p "$OUT"
X264=(-c:v libx264 -pix_fmt yuv420p -movflags +faststart)

if [ "${REEL_ONLY:-}" != story ]; then                     # REEL_ONLY=story: only the Instagram story
# 16:9, native 4K at 120 fps, with the soundtrack
node web/scripts/render-video.mjs "$KIND" "$URL" docs/video | tee "$OUT/$NAME-render.log"
python web/scripts/video/soundtrack.py "$OUT/frames/cues.json" "$OUT/$NAME.wav"
cd "$OUT/frames"
cp poster.jpg "../$NAME-thumbnail.jpg"
ffmpeg -v error -y -f concat -safe 0 -i list.txt -i "../$NAME.wav" -vf "fps=${REEL_FPS:-120}" "${X264[@]}" -preset medium -crf 16 \
  -c:a aac -b:a 256k -shortest "../$NAME-4k.mp4"
cd "$OUT"
rm -rf frames
ffmpeg -v error -y -i "$NAME-4k.mp4" -vf "fps=60" "${X264[@]}" -preset medium -crf 17 -c:a copy "$NAME-linkedin.mp4"
ffmpeg -v error -y -i "$NAME-4k.mp4" -vf "fps=60,scale=1920:1080:flags=lanczos" "${X264[@]}" -preset slow -crf 17 -c:a copy "$NAME.mp4"

fi

if [ "${REEL_ONLY:-}" != wide ]; then                      # REEL_ONLY=wide: only the 16:9 videos
# 9:16 story, drawn at 2160 x 3840, 60 fps, with the soundtrack
cd "$ROOT"
REEL_DPR="${REEL_STORY_DPR:-${REEL_DPR:-2}}" node web/scripts/render-video.mjs "$KIND" "$URL" docs/video story | tee -a "$OUT/$NAME-render.log"
python web/scripts/video/soundtrack.py "$OUT/frames/cues.json" "$OUT/$NAME-story.wav"
cd "$OUT/frames"
ffmpeg -v error -y -f concat -safe 0 -i list.txt -i "../$NAME-story.wav" -vf "fps=60" "${X264[@]}" -preset medium -crf 17 \
  -c:a aac -b:a 256k -shortest "../$NAME-story-4k.mp4"
cd "$OUT"
rm -rf frames
ffmpeg -v error -y -i "$NAME-story-4k.mp4" -vf "scale=1080:1920:flags=lanczos" "${X264[@]}" -preset slow -b:v 5000k -maxrate 7000k -bufsize 14000k \
  -c:a aac -b:a 192k "$NAME-story.mp4"
fi
rm -f "$NAME.wav" "$NAME-story.wav"
if [ "${REEL_ONLY:-}" = story ]; then echo "video: $OUT/$NAME-story.mp4"; exit 0; fi
ffprobe -v error -show_entries stream=width,height,r_frame_rate -show_entries format=duration,size -of csv=p=0 "$NAME-4k.mp4"
echo "video: $OUT/$NAME-4k.mp4"
