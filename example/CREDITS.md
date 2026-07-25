# Credits

## Background music

**"Spark of Inspiration"** by ViraMiller
- License: Creative Commons Attribution 4.0 (CC-BY 4.0)
- Source: https://freesound.org/people/ViraMiller/sounds/746454/
- Duration: 104.3 seconds (trimmed to 53s in the mix)
- Use in this project: background score — normalized to ≈-30 LUFS, high-passed, a −3 dB dip at 2.5 kHz to clear the voice, sidechain-ducked under the voiceover, 2s fade-in / 4s fade-out

## Voiceover

Generated via [ElevenLabs](https://elevenlabs.io) using the **Matilda** voice (`XrExE9yKIg1WjnnlVkGX`) and the `eleven_multilingual_v2` model. Script in `voiceover.py`. Not Creative Commons — generated voiceover content is owned under MIT.

## Product captured

Screenshots in `public/screenshots/` are of **[blog.nebrass.fr](https://blog.nebrass.fr)** — Nebrass Lamouchi's own blog — captured live via Chrome DevTools in Phase 2. The blog is the subject of this promo.

## Transcription

Word-level timing verified using [HyperFrames'](https://www.npmjs.com/package/hyperframes) bundled Whisper (`npx hyperframes transcribe`), tiny model.

## Render

Composition rendered by [HyperFrames CLI](https://www.npmjs.com/package/hyperframes) via headless Chromium, then muxed against `voiceover-with-music.mp3`.
