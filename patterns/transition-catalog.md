# Transition Catalog

**What this file owns:** *which* transition serves *which* moment in a product video, and how much
transition energy one film may spend. That is a directorial judgment about product-video pacing,
and it is nearly all that is left here — the exception is one markup prohibition (§ The markup rule
with no upstream owner) that no upstream page states and no other file in this repo carries.

**What it does not own:** the mechanics. How a seam is constructed, how two scenes composite across
it, what parameters a named seam takes — every one of those has an upstream owner now (§ Where the
mechanics live). Where this file and one of those disagree, **they win**; a mechanic re-stated here
would be a fork with no maintainer.

## Picking by mood

| Moment in the video | Reach for | Why |
|---|---|---|
| Default scene-to-scene cut | **Crossfade** or **Blur Crossfade** | Quiet, professional. Default of the dissolve family. |
| Section boundary (Hook → Pain, Solution → Features) | **Light Leak** or **Flash through White** | Signals "new chapter" without overpowering — light family. |
| Hero / product reveal | **Cinematic Zoom** or **Zoom Through** | Earns the visual flourish — scale family. |
| Stat or proof moment | **Chromatic Radial Split** or **Diamond Iris** | Energetic, pulls eye to the centre — radial family. |
| Before / after, competitor comparison | **Diagonal Split** or **Push Slide** | Spatial metaphor for "this vs that" — radial + push families. |
| Editorial pull-quote | **Focus Pull** or **Color Dip** | Cinema-y, soft. Dissolve family. |
| Drama / tension reveal | **Glitch** or **Page Burn** | Use ONCE per video at most — distortion + destruction families. |
| Mechanical / countdown | **Shutter** or **Clock Wipe** | Editorial gravitas — mechanical family. |
| Closing fade-to-end-card | Plain **Crossfade** to a held final frame | Never use a "flashy" transition on the final exit. |

The names above are moment-to-look mappings, not identifiers this file defines. A **family** name
resolves through `TRANSITION_FAMILIES`; a **shipped block** name resolves through
`REGISTRY_CATALOG`; for upstream's own energy/mood selection guidance read `TRANSITION_OVERVIEW`.

**`transition_style: metallic-swoosh`** — the brief vocabulary keeps this name. The look it asks
for is a full-frame light overlay riding a crossfade at a section boundary, which is the **light**
family; take the implementation from `TRANSITION_FAMILIES` rather than re-deriving an overlay
locally. Confirm the style with the user as before, then wire the family recipe.

> **`shimmer-sweep` is not a transition.** `REGISTRY_CATALOG` lists it as a *component* tagged
> `text, shimmer, highlight, effect` — an element-scoped gradient sweep. It serves the in-scene
> card shine (`patterns/visual-patterns.md` § In-Scene Shine Sweep) and cannot straddle two scene
> wrappers. Earlier revisions of this repo called it the cousin of the retired hand-authored
> swoosh; that was wrong, and wiring it as a seam yields a decoration on one element while every
> gate stays green.

**Reach for a shipped block before hand-authoring.** `flash-through-white`,
`chromatic-radial-split` and `cinematic-zoom` are real inter-scene transition blocks — tested,
deterministic and aspect-ratio-aware — and cover most needs above. `REGISTRY_CATALOG`
(`hyperframes-registry`) is the authoritative list of names `npx hyperframes add` accepts, and the
place to confirm a name is a transition rather than a component before you wire it as one; this
file deliberately keeps no copy of that inventory, nor of which named transition sits in which
family. `REGISTRY_BLOCKS` and `REGISTRY_ADD_EXAMPLE` cover the wiring;
`workflows/phase-4-production.md` Step 4.2 is the local call site.

## Energy budget

Transitions are a spend, not a decoration. The **numbers** — one primary style plus a small number
of accents across a film, and the rest of the cognitive-load limits — live in exactly one place:
the budget table in `reasoning/scene-analysis.md` (ADR-008). Read them there; the judgment for
spending them is here.

1. **Default to invisible.** Most cuts in a product video should not be noticed. A transition the
   viewer *sees* has to be paying for something — a new chapter, a reveal, a proof beat. Everything
   else is a crossfade.
2. **Match energy to the moment, not to the shot list.** A 0.4s glitch into a pricing table is
   wrong; a 0.4s glitch into "your data is everywhere" is right. Transition energy should track the
   `energy:` curve between adjacent frames, which is what the budget table checks it against.
3. **Match duration to total runtime when *recommending* a speed.** A 30s spot wants transitions
   around a half-second; a 60s spot can carry longer ones; past a second the film starts to read as
   sluggish. This is advice for the recommendation you make in Phase 1 — once `transition_speed` is
   confirmed in the brief, the confirmed value binds (ADR-001). Never silently shorten a `slow`
   the user deliberately chose.
