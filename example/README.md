# Reference build — a 60s promo the skill made about itself

The committed output of one real `/hve-video-director` run, start to finish: Phase 0
discovery through Phase 5 render, every gate, every per-phase approval given by a human.
Nothing here is illustrative — it is what the pipeline actually produced.

Its subject is the skill itself, which makes it the honest test: the reasoning layer had
to decide how to show an *idea* with no product UI to lean on.

## What is here

| File | Phase | What it is |
|---|---|---|
| `project-plan.md` | 1 | the Creative Brief — every lever the user owns, and their answers |
| `.hve/brief-state.json` | 1–5 | the consent record: story/audio fingerprints and a stamp per phase |
| `context.md` | 0 | product, audience, angle, constraints |
| `storyboard.md` | 1 | 8 frames in the official shape, each carrying its director keys |
| `DESIGN.md` | 3 | palette, type scale, motion language |
| `scenes/*.html` | 3 | one sub-composition per frame |
| `ledger.json` | 4 | the seam ledger — four z-seams, stamped and numerically verified |
| `index.html` | 4 | the root composition that mounts all eight scenes on one clock |
| `voiceover.py` | 5 | the per-project section assembler |

Media is **not** committed (`.gitignore`): the MP4 ships as a Release asset, and audio,
transcripts, captions and review snapshots are all regenerable from what is here.

## What it demonstrates

**Runtime selection is derived, never requested.** `visual_ceiling: derived` imposed no
ceiling, and the reasoning layer still spent Three.js on exactly **one** frame of eight.
Nobody asked for 3D anywhere. The three verdicts are worth reading together:

- **Frame 6 earns it** — `cinematic-hero, perspective-camera, material-realism` with an
  `orbit-3d` camera. The viewpoint travels and the surface finish carries meaning, and
  neither survives being flattened.
- **Frame 5 rejects it** — *"`spatial-depth` alone is served by GSAP's 2.5D layering.
  Real occlusion would cost a hero beat and add nothing the viewer must understand
  here."* Depth was present; it just did not need three dimensions.
- **Frame 6 also rejects `html-in-canvas`** — *"it elevates a real captured surface, and
  `product_surface: none` means there is none to elevate."* A capability the film cannot
  feed is not a capability it has.

A rejection carrying its reason is the point: without it, "no 3D here" is indistinguishable
from never having considered it.

**Seams are numbers, not adjectives.** `ledger.json` holds four `zoom-through` seams;
Phase 4 stamped them and `SEAM_VERIFIER` checked axis, direction and speed match at each
cut. `lint` and `check` pass a mirrored seam happily — the ledger is why they cannot.

**The brief is the consent record.** Every lever in `project-plan.md` was answered by the
user. `music_strategy: freesound` pins an exact CC0 track by URL and numeric sound ID.

## Reproducing the render

```bash
export ELEVENLABS_API_KEY=...            # narration; or pick a local Kokoro voice
export FREESOUND_API_KEY=...             # only if re-searching music

npx hyperframes lint      .              # fast structural check
npx hyperframes check     .              # required gate: runtime, layout, motion, contrast
python3 ../scripts/generate_voiceover.py --assemble-only
npx hyperframes render    .              # writes out/final.mp4
```

The exact mix recipe and the caption review contract are in
`workflows/phase-5-audio.md`; audio is deliberately not a single command, because the
exact-track confirmation and caption approval are gates a human passes.

## What it is not

Not a template to copy. Scene HTML here answers *this* film's storyboard; the skill
writes new scenes per run from the frame packets. Read it to see what a finished run
looks like, not to reuse its markup.

## It is allowed to be wrong

`keys-audit`, written two milestones after this run, reports four findings here: frames 2 and 7
carry `capabilities: —` and frame 6 carries `motion: —` with no `blueprint:` — the em dash copied
from a grammar table's "adds nothing beyond the baseline" convention, where on a frame it is not a
value. The key contract already forbade it the day this storyboard was written; no check existed to
say so, and the two grammar files that taught the reading have since been corrected.

They are not fixed, and will not be. An artifact edited to pass a check is a fixture, and a fixture
proves nothing. What a defect found later in a frozen record demonstrates is exactly the thing this
directory exists to demonstrate: the audit sees something a full human approval pass did not.
