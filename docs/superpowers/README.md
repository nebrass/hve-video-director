# What this bundle is — and what supersedes it

`specs/2026-08-01-visual-storytelling-director/` is the **M1 design-time
snapshot** of the reasoning layer: the proposals the milestone was reviewed
against, kept byte-for-byte as spec history. Per `compat/ecosystem.md`
§ scan surfaces, `docs/` is a record — outside every pointer check, and not
to be edited to match later reality (that is why the files below carry no
banner: stamping a record falsifies it; this README is the signpost instead).

**Do not read the snapshot as the current grammar or reasoning layer.** The
shipped modules moved on (they are longer, tagged, and pointer-checked); the
snapshot did not, by design.

| Snapshot (frozen, M1 proposal) | Shipped module (authoritative) |
| --- | --- |
| `specs/…/grammar/camera.md` | [`grammar/camera.md`](../../grammar/camera.md) |
| `specs/…/grammar/motion.md` | [`grammar/motion.md`](../../grammar/motion.md) |
| `specs/…/grammar/metaphors.md` | [`grammar/metaphors.md`](../../grammar/metaphors.md) |
| `specs/…/grammar/three-taxonomy.md` | [`grammar/three-taxonomy.md`](../../grammar/three-taxonomy.md) |
| `specs/…/reasoning/scene-analysis.md` | [`reasoning/scene-analysis.md`](../../reasoning/scene-analysis.md) |
| `specs/…/reasoning/capability-catalog.md` | [`reasoning/capability-catalog.md`](../../reasoning/capability-catalog.md) |

**The one living file in here is `specs/…/adr.md`** — the Architecture
Decision Records every layer of the repo cites. It is amended in place (its
own amendment log records each revision); the snapshot rule above does not
apply to it.
