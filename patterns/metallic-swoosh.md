# Metallic Swoosh Transition

A premium diagonal shine for section changes. Implemented as a crossfade between two adjacent scenes with a moving gradient overlay synchronized to the fade. The transition is **authored inline in the root composition's timeline**, not as a separate sub-composition — it straddles two scene clips, so it cannot live inside either one.

**Why not `clipPath`:** Polygon `clipPath` transitions leave an anti-aliased 1px black sliver between the exiting and entering scenes because the two half-planes never share an exact subpixel boundary. The crossfade + shine approach has no seam.

## Anatomy

Three things happen during the swoosh window:

1. **Outgoing scene clip** stays opaque underneath until its clip ends — it is *not* faded out (see the crossfade note below).
2. **Incoming scene clip** fades `opacity: 0 → 1`, painting on top of the outgoing scene.
3. **Shine overlay** — a thin, hot diagonal band whose `background-position` sweeps across the frame during the same window.

## Implementation (inline in the root `index.html`)

In Phase 4, the root composition wires inter-scene transitions in its own timeline. Drop the overlay element next to your scene clips and add the swoosh tweens to the root timeline:

Set `D` from the confirmed `transition_speed` (`quick = 0.4`, `medium = 0.7`, `slow = 1.2`) and
replace the uppercase duration tokens below with numeric literals before linting.

```html
<!-- Two adjacent scene clips in the root composition. Both start invisible if
     they're not the first scene; the swoosh tweens them in/out. -->
<div data-composition-id="scene-01"
     data-composition-src="scenes/01.html"
     data-start="0" data-duration="5_PLUS_D" data-track-index="1"
     style="opacity:1"></div>

<div data-composition-id="scene-02"
     data-composition-src="scenes/02.html"
     data-start="5"  data-duration="5"   data-track-index="2"
     style="opacity:0"></div>

<!-- Shine overlay. Painting order is controlled by CSS z-index (see <style> below);
     data-track-index="9" only keeps it on a separate track so it can overlap the
     scene clips without tripping HyperFrames' same-track overlap check. -->
<div id="swoosh-01-02"
     data-start="5" data-duration="D" data-track-index="9"
     aria-hidden="true"
     style="opacity:0;"></div>

<style>
  #swoosh-01-02 {
    position: absolute;
    inset: 0;
    z-index: 50;
    pointer-events: none;
    background: linear-gradient(
      115deg,
      transparent 35%,
      rgba(255,255,255,0.35) 47%,
      rgba(255,255,255,0.85) 50%,
      rgba(255,255,255,0.35) 53%,
      transparent 65%
    );
    background-size: 250% 100%;
    background-position: -75% 0;
    mix-blend-mode: screen;
  }
</style>

<script>
  // Add these tweens to the ROOT composition's timeline. Times below are
  // absolute (in seconds) on the root timeline — the swoosh fires at t=5s.
  // window.__timelines["main"] is registered in index.html (see Phase 4).
  const root = window.__timelines["main"];
  const D = Number("TRANSITION_DURATION_SECONDS");

  // Fade ONLY the incoming scene 0→1; the outgoing scene stays opaque
  // underneath until its D-extended clip ends. Fading
  // both at once drops each to ~0.5 opacity at the midpoint, letting the white
  // body bg show through everywhere the shine band isn't — a brightness flash.
  // (Same incoming-only rule as transition-catalog.md / phase-4-production.md.)
  root.to('[data-composition-id="scene-02"]',
    { opacity: 1, duration: D, ease: "power2.inOut" }, 5);

  // Shine: pop in, sweep across, fade out — all inside D.
  root.to("#swoosh-01-02",
    { opacity: 1, duration: D * 0.2, ease: "power1.out" }, 5);
  root.to("#swoosh-01-02",
    { backgroundPosition: "175% 0", duration: D, ease: "power2.inOut" }, 5);
  root.to("#swoosh-01-02",
    { opacity: 0, duration: D * 0.2, ease: "power1.in" }, 5 + D * 0.8);
</script>
```

## Tuning Knobs

- **Band thickness** — widen the `transparent ... transparent` stops (e.g. 30% / 70%) for a softer, more cinematic sweep.
- **Sweep angle** — `115deg` reads as left-to-right with a slight downward tilt. Use `65deg` to reverse direction for "going back" beats.
- **Hot-spot intensity** — push the centre stop to `rgba(255,255,255,1.0)` for a brighter pop on dark backgrounds; pull it to `0.6` on light scenes.
- **Crossfade vs shine timing** — keep the shine peak (`background-position` at 50%) aligned with the midpoint of the crossfade so the bright moment lines up with the visual hand-off.

## Where Not to Use It

- Dialog-driven beats — the swoosh implies "we're moving forward". Don't fire it mid-sentence.
- Back-to-back swooshes — readers stop noticing after the second; rotate with a quiet crossfade for breathing room.
- Final fade-to-black — the closing scene should exit passively (no shine).

## Validation

After wiring the swoosh, run `npx hyperframes inspect .` to confirm no overlay element overflows the canvas, and `npx hyperframes validate .` to confirm contrast on any text visible *behind* the overlay is still WCAG-clean during the sweep. (The gates take the project directory, not a file.)

**Manual check:** neither `inspect` nor `validate` detects `mix-blend-mode: screen` luminance overflow — they're layout and contrast checks, not luminance audits. Preview the swoosh against your brightest scene background by eye; `screen` blending can push near-white past 100% luminance and produce a flash. If that happens, drop the band's `rgba` alpha to ~0.65, or remove the blend mode and rely on `opacity` alone.
