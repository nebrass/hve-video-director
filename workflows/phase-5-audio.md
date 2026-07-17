# Phase 5: Audio & Render

Generate voiceover, mix music, and render the final video.

## Step 5.1: Generate Voiceover

**The voiceover must match the visuals.** This is non-negotiable.

### Extract Scene Timings

Read the main composition file to extract exact scene timings and content. Build a timing table:

```
Scene              | Start | End  | Duration | Visual Content
-------------------|-------|------|----------|---------------
Hook               | 0s    | 5s   | 5s       | "Title text" + stat
Pain Point 1       | 5s    | 9s   | 4s       | "Pain title" + icon
...
```

### Write Aligned Script

For each scene, write voiceover text that:
- References what's visually on screen
- Starts 1s after scene start (buffer)
- Ends 0.5s before scene end (buffer)
- Matches the spoken stat to the visual stat

#### Pronouncing acronyms and brand abbreviations

ElevenLabs voices (and most current TTS models) run space-separated capital letters together as a phonetic blob, not as spelled letters. Writing "H V E" in a script can render as "Sage V E" or similar — the model treats it as a single syllable.

**Always write acronyms phonetically** when you want them spelled out:

| Want spoken | Write in script |
|---|---|
| H V E spielberg | `Aitch Vee Ee Spielberg` |
| AI | `A I` *(spelled)* or `aye eye` *(emphasized)* |
| API | `A P I` *(spelled)* or `ay pee eye` *(emphasized)* |
| SaaS | `sass` *(natural word)* or `S A A S` *(spelled)* |
| URL | `U R L` *(spelled)* or `earl` *(natural)* |

Periods between letters (`H. V. E.`) work in some TTS but cause sentence-end pauses in others — phonetic spelling is the most reliable. Test the section once and inspect the output before generating the rest.

#### Voice timing is non-linear with word count

Word count is a weak proxy for spoken duration. Comma density matters more — Matilda (and most TTS voices) take ~0.3–0.5s of pause at each comma. A 22-word sentence with 5 commas can run 15 seconds; the same idea in 26 commaless words takes 10 seconds.

When a section overruns budget, **drop commas before dropping words**. Restructure with fewer subclauses and more direct phrasing. Same information, half the commas, same content density:

```
❌ Longer — "Discover the product, using design thinking. Write the narrative, scene by scene. Capture the live app via Chrome DevTools."
✅ Shorter — "Discover with design thinking. Storyboard the narrative. Capture via Chrome DevTools."
```

Each comma you remove saves ~0.3–0.5s. A 5-comma rewrite can reclaim 2+ seconds without cutting meaning.

`scripts/generate_voiceover.py` catches this for you at assembly time: when a section's audio overruns its slot it prints a stderr warning like `WARNING: section N audio overruns its Xs slot by Ys — every later section starts early and desyncs from its scene. Shorten this section's text.` **Watch stderr** — a single overrun cascades into every later section, so fix the flagged one (drop commas first) and re-run before moving on.

### Clip scenes and VO timing

For clip scenes the scene window is footage-derived (Phase 4), not VO-derived.
Write that scene's VO to fit the existing window (start ~1s in, end ≥0.5s before
the window ends) exactly as for any scene — do not stretch the clip. Captions for
footage use the existing Whisper VO transcript (`auto`).
**Clip-own audio is opt-in.** Default is `Clip audio: none` (clips muted, only
`voiceover-with-music.mp3` plays). A scene that sets `Clip audio: <volume>` gets its sound
mixed in with the VO ducked under it — see Step 5.3a.

### Generate with ElevenLabs (default, higher quality)

Copy the canonical script into the project first, then edit the **project-local
copy** — never edit the shared skill install. Editing `$SKILL_DIR`'s script
would bake this project's config into every future project, and two projects
could not run concurrently.

```bash
# $SKILL_HOMES is the canonical home list defined in SKILL.md § Runtime Compatibility.
# Keep this line identical to that definition; edit it there, not here.
SKILL_HOMES="$HOME/.claude/skills $HOME/.copilot/skills $HOME/.agents/skills .claude/skills .github/skills .agents/skills"
SKILL_DIR=$(for h in $SKILL_HOMES; do [ -d "$h/hve-spielberg" ] && echo "$h/hve-spielberg" && break; done)
[ -n "$SKILL_DIR" ] || { echo "ERROR: hve-spielberg install dir not found — set SKILL_DIR to the skill's path manually" >&2; }
cp "$SKILL_DIR/scripts/generate_voiceover.py" ./voiceover.py
```

Edit the project-local `./voiceover.py`:
- Set `VOICE_ID` to selected voice from Phase 1
- Set `sections` list with `(start_time, text)` pairs
- Set `VIDEO_DURATION` to match composition

```bash
python3 ./voiceover.py    # writes vo_section_NN.mp3 + voiceover.mp3 into the project dir
```

### Alternative: HyperFrames-native TTS (no API key, local)

If `ELEVENLABS_API_KEY` is unset, HyperFrames ships a local TTS via Kokoro-82M (no API key, no rate limits, ~54 voices across 8 languages). Quality is good but noticeably below ElevenLabs Multilingual v2 — prefer ElevenLabs when you can.

```bash
# Single-line narration
npx hyperframes tts "Your script line here." --voice af_nova --output voiceover.mp3

