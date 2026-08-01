# Scene Analysis

The director's core instrument. Run in Phase 1 for every storyboard frame (after beats exist,
before capture planning) and re-checked in Phase 3 before scene direction is packetized. Its
output is a closed set of **director keys** written onto the frame.

Optimization order is fixed (ADR-008): **comprehension → retention → engagement**. Honesty,
consent, and determinism are constraints, never traded against any of the three.

## The twelve questions

Answer all twelve for every frame. One line each, no essays — the answers *are* the plan.

| # | Question | Key | Value vocabulary |
|---|---|---|---|
| 1 | What must the viewer **understand** when this frame ends? | `goal:` | one sentence, viewer's perspective |
| 2 | What **abstraction level**? | `abstraction:` | `literal` (real product) · `analog` (mock UI) · `metaphor` (invented visual) · `symbolic` (type/data only) |
| 3 | How **complex** is the idea? | `complexity:` | `atomic` · `compound` · `systemic` — a systemic idea gets progressive disclosure or splits into two frames |
| 4 | What **emotional tone** serves the beat? | `tone:` | one word, drawn from the Phase-0 emotional journey |
| 5 | What **energy / pacing**? | `energy:` | `calm` · `build` · `peak` · `resolve` |
| 6 | How **dense** is the information? | `density:` | `focal` · `composed` · `dense` — counts in the budget table below |
| 7 | Does it need **spatial reasoning** (parts, layers, topology, scale)? | *no key of its own* | feeds Q11 as an asset/subject reality |
| 8 | Does it need **perspective or camera travel**? | `camera:` | one move from `grammar/camera.md`, or `static` |
| 9 | What **metaphor**, if any? | `metaphor:` | one entry from `grammar/metaphors.md`, or `none — real product` |
| 10 | What **motion vocabulary**? | `blueprint:` / `motion:` | a blueprint id via `BLUEPRINT_INDEX` when one fits; otherwise 2–4 rule names via `RULES_INDEX` |
| 11 | Which **capabilities** follow? | `capabilities:` | see the derivation rule below |
| 12 | Which **runtime**, and what lost? | `runtime:` / `runtime_rejected:` | the procedure in `reasoning/capability-catalog.md` |

### Judgment vs. derivation — the split is not a style choice

- **Q1–Q10 are judgment.** Story and visual intelligence, guided by the grammars. No capability
  term and no runtime name may appear in these answers.
- **Q11 is a MECHANICAL derivation** (ADR-005). It is the union of three sets, and nothing else:
  1. every capability tag **declared by each grammar entry the frame cites** in Q8/Q9/Q10;
  2. **asset and subject realities** — a prebaked export exists → `prebaked-asset`; the subject is
     a per-frame simulation → `gpu-compute`; Q7 answered yes → the spatial tag it names;
  3. **explicit additions**, each of which must carry a stated reason on the frame.
  Tags come from the vocabulary owned by `reasoning/capability-catalog.md`. Never invent one.
  A frame citing a spatial camera move while declaring no spatial capability is a derivation bug.
- **Q12 follows the catalog's procedure.** Not a preference, not a taste call.

A reviewer reading the keys alone must be able to reconstruct *why* every visual choice exists.
Reasoning traceability is load-bearing: a change that makes a frame's rationale unrecoverable
from its keys is an architecture regression (ADR-008).

## Director keys — the closed contract

Fourteen key names, emitted by the twelve questions plus the ADR-001 override. **The set is
closed.** Adding a key means adding or replacing a question, which is an architecture change
reviewed as such — not a convenience. Written as `- key: value` bullets on the frame; upstream's
storyboard parser preserves unknown bullets under `extra` (`STORYBOARD_FORMAT`, and the
`STORYBOARD_EXTRA_KEYS` behavior probe in `compat/ecosystem.md`), so the keys survive the move to
the official format unchanged.

| Key | Required | Allowed values |
|---|---|---|
| `goal:` | yes | free text, one sentence |
| `abstraction:` | yes | `literal` \| `analog` \| `metaphor` \| `symbolic` |
| `complexity:` | yes | `atomic` \| `compound` \| `systemic` |
| `tone:` | yes | one lowercase word, from the film's Phase-0 emotional journey (e.g. `tension`, `curiosity`, `relief`, `confidence`, `urgency`) |
| `energy:` | yes | `calm` \| `build` \| `peak` \| `resolve` |
| `density:` | yes | `focal` \| `composed` \| `dense` |
| `camera:` | yes | a move name from `grammar/camera.md`, or `static` |
| `metaphor:` | yes | an entry name from `grammar/metaphors.md`, or `none — real product` |
| `blueprint:` | conditional | one blueprint id resolved through `BLUEPRINT_INDEX`. At least one of `blueprint:` / `motion:` must be present |
| `motion:` | conditional | 2–4 rule names, comma-separated, resolved through `RULES_INDEX`. Required when no blueprint fits; allowed alongside one (Adapt / Compose posture) |
| `capabilities:` | yes, non-empty | comma-separated tags from the catalog vocabulary only |
| `runtime:` | optional | `three` \| `html-in-canvas` \| `typegpu` \| `lottie` \| `anime` \| `css` \| `waapi`. **Omit for GSAP** — it is the default |
| `runtime_rejected:` | conditional | `<runtime> — <reason>`. Required whenever a non-default runtime was considered and not chosen |
| `user_directed:` | optional | `true` (only value) |

