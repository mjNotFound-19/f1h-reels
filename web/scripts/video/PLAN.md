# f1.h reels: plan

Generated for every race from `site.json` by `render-video.mjs`: a template, not one video. Every frame is a pure
function of time, and the cut is locked to the soundtrack's tempo.

- **What it is:** a public F1 forecast, scored after every race. **For:** F1 fans and data people.
- **Different because:** it is checked in public against the starting grid, race after race.
- **Hook:** the red start lights come on one per beat, then lights out and the answer slams in.
- **Tone:** motorsport broadcast. Big type, cuts on the downbeat, team-colour wipes, speed streaks, a light sweep.
- **Identity:** the site's colours and fonts (Tektur, Fira Code), real driver photos, real numbers. Nothing invented.
- **Tempo:** 126 BPM; one bar is 1.905 s; 11 bars make 21 s. Scenes start on a bar.

## Result reel
| Bars | Scene |
|---|---|
| 0-1 | Lights on the beats; lights out on bar 2: "VERSTAPPEN WINS" slams in |
| 2 | The winner holds: photo push-in, race and grid slot, forecast win chance |
| 3-4 | Podium: team-colour wipe, blocks rise P3, P2, P1 on the beats |
| 5-6 | "Did the model call it?": three verdicts land on the beats |
| 7-8 | The season: race bars cascade, "closer than the grid in N of M races" |
| 9-10 | End card and final hit |

## Forecast reel
| Bars | Scene |
|---|---|
| 0-1 | Lights, lights out: "WHO WINS QATAR?" |
| 2-3 | The favourite: photo, name, win chance counting up |
| 4-5 | The top five: win-chance bars on the beats |
| 6-7 | The circuit draws itself and a car laps it |
| 8 | The likeliest plan: tyres pop in on the beats |
| 9-10 | End card |

## Sound (Instagram story)
Original and generated in code (`soundtrack.py`): 126 BPM, D minor, no samples. The reel exports its cues (light
ticks, lights out, wipes, verdicts, end hit); the effects are tuned to D minor and sit under the music. The 16:9
version for LinkedIn stays silent, as it autoplays muted there.

## Checks
Stills of every scene and mid-transition, in both formats, before the full render. Poster: the settled
lights-out frame, baked in as frame 0.
