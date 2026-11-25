# f1.h reels

The renderer behind the race videos of [f1.h](https://manasjha.online/f1/), a public Formula 1 forecast scored after
every race. Each reel is generated frame by frame from the site's public data, drawn natively at 4K (120 fps master),
cut to an original soundtrack with a synthesized F1 engine (no recordings, no samples).

    bash web/scripts/make-video.sh result https://manasjha.online/f1/ f1h-R21-result

## Credits
- 3D car models: by Dave Love and others on Sketchfab, CC BY 4.0, adapted (each credit is in
  `web/assets/cars/manifest.json` and in every video's credit line).
- three.js: MIT licence (`web/vendor/three/LICENSE`).
- Driver photos in the videos are loaded from Formula 1's image service at render time and are not stored here.
- Music and engine sound: original, generated in code (`web/scripts/make-music.py`, `web/scripts/video/engine.py`).
