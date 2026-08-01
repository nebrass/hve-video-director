# Architectural Decision Records — Visual Storytelling Director

**Status of all ADRs:** PROPOSED (accepted together with the 2026-08-01 design spec).
**Revision note (2026-08-01):** updated after the Principal Engineer review
(`review-principal.md`): ADR-002 and ADR-005 replaced, ADR-001 and ADR-007 amended,
ADR-008 added.
**Revision note (2026-08-01, M0.5 implementation):** corrected against the shipped compat layer:
ADR-007 decision point 2 overstated what `skills-lock.json` protects. No other ADR changed.
Format: Context → Decision → Consequences → Alternatives rejected. Evidence citations refer to
the design spec (`../2026-08-01-visual-storytelling-director-design.md`) and the six review
reports summarized in it.

---

## ADR-001 — Governance stays local

**Context.** hve-video-director's governance is: the consent doctrine ("recommendations are
visible guidance, never a selection"), per-phase user approval, revision-bound fingerprints
with staleness routing (`validate_brief.py`), the reviewed-caption contract
(draft → approve-with-cue-fingerprints → finalize → validate, transactional publish), and
capture attempt/pending state. The ecosystem has an adjacent but different philosophy:
`brief-contract.md` derives a collaborative/autonomous run shape and *skips questions the
request already answers*; official workflows gate only plan approval and final render;
`motion-graphics` is autonomous by design. The ecosystem sweep confirmed no official skill
owns per-phase approval, revision fingerprints, or caption review governance (spec §8,
white-space items).

**Decision.** All governance remains in hve-video-director: the consent doctrine, the
`require`/`confirm-*`/`stamp` chain, caption governance, and capture state. In M4 the state
engine re-points at official artifacts (BRIEF.md/STORYBOARD.md) but the *policy* never moves.

**User-override clause (added in review).** Consent cuts both ways: never infer, never
overrule. The user's *explicit* creative instruction overrides any reasoning verdict —
including runtime selection and the budgets. The director states the tradeoff once, then
complies, recording `user_directed: true` on the affected frame; gates and budget checks
treat such frames as exempt-but-visible, so reviews still see that the choice was directed,
not derived.

**Why.** (1) Governance is **policy**, not mechanism — policy encodes this skill's promise to
its users and is the part upstream churn can never break. (2) The doctrines genuinely
conflict: "never infer, never preselect" cannot be delegated to a contract whose stated rule
is to answer inferable questions itself. (3) It is the differentiation: users who want
autonomous speed already have the official workflows. (4) Cross-runtime portability (Claude
Code + Copilot CLI) requires owning the question/consent protocol.

**Consequences.** We maintain the fingerprint engine forever; it must track official format
evolution (mitigated by ADR-007: consume formats through the official parser). We accept a
duplicated *surface* (two brief philosophies exist in the ecosystem) and document the routing
honesty rule so users can pick.

**Alternatives rejected.** Adopt `brief-contract.md` gates wholesale — loses the consent
guarantees that define the skill. Upstream the governance into HyperFrames — a policy
conflict, not a gap; upstream optimizes for autonomous throughput.

---

## ADR-002 — Runtime prompting: zero duplicated authorship *(replaced in review)*

**Context.** The v1 workflows embed ~2,200 lines of runtime knowledge (GSAP skeletons, the
clip `<video>` contract ×3, transition recipes, SRI-pinned CDN tags ×7, adapter lore), with
documented drift costs: a total rewrite on the Remotion migration, three "keep in sync"
duties, two pattern files already dead-ended by an upstream relayout. The original rule —
"zero runtime-specific prompting" — proved imprecise: the redesign's own necessary artifacts
violate it (the builder delta names `hf-seek`/`data-duration`; the Three.js taxonomy names
ingredient defaults; the packet builder *copies* official recipe bodies into packets at
dispatch time). A rule the design itself cannot satisfy dies in review debates.

**Decision.** hve-video-director must never be the **author of record** for runtime mechanism
text. Three forms of runtime-specific content are legal:

1. **Pointer citation** — naming an official file, rule, blueprint, or adapter concept.
2. **Mechanical inlining at dispatch time** — the packet builder copies recipe/adapter bodies
   from the *installed upstream files* into ephemeral, generated packets. Copies are never
   committed, never edited, and regenerate on every dispatch.