4. **Spend the loud ones early-to-middle.** A flourish in the first third sets a register; the same
   flourish in the last beat competes with the CTA.
5. **Land a flourish on a narrative boundary, never mid-sentence.** A section transition announces
   a chapter; firing it while the voiceover is mid-thought contradicts the words and reads as a
   mistimed edit rather than a beat. Cut it to the boundary in the script, not to a round number.
6. **Never run two flourishes back-to-back**, even when the count is still under budget. The second
   one stops registering as an event — the viewer reads "this video does that" and tunes it out.
   Put a quiet crossfade between them for breathing room.
7. **Do not transition out of the closing scene.** The video ends on a held frame, not a flourish.

## Banned — tried here, they look fake

Local craft judgment, not an upstream rule. These are available upstream and still not worth it in
a product video:

- **Star iris** — polygon interpolation is visibly broken at the vertices.
- **Tilt-shift** — there is no selective CSS blur that survives a seek; the result reads as a
  uniform smear.
- **Lens flare** — renders as a visible *shape* rather than an optical artifact.
- **Hinge / door** — distorts far too fast to read at product-video pacing.

## The markup rule with no upstream owner

Local law, and the one piece of mechanism this file still states — because nobody else states it.
`hyperframes-core` → `DATA_ATTRIBUTES` gives the *positive* form (`class="clip"` is **required** on
a visible timed element, and such clips must be direct children of their composition root;
`<video>` and `<audio>` are exempt), and `SUB_COMPOSITIONS` gives which attributes a host slot
carries versus the attributes of the loaded file's own root. Neither states the prohibition those
two imply for this skill's file layout, and a builder who reads only the positive form marks a
scene root as a clip:

- **A scene file's own root `<div>` is not a clip.** No `class="clip"`, no `data-start`, no
  `data-duration` on it — it carries `data-composition-id` + `data-width` + `data-height`, and
  that is all. A scene's *timing* is declared exactly once, on its loader slot in the root
  `index.html`. Timing attributes on a scene root declare a window nothing renders by
  (`DATA_ATTRIBUTES` explains why an element that is not a direct child of the composition root is
  never registered as a clip), so the scene reads as if it owned its own window while only the
  loader's window is real — every gate stays green (verified, `GATE_BLIND_SPOTS`; note the
  adjacent case behaves oppositely — timing attributes on a *direct child of the composition
  root* without `class="clip"` are a lint **error**), and the two numbers drift apart the first time
  one of them changes.

The single exception is the `<video>` inside a clip scene, which **does** carry its own
`data-start`/`data-duration`/`data-media-start`/`data-track-index` and must never be stripped. That
contract is owned by `workflows/phase-3-design.md` § Clip scene and is not restated here.

## Where the mechanics live

Nothing in this section is restated locally. Load the owner.

| You need | Owner | Cite |
|---|---|---|
| The law of the seam — how Scene A's exit determines Scene B's entry (axis, direction, speed, phase) | `motion-doctrine` | `SEAM_LAW` |
| Numeric verification of the assembled seams | `motion-doctrine` | `SEAM_VERIFIER` (and `SEAM_STAMP` to pass by construction) |
| Render-side compositing — the opaque stage-ground white-flash guard, how wrapper overlap, track ping-pong and the incoming/outgoing blend actually work | `seam-craft` | `SEAM_RENDER_MECHANICS` |
| The named velocity-matched seams and their parameters | `cut-the-curve` | `CUT_CATALOG` |
| Track/clip timing — unique `data-track-index` for overlapping scenes, clip windows | `hyperframes-core` | `TRACKS_AND_CLIPS` |
| Why a transition may never animate `display`/`visibility` or call `.play()` | `hyperframes-core` | `DETERMINISM_RULES` |
| The normative CSS-transition page: hard rules, scene template, shader rules | `hyperframes-animation` | `TRANSITION_CATALOG` |
| Per-family implementations behind the family names above | `hyperframes-animation` | `TRANSITION_FAMILIES` |
| Selection guidance from upstream's own point of view | `hyperframes-animation` | `TRANSITION_OVERVIEW` |
| The machine-readable registry (a curated subset, **not** the full catalog) | `hyperframes-animation` | `TRANSITION_REGISTRY` |

`SEAM_LAW` **supersedes** any local transition guidance where the two disagree. `CUT_CATALOG`
supplies the parameters underneath it. `SEAM_RENDER_MECHANICS` is the render-side prerequisite that
makes either composite correctly — including the stage-ground rule, which is why this file no
longer carries an opinion about what colour the page behind the scenes should be.

Every path behind those symbols is resolved by `compat/ecosystem.md`, and lives nowhere else
(ADR-007).
