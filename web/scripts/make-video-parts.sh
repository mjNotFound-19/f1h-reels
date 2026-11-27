#!/usr/bin/env bash
# The cloud version of make-video.sh: one reel format split across several machines at once (no GPU in the cloud, so
# one machine takes ~50 min for a story; N machines take ~50/N). Two stages:
#   bash web/scripts/make-video-parts.sh part  <kind> <url> <name> <story|wide> <i> <N>   render slice i of N -> docs/video/parts/seg-<i>.mp4
#   bash web/scripts/make-video-parts.sh merge <kind> <url> <name> <story|wide>           join the slices, add the soundtrack, make the files
# The files match make-video.sh's: wide -> <name>-4k.mp4, <name>-linkedin.mp4, <name>.mp4, <name>-thumbnail.jpg,
# <name>-render.log; story -> <name>-story-4k.mp4, <name>-story.mp4. Settings (env): REEL_FPS (wide frame rate), REEL_STORY_DPR.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STAGE="$1" KIND="$2" URL="$3" NAME="$4" ONLY="$5"
OUT="$ROOT/docs/video"; PARTS="$OUT/parts"
X264=(-c:v libx264 -pix_fmt yuv420p)
cd "$ROOT"; mkdir -p "$PARTS"
FPS=$([ "$ONLY" = story ] && echo 60 || echo "${REEL_FPS:-120}")

if [ "$STAGE" = part ]; then
  I="$6" N="$7"
  if [ "$ONLY" = story ]; then
    REEL_PART="$I/$N" REEL_DPR="${REEL_STORY_DPR:-${REEL_DPR:-2}}" node web/scripts/render-video.mjs "$KIND" "$URL" docs/video story
  else
    REEL_PART="$I/$N" REEL_FPS="$FPS" node web/scripts/render-video.mjs "$KIND" "$URL" docs/video
  fi
  cd "$OUT/frames"
  FIRST=$(ls f[0-9]*.jpg | sort | head -1 | tr -dc 0-9); COUNT=$(ls f[0-9]*.jpg | wc -l)   # exactly this slice's frames
  ffmpeg -v error -y -framerate "$FPS" -start_number "$((10#$FIRST))" -i f%06d.jpg -frames:v "$COUNT" "${X264[@]}" -r "$FPS" -preset medium -crf 16 -an "$PARTS/seg-$I.mp4"
  [ "$I" = 0 ] && cp cues.json "$PARTS/cues.json" && cp poster.jpg "$PARTS/poster.jpg"
  echo "segment: $PARTS/seg-$I.mp4"
  exit 0
fi

# merge: the slices in order, joined without re-encoding, then the soundtrack
cd "$PARTS"
ls seg-*.mp4 | sort -t- -k2 -n | sed "s/.*/file '&'/" > segs.txt
ffmpeg -v error -y -f concat -safe 0 -i segs.txt -c copy joined.mp4
python "$ROOT/web/scripts/video/soundtrack.py" cues.json sound.wav
FRAMES=$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 joined.mp4)
DUR=$(python -c "import json;print(json.load(open('cues.json'))['duration'])")
cd "$OUT"
if [ "$ONLY" = story ]; then
  ffmpeg -v error -y -i parts/joined.mp4 -i parts/sound.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart "$NAME-story-4k.mp4"
  ffmpeg -v error -y -i "$NAME-story-4k.mp4" -vf "scale=1080:1920:flags=lanczos" "${X264[@]}" -movflags +faststart -preset slow -b:v 5000k -maxrate 7000k -bufsize 14000k \
    -c:a aac -b:a 192k "$NAME-story.mp4"
  echo "video: $OUT/$NAME-story.mp4"
else
  # the same summary line a whole render prints: the agent checks the frame rate from it
  python -c "print(f'frames: $FRAMES over {float($DUR):.1f} s = {float($FPS):.1f} fps captured (generated in parts) -> parts')" > "$NAME-render.log"
  cp parts/poster.jpg "$NAME-thumbnail.jpg"
  ffmpeg -v error -y -i parts/joined.mp4 -i parts/sound.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart "$NAME-4k.mp4"
  if [ "$FPS" = 60 ]; then cp "$NAME-4k.mp4" "$NAME-linkedin.mp4"
  else ffmpeg -v error -y -i "$NAME-4k.mp4" -vf "fps=60" "${X264[@]}" -movflags +faststart -preset medium -crf 17 -c:a copy "$NAME-linkedin.mp4"; fi
  ffmpeg -v error -y -i "$NAME-4k.mp4" -vf "fps=60,scale=1920:1080:flags=lanczos" "${X264[@]}" -movflags +faststart -preset slow -crf 17 -c:a copy "$NAME.mp4"
  cat "$NAME-render.log"
  echo "video: $OUT/$NAME-4k.mp4"
fi
rm -rf parts frames