3. **Additive local constraints** — budgets, data honesty, brand law, consent — which
   constrain what may be requested but never restate *how* a mechanism works.

One form is illegal: a **committed, locally maintained restatement** of any mechanism an
official file owns.

**The test** (applied in every review): *if the owning upstream file changes, is any
committed hve file now incorrect?* If yes — outside the compat map (ADR-007) — the rule is
violated.

**Consequences.** Upstream improvements flow in with zero local edits. Packet generation must
re-read upstream files at each dispatch (no cached recipe bodies in the repo). The escape
hatch for upstream bugs is an upstream PR or an additive local constraint — never a local
copy.

**Alternatives rejected.** Absolute "zero runtime-specific prompting" — unimplementable
(even naming `hf-seek` violates it); precision beats slogan. Vendoring upstream files —
proven drift; the SRI ritual is the cautionary tale. Fork-and-pin forever — loses the
improvement stream that motivates HyperFrames-first.

---

## ADR-003 — HyperFrames owns rendering

**Context.** Rendering correctness in this stack is inseparable from the deterministic-seek
contract, which only the framework can enforce end-to-end: the `check` gate audits runtime/
layout/motion/contrast in one browser session, `seam-gate.mjs` verifies seams numerically,
`doctor` owns environment diagnosis, and render itself spans local/docker/cloud/lambda. v1
partially shadowed this (deprecated gate chains, a `node_modules/...` internal script path,
version-pinned troubleshooting lore — the fastest-rotting content in the repo).

**Decision.** All rendering, previewing, and *mechanical* verification is exclusively the
`hyperframes` CLI and its gates. The director contributes only: gate **sequencing**, the
**hero-frame content check** (a semantic check — "is the right content on screen" — that green
gates cannot make), the capture-clip contract (a pre-render input contract, not rendering),
and render **approval** (a governance act, per ADR-001).

**Consequences.** Troubleshooting defers to `doctor`; when a gate misses a failure class we
add a *semantic* check or file upstream feedback (`hyperframes feedback`), never a parallel
validator. The hero-frame check stays local because it requires storyboard intent, which only
the director has — but it is an **incubate→upstream candidate** (ADR-006): if the CLI's
opt-in `--frame-check` gate ever accepts intent/expected-content input, delegate it.

**Alternatives rejected.** Owning an ffmpeg/render path (out of mission). Keeping the
`lint|inspect|validate` chain (deprecated; `check` subsumes it — spec M0).

---

## ADR-004 — The director owns reasoning

