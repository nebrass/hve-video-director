# Example Project — a real promo for blog.nebrass.fr

This is a **real promo video for [blog.nebrass.fr](https://blog.nebrass.fr)**, built by the
pipeline it ships with. It's hve-video-director's **reference build**: a genuine video the skill
produced for a real app with a real UI, so **the actual product is on screen** as the spine —
captured live via Chrome DevTools. It still dogfoods the skill (closing "made with
`/hve-video-director`" sign-off).

> **Why the subject changed (v0.0.4).** The previous flagship promoted *this skill* itself —
> a UI-less CLI/prompt skill — so it had no app to film and was built entirely from typography
> and a simulated terminal. That made the reference build model flat text-on-white ("simple
> shapes and text"). Re-subjecting it to a real app puts the real product on screen, which is
> what the skill is for.

Every *input* artifact lives in this directory — it's the project's primary demo, not a staged
sample. The rendered video and audio are the only things not committed.

## What's here

| Path | Phase | What it is |
|---|---|---|
| `project-plan.md` | 0 | Mode (promo), `product_surface: ui`, aspect (16:9), design-system (vercel), phase tracker |
| `context.md` | 0 | Product brief — what blog.nebrass.fr is, audience, goal of the video |
| `storyboard.md` | 1 | 5-scene 53s plan: Establishing → Depth → Breadth → Volume → CTA |
| `public/screenshots/*.png` | 2 | 5 real Chrome-DevTools captures of the live blog (the on-screen spine) |
| `DESIGN.md` | 3 | Copied from `design-systems/vercel/DESIGN.md` |
| `scenes/00-establishing.html` | 3 | Homepage hero in a browser frame + slow motivated push-in |
| `scenes/01-depth.html` | 3 | A real post's syntax-highlighted code + diff, push-in toward the code |
| `scenes/02-breadth.html` | 3 | The categories index (real tag counts), static settle |
| `scenes/03-scroll.html` | 3 | Full-page homepage, scroll-within-frame down the post list |
| `scenes/04-cta.html` | 3 | `blog.nebrass.fr` + "made with `/hve-video-director`" sign-off (closing scene) |
| `index.html` | 4 | Root 53s composition with 5 sub-comp loaders + incoming-only crossfades |
| `voiceover.py` | 5 | ElevenLabs TTS (Matilda) + `npx hyperframes transcribe` verification + auto-pad to VIDEO_DURATION |
| `voiceover.mp3` | 5 | Generated 53s voiceover (5 sections with silence padding) — gitignored, regenerable |
| `background-music.mp3` | 5 | "Spark of Inspiration" by ViraMiller (Freesound, CC-BY 4.0) — gitignored, fetch via Step 3 |
| `voiceover-with-music.mp3` | 5 | ffmpeg-mixed final audio: music normalized + EQ'd + sidechain-ducked under the voice — gitignored, regenerable |
| `out/final.mp4` | 5 | **The rendered video.** `npx hyperframes render` output — not committed; regenerable build artifact. |
| `CREDITS.md` | — | CC-BY attribution for the music + capture provenance + voiceover provenance |

The source files (`.html`, `.md`, `.py`) **and the real screenshots** (`public/screenshots/*.png`)
are committed as the reference build. The rendered `out/final.mp4` and the intermediate audio
(`voiceover.mp3`, `background-music.mp3`, `voiceover-with-music.mp3`, `vo_section_*.mp3`,
`transcript.json`) are regenerable and `.gitignore`'d — see `example/.gitignore`.

## Reproducing the render

```bash
# 1. Set your API keys
export ELEVENLABS_API_KEY=<your-key>
export FREESOUND_API_KEY=<your-key>     # only needed if rebuilding music search

# 2. Regenerate the voiceover
python3 voiceover.py
#  → produces voiceover.mp3 + transcript.json
#  → ~$0.04 of ElevenLabs credits (5 sections, ~100 words)

# 3. (Optional) re-search Freesound for music; otherwise re-fetch the
#    same track used in the committed version:
curl -sL "https://cdn.freesound.org/previews/746/746454_16085323-hq.mp3" \
  -o background-music.mp3
#    See workflows/phase-5-audio.md § Step 5.2 for the search recipe.

# 4. Mix audio. `apad=whole_dur=53` is critical — without it the mix ends
#    where the voiceover ends, and HyperFrames render finds no audio for the
#    trailing frames of the 53s composition. voiceover.py already pads, but the
#    recipe pads again as a belt-and-suspenders guard in case you brought your
#    own voiceover.mp3.
ffmpeg -y -i voiceover.mp3 \
  -af "apad=whole_dur=53,loudnorm=I=-16:TP=-1.5:LRA=11" \
  voiceover-normalized.mp3
ffmpeg -y -i voiceover-normalized.mp3 -i background-music.mp3 \
  -filter_complex "
    [1:a]atrim=0:53,loudnorm=I=-30:TP=-3:LRA=11,
         highpass=f=100,equalizer=f=2500:t=q:w=1:g=-3,
         afade=t=in:st=0:d=2,afade=t=out:st=49:d=4,aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[music];
    [0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,asplit=2[vo][key];
    [music][key]sidechaincompress=threshold=0.05:ratio=3:attack=150:release=900[ducked];
    [vo][ducked]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,
                alimiter=limit=0.89,aresample=44100[out]" \
  -map "[out]" -c:a libmp3lame -q:a 2 voiceover-with-music.mp3
# ↑ aformat (not bare aresample) on BOTH legs: ElevenLabs/tts often emit a MONO voiceover, and
#   sidechaincompress aborts ("Failed to inject frame into filter network") if the key and music
#   differ in channel layout. Forcing both to stereo/44.1k up front avoids it.

# 5. Run quality gates + render
npx hyperframes doctor
npx hyperframes lint     .                 # operates on the project DIR (finds index.html)
npx hyperframes inspect  . --samples 12
npx hyperframes validate .
mkdir -p out
npx hyperframes render   . --output out/final.mp4 --quality high
#   On WSL2 (and some sandboxed hosts) native render fails at
#   "Protocol error (Page.captureScreenshot)"; add --docker to render in a container
#   (needs Docker running): npx hyperframes render . --output out/final.mp4 --quality high --docker
#   On machines with <=8 GB RAM, also add --no-low-memory-mode — low-memory mode forces the same
#   screenshot capture that fails; it switches Docker back to beginframe capture:
#   npx hyperframes render . --output out/final.mp4 --quality high --docker --no-low-memory-mode
```

Render time: ~20–30s on a 16-core machine with hardware GPU.

## What this example demonstrates

The **real product is the spine** — 4 of 5 scenes composite a live blog capture framed in
browser chrome with a distinct, motivated, deterministic camera move; scene 4 is the closing
text CTA (connective tissue). Every claim in the voiceover maps to something verifiable on the
live blog:

- **Establishing** → the real homepage hero (`01-home-hero-light.png`)
- **"Real bugs, real fixes… Puppeteer's screencasts, merged upstream"** → the post
  (`04-post-code-light.png`) + merged Puppeteer PR #15112, both real
- **"Kubernetes, security, Azure, machine learning — dozens of topics"** → the categories index
  (`05-categories-light.png`), real tag counts
- **"Years of write-ups"** → the full homepage post list, scrolled inside the frame
  (`01-home-full-light.png`), posts dated 2023–2026
- **Camera language is deterministic + seekable** → push-in / scroll are wrapper-transform
  tweens on a paused GSAP timeline; no `<img>`-dimension tweens, no `tl.from()`, no clipPath

No invented metrics. No filler copy. No fictional product — a stranger pausing on any product
frame can identify the blog (the `patterns/anti-slop.md` screenshot test).

## Caveats

- **Voice pronunciation:** ".fr" is spoken as "eff arr" and "hve-video-director" as "Aitch Vee Ee
  Video Director" (phonetic spelling) — space-separated capital letters render as a blob otherwise.
  See `workflows/phase-5-audio.md` § "Pronouncing acronyms".
- **Music attribution:** the chosen track is CC-BY 4.0, requiring attribution. See `CREDITS.md`.
  To swap for a different track, re-run the Freesound search in Phase 5.2.
- **`vo_section_NN.mp3` and `transcript.json` are debugging intermediates.** They're created by
  `voiceover.py` on every run, `.gitignore`'d, and safe to delete.
- **Full-page capture + lazy images:** the homepage thumbnails lazy-load; the Phase-2 capture
  forces `loading="eager"` and scrolls the page before `fullPage` capture so `03-scroll` shows
  real thumbnails, not blank boxes.
