# Marker Highlight — the editorial rules

The drawn word-emphasis device: a marker sweep behind a phrase, a hand-drawn ring around a word, a
burst radiating from a stat, a scribbled underline, a struck-out line.

**This file owns none of the drawing.** `MARKER_PATTERNS` (`hyperframes-animation`) owns all five
mode implementations — markup, CSS, the timeline tween, the path-length math, multi-line handling,
per-word styling and mode cycling. Load it when you build one; do not re-derive a mode here.

What is local — and what no upstream page states — is **which moment in a promo arc each mode
belongs to, and how sparingly the device may be spent.** A marker is editorial punctuation, not a
decoration applied because a scene looks empty.

## When to use which mode

| Mode | Best for | Energy | Promo arc moment |
|------|----------|--------|------------------|
| Highlight | Kicker lines, value props, single emphasis words | Calm, confident | Hook, solution, results |
| Circle | One-word emphasis on a critical claim | Casual, hand-drawn | Pain reveal, before/after |
| Burst | High-energy stat numbers, surprise reveals | Loud, kinetic | Stat moments, CTA |
| Scribble | Underline a phrase, draw attention to a quote | Editorial, playful | Pull-quotes, social proof |
| Sketchout | "Before" prices, struck-out competitors | Comparative | Before/after, competitor frames |

The mode names are `MARKER_PATTERNS`' names — this table maps them onto the arc, it does not define
them. Pick the row whose *moment* matches the frame's `tone:` and `energy:` keys
(`reasoning/scene-analysis.md`), never the row that looks most impressive.

## The caps

1. **One marker per film.** The drawn marker is a single reserved beat — the count is a row of the
   budget table in `reasoning/scene-analysis.md`, the only place that number lives (ADR-008). Spend
   it on the one moment that most deserves it. Once it is spent, the lighter alternative is a
   spotlight (`patterns/visual-patterns.md` § Anchored Callout / Spotlight), and never both cues on
   the same region.
2. **One mode per scene.** Cycling modes inside a scene reads as undisciplined; rotate only across
   major narrative beats, and only within the film-wide cap above.
3. **Never strike out your own brand name.** Sketchout is for *what you replace* — an outdated
   price, a competitor, the old way. Striking your own name reads as self-deprecation the viewer
   did not ask for. If the beat wants irony, circle it instead.
4. **Never animate the marker's colour.** Set it once from the design system's emphasis token, then
   fade or scale it in. An animated hue shift on an emphasis cue reads as Web 2.0.
5. **Fire it after the word has settled**, never during the word's own entrance. A marker that
   arrives with the text looks like it is leading the text rather than reacting to it; the
   entrance tween must complete first.
6. **The active design system's Avoid list outranks this table.** Some brands are built for the
   device (`design-systems/notion/DESIGN.md` names it a signature flourish); others ban it outright
   (`design-systems/linear-app/DESIGN.md`). Brand fit is decided before the arc moment is.