**Context.** The ecosystem sweep found no owner for per-scene communication analysis,
capability-driven runtime selection, camera/motion/metaphor grammars, or consequential
emotional pacing. Official workflows carry genre-fixed story shapes ("borrow their story
shape and taste, not their private scripts"); `hyperframes-creative` provides story doctrine
but not per-scene decision instruments. Meanwhile v1's storytelling spine was its thinnest
layer — the emotional arc was collected and dropped.

**Decision.** The reasoning layer (`reasoning/scene-analysis.md`, `reasoning/
capability-catalog.md`, `grammar/*`) lives in hve-video-director and is its center of
gravity. Its outputs are auditable director keys in the official storyboard format. Builders
never load reasoning modules — they receive conclusions via packets.

**Consequences.** The skill's quality now rises and falls with the reasoning modules —
they get the test investment (question-contract suite extended to director keys). If
HyperFrames later ships an equivalent director layer, ADR-006's criteria apply: delegate the
overlap, keep only the delta.

**Alternatives rejected.** Relying on official workflows' story steps (genre-fixed; no
capability selection). Putting reasoning into a shared upstream contribution now (premature —
incubate first, per ADR-006's lifecycle).

---

## ADR-005 — Three-stage reasoning: visual intelligence → capability derivation → runtime selection *(replaced in review)*

**Context.** The original two-stage framing (visual intelligence emits capability tags;
catalog maps tags to runtimes) left capability identification as a per-scene *judgment*
(scene-analysis Q11). That coupled the visual layer to the runtime-facing vocabulary and
permitted a silent inconsistency class: a frame citing `camera: hero-orbit` while listing no
spatial capability, with no gate able to notice.

**Decision.** Three stages with distinct ownership and a mechanical middle:

1. **Visual intelligence** (pipeline stages 8–12; scene-analysis Q1–Q10). Purely
   communicative outputs: goal, abstraction, tone, energy, density, metaphor, camera, motion.
   Owner: director judgment guided by the grammars. No capability or runtime terms appear.
2. **Capability derivation** (stage 13). *Mechanical, not judgmental:* a frame's capability
   set is the **union of the capability tags declared by each grammar entry it cites**
   (every grammar row carries `capabilities:` annotations), plus **asset/subject realities**
   (a prebaked Lottie asset exists → `prebaked-asset`; a simulation subject → `gpu-compute`),
   plus optional explicit additions — each requiring a stated reason. Owner: the grammars
   declare; the procedure unions.
3. **Runtime selection** (stage 14). The catalog's procedure: GSAP-first prior, hero budget,
   environment gating, and the single tie-break rubric. Verdicts and rejections recorded
   (`runtime:` / `runtime_rejected:`). Owner: the capability catalog.

**Vocabulary ownership.** The capability vocabulary is owned and *versioned* by the catalog;
grammars import it; scene analysis never invents tags.

**Scoring decision.** Scoring remains exactly **one rubric at the one contested decision**
(runtime tie-break). A cascade of numeric Communication/Visual/Capability/Runtime scores is
explicitly rejected: an LLM-invented number is the same class of fabricated metric that
`anti-slop.md` bans from the screen, and it *reduces* auditability — a number hides its
rationale, a recorded rejection exposes it. Measured scores (from a real evaluator, ADR-008)
enter through the gate ladder, never here.

**Consequences.** Grammar entries gain one-time capability annotations (scheduled in M1).
Per-scene ceremony drops from twelve judgments to ten judgments plus two derivations. The
inconsistency class is eliminated, and every tag traces to a citing entry — strengthening the
reasoning traceability ADR-008 depends on. New runtimes or vocabulary evolve without touching
the judgment instrument.

**Alternatives rejected.** Two-stage as originally written — coupling + judgment burden.
Direct scene→runtime mapping — couples story plans to technology churn. A four-layer scoring
architecture — over-engineering plus pseudo-metrics (above). Runtime hints from the user as
input — users never request technology (mission); explicit user *instructions* are handled by
ADR-001's override clause instead.

---

## ADR-006 — Placement criteria: hve-video-director vs upstream HyperFrames

**Context.** Future features will keep arriving on both sides. Without criteria, the shadow-
copy pattern regrows.

**Decision.** A feature belongs **in hve-video-director** iff it passes at least one of:

1. **Policy test** — it encodes consent, approval, fingerprinting, or editorial law (ADR-001).
2. **Judgment test** — it is reasoning about communication (analysis, grammars, selection)
   rather than execution (ADR-004/005).
3. **Moat test** — it captures a live, authenticated, or native product surface the ecosystem
   cannot reach (Phase-2 machinery), *until* upstream accepts a contribution.
4. **Semantic-gate test** — it verifies intent against output (hero-frame check) using
   knowledge only the director has.

A feature belongs **upstream** iff any of:

5. **Mechanism test** — it renders, animates, verifies mechanically, or processes media.
   Route: registry block, media-use provider, adapter, or CLI feature — then hve keeps only
   the *selection* logic.
6. **Reuse test** — another workflow/genre could use it unchanged (design systems, capture
   protocols once stable, new scene archetypes → registry).
7. **Restatement test** — implementing it locally would restate any official file. Hard stop:
   contribute or point, never copy.
8. **Churn test** — it must track HyperFrames internals (paths, flags, formats). It may exist
   locally **only inside the compat layer** (ADR-007), never in phase prose.

**Lifecycle for ambiguous cases:** *incubate → upstream → delegate.* Build it in hve behind
the compat map, propose it upstream once proven, delete the local copy when accepted. Live
examples already queued: `design-systems/` brand packs → `hyperframes-creative`; the
authenticated-capture protocol + native recorder pattern → ecosystem capture gap; the
hero-frame check → `--frame-check`, if it gains intent input (ADR-003).

**Consequences.** Every future PR review asks these eight questions; the answer is recorded
in the PR description. The question-contract test suite enforces test 7 mechanically where it
can (no official-file content duplicated verbatim).

---

## ADR-007 — A thin compatibility layer isolates ecosystem churn *(amended in review)*

**Context (evidence gathered 2026-08-01).** The review initially leaned on the current
HyperFrames layout being stable. Verification says otherwise: **no stability guarantees are
documented** in `hyperframes-core`/`-cli`/`-animation`; `validate`/`inspect`/`layout` were
recently deprecated in favor of `check` (still working, emitting `_meta.deprecated: true` in
`--json` — deprecation is graceful and machine-detectable); the monolith→split relayout broke
this repo's `patterns/INDEX.md` pointers within weeks; skills install/refresh lazily with
staleness nagging (`skills check/update`); projects pin CLI versions in `package.json` with
`upgrade --project` to bump; and `skills-lock.json` (already present in this repo) records
content hashes per skill. Conclusion: the ecosystem is **actively evolving with good
versioning affordances** — plan for change, not stability.

**Decision.** Introduce a thin waist, as roadmap step **M0.5** (before M1), so that any
upstream change requires edits in exactly one place:

1. **`compat/ecosystem.md`** — the *only* file permitted to contain cross-skill file paths,
   CLI command names/flags, and format-version notes. All phases, grammars, and reasoning
   modules refer to capabilities by symbolic name (`SEAM_GATE_VERIFY`, `AUDIO_ENGINE`,
   `CHECK_GATE`, `BLUEPRINT_INDEX`…), and the map binds names to current reality. This
   generalizes the repo's proven "name actions, not tools" rule (which already does exactly
   this for per-runtime tool names) to "name capabilities, not paths".