# From a file
npx hyperframes tts script.txt --voice af_heart --output voiceover.mp3

# List all 54 voices (8 languages)
npx hyperframes tts --list
```

Voice naming convention: `<lang><gender>_<name>` (e.g. `af_nova` = American female "Nova", `bm_george` = British male "George"). For non-English narration, install `espeak-ng` system-wide (`brew install espeak-ng` / `apt-get install espeak-ng`).

Whisper verification (next step) is renderer-agnostic and works identically for either TTS path.

### Verify timing (CRITICAL — do not skip!)

Prefer `hyperframes transcribe` (bundled with HyperFrames, no separate install):

```bash
npx hyperframes transcribe voiceover.mp3 --model tiny
cat transcript.json | python3 -m json.tool | head -30
```

Falls back to standalone `whisper` (use `--output_format json` so the timing data is consumable by `scripts/generate_voiceover.py` — SRT is a presentation format, not a parsing target; add `--word_timestamps True` so segments carry per-word timing, which the overlap check needs — sentence-level segments produce false positives):

```bash
whisper voiceover.mp3 --model tiny --output_format json --word_timestamps True --output_dir .
cat voiceover.json | python3 -m json.tool | head -30
```

**Whisper tiny-model timestamps drift ±0.5s** because the model extends word boundaries into trailing silence. For precise per-section gap analysis, use `ffmpeg silencedetect` instead — it's exact:

```bash
ffmpeg -i voiceover.mp3 -af "silencedetect=noise=-40dB:d=0.3" -f null - 2>&1 | grep silence
```

Output gives precise `silence_start` / `silence_end` timestamps for every gap ≥0.3s of silence below -40dB. Compare these against your section timings to verify each section ends within its scene's window.

Compare timestamps against scene timings. If ANY overlap detected:

1. **Drop commas before dropping words** — comma pauses inflate duration significantly (see "Voice timing is non-linear" above)
2. **Shorten text** — make it punchier, cut filler words
3. **Increase gaps** — push next section's start time 1-2s later
4. **Add pauses** — insert "..." in text
5. **Regenerate and verify again**

**Repeat until ZERO overlaps. Do NOT ask the user — just fix it.**

### Captions (REQUIRED in tutorial mode)

If the content-mode is `tutorial`, on-screen VO captions are **mandatory on every footage
segment** (spec §7.2) and this **intentionally overrides** the default-optional policy in
`patterns/INDEX.md`. Silence-only segments (no VO words in the window) are exempt, as are
segments whose on-screen copy already renders the spoken line verbatim (e.g. a recap beat or
step title card where the visible text IS the narration) — in that case mark `Captions: carried`
on the storyboard scene so the skip is a recorded, deliberate choice rather than an oversight.
In promo/showcase captions stay optional.

Captions are a HyperFrames caption sub-comp synced to `transcript.json` — see
`references/captions.md` (GROUPS mechanism) and the Phase-3 caption-track recipe. Each
footage scene whose storyboard `Captions:` is `auto` must carry a caption track wired over
its window in `index.html`.

Orchestrator enforcement before render (tutorial mode) — do not advance until all hold:
1. `transcript.json` exists and passed the timing check.
2. Every footage scene with VO has a caption track, UNLESS its storyboard marks `Captions: carried`
   (on-screen copy already shows the spoken line) or the window is silence-only. A bare
   `Captions: auto` scene with VO and no track still blocks.
3. Each caption group has a hard `tl.set(... {opacity:0, visibility:"hidden"}, group.end)` kill
   (the `references/captions.md` `[caption-lint]` self-check logs warnings otherwise).
There is no programmatic gate; a true build-time rule would be upstream `hyperframes` lint work (spec §14).

### Caption sidecars — draft subtitles (all modes)

Separate from the burned-in tutorial captions above: emit **toggleable** subtitle sidecars next to
the render so the voiceover is readable in any player and friendly to screen readers / scrubbers.
Run this in **every** mode (promo / showcase / tutorial) once `transcript.json` exists.
`scripts/caption_gen.py` groups the word timings into readable cues and writes `voiceover.srt` +
`voiceover.vtt` (the names `.gitignore` already reserves):

```bash
# Reuse $SKILL_DIR resolved in § Generate with ElevenLabs (re-resolve it the same way in a fresh shell).
python3 "$SKILL_DIR/scripts/caption_gen.py"   # auto-detects transcript.json, then voiceover.json
```

These are **ASR draft subtitles** of the spoken track — not yet WCAG 2.1 closed captions, which also
transcribe meaningful non-speech audio (music/sfx cues, speaker IDs) and require a human review pass
over the ASR output. Ship them as a reviewable starting point; the burned-in tutorial captions
(above) remain the in-frame accessibility layer.

### Pad voiceover to VIDEO_DURATION

The voiceover audio must match the composition's total duration exactly. If it's shorter, HyperFrames render finds no audio for trailing frames and may truncate. Pad with `apad`. Use the same `VIDEO_DURATION` the composition uses (from `project-plan.md`); the literal `60` below is just an example for a 60s spot — replace it with your project's duration:

```bash
VIDEO_DURATION=60   # match the duration chosen in Phase 1
ffmpeg -y -i voiceover.mp3 -af "apad=whole_dur=${VIDEO_DURATION}" -c:a libmp3lame -q:a 2 voiceover-padded.mp3
mv voiceover-padded.mp3 voiceover.mp3
```

(`scripts/generate_voiceover.py` does this automatically using `VIDEO_DURATION`.)

## Step 5.2: Background Music

### Freesound API (if FREESOUND_API_KEY set)

Freesound provides a real, public CC-licensed audio search API. Get a key at <https://freesound.org/apiv2/apply>. Authentication uses a `token` query parameter; previews require no OAuth2.

Derive mood/genre keywords from the storytelling phase (e.g., "cinematic corporate uplifting loop"). Filter by `duration` so you don't pick a 10-minute ambient drone for a 45s spot, and by `license` so you stay on safe ground (CC0 or CC-BY).

```bash
QUERY="cinematic corporate uplifting"
DURATION_S=42  # match your video duration

