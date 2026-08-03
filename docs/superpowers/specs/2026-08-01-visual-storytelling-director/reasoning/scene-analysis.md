# Scene Analysis & Planning Framework

> **Proposed skill module** — target location after approval: `reasoning/scene-analysis.md`.
> This is the director's core reasoning instrument, run in Phase 1 for every storyboard frame
> (after story beats exist, before capture planning) and re-checked in Phase 3 before scene
> direction is packetized. Its output is a set of **director keys** written into each
> `## Frame N` storyboard block — the official storyboard parser preserves unknown
> `- key: value` bullets in `extra`, so these keys ride the official format untouched.

## Per-scene analysis — the twelve questions

Answer ALL twelve for every frame. One line each; no essays. The answers ARE the plan.

| # | Question | Storyboard key | Value vocabulary |
|---|---|---|---|
| 1 | What must the viewer **understand** when this frame ends? | `goal:` | one sentence, viewer-perspective |
| 2 | What is the **abstraction level**? | `abstraction:` | `literal` (real product) / `analog` (mock UI) / `metaphor` (invented visual) / `symbolic` (type/data only) |
| 3 | How **complex** is the idea? | `complexity:` | `atomic` / `compound` / `systemic` — systemic ideas get progressive disclosure or split into two frames |
| 4 | What **emotional tone** serves the beat? | `tone:` | from the Phase-0 emotional journey: e.g. `tension`, `relief`, `curiosity`, `confidence`, `urgency` |
| 5 | What **energy/pacing**? | `energy:` | `calm` / `build` / `peak` / `resolve` — drives camera speed, transition energy, easing register |
| 6 | How **dense** is the information? | `density:` | `focal` (one element) / `composed` (3–5) / `dense` (grid/diagram — needs disclosure order) |
| 7 | Does it need **spatial reasoning** (parts, layers, topology, scale)? | feeds `capabilities:` | `spatial-depth`, `topology-3d`, `volumetric-count` |
| 8 | Does it need **perspective/camera travel**? | `camera:` | one move from `grammar/camera.md`, or `static` |
| 9 | What **metaphor**, if any? | `metaphor:` | one entry from `grammar/metaphors.md`, or `none — real product` |
| 10 | What **motion vocabulary**? | `blueprint:` / `motion:` | blueprint id from `blueprints-index.md` when one fits; else 2–4 named rules — never invented names |
| 11 | Which **capabilities** follow from the cited choices? | `capabilities:` | **DERIVED (ADR-005):** union of the tags declared by each cited grammar entry + asset/subject realities (prebaked asset → `prebaked-asset`; simulation → `gpu-compute`); explicit additions require a stated reason |
| 12 | What is the **selected runtime** and what was rejected? | `runtime:` / `runtime_rejected:` | per the catalog's selection procedure; omit `runtime:` for GSAP |

Keys 1–10 are director judgment (story + visual intelligence). Key 11 is a mechanical
derivation (ADR-005); key 12 follows the catalog's procedure. A user's explicit creative
instruction overrides any derived/procedural verdict — record `user_directed: true`
(ADR-001). A reviewer reading the storyboard must be able to reconstruct *why* every visual
choice exists.

## Video-level budgets (checked after all frames are analyzed)

> **Single source (ADR-008/C6):** this table is the ONLY place local budget numbers live.
> Every other file cites "the budget table in reasoning/scene-analysis.md" without numbers.
> Frames marked `user_directed: true` are exempt-but-visible (ADR-001).

- **Hero budget:** ≤3 frames total may carry `runtime: three | html-in-canvas | typegpu`.
  If more qualify, keep the highest story-leverage ones; degrade the rest to Tier-A camera
  expressions and note it.
- **Transition budget:** ONE primary + 1–2 accents across the film (transitions doctrine);
  transition energy follows the `energy:` curve between adjacent frames.
- **Emphasis budget:** one emphasis device per scene; one marker-highlight per video.
- **Metaphor consistency:** the same concept always re-uses the same metaphor.
- **Anti-slideshow:** scene durations must vary; check the duration column against the
  `energy:` curve — a flat duration profile is a defect.
- **Emotional arc closure:** the sequence of `tone:` values must trace the Phase-0 emotional
  journey answer. This is the stage that finally *consumes* what Phase 0 collects.

## Emotional pacing → mechanics mapping

| `tone:` | `energy:` default | Easing register | Transition family | Music behavior (Phase 5 input) |
|---|---|---|---|---|
| tension / pain | build | `power2.in` entries, tightening staggers | push-slide, squeeze | rising bed, no resolve |
| curiosity | build | `power3.out`, staggered reveals | blur-crossfade | sparse, questioning |
| relief / solution | peak→resolve | `power3.out` + spring settle | zoom-through INTO the product | theme statement lands |
| confidence / proof | calm | long `sine.inOut` drifts | crossfade | steady bed under data |
| urgency (CTA) | peak | `power4`, short | hard velocity-matched seam | duck for VO, final hit |

This table is a *prior* for Phase 5's music brief and the seam ledger — it makes the emotional
arc mechanically consequential instead of decorative.

## Output contract

Phase 1 writes the keys into `STORYBOARD.md` frames. Phase 3's packet builder forwards each
frame's keys (plus the design spec and the cited blueprint/rule bodies) to its scene builder.
Builders treat `goal:`/`tone:`/`energy:` as binding direction and `blueprint:`/`motion:`/
`camera:` as the vocabulary they implement from official recipes. Builders never see this file.