2. **Pin + verify:** `skills-lock.json` records the tested-against skill hashes; upgrading the
   ecosystem = run `npx hyperframes skills update`, re-run the **pointer-validity test suite**
   (asserts every path in `compat/ecosystem.md` exists and every symbolic name resolves) plus
   the question-contract tests, then commit the new lock. A hash drift without a green suite
   fails CI. *Cadence and ownership (added in review):* lock bumps happen at milestone
   boundaries or monthly, whichever comes first; the maintainer owns them.

   **The lock is provenance, not a registry gate (corrected during M0.5 implementation).** The
   sentence above reads as if the lock file protected the capability registry. It does not, and
   nothing in this decision should be built on the assumption that it does. Three verified
   facts, in increasing order of consequence:

   1. **The only path the lock records is one file per skill.** Each entry carries a single
      `skillPath` naming that skill's own `SKILL.md`. No `references/`, `transitions/`, `rules/`
      or `scripts/` path is ever enumerated in the lock, so the pointers this repo actually
      depends on have no representation in it.
   2. **The digest is one opaque value per skill.** A hash reports *that* a skill changed. It
      can never report *which* file moved, or whether this repo's citations still resolve — it
      cannot distinguish a typo fix in `SKILL.md` from a wholesale relayout of `references/`. A
      content hash is not a pointer check, and no amount of hash coverage makes it one.
   3. **Nothing recomputes it.** The installed `skills` CLI (verified against 1.5.20 and 1.5.21)
      compares `computedHash` at exactly one call site — the `experimental_sync` node_modules
      flow — and ships no `check` command at all. For a GitHub-sourced skill, which is how this
      repo's entire ecosystem is installed, the recorded hash is written once and never read
      again. (The recorded values are also not locally reproducible from the installed tree by
      either whole-folder or single-file hashing, so they cannot be re-derived by hand either.)
      *Scope of this check:* it covers the `skills` CLI, which is what writes the lock file.
      Whether `npx hyperframes skills check` re-verifies the lock could not be tested — the
      `hyperframes` CLI is not installed in the verification environment. If it turns out to,
      this third point weakens; the first two are unaffected and carry the conclusion alone.

   ⟹ `skills-lock.json` is a **provenance and reinstall record**: it says which skills came from
   where, so an install can be reproduced. The **pointer-validity suite is the only thing that
   protects the registry**, because it is the only mechanism that resolves every registered path
   against the installed tree and fails on the specific breakage that motivated this ADR — the
   monolith→split relayout that silently rotted `patterns/INDEX.md`. Treat a lock bump as an
   *invitation* to re-run the suite, never as evidence the suite would pass. The Context
   paragraph above is unaffected: the lock does record content hashes per skill; the error was
   inferring registry protection from that fact.