curl -sG "https://freesound.org/apiv2/search/text/" \
  --data-urlencode "query=${QUERY}" \
  --data-urlencode "filter=duration:[${DURATION_S} TO 180] license:(\"Creative Commons 0\" OR \"Attribution\")" \
  --data-urlencode "fields=id,name,duration,license,username,previews,url" \
  --data-urlencode "page_size=10" \
  --data-urlencode "token=${FREESOUND_API_KEY}" \
| python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('results', []):
    print(f\"  [{r['id']}] {r['name']} ({r['duration']:.1f}s) — {r['license']} by {r['username']}\")
    print(f\"      page:    {r['url']}\")
    print(f\"      preview: {r.get('previews', {}).get('preview-hq-mp3') or r.get('previews', {}).get('preview-lq-mp3', '')}\")
"
```

Present results to the user. Each hit has a high-quality .mp3 preview URL (`previews.preview-hq-mp3`) usable directly as a soundtrack. Download the chosen track:

```bash
curl -sL "<selected-preview-hq-mp3-url>" -o background-music.mp3
```

**Attribution:** If the chosen track is CC-BY (not CC0), you must credit the author. Write `CREDITS.md` in the project root:

```
Background music: "<track name>" by <username> (Freesound, <license>)
URL: <track page URL>
```

Full-quality original downloads require OAuth2; previews are sufficient for video soundtracks.

### User-Provided (fallback)

If no FREESOUND_API_KEY or user prefers own music:

```json
{
  "questions": [{
    "question": "Background music?",
    "header": "Music",
    "options": [
      { "label": "I'll provide a file", "description": "Provide path to an MP3" },
      { "label": "No music", "description": "Voiceover only" }
    ],
    "multiSelect": false
  }]
}
```

## Step 5.3: Audio Mixing

### Normalize voiceover
```bash
ffmpeg -y -i voiceover.mp3 -af "loudnorm=I=-16:TP=-1.5:LRA=11" voiceover-normalized.mp3
```

### Mix music (if using background music)

The music is a **subtle bed under the voice**, not a soundtrack — it should be *felt more than
heard* while words play, and only noticeable in its absence. Three things make it behave:
(1) normalize the music to a **known base level** so the balance doesn't depend on how hot the
source file happens to be, (2) **EQ space** around the voice, and (3) **sidechain-duck the music
under the voiceover** so it dips while words play and breathes back in the gaps.

```bash
# DURATION = video length in seconds (from Phase 1 / project-plan.md).
# Fade-out runs 4s (3–5s is the polished range); never cut the music abruptly.
DURATION=60                                # ← replace with your video duration
FADE_OUT_START=$((DURATION - 4))

ffmpeg -y -i voiceover-normalized.mp3 -i background-music.mp3 \
  -filter_complex "
    [1:a]atrim=0:${DURATION},
         loudnorm=I=-30:TP=-3:LRA=11,
         highpass=f=100,
         equalizer=f=2500:t=q:w=1:g=-3,
         afade=t=in:st=0:d=2,
         afade=t=out:st=${FADE_OUT_START}:d=4,
         aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[music];
    [0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,asplit=2[vo][key];
    [music][key]sidechaincompress=threshold=0.05:ratio=3:attack=150:release=900[ducked];
    [vo][ducked]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,
                alimiter=limit=0.89,
                aresample=44100[out]" \
  -map "[out]" -c:a libmp3lame -q:a 2 \
  voiceover-with-music.mp3
```

What each stage does — tune by ear, the numbers are starting points, not targets:

- **`loudnorm=I=-30` (music base level)** — normalizes the bed to ~-30 LUFS, ~14 LU under the
  -16 LUFS voice, so the mix no longer depends on the track's mastered level. This replaces the
  old fixed `volume=0.22`, which scaled an *un-normalized* download and gave unpredictable
  loudness. If the music vanishes under speech, raise toward -28/-26; if it competes, lower toward -32.
- **`highpass=f=100` + `equalizer=f=2500…g=-3` (music EQ)** — strips sub-100 Hz rumble (product
  demos rarely need deep bass) and dips ~3 dB around 2.5 kHz to carve room for speech clarity.
- **`sidechaincompress` keyed by the voice (`[key]`)** — the core move: the music ducks ~3–6 dB
  whenever the voiceover plays (attack 150 ms, release 900 ms = smooth, not pumping) and returns
  in pauses. Same filter the clip-audio path uses in Step 5.3a, here applied to the *music* with
  the *voice* as the trigger. If it pumps, lower `ratio` or lengthen `release`; if the first
  words are masked, drop `attack` toward 100.
- **`alimiter=limit=0.89` (master ≈ -1 dBFS ceiling)** — a peak limiter, *not* a loudness
  normalizer. The voiceover is already at -16 LUFS (normalize step) and dominates the mix, so a
  -30 LUFS bed only nudges integrated loudness ~+0.2 LU — the mix lands ≈-15.8 LUFS on its own,
  in-spec. This matches the guide's master chain ("limiter, ceiling -1 dB").
  **Do not add a dynamic `loudnorm` master here.** Single-pass `loudnorm` rides gain, so it boosts
  the bed in the intro, outro, and every VO pause (chasing -16 when only the quiet music is present),
  which *undoes the sidechain duck and fights the fades* — verified: with a dynamic master the music
  measures **louder** under speech than in the gaps. If you need to hit -16 LUFS more exactly,
  correct with a **constant** gain after validation (below), never a dynamic pass.
- **`aformat=…:channel_layouts=stereo` on both legs (not `aresample`)** — `sidechaincompress`
  requires its two inputs to share sample format, rate, **and channel layout**; ElevenLabs (and the
  `hyperframes tts` fallback) often emit a **mono** voiceover, and mixing a mono key against a stereo
  music bed makes the filter abort with `Error reinitializing filters! Failed to inject frame into
  filter network`. `aformat` forces both legs to stereo/44.1k/fltp up front — a superset of the old
  `aresample=44100` (which fixed only the rate). The music-branch `loudnorm` can also internally
  switch to 192 kHz, so pinning the rate here keeps the `amix`/MP3 encoder happy too.

**Critical:** keep `amix … normalize=0`. The default `normalize=1` divides each input by the input
count (a hidden -6 dB per track), which would gut the already-quiet bed. Set level via the music
base (`loudnorm=I=-30`) plus the VO's own -16 LUFS normalization, not `amix` normalization.

### No-music path (voiceover only)

If the user chose "No music" in Step 5.2, **you still need to produce `voiceover-with-music.mp3`** — the root composition's `<audio>` element references that filename. Without it, the rendered video has no audio.

Two equivalent options. Pick whichever is more readable in your project:

```bash
# Option A: re-encode the normalized voiceover to the canonical output name
ffmpeg -y -i voiceover-normalized.mp3 -c:a libmp3lame -q:a 2 voiceover-with-music.mp3

# Option B: hard-link / copy (faster, identical content)
cp voiceover-normalized.mp3 voiceover-with-music.mp3
```

Then proceed to Step 5.4 — the render step doesn't care whether music was mixed in or not, as long as `voiceover-with-music.mp3` exists and is the full composition duration.

Validate with `ebur128`: integrated loudness should land around -16 LUFS, and the reported true peak should come in at or under -1 dBTP. `alimiter` caps *sample* peaks, not inter-sample/true peaks, so treat -1 dBTP as a target to **verify** — if `ebur128` reports a true peak above -1 dBTP, lower the Step 5.3 limiter ceiling (e.g. `alimiter=limit=0.79`, ≈ -2 dBFS) and re-render.

```bash
ffmpeg -hide_banner -i voiceover-with-music.mp3 -af ebur128=peak=true -f null - 2>&1 | tail -16
```

If integrated loudness lands outside -16 ±1.5 LUFS (e.g. a sparse, pause-heavy VO drags it low),
nudge it with a **constant** gain — `volume=<delta>dB` shifts the whole mix uniformly, so it
preserves the duck and the fades, unlike a dynamic `loudnorm` — then re-cap the peak:

```bash
ffmpeg -y -i voiceover-with-music.mp3 -af "volume=1.5dB,alimiter=limit=0.89" \
  -c:a libmp3lame -q:a 2 voiceover-with-music.fixed.mp3
mv voiceover-with-music.fixed.mp3 voiceover-with-music.mp3
```

## Step 5.3a: Clip-own audio (opt-in)

Run only when a storyboard scene sets `Clip audio: <volume>` (not `none`). Per clip you need:
clip path (`Clip:`), the scene `data-start` (`CW`, from index.html), `Clip in/out`, `Speed`, `<volume>`.

```bash
CLIP=public/clips/scene-03-demo.mp4       # storyboard `Clip:`
CIN=2.0 ; COUT=8.0 ; SPEED=1.0            # `Clip in/out` + `Speed` — CIN must equal the
                                           # scene <video>'s data-media-start or A/V desync
CW=18.5                                    # scene data-start in index.html
VOL=0.6                                    # `Clip audio` value
DELAY=$(echo "$CW*1000/1" | bc)

# 1. Extract+trim clip audio, loudness-normalize, scale by VOL, delay to start at CW.
ffmpeg -y -ss "$CIN" -to "$COUT" -i "$CLIP" \
  -af "loudnorm=I=-18:TP=-2:LRA=11,volume=${VOL},adelay=${DELAY}|${DELAY}" \
  -ac 2 clip-audio-03.mp3

# 2. Duck the VO+music under the clip (sidechain), then mix the clip on top. Keep the
#    canonical output filename — Step 5.4 reads it unchanged.
ffmpeg -y -i voiceover-with-music.mp3 -i clip-audio-03.mp3 \
  -filter_complex "
    [1:a]asplit=2[clip][key];
    [0:a][key]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300[ducked];
    [ducked][clip]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,
                  alimiter=limit=0.89[out]" \
  -map "[out]" -c:a libmp3lame -q:a 2 voiceover-with-music.tmp.mp3
mv voiceover-with-music.tmp.mp3 voiceover-with-music.mp3
```

Repeat per opt-in clip (each pass overwrites the canonical file). Re-validate:
```bash
ffmpeg -hide_banner -i voiceover-with-music.mp3 -af ebur128=peak=true -f null - 2>&1 | tail -16
```
Expected: integrated loudness ≈ -16 LUFS, with true peak at or under -1 dBTP; the ducked window is audibly quieter under the clip's sound. As in Step 5.3, `alimiter` caps sample peaks — verify the true peak with `ebur128` and lower the limiter ceiling if it reports above -1 dBTP.

## Step 5.4: Final Render

The HyperFrames composition (`index.html`) already references `voiceover-with-music.mp3` via an `<audio>` clip on track 0 (see Phase 4). A single render command produces the final MP4 with embedded audio — no separate mux step.

### Pre-flight gates

Re-run the validation gates after wiring the audio clip, in case any caption sub-composition overlaps a visual element:

```bash
npx hyperframes lint     .                # flags "audio element has no id" (silent-video failure mode) by default
npx hyperframes inspect  . --samples 10
npx hyperframes validate .
```

### Render

```bash
mkdir -p out
npx hyperframes render . --output out/final.mp4
```

```bash
ffprobe -v error -select_streams a -show_entries stream=codec_name,duration -of default=nw=1 out/final.mp4
```
Expected: `codec_name=aac` + duration ≈ composition length — the end-to-end proof the (ducked) clip audio reached `out/final.mp4`, since footage is muted in the composition.

HyperFrames renders via headless Chromium and muxes audio in the same pass. Output is an MP4 (H.264 + AAC) at the canvas size chosen in Phase 1 (1920×1080 / 1080×1920 / 1080×1080 / 1080×1350).

### If you need a silent video first (rarely)

Render without the audio clip wired up, then mux separately with ffmpeg:

```bash
mkdir -p out
npx hyperframes render . --output out/video-silent.mp4
ffmpeg -y -i out/video-silent.mp4 -i voiceover-with-music.mp3 \
  -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest \
  out/final.mp4
```

### Verify
```bash
ffprobe out/final.mp4 2>&1 | grep -E "Duration|Video|Audio"
```

### Troubleshooting render failures

If `npx hyperframes render` hangs, errors, or produces an unexpected output, **always run `npx hyperframes doctor` first**:

```bash
npx hyperframes doctor
```

`doctor` checks Node version, FFmpeg, Chromium binary, and reports which capture path will be used. It prints actionable fix instructions for anything broken.

Known issues:

- **`HeadlessExperimental.beginFrame' wasn't found`** — Chromium 147+ removed this protocol. The HyperFrames CLI from v0.4.2 onwards auto-detects and falls back to screenshot mode. If you're on a pinned older CLI, set the escape hatch: `export PRODUCER_FORCE_SCREENSHOT=true` before render.
- **`Protocol error (Page.captureScreenshot): Unable to capture screenshot`** — the host's headless Chrome can't screenshot (observed on WSL2; can also hit sandboxed/container hosts). `doctor` passes and the composition compiles, but capture dies. Render in Docker instead — the CLI ships a containerized path: `npx hyperframes render . --output out/final.mp4 --docker` (needs Docker running; the first run pulls the image). On machines with ≤8 GB RAM the CLI auto-enables low-memory mode, which *forces the same screenshot capture* and can fail again inside Docker too — add `--no-low-memory-mode` to switch back to `beginframe` capture: `npx hyperframes render . --output out/final.mp4 --docker --no-low-memory-mode`. Output is identical.
- **Render hangs ~120 seconds then times out** — HyperFrames is trying to use system Chrome instead of `chrome-headless-shell`. Fix:
  ```bash
  npx puppeteer browsers install chrome-headless-shell
  ```
  Re-run `npx hyperframes doctor` to confirm the chrome-headless-shell binary is now detected. This is the same binary the `setup.sh` step in README's prerequisites should have installed.
- **Render succeeds but output is silent** — verify the `<audio>` element in `index.html` has an `id` attribute (HyperFrames `lint` requires this — without an `id`, the audio is silently dropped during render).
- **Some scenes look blank during transitions** — adjacent scenes need to OVERLAP during the crossfade window. See `patterns/transition-catalog.md` § Hard Rules.

## Output

- `out/final.mp4` — Final video with voiceover and music
- `voiceover.mp3` — Raw voiceover (padded to `VIDEO_DURATION`)
- `voiceover-normalized.mp3` — Loudness-normalized voiceover (input to the mix step)
- `background-music.mp3` — Selected Freesound track (if Step 5.2 ran)
- `voiceover-with-music.mp3` — Voiceover + music mix; **the file `index.html`'s `<audio src>` references — render is silent without it**
- `transcript.json` — Word-level timing from `npx hyperframes transcribe` (default), OR `voiceover.json` if you used the standalone-whisper fallback (`--output_format json`)
- `voiceover.srt` / `voiceover.vtt` — Toggleable caption sidecars (ASR draft subtitles; see § Caption sidecars — draft subtitles)

## Checkpoint

Surface the **absolute** output path (issue #21) so the user never has to hunt for the file:

```bash
FINAL="$(cd "$(dirname out/final.mp4)" && pwd)/final.mp4"   # absolute path to the render
PROJECT_DIR="$(pwd)"                                        # absolute path to the project folder
echo "Final video:    $FINAL"
echo "Project folder: $PROJECT_DIR"
```

> "Video rendered! 🎬
>
> Final video: `<absolute path to out/final.mp4>`
> Project folder: `<absolute path to the project dir>`
>
> Duration: [X]s | Resolution: [W]×[H] ([aspect]) | Audio: voiceover + music
>
> Watch it and let me know if you'd like any adjustments."

**Offer to open the result — consent-gated, never auto-launch.** Ask (native prompt) whether to open
the project folder or the file; only after the user says yes, run the matching launcher **directly**
(argv only — no `eval`, no `sh -c`, no shell interpolation of the path):

| Platform | Open folder | Open in VS Code |
|---|---|---|
| macOS | `open "<project-dir>"` | `code "<project-dir>"` |
| Windows | `explorer "<project-dir>"` | `code "<project-dir>"` |
| Linux | `xdg-open "<project-dir>"` | `code "<project-dir>"` |
| WSL | `wslview "<project-dir>"` (or `explorer.exe .`) | `code "<project-dir>"` |

Recompute these machine-specific absolute paths from the CWD each run — never persist them into a
committed artifact.
