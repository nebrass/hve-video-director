# Credits

## Music

| | |
|---|---|
| **Title** | Warm Pad Essentials Drone by Mantice |
| **Source** | https://freesound.org/people/bassimat/sounds/854842/ |
| **Licence** | CC0-1.0 (public domain dedication) |
| **File** | `background-music.mp3` (not committed — see `.gitignore`) |

Chosen by the user from Freesound candidates and confirmed as the exact track before
mixing, per the Phase-5 contract. The brief pins the URL with its numeric sound ID,
which is what `scripts/validate_brief.py` verifies — a title alone is not provenance.

## Voice

Narration synthesised with ElevenLabs (voice **Daniel**), confirmed in the Creative
Brief as `voice: elevenlabs:Daniel:onwK4e9ZLuTAKqWW03F9`. Section audio is assembled
by `scripts/generate_voiceover.py --assemble-only`.

## Fonts and design system

Stripe-derived dark palette from `design-systems/`, rendered with system-stack
typography. No third-party font files are bundled.

## Rendering

HyperFrames (HTML + GSAP, headless Chromium) via `npx hyperframes render`. GSAP is
loaded from jsDelivr under Subresource Integrity, pinned in the scene files.