3. **Feature-detect, never version-sniff:** probe capabilities at run time (`check` present?
   `--json` `_meta.deprecated`? `doctor --json .ok`?) with documented fallbacks (`lint` +
   deprecated aliases) — matching how the CLI itself signals deprecation.
4. **Formats through official parsers:** `validate_brief.py` v2 consumes STORYBOARD.md via
   `@hyperframes/core/storyboard` (lenient, warning-collecting) rather than hand-parsing, so
   format evolution is absorbed where it is maintained.
5. **Named behavior probes (added in review).** Load-bearing upstream *behaviors* — not just
   paths — are listed in the compat map, each with a probe test. Founding entries:
   (a) **STORYBOARD.md unknown-bullet preservation in `extra`** — the entire director-key
   mechanism rides on it; probed by a round-trip test (write keys → parse → assert preserved);
   (b) `check`'s `_meta.deprecated` signaling; (c) the packet builder's recipe source paths.

**Consequences.** One extra indirection when authoring phases (a symbolic-name lookup) —
cheap, and it *replaces* the four byte-identical resolver copies and grep-parity rituals with
one mechanism. M0's hotfixes land inside the compat map from day one. The layer is mostly
naming discipline + tests, not code — deliberately thin.

**Alternatives rejected.** No layer (status quo — already broken once). A heavyweight adapter
code layer (over-engineering for a prompt-first skill; the churn surface is paths/flags/
formats, which naming + tests cover). Freezing on today's ecosystem snapshot (forfeits the
improvement stream and contradicts ADR-002's economics).

---

## ADR-008 — The optimization target: comprehension first *(added in review)*

**Context.** The architecture repeatedly implies what it optimizes — the metaphor library's
"maximize understanding rather than visual novelty", the runtime rubric's understands-vs-
looks clause, anti-slop's honesty law — but never states it. Unstated targets surface as
unadjudicated conflicts: does a hero beat earn its budget by engagement or by clarity? Is a
denser frame better because it is complete or worse because it is heavy? Every such debate
would otherwise be settled by per-PR taste, and any future evaluator would have to invent its
own rubric.

**Decision.** The director optimizes, in strict precedence:

1. **Comprehension** — after one viewing, the target audience can restate the communication
   goals (reasoning stage 3).
2. **Retention** — the one thing that must be remembered is the most visually distinct thing
   in the film.
3. **Engagement** — attention held (pacing, spectacle, delight) only in service of 1–2.

**Constraints, not tradeoffs** (never exchanged for any amount of 1–3): honesty
(anti-slop — real data, real product, no invented metrics), consent (ADR-001), and
determinism/gates (ADR-003).

**Enforcement mechanism.** The cognitive-load budgets (density, emphasis, marker, hero,
transition) are how this precedence becomes mechanical; they are **single-sourced in
`reasoning/scene-analysis.md`** — every other file cites the budget table, never restates
numbers (C6 of the Principal review).

**Conflict rule.** When two treatments tie on comprehension, choose the more memorable.
Engagement never justifies a comprehension cost. A hero beat exists because dimension aids
understanding or anchors retention of THE key moment — never engagement alone.

**Consequences.** (a) Every contested design decision has an adjudication order, citable in
review. (b) The target defines the rubric for any future evaluator: **AI-assisted evaluation
(render → vision-model review scored against the storyboard's `goal:`/`tone:` keys →
revision suggestions → human approval) is deferred future work with a reserved seam** — it
inserts as one more step in the director-sequenced gate ladder (ADR-003) before human
approval, consuming artifacts that already exist; adopting it changes no architectural
boundary. (c) **Reasoning traceability is a load-bearing property**: the director keys must
remain sufficient for an external reviewer — human or model — to score a frame against this
target; any change that would make a frame's rationale unrecoverable from its keys is an
architecture regression, not a style choice.

**Alternatives rejected.** Multi-objective without precedence — the conflicts return.
Numeric communication scores now — pseudo-metrics (see ADR-005's scoring decision).
Engagement-first — contradicts the mission ("maximizing understanding rather than visual
novelty") and the anti-slop constitution.
