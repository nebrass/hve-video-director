# Principal Engineer Architecture Review — Final Pre-Implementation Pass

**Baseline under review:** `2026-08-01-visual-storytelling-director-design.md` + `adr.md`
(ADR-001…007). **Posture:** critique, not redesign. **Bar for change:** clear long-term
benefit; smallest possible set.

---

## 1. Executive review

The architecture is sound where it matters most: the ownership boundaries (ADR-001/002/003/
004) are the right cuts, ADR-006's placement tests plus ADR-007's compat waist give it a real
maintenance story, and the design consistently converts taste into auditable artifacts. Four
genuine defects survive, all fixable with small changes:

1. **ADR-005 under-specifies its middle.** Capability identification is currently a per-scene
   *judgment* (scene-analysis Q11), which couples the visual layer to the runtime-facing
   vocabulary and permits silent inconsistency (a frame citing `hero-orbit` while listing no
   spatial capability). It should be a *derivation*. → Replace ADR-005 (three-stage).
2. **ADR-002's slogan is falsified by the design itself.** "Zero runtime-specific prompting"
   is violated by the builder delta (names `hf-seek`), the three-taxonomy (names materials),
   and packet inlining (copies recipes at dispatch). The intent is right; the rule is
   imprecise, and imprecise rules die in review debates. → Replace ADR-002 ("zero duplicated
   authorship" + a mechanical test).
3. **The optimization target is implied, never stated.** "Maximize understanding," the
   scoring heuristic's understands-vs-looks clause, and anti-slop all gesture at it, but no
   principle adjudicates comprehension vs engagement vs memorability — exactly the conflict
   every hero-beat debate will hit. → New ADR-008.
4. **Two hidden couplings.** (a) The entire director-keys mechanism rides on the official
   storyboard parser preserving unknown bullets in `extra` — an undocumented upstream
   behavior with no probe; the highest-severity silent-failure risk in the design.
   (b) The local budgets (emphasis/marker/hero/transition counts) are restated in four
   places — the precise drift class this redesign exists to kill. → ADR-007 amendment +
   budget single-sourcing.

Everything else reviewed below is affirmation with notes. **Verdict: APPROVED WITH CHANGES**
(changes C1–C6; two optional simplifications).

## 2. ADR-by-ADR critique

- **ADR-001 (governance local) — AFFIRMED, one ambiguity.** The policy/mechanism argument
  holds and the doctrinal conflict with `brief-contract.md` is real, not invented. Gap: the
  consent doctrine covers *brief levers* but is silent on per-scene authority — who wins when
  the user explicitly demands "make scene 3 Three.js" against the hero budget? Unowned today.
  → C5: amend with a user-override clause (user's explicit creative instruction wins, recorded
  `user_directed: true`, exempt-but-visible to gates). Consent cuts both ways: never infer,
  never overrule.
- **ADR-002 — REPLACE** (defect #2 above; full text applied in `adr.md`). The revised rule:
  hve is never the *author of record* for runtime mechanism text; pointer citations,
  dispatch-time mechanical inlining, and additive constraints are legal; committed restatement
  is not. Mechanical test: *if the owning upstream file changes, is any committed hve file now
  wrong?* (compat map excepted). That test is what reviewers will actually apply.
- **ADR-003 (HyperFrames owns rendering) — AFFIRMED, one forward note.** The four local
  retentions (sequencing, hero-frame check, capture contract, approval) are each justified.
  Note: the CLI already exposes an opt-in `--frame-check` gate; if it ever accepts
  intent/expected-content input, the hero-frame check becomes an incubate→upstream candidate
  under ADR-006 — record that so nobody defends it as permanently local.
- **ADR-004 (director owns reasoning) — AFFIRMED.** The builders-never-load-reasoning rule is
  the load-bearing part; keep it absolute. The delegation-if-upstream-ships-a-director clause
  correctly prevents future turf defense.
- **ADR-005 — REPLACE** (defect #1; full text applied). Also resolves the scoring question:
  see §4.
- **ADR-006 (placement criteria) — AFFIRMED.** The eight tests are crisp and the
  incubate→upstream→delegate lifecycle already has two live candidates. No change.
- **ADR-007 (compat waist) — AFFIRMED, strengthen.** The evidence base is honest and the
  layer is appropriately thin. Two gaps: (a) load-bearing upstream *behaviors* (not just
  paths) need named probes — first entry must be the `extra`-key preservation round-trip
  (defect #4a); (b) lock-update cadence is unowned. → C4 amendment.

## 3. The specific questions

**ADR-005 / three-stage split.** Yes — the architecture should read
*Visual Intelligence → Capability Derivation → Runtime Selection*, with the middle stage
**mechanical, not judgmental**: every grammar entry declares its capability tags; a frame's
capability set is the union of tags from its cited entries, plus asset/subject realities
(a Lottie file exists → `prebaked-asset`; a simulation subject → `gpu-compute`), plus
explicit additions that require a stated reason. Ownership: the catalog owns and versions
the vocabulary; grammars import it; scene analysis never invents tags. Benefits: kills the
inconsistency class, cuts per-scene ceremony from twelve judgments to ten, and makes every
tag traceable to a citing entry. Cost: one-time capability annotation of grammar tables
(scheduled as an M1 task — the grammar files are proposals; annotate when applied).

**Does capability scoring deserve its own architectural responsibility? No.** A reusable
cascade of Communication/Visual/Capability/Runtime scores is rejected as over-engineering
with a principled reason, not just parsimony: the scores would be LLM-invented numbers — the
same class of fabricated metric `anti-slop.md` bans from the screen. Pseudo-quantification
would *reduce* auditability (a number hides its rationale; a recorded rejection exposes it).
Scoring remains exactly one rubric at the one genuinely contested decision point (runtime
tie-break), now stated in revised ADR-005. If a future evaluator produces *measured* scores
(ADR-008's seam), those are real measurements and enter through the gate ladder, not here.

**Optimization target.** Justified — this is the review's most valuable addition. ADR-008
(full text in `adr.md`): strict precedence **comprehension → retention → engagement**, with
honesty/consent/determinism as non-tradeable constraints, cognitive-load budgets as the
enforcement mechanism (single-sourced, C6), an explicit conflict rule ("engagement never
justifies a comprehension cost; a hero beat exists because dimension aids understanding or
anchors retention of THE key moment — never engagement alone"), and the traceability
consequence (director keys must stay sufficient for an external reviewer to score a frame).

**Future AI evaluation.** Deferred as future work — deliberately not an eighth pipeline
stage now. Reasoning: the ingredients are unproven (vision-model rubric quality) but the
architecture already reserves the correct seam without any change: the director sequences the
gate ladder (ADR-003), so `render → vision review against the frame's goal:/tone: keys →
suggestions → human approval` inserts as one more ladder step; the storyboard director keys
— designed as audit artifacts — double as the machine-readable rubric, and ADR-008 defines
what the evaluator scores. Adopting it later changes zero boundaries. Recorded as a
consequence of ADR-008 rather than a standalone ADR (a deferral with a named seam does not
need its own decision record).

**Additional ADR candidates — dispositions.** Communication Effectiveness → ADR-008 (added).
Evaluation & Feedback / Continuous Visual QA → folded into ADR-008 consequence (deferred
seam). Explainability / Reasoning Traceability → property already designed-in
(`runtime_rejected:`, derivation tracing); protected by ADR-008's consequence clause rather
than a separate ADR. Human Override → ADR-001 amendment, not a new ADR. Capability Scoring →
rejected (above). Evolution Strategy → already ADR-006+007. Net: **one** new ADR. ADR sprawl
is itself a maintenance cost; seven-plus-one is the right count.

## 4. Recommended modifications (the complete set)

| # | Change | Why / what improves | Long-term impact | Migration cost | Status |
|---|---|---|---|---|---|
| C1 | Replace ADR-005 with the three-stage model; catalog owns the versioned vocabulary; grammars declare tags; scoring = one rubric | Kills a silent-inconsistency class; less ceremony; traceable tags | New runtimes/vocab evolve without touching the judgment instrument | Small (ADR text now; grammar annotation in M1) | **Mandatory — applied** |
| C2 | Replace ADR-002: "zero duplicated authorship" + the upstream-change test; 3 legal forms, 1 illegal | Precise, enforceable rule instead of a falsifiable slogan | Review debates end with a mechanical test | Nil (text only) | **Mandatory — applied** |
| C3 | Add ADR-008 (optimization target + constraints + evaluation seam + traceability) | Adjudicates every future taste conflict; rubric for any evaluator | Prevents engagement creep — the mission's named failure mode | Nil (text only) | **Mandatory — applied** |
| C4 | Amend ADR-007: named behavior probes (first: storyboard `extra`-key round-trip; `_meta.deprecated` signal) + lock cadence owner (milestone boundaries or monthly, maintainer) | Converts the design's highest-severity hidden coupling into a red test | Parser/CLI evolution can't silently break director keys | Small (one probe test in M0.5) | **Mandatory — applied** |
| C5 | Amend ADR-001: user-override clause (`user_directed: true`, exempt-but-visible) | Closes the only found ownership ambiguity | No future dispute over per-scene authority | Nil | **Mandatory — applied** |
| C6 | Single-source local budgets in `reasoning/scene-analysis.md`; all other mentions cite, never restate numbers (official numbers stay upstream-cited) | The redesign's own anti-drift rule, applied to itself | One edit point for budget tuning | Small (3 file touches — applied) | **Mandatory — applied** |
| S1 | Connective-scene fast path: frames with `density: focal` + no product content may answer Q7–Q11 as `standard` defaults | Keeps the instrument from becoming checkbox ritual on title cards/recaps | Sustained analysis quality on the frames that matter | Small | Optional (decide during M1) |
| S2 | Compat map entries carry a one-line "what this is" per symbol | Onboarding: symbolic indirection stays readable | Lower contributor ramp | Trivial | Optional |

## 5. Simplicity check — findings

- **Rejected as over-engineering:** the four-score cascade (§3); any new sibling skills; an
  evaluation phase now; a code-heavy compat layer (naming + tests suffice).
- **Ceremony reduced:** C1 turns two of twelve per-scene questions into derivations; S1
  available if real use still feels heavy.
- **Cleverness audit:** the 16 "stages" are labels over existing phase work, not process —
  keep, but never let them become checkpoints; the compat map's indirection is the one
  deliberate cost accepted (S2 mitigates); the seam-gate/packet machinery is upstream's
  complexity, correctly not ours.
- **Found and fixed in our own artifacts:** budget numbers stated in four places (C6) — the
  baseline committed the sin it was designed to abolish; caught before implementation.

## 6. Risks if recommendations are ignored

- Skip C1 → visual plans and capability lists drift apart with no gate able to notice;
  vocabulary changes ripple into the judgment instrument.
- Skip C2 → the slogan either blocks legitimate artifacts (pedantry) or gets shrugged past
  (erosion); both end in unreviewable precedent.
- Skip C3 → hero-beat and density debates are settled by per-PR taste; engagement creep
  returns; any future evaluator has no rubric and will invent one.
- Skip C4 → an upstream parser change silently strips director keys: storyboards still parse,
  builds still pass, and every frame loses its direction — the exact "all gates green, output
  wrong" archetype the changelog documents.
- Skip C5 → the first user who demands a technology fights the budget system with no rule.
- Skip C6 → budget drift across four files; the redesign loses its own moral authority.

## 7. Architecture diagram

Unchanged. The revisions refine responsibilities inside the existing "reasoning modules" box
and ADR text; no boundary moved, so no new diagram is issued (per the review's own bar).

## 8. Final recommendation

**APPROVED WITH CHANGES** — C1–C6 (all applied to `adr.md` and the affected spec files in
this bundle; grammar capability-annotation scheduled into M1). S1/S2 optional. With these
changes the architecture is ready for implementation starting at M0, and no further
architecture-level review is required before M4 (the isolated high-risk step, which should
get its own focused review when its converter exists).