### User override (ADR-001)

A user's **explicit creative instruction overrides any derived or procedural verdict** — including
runtime selection and every budget below. State the tradeoff once, then comply, and record
`user_directed: true` on the affected frame. Such frames are **exempt from the budgets but still
counted and shown** in the budget report, so a reviewer sees the choice was directed, not derived.
Never infer an override from a vague preference; only an explicit instruction qualifies.

## Cognitive-load budgets — THE single source

> **ADR-008/C6: this table is the only place these numbers live.** Every other file in this repo
> cites "the budget table in `reasoning/scene-analysis.md`" and carries no number of its own.
> Checked after all frames are analyzed. `user_directed: true` frames are exempt-but-visible.

| Budget | Limit | How it is checked |
|---|---|---|
| **Hero beats** | ≤ 3 frames in the film | count frames whose `runtime:` is `three`, `html-in-canvas`, or `typegpu`. Over budget → keep the highest story-leverage frames, degrade the rest to their Tier-A camera expression and say so. Origin: `HTML_IN_CANVAS` — the contrast between flat beats and hero beats *is* the storytelling |
| **Transitions** | 1 primary style + ≤ 2 accents across the film | transition energy follows the `energy:` curve between adjacent frames; `SEAM_LAW` governs the handoff |
| **Emphasis** | 1 emphasis device per frame | more than one device competing in a frame splits attention |
| **Marker highlight** | 1 per film | the drawn-marker device is a single reserved moment (`MARKER_PATTERNS`) |
| **Density** | `focal` = 1 element · `composed` = 3–5 · `dense` = grid or diagram, and only with a stated disclosure order | video frames are not web pages — doctrine in `VIDEO_COMPOSITION` |
| **Duration variance** | no flat duration profile | check durations against the `energy:` curve; uniform scene lengths are a defect (the slideshow failure) |
| **Metaphor consistency** | 1 concept → 1 metaphor, film-wide | the same idea never gets two visual treatments |
| **Emotional arc closure** | the `tone:` sequence traces the Phase-0 journey | this is the stage that finally **consumes** what Phase 0 collects |

## Emotional pacing → mechanics

The bridge from `tone:` to actual craft. Defaults, not laws — a frame may depart with a reason.

| `tone:` | `energy:` default | Easing character | Transition to reach for | Music behavior (Phase 5 input) |
|---|---|---|---|---|
| tension / pain | `build` | accelerating entries, tightening staggers | Push Slide | rising bed, no resolve |
| curiosity | `build` | standard settle, staggered reveals | Blur Crossfade | sparse, questioning |
| relief / solution | `peak` → `resolve` | standard settle, optional baked spring | Zoom Through, *into* the product | theme statement lands |
| confidence / proof | `calm` | long calm drifts | Crossfade | steady bed under data |
| urgency (CTA) | `peak` | punch, short | hard velocity-matched seam **into** the CTA (never out of the closing frame) | duck for VO, final hit |

**Easing character resolves through `EASING_AND_STAGGER`**, which owns the family palette and its
mood mapping — calm → standard → punch within the smooth families, with overshoot as a rare
explicitly-playful register. Never write a literal ease name into a director key; name the
character and let the builder pick the family from the owning recipe.

Transition names resolve through `patterns/transition-catalog.md`; velocity-matched seams and their
parameters through `CUT_CATALOG`, under `SEAM_LAW`.

This table is a *prior* for Phase 5's music brief and for the seam ledger — it makes the emotional
arc mechanically consequential instead of decorative.

## Output contract

Phase 1 writes the keys onto each frame. Phase 3's packet builder forwards a frame's keys — with
the design spec and the cited blueprint/rule bodies pulled from the installed upstream files — to
its scene builder. Builders treat `goal:` / `tone:` / `energy:` as binding direction and
`blueprint:` / `motion:` / `camera:` as vocabulary they implement from the official recipes.
**Builders never load this file.**
