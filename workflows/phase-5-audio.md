# Phase 5: Audio & Render

Generate voiceover, mix music, and render the final video.

**Division of labour.** *Acquisition* is delegated: the `media-use` skill's audio engine
(`AUDIO_ENGINE`) synthesizes narration, retrieves or generates a music bed (`BGM`), resolves sound
effects (`SFX`), and returns word timings. *Governance stays here* — the confirmed voice, the
exact-track music confirmation, the reviewed captions, the verified mix recipes, and render
approval. Delegation moves the search and the synthesis; it never moves a choice (ADR-001).

Resolve the tool paths in Step 5.0 first, then require the accepted composition to match the current
story fingerprint before generating any final audio:

```bash
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" require phase-4
```

A nonzero exit routes back to the earliest stale phase. A changed exact music track does not stale
Phase 1–4, so it returns here to Phase 5.

## Step 5.0: Resolve the tools this phase runs

Shell state does not survive between calls; re-state this block whenever a later call needs it.

```bash
# $SKILL_HOMES is the canonical home list defined in SKILL.md § Runtime Compatibility.
# Keep this line identical to that definition; edit it there, not here.
SKILL_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SKILL_HOMES="$HOME/.claude/skills|$HOME/.copilot/skills|$HOME/.agents/skills|$HOME/.pi/agent/skills|$HOME/.config/opencode/skills|$HOME/.cursor/skills|$HOME/.codex/skills|/etc/codex/skills|.claude/skills|.github/skills|.agents/skills|.pi/skills|.opencode/skills|.cursor/skills|.codex/skills|$SKILL_ROOT/.claude/skills|$SKILL_ROOT/.github/skills|$SKILL_ROOT/.agents/skills|$SKILL_ROOT/.pi/skills|$SKILL_ROOT/.opencode/skills|$SKILL_ROOT/.cursor/skills|$SKILL_ROOT/.codex/skills"
# zsh does not word-split unquoted $SKILL_HOMES and makes an unmatched glob fatal;
# both make this loop silently resolve to nothing. No-ops in bash/dash/sh.
if [ -n "${ZSH_VERSION:-}" ]; then setopt shwordsplit nullglob; fi
SKILL_DIR=$(
  OLD_IFS=$IFS
  IFS='|'
  for h in $SKILL_HOMES; do
    [ -d "$h/hve-video-director" ] && { echo "$h/hve-video-director"; break; }
    # Fallback: a clone left under a pre-v0.1.0 directory name. Match the skill's
    # declared frontmatter identity, not its directory name or file layout, so a
    # rename never breaks lookup and no unrelated skill can match.
    for c in "$h"/*/; do
      [ -f "$c/SKILL.md" ] && grep -q '^name:[[:space:]]*hve-video-director[[:space:]]*$' "$c/SKILL.md" \
        && { echo "${c%/}"; break 2; }
    done
  done
  IFS=$OLD_IFS
)
[ -n "$SKILL_DIR" ] || { echo "ERROR: hve-video-director install dir not found — set SKILL_DIR to the skill's path manually" >&2; }

# The delegated audio engine ships in `media-use`, resolved from the same homes.
MEDIA_SKILL_DIR=$(
  OLD_IFS=$IFS
  IFS='|'
  for h in $SKILL_HOMES; do
    [ -d "$h/media-use" ] && { echo "$h/media-use"; break; }
  done
  IFS=$OLD_IFS
)
# ENGINE = $MEDIA_SKILL_DIR + the AUDIO_ENGINE path registered in compat/ecosystem.md. Read that
# row and substitute the skill-relative path; when upstream moves it, only the map changes.
ENGINE="$MEDIA_SKILL_DIR/<AUDIO_ENGINE skill-relative path from compat/ecosystem.md>"
```

**When the delegated path is unavailable.** An empty `$MEDIA_SKILL_DIR` (skill not installed), or a
provider the user declines to authenticate, still has a music path: `scripts/search_music.py`
searches Freesound directly and needs no engine. Narration has no local acquisition fallback —
`scripts/generate_voiceover.py` keeps only `--assemble-only`, the section assembler both paths use
— so without the engine narration comes from the user (a supplied voiceover file) while music
still searches normally. The confirmation gates are unchanged either way. Say which path you took; never switch
silently. `generate_voiceover.py` has a second role that is **not** deprecated: `--assemble-only` is
the canonical timeline assembler for either path — it places each section at its exact start time,
pads to `VIDEO_DURATION`, and warns on overrun.

## Step 5.1: Generate Voiceover

**The voiceover must match the visuals.** This is non-negotiable.

Read the exact confirmed `voice` from the Creative Brief. Its prefix is binding:

- `elevenlabs:<name>:<voice-id>` → ElevenLabs with that exact ID.
- `kokoro:<voice-id>` → local Kokoro TTS (`TTS_LOCAL`) with that exact ID, even if an
  ElevenLabs key is available.

Do not choose a provider from environment-variable availability. Do not replace the confirmed voice
with a default, and do not silently fall back between providers — including inside the engine:
always pass an explicit provider, never its auto mode, which picks by whichever credential happens
to be present. An invalid value routes back to Phase 1.

### Write the aligned script

Read the main composition for each scene's exact start, end, and on-screen content, then write one
section per scene: reference what is on screen, start ~1s after the scene starts, end ~0.5s before
it ends, and speak the same stat the visual shows. **Start from the storyboard's own line** — each
frame's `voiceover` bullet is the narration the user accepted in Phase 1; fit it to the real
window rather than writing a fresh line, and say so if a beat needs rewording to fit. Two failure
modes cost real re-renders here:

- **Acronyms.** TTS runs space-separated capitals together as a phonetic blob — "H V E" renders as
  "Sage V E". Write them phonetically: `Aitch Vee Ee`, `A I`, `ay pee eye`, `sass`, `earl`. Periods
  between letters (`H. V. E.`) work in some voices and add sentence-end pauses in others. Generate
  one section and listen before doing the rest.
- **Duration is not word count.** Comma density dominates — most voices pause ~0.3–0.5s per comma,
  so 22 words with 5 commas can run 15s while the same idea in 26 commaless words takes 10s. When a
  section overruns, **drop commas before dropping words**. The assembler prints a stderr warning
  naming any section that overruns its slot; **watch stderr**, because one overrun starts every
  later section early.

For a clip scene the window is footage-derived (Phase 4), not VO-derived: fit the VO to the existing
window, never stretch the clip. **Clip-own audio is opt-in** — default `clip_audio: none` (clips
muted, only `voiceover-with-music.mp3` plays); a frame that sets `clip_audio: <volume>` gets its
sound mixed in with the VO ducked under it (Step 5.3a).

### Prepare the canonical timing assembler

Copy the assembler in and edit the **project-local copy** — editing `$SKILL_DIR`'s copy would bake
this project's config into every future project, and two projects could not run concurrently. In
`./voiceover.py`, set the `sections` list of `(start_time, text)` pairs (one per scene beat) and
`VIDEO_DURATION` to the composition length.

```bash
cp "$SKILL_DIR/scripts/generate_voiceover.py" ./voiceover.py
```

### Synthesize through the delegated engine

Write `audio_request.json` in the project directory: one `lines[]` entry per `sections` entry, same
order, **`id` = the zero-padded section index**. That id is what joins returned audio to its slot.

```json
{
  "provider": "elevenlabs",
  "voice": "<voice-id from the confirmed value>",
  "lang": "en",
  "speed": 1.0,
  "lines": [
    { "id": "00", "text": "First section text." },
    { "id": "01", "text": "Second section text." }
  ]
}
```

| Confirmed prefix | `provider` | `voice` |
|---|---|---|
| `elevenlabs:<name>:<voice-id>` | `elevenlabs` | the exact third field |
| `kokoro:<voice-id>` | `kokoro` | the exact ID after the prefix |

`lang` is load-bearing. The engine derives its internal transcription model from it, and the default
English model **translates** non-English audio instead of transcribing it — the
`TRANSCRIBE_MODEL_DEFAULT` probe in `compat/ecosystem.md`, documented upstream under `TRANSCRIBE`.
Set it to the narration's actual language every time.

```bash
# Reuse $ENGINE from Step 5.0. --only tts keeps this call to narration.
node "$ENGINE" --request ./audio_request.json --hyperframes . --out ./audio_meta.json --only tts
```

`audio_meta.json` carries `voices[]` — per line: file path, duration, word timings.

**The engine exits 0 with a missing line.** A failed synthesis is a non-fatal anomaly and the run
still succeeds, so check before assembling: `voices[]` must hold one entry per section and the
printed `anomalies` block must be empty. A short count is a provider problem — with `elevenlabs`,
usually a missing `ELEVENLABS_API_KEY` or local `elevenlabs` Python package; with `kokoro`,
non-English narration also needs `espeak-ng` system-wide (`brew install espeak-ng` /
`apt-get install espeak-ng`; `AUDIO_REQUIREMENTS` lists the rest). Fix the cause or take the
fallback; never assemble a short set.

The assembler concatenates against mono 44.1 kHz MP3 silence spacers, so transcode each line to that
shape under the name it expects:

```bash
# One per section; NN matches the request id.
ffmpeg -y -i "assets/voice/00.wav" -ac 1 -ar 44100 -c:a libmp3lame -q:a 2 vo_section_00.mp3

python3 ./voiceover.py --assemble-only    # places each section, pads to VIDEO_DURATION
```

The pad is not cosmetic: a voiceover shorter than the composition leaves the render with no audio
for the trailing frames, and it may truncate.

**When the engine is unavailable.** For a confirmed Kokoro voice, `npx hyperframes tts "<section text>" --voice
<id> --output vo_section_NN.mp3` per section, then `--assemble-only`. Kokoro IDs read
`<lang><gender>_<name>` (`af_nova` = American female "Nova"); `TTS_LOCAL` has the catalog.

### Verify timing (CRITICAL — do not skip!)

Transcribe the **assembled** `voiceover.mp3`, not the per-line files: the engine's per-line `words[]`
are relative to each line's own audio, while captions and this check need composition-absolute
times. Pass `--model` explicitly here too.

```bash
npx hyperframes transcribe voiceover.mp3 --model small.en        # known English
# ... --model small --language <iso>                             # known non-English
# ... --model small                                              # unknown language
python3 -m json.tool transcript.json | head -30
```

Standalone `whisper` remains a fallback: use `--output_format json` (SRT is a presentation format,
not a parsing target) plus `--word_timestamps True`, which writes `voiceover.json`. Sentence-level
segments produce false positives in the overlap check.

**Small-model timestamps drift ±0.5s** — the model extends word boundaries into trailing silence.
For exact per-section gaps use `silencedetect`:

```bash
ffmpeg -i voiceover.mp3 -af "silencedetect=noise=-40dB:d=0.3" -f null - 2>&1 | grep silence
```

Compare the reported `silence_start` / `silence_end` against your section timings. On ANY overlap:
drop commas first, then shorten text, then push the next section's start 1–2s later, then add "..."
pauses; regenerate and re-verify. **Repeat until ZERO overlaps. Do NOT ask the user — just fix it.**

### Captions (REQUIRED in tutorial mode)

If the content-mode is `tutorial`, on-screen VO captions are **mandatory on every footage segment**
(spec §7.2) and this **intentionally overrides** the default-optional policy in `patterns/INDEX.md`.
Silence-only segments are exempt, as are segments whose on-screen copy already renders the spoken
line verbatim (a recap beat, a step title card) — mark those `captions: carried` on the storyboard
frame so the skip is a recorded choice, not an oversight. In promo/showcase captions stay optional.

Captions are a HyperFrames caption sub-comp synced to `transcript.json` — see `media-use` →
`CAPTIONS_AUTHORING` (the GROUPS mechanism) and `TRANSCRIPT_HANDLING` for turning word timings into
cues, plus the Phase-3 caption-track recipe.

Orchestrator enforcement before render (tutorial mode) — do not advance until all hold:
1. `transcript.json` exists and passed the timing check.
2. Every footage scene with VO has a caption track, UNLESS its storyboard frame marks
   `captions: carried` or the window is silence-only. A frame left at `captions: auto` with VO and
   no track still blocks.
3. Each caption group has a hard `tl.set(... {opacity:0, visibility:"hidden"}, group.end)` kill (the
   `CAPTIONS_AUTHORING` `[caption-lint]` self-check warns otherwise).

There is no programmatic gate; a build-time rule would be upstream `hyperframes` lint work (§14).

`transcript.json` (or `voiceover.json`) stays the speech-timing source for every mode, but do not
finalize delivery captions here: music and clip audio are not mixed yet, so any audio fingerprint
would go stale immediately. Step 5.3b drafts them against the finished soundtrack.

## Step 5.2: Background Music

Follow the user's confirmed `music_strategy`; never silently fall back to another. If the chosen
strategy cannot run, return to the Phase-1 music prompt, update the Creative Brief, and reconfirm
the story — music strategy is a story field, so changing it stales Phase 1–5.

Whatever finds the candidate, the user confirms the exact track before it becomes the soundtrack —
before it is copied to `background-music.mp3`, mixed, encoded, or rendered.

### Delegated strategy

`media-use` → `BGM` produces one bed per composition from the same engine and request as the
voiceover, by one of two routes: **retrieve** it from the provider catalog (needs a HeyGen
credential — `scripts/check_requirements.sh` reports it as `heygen-credential`) or **generate** it
locally. The two carry different licensing, which is what makes the route a user choice rather than
an implementation detail, and why `BGM`'s own preflight rule is that a missing credential is never
a silent license to generate. An empty `$MEDIA_SKILL_DIR` means this strategy cannot run at all:
say so and return to the Phase-1 music prompt rather than substituting another strategy.

Ask before running the engine — recommend a route, never preselect one:

```json
{
  "questions": [{
    "question": "Which route should produce the delegated music bed?",
    "header": "Music route",
    "options": [
      { "label": "Retrieve from catalog", "description": "Needs a HeyGen credential. The bed comes from the provider catalog, under the catalog's terms." },
      { "label": "Search Freesound instead", "description": "Switches to `music_strategy: freesound` — a real recording with a human author, a stable URL and an auditable licence. Changing a confirmed brief field re-stamps phases 1-5." },
      { "label": "Change music strategy", "description": "Return to the Phase-1 music prompt; nothing is produced." }
    ],
    "multiSelect": false
  }]
}
```

Add the answered route to `audio_request.json` as an **explicit** `mode`, then run the engine for
the bed alone. Never omit `mode`: an omitted mode is the engine's auto route, which picks by
whichever credential happens to be present — the same objection as the voice provider in Step 5.1,
and here it also destroys the record, because `auto` is a request, not provenance. Send exactly one
of `query` (a mood, derived from the storytelling phase) or `prompt` (a full generation prompt), so
the request behind the track stays unambiguous.

```json
{
  "bgm": { "mode": "retrieve", "query": "calm cinematic underscore" }
}
```

```bash
# Reuse $ENGINE from Step 5.0. --only bgm keeps this call to the music bed.
node "$ENGINE" --request ./audio_request.json --hyperframes . --out ./audio_meta.json --only bgm
```

Generation runs detached, so the file is not on disk when the engine returns — run `BGM`'s
wait/status step and require a ready status before reading anything.

**No candidate is not a fallback.** A skipped retrieval (an explicit `retrieve` with no credential),
a failed generation, or an empty bgm cue means the delegated strategy produced nothing. Upstream
treats that as harmless because a missing bed never blocks *its* render; here it is a story-field
problem, not a render problem. Do not substitute Freesound and do not carry on without music —
carrying on is a silent switch to `music_strategy: none`. Report what happened and return to the
Phase-1 music prompt.

**The bytes exist before confirmation, and the gate is unchanged.** A delegated bed has no catalog
page to preview, so the candidate *is* the file the engine wrote under `assets/bgm/`. That is
candidate production — the counterpart of a Freesound search result — and it is not the soundtrack.
Nothing reaches `background-music.mp3`, a mix, an encode, or a render until the exact-track
confirmation below has passed `require audio`.

**Record the route that ran, not the route you asked for.** `audio_meta.json`'s bgm cue reports the
`mode` actually taken, the request behind it, and the file written. Build `source` from the cue; if
it differs from what you sent, the cue is what gets recorded and what you tell the user.

```bash
BGM_PATH=assets/bgm/track.mp3            # bgm cue: path (the generate route writes .wav)
BGM_MODE=retrieve                        # bgm cue: mode — the route that RAN
BGM_KEY=query                            # query, or prompt when that is what produced it
BGM_REQUEST="calm cinematic underscore"  # bgm cue: the request text, verbatim

python3 - "$BGM_PATH" "$BGM_MODE" "$BGM_KEY" "$BGM_REQUEST" <<'PY'
import hashlib, pathlib, sys, urllib.parse
path, mode, key, request = sys.argv[1:5]
digest = hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
print(f"media-use:bgm?mode={mode}&{key}={urllib.parse.quote(request, safe='')}#sha256={digest}")
PY
```

Paste that line verbatim into `final_music_track.source`. Both halves are hand-editing hazards the
validator rejects: the digest is 64 lowercase hex characters of the exact bytes (a shortened one
fails), and the request is URL-encoded so an `&` or a `#` in the mood cannot truncate the record.

Fill the other three fields honestly:

- `path` — `background-music.mp3`, the file the confirmed digest must still describe after
  materialization below.
- `title` — a human-readable name: the catalog track's title, or the mood the bed was generated
  from.
- `license` — required, and never invented. On `retrieve` the bytes came from the catalog, so the
  catalog's terms are what apply and the user confirms them with the track. On `generate` the cue
  records *that* generation ran, not which local backend ran it, and the backends do not share
  terms — ask the user which license applies before writing the field. A guessed license is a
  fabricated provenance record.

Never record a delegated track as `user-provided`: that repurposes a Phase-1 answer the user gave
before any candidate existed and erases the only machine-checked provenance the brief carries. The
engine's request-side `mode: none` is likewise not a delegated outcome — no music is
`music_strategy: none`, chosen in Phase 1.

### Freesound strategy

Freesound is a public CC-licensed audio library and the default music path. Derive mood keywords
from the storytelling phase, then search:

```bash
FREESOUND_API_KEY=... python3 "$SKILL_DIR/scripts/search_music.py" \
  "calm cinematic ambient pad" --min-duration 58
```

Each hit prints title, author, duration, licence, its **track page URL** and a high-quality MP3
preview URL usable as the soundtrack. The Creative Brief pins that exact `freesound.org` URL with
its numeric sound id — the provenance the audio gate checks — so present ranked candidates and let
the user confirm one. Prefer CC0 where the choice is close: it carries no attribution obligation
and no NonCommercial restriction, which a promo usually needs.

Searching moves; the choice never does. Never silently switch strategies — the one the user
confirmed is the one that runs. Present ranked candidates in pages of at most three tracks plus a
**More candidates** option, so no prompt exceeds four:

```json
{
  "questions": [{
    "question": "Which Freesound candidate should become the final track?",
    "header": "Music pick",
    "options": [
      { "label": "<track 1 title>", "description": "<author> - <license> - <duration> - <page URL>" },
      { "label": "<track 2 title>", "description": "<author> - <license> - <duration> - <page URL>" },
      { "label": "<track 3 title>", "description": "<author> - <license> - <duration> - <page URL>" },
      { "label": "More candidates", "description": "Show the next page; no track is selected yet." }
    ],
    "multiSelect": false
  }]
}
```

This choice is provisional until the exact-track confirmation below. Do not download or mix it yet.

### User-provided and no-music strategies

**User-provided:** ask for the exact audio path and verify it exists and is a non-empty readable
file. Collect a human-readable title, record the source as `user-provided`, and record the license
as `user-owned` or another license the user states. Do not copy or mix before exact confirmation.

**No music:** set the candidate to the exact value `none`. That is still a user-owned final choice
and needs the explicit no-music confirmation below.

### Confirm the final exact music choice

Write `final_music_track` in the Creative Brief before asking for confirmation:

- No music: `none`
- Track: compact single-line JSON with exactly `title`, `path`, `source`, and `license`.

Present the exact candidate details — not merely the strategy:

```json
{
  "questions": [{
    "question": "Confirm the final music choice: title=<title>; path=<path>; source=<source>; license=<license>?",
    "header": "Final music",
    "options": [
      { "label": "Confirm this exact track", "description": "Fingerprint this title/path/source/license and allow download, mixing, encoding, and render." },
      { "label": "Choose another track", "description": "Keep Phase 5 open; do not mix or render this candidate." }
    ],
    "multiSelect": false
  }]
}
```

For `music_strategy: none`, use this explicit no-music prompt instead:

```json
{
  "questions": [{
    "question": "Confirm no background music for the final video?",
    "header": "Final music",
    "options": [
      { "label": "Confirm no music", "description": "Record explicit none and use voiceover only." },
      { "label": "Change music strategy", "description": "Return to Phase 1; do not mix or render yet." }
    ],
    "multiSelect": false
  }]
}
```

After explicit confirmation, run:

```bash
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" confirm-audio --json
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" require audio
```

Any nonzero exit blocks all track download/copy, mixing, encoding, and rendering. If the user
changes only `final_music_track`, the audio fingerprint changes and only the Phase-5 stamp becomes
stale; Phase 1–4 remain fresh.

Only after `require audio` passes, materialize the confirmed track into `background-music.mp3`:

- **Freesound** — `curl -sL "<confirmed-preview-hq-mp3-url>" -o background-music.mp3` (previews are
  sufficient for a soundtrack; full-quality downloads need OAuth2).
- **User-provided** — `cp "<confirmed-user-path>" background-music.mp3`.
- **Delegated** — copy the cue's file, a **byte copy and never a re-encode**. Re-encoding changes
  the bytes, so the confirmed `sha256` stops describing the file at `path` and the record's only
  checkable claim is gone. The `generate` route writes a WAV; copy it under the `.mp3` name anyway
  — ffmpeg probes by content, so the extension is cosmetic here where the digest is not. Then
  re-verify:

```bash
cp assets/bgm/track.mp3 background-music.mp3     # the bgm cue's path; may be .wav
python3 -c "import hashlib,pathlib;print(hashlib.sha256(pathlib.Path('background-music.mp3').read_bytes()).hexdigest())"
# must equal the sha256 in the confirmed final_music_track.source
```

A mismatch means the confirmed record no longer describes the file that would be mixed. Re-run the
confirmation on the real bytes; never edit the brief to match a file you changed after it was
confirmed.

If the confirmed license requires attribution — a CC-BY Freesound track, or a delegated bed whose
stated terms ask for credit — write `CREDITS.md` in whichever form the strategy affords. A
Freesound track has a public page to cite:

```
Background music: "<track name>" by <username> (Freesound, <license>)
URL: <track page URL>
```

A delegated bed has none, so credit the producer and route its provenance URI already records:

```
Background music: "<title>" (<license>)
Provenance: <the confirmed final_music_track.source>
```

## Step 5.3: Audio Mixing

Do not enter this step unless `validate_brief.py ... require audio` passed for the current exact
track or explicit `none`.

### Normalize voiceover
```bash
ffmpeg -y -i voiceover.mp3 -af "loudnorm=I=-16:TP=-1.5:LRA=11" voiceover-normalized.mp3
```

### Mix music (if using background music)

The music is a **subtle bed under the voice**, not a soundtrack — *felt more than heard* while words
play, noticeable only in its absence. Three things make it behave: normalize the music to a **known
base level** so the balance does not depend on how hot the source file is, **EQ space** around the
voice, and **sidechain-duck the music under the voiceover** so it dips while words play and breathes
back in the gaps.

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

Each stage, and why it is what it is — the numbers are starting points, tune by ear:

- **`loudnorm=I=-30` (music base level)** — puts the bed ~14 LU under the -16 LUFS voice so the mix
  no longer depends on the track's mastered level. It replaces a fixed `volume=0.22`, which scaled an
  *un-normalized* download and gave unpredictable loudness. Bed vanishing under speech: raise toward
  -28/-26. Bed competing: lower toward -32.
- **`highpass=f=100` + `equalizer=f=2500…g=-3` (music EQ)** — strips sub-100 Hz rumble (product demos
  rarely need deep bass) and dips ~3 dB around 2.5 kHz to carve room for speech.
- **`sidechaincompress` keyed by the voice (`[key]`)** — the core move: the music ducks ~3–6 dB
  whenever the VO plays (attack 150 ms, release 900 ms = smooth, not pumping) and returns in pauses.
  If it pumps, lower `ratio` or lengthen `release`; if the first words are masked, drop `attack`
  toward 100. Step 5.3a applies the same filter with the roles swapped.
- **`alimiter=limit=0.89` (master ≈ -1 dBFS ceiling)** — a peak limiter, *not* a loudness normalizer.
  The VO already sits at -16 LUFS and dominates, so a -30 LUFS bed nudges integrated loudness only
  ~+0.2 LU and the mix lands ≈-15.8 LUFS, in-spec. **Do not add a dynamic `loudnorm` master here.**
  It rides gain, boosting the bed in the intro, the outro, and every VO pause (chasing -16 when only
  quiet music is present), which *undoes the duck and fights the fades* — verified: with a dynamic
  master the music measures **louder** under speech than in the gaps. Correct loudness with a
  **constant** gain after validation instead.
- **`aformat=…:channel_layouts=stereo` on both legs (not `aresample`)** — `sidechaincompress`
  requires its inputs to share sample format, rate, **and channel layout**. Cloud TTS and the local
  Kokoro path often emit a **mono** voiceover, and a mono key against a stereo bed aborts the filter
  with `Error reinitializing filters! Failed to inject frame into filter network`. `aformat` pins
  both legs to stereo/44.1k/fltp — a superset of the old `aresample=44100`, which fixed only the
  rate. The music-branch `loudnorm` can also switch internally to 192 kHz, so pinning the rate keeps
  `amix` and the MP3 encoder happy too.
- **`amix … normalize=0` (critical)** — the default `normalize=1` divides each input by the input
  count, a hidden -6 dB per track that would gut the already-quiet bed.

### No-music path (voiceover only)

If the user chose "No music", **you still need `voiceover-with-music.mp3`** — the root composition's
`<audio>` element references that filename, and without it the render has no audio.

```bash
cp voiceover-normalized.mp3 voiceover-with-music.mp3
```

### Validate the mix

Integrated loudness should land around -16 LUFS with true peak at or under -1 dBTP. `alimiter` caps
*sample* peaks, not inter-sample peaks, so -1 dBTP is a target to **verify**: if `ebur128` reports
above it, lower the ceiling (e.g. `alimiter=limit=0.79`, ≈ -2 dBFS) and re-render.

```bash
ffmpeg -hide_banner -i voiceover-with-music.mp3 -af ebur128=peak=true -f null - 2>&1 | tail -16
```

If loudness lands outside -16 ±1.5 LUFS (a sparse, pause-heavy VO drags it low), correct with a
**constant** gain — `volume=<delta>dB` shifts the whole mix uniformly and so preserves the duck and
the fades, unlike a dynamic `loudnorm` — then re-cap the peak:

```bash
ffmpeg -y -i voiceover-with-music.mp3 -af "volume=1.5dB,alimiter=limit=0.89" \
  -c:a libmp3lame -q:a 2 fixed.mp3
mv fixed.mp3 voiceover-with-music.mp3
```

### Optional: sound-effect cues

Skip this unless a storyboard beat asks for an effect or the user requests one. Never add effects on
your own initiative; a missing effect never blocks a render.

`media-use` → `SFX` resolves named cues from the same engine and request: attach names to the line
whose scene carries them (`"sfx": ["whoosh", "ui click"]`) and run with `--only sfx`. It retrieves
from the provider catalog when credentialed, otherwise matches an offline bundled library whose
manifest carries each file's duration — so a cue's length is known without playing it, which is what
lets a long riser *land* on a beat. `audio_meta.sfx[]` records each cue's `file`, `duration_s`, and a
`volume` that already sits under voice and music. Placement is yours: every cue is recorded at
offset 0.

```bash
CUE=assets/sfx/whoosh.mp3       # audio_meta.sfx[].file
AT_S=18.5                       # scene data-start, copied VERBATIM from index.html — SECONDS.
                                # data-start is always seconds; adelay wants milliseconds, so the
                                # conversion below is the only place the two units meet. Writing a
                                # seconds value into a millisecond field places the cue ~1000x early
                                # and nothing downstream can detect it.
AT_MS=$(awk -v s="$AT_S" 'BEGIN{printf "%d", s*1000}')
SFX_VOL=0.35                    # audio_meta.sfx[].volume

ffmpeg -y -i voiceover-with-music.mp3 -i "$CUE" \
  -filter_complex "
    [0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[base];
    [1:a]volume=${SFX_VOL},adelay=${AT_MS}|${AT_MS},
         aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[fx];
    [base][fx]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,
              alimiter=limit=0.89[out]" \
  -map "[out]" -c:a libmp3lame -q:a 2 mixed.mp3
mv mixed.mp3 voiceover-with-music.mp3
```

`duration=first` preserves the master length; re-run `ebur128` after the last cue. Any effect audible
in the final soundtrack is a meaningful sound for caption purposes — Step 5.3b reviews it.

## Step 5.3a: Clip-own audio (opt-in)

Run only when a storyboard frame sets `clip_audio: <volume>` (not `none`). One reviewed script does
the whole mix — trim → `speed` → normalize → place, then the Step 5.2 sidechain with the roles
swapped (voice+music ducked under the clip) — and it replaces the canonical soundtrack atomically.

**Every time value is in seconds.** Copy the scene's `data-start` out of `index.html` verbatim into
`--at`; the script converts to the milliseconds ffmpeg wants.

```bash
# Reuse $SKILL_DIR resolved in Step 5.0.
python3 "$SKILL_DIR/scripts/mix_clip_audio.py" public/clips/scene-03-demo.mp4 \
  --soundtrack voiceover-with-music.mp3 \
  --clip-in 2.0 --clip-out 8.0 --speed 1.0 \
  --at 18.5 --volume 0.6
```

- the clip path — the frame's `clip` bullet
- `--clip-in` / `--clip-out` — the frame's `clip_in` / `clip_out` bullets. `--clip-in` MUST equal
  the scene `<video>`'s `data-media-start`, or the audio desyncs from the picture.
- `--speed` — the frame's `speed` bullet; the script chains the `atempo` stages that factor needs.
- `--at` — the scene's `data-start` **in seconds** (`18.5` is 18.5s, not 18.5ms).
- `--volume` — the `clip_audio` value.

It refuses, before encoding anything, a clip that would not fit inside the soundtrack (the real
failure: audio truncated at the end of the film), a window past the end of the clip, a clip that
carries no audio stream at all, and any out-of-range argument. After mixing it re-checks the
soundtrack length and that the placed window actually changed. Every refusal exits non-zero and
leaves `voiceover-with-music.mp3` byte-identical — fix what the message names and re-run.

### A second run for the same clip is refused

Mixing one clip in twice is audible and afterwards **undetectable**: a mix cannot be subtracted, and
no measurement distinguishes "this clip at 0.6" from "this clip at 0.6 plus this clip at 0.4". So
each published mix is recorded beside the soundtrack in `voiceover-with-music.mp3.clip-mix.json` —
the soundtrack's SHA-256 and duration, plus one entry per mix (the resolved clip path, its
`--clip-in`/`--clip-out`, `--speed`, `--volume`, `--at`, and the play duration those imply). The mix
and its record publish together or not at all: a record that cannot be written rolls the soundtrack
back, and a failed run publishes neither.

Three states are then refused, each before any encoding, so the soundtrack stays byte-identical:

1. **This clip is already placed there.** A recorded pass of the *same* clip whose placed window
   overlaps the requested one. Overlap, not an exact `--at` match — a mistyped retake (`18.5` →
   `18.05`) is the same double mix — and it cannot false-positive, because one scene cannot play at
   two overlapping points in the film.
2. **The record no longer describes the soundtrack on disk.** Its SHA-256 has moved — a Step 5.2
   rebuild, the sound-effect cues above, a constant `volume=<delta>dB` loudness pass — so nothing
   can tell whether the recorded clip audio is still inside it.
3. **The record is unusable** — unreadable JSON, an unexpected schema version, or an entry with no
   usable clip path or placement.

The guard never resets itself, and the message names the ways forward rather than picking one.
Resolve a refusal by what actually happened:

- **To change a clip's volume or window** — rebuild the soundtrack from Step 5.2 (voiceover +
  music, before any clip audio) and mix every opt-in clip into it again. There is no re-mix in
  place; the first pass is already baked in.
- **If you rebuilt the soundtrack yourself** — delete `voiceover-with-music.mp3.clip-mix.json` and
  re-run. Deleting it is safe: nothing but this guard reads it.
- **`--force`** overrides those three refusals and **nothing else** — never the fit, window,
  argument, or no-op checks. It layers a second copy of audio that no later step can detect or
  subtract, so pass it only when that is deliberately what you want: on state 2, when you edited the
  soundtrack yourself and the recorded clip audio is still inside (earlier entries are kept), or on
  state 3, where the sidecar is rewritten from this pass alone and every earlier entry is lost.
  Each prints a `Note:` on stderr saying exactly what it accepted. It is not the way past a refusal
  you have not read.

Run once per opt-in clip — each pass rewrites the canonical file Step 5.4 reads, and a second pass
over the same clip and placement is refused rather than silently layered. Then re-run the `ebur128`
check. Expected: ≈ -16 LUFS, true peak at or under -1 dBTP, and the ducked window audibly quieter
under the clip's sound.

## Step 5.3b: Reviewed Closed-Caption Delivery (all modes)

Run this after **all** music, effects, and opt-in clip audio have been mixed into the canonical
`voiceover-with-music.mp3`. WCAG captions represent the information in the complete soundtrack, not
speech alone: correct every spoken line, identify a speaker when the identity is not obvious, and
include meaningful music/sound-effect cues. Mandatory in promo, showcase, and tutorial modes;
burned-in tutorial captions remain a separate in-frame layer.

### 1. Create an audio-bound review draft

```bash
# Reuse $SKILL_DIR resolved in Step 5.0.
python3 "$SKILL_DIR/scripts/caption_gen.py" draft \
  --audio voiceover-with-music.mp3 \
  --manifest captions-review.json \
  --srt voiceover.srt \
  --vtt voiceover.vtt
```

This writes backward-compatible ASR drafts plus `captions-review.json`, which records the final
soundtrack's SHA-256 and duration, starts with `reviewed: false`, and leaves `speech_review`,
`speaker_review`, and `sound_review` pending. It is the human-review source; `voiceover.srt`/`.vtt`
are never final captions. If it already exists, `draft` fails instead of overwriting review work:
when the audio changed, preserve the prior manifest as `captions-review.previous.json`, and use
`--force` only after the user explicitly approves replacing the canonical one.

### 2. Review the complete soundtrack

Compare every speech cue to the approved narration and show the user the full timestamped cue list.
Correct ASR words, punctuation, timing, and line breaks. Each manifest cue has:

```json
{
  "start": 0.5,
  "end": 2.8,
  "text": "The spoken line.",
  "speaker": "",
  "sound": "Upbeat electronic music begins"
}
```

`speaker` is optional when one narrator is obvious. `sound` is a meaningful non-speech cue rendered
as `[Upbeat electronic music begins]`; it may share a cue with speech so simultaneous narration and
sound stay in one two-line caption, and standalone sound-only cues fit between speech cues. Review
effects and clip-own audio as well as music. Present all three review decisions:

```json
{
  "questions": [
    {
      "question": "Was every spoken caption corrected against the final soundtrack?",
      "header": "Speech",
      "options": [
        { "label": "Speech verified", "description": "All words, punctuation, timing, and line breaks match the final soundtrack." },
        { "label": "Needs edits", "description": "Keep captions unreviewed and correct the spoken cues." }
      ],
      "multiSelect": false
    },
    {
      "question": "How was speaker identity handled in the complete caption review?",
      "header": "Speakers",
      "options": [
        { "label": "Single obvious speaker", "description": "One narrator is unambiguous; speaker labels are unnecessary." },
        { "label": "Labels included", "description": "Required speaker labels are present in the reviewed cues." },
        { "label": "Needs edits", "description": "Keep captions unreviewed and revise speaker coverage." }
      ],
      "multiSelect": false
    },
    {
      "question": "How was meaningful music and sound handled in the complete caption review?",
      "header": "Sound cues",
      "options": [
        { "label": "Cues included", "description": "Meaningful music/SFX cues are present, including clip-own audio." },
        { "label": "None meaningful", "description": "The final soundtrack has no non-speech information needed to understand it." },
        { "label": "Needs edits", "description": "Keep captions unreviewed and revise sound coverage." }
      ],
      "multiSelect": false
    }
  ]
}
```

Map the accepted answers to `speech_review: verified`,
`speaker_review: single-obvious | included`, and `sound_review: none-meaningful | included`. Any
**Needs edits** response leaves `reviewed: false`. After the user has read the complete cue list,
ask for final approval:

```json
{
  "questions": [{
    "question": "Approve these complete captions against the final soundtrack?",
    "header": "Captions",
    "options": [
      { "label": "Approve captions", "description": "Mark this exact cue list human-reviewed and create final sidecars." },
      { "label": "Needs changes", "description": "Keep reviewed=false and revise the named cues." }
    ],
    "multiSelect": false
  }]
}
```

Only after the user's **Approve captions** answer, run the approval command:

```bash
python3 "$SKILL_DIR/scripts/caption_gen.py" approve \
  --audio voiceover-with-music.mp3 \
  --manifest captions-review.json
```

It validates the three review decisions, sets `reviewed: true`, and fingerprints the exact audio,
language, cue list, and decisions. Any later cue or decision edit invalidates approval and requires
showing the revised list again. Never run `approve` from the narration script or ASR output without
that explicit user answer.

### 3. Finalize and validate delivery sidecars

```bash
python3 "$SKILL_DIR/scripts/caption_gen.py" finalize \
  --audio voiceover-with-music.mp3 \
  --manifest captions-review.json \
  --srt out/final.srt \
  --vtt out/final.vtt \
  --state .hve/captions-state.json

python3 "$SKILL_DIR/scripts/caption_gen.py" validate \
  --audio voiceover-with-music.mp3 \
  --manifest captions-review.json \
  --srt out/final.srt \
  --vtt out/final.vtt \
  --state .hve/captions-state.json
```

`finalize` rejects unapproved or changed review content, missing speech/speaker/sound decisions,
stale audio, overlapping or out-of-range cues, more than two lines, lines over 42 characters, and
reading speed above 25 characters/second; it stages the sidecars and deterministic state before
publication and restores the prior delivery set if any replacement fails. `validate` rechecks the
state schema and regenerates expected state and sidecar content in memory; any soundtrack, manifest,
state, or output change routes back to this step.

## Step 5.4: Final Render

`index.html` already references `voiceover-with-music.mp3` via an `<audio>` clip on track 0 (Phase
4). One render command produces the final MP4 with embedded audio — no separate mux step.

Re-run the composition gate first (`CHECK_GATE`), in case a caption sub-composition overlaps a
visual element.

**If any scene was re-timed to the voiceover, re-run the seam gate too.** Audio is the clock: a
scene whose duration moved to fit real word timings has shifted its own cut, so the seam vectors
Phase 4 stamped and verified no longer describe the boundary. `SEAM_LAW` is explicit that editing a
scene's first or last ~1s re-opens its seam, and a VO regeneration re-opens every seam it touches.
Resolve `SEAM_VERIFIER` the same way Phase 4 does (Step 4.5) and re-run it; if the tool is
unavailable, say plainly that the seams went unverified rather than implying the gate passed.
Skip only when no scene duration changed in this phase.

```bash
npx hyperframes check . --samples 10      # reruns lint (flags "audio element has no id")

mkdir -p out
npx hyperframes render . --output out/final.mp4

ffprobe -v error -select_streams a -show_entries stream=codec_name,duration \
  -of default=nw=1 out/final.mp4
```

Expected: `codec_name=aac` and duration ≈ composition length — the end-to-end proof the (ducked)
clip audio reached `out/final.mp4`, since footage is muted in the composition. HyperFrames renders
via headless Chromium and muxes in the same pass; output is H.264 + AAC at the canvas size chosen in
Phase 1.

If you need a silent video first (rarely), render without the audio clip wired and mux after:

```bash
npx hyperframes render . --output out/video-silent.mp4
ffmpeg -y -i out/video-silent.mp4 -i voiceover-with-music.mp3 \
  -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest out/final.mp4
```

Finally, confirm the delivered captions still match the shipped soundtrack:

```bash
python3 "$SKILL_DIR/scripts/caption_gen.py" validate \
  --audio voiceover-with-music.mp3 \
  --manifest captions-review.json \
  --srt out/final.srt --vtt out/final.vtt --state .hve/captions-state.json
```

### Troubleshooting render failures

**Environment failures are `doctor`'s job, not this file's** (ADR-003). If the render hangs, errors,
or produces unexpected output, run it first — it diagnoses Node, FFmpeg, the Chromium binary, and
the capture path in use, and prints the fix for whatever is broken. `DOCTOR` documents its coverage;
do not build a parallel diagnostic here, and never branch on a CLI version.

```bash
npx hyperframes doctor
```

Two failures belong to the *composition*, so `doctor` passes while the output is still wrong:

- **Render succeeds but the output is silent** — the `<audio>` element in `index.html` has no `id`.
  Without one the audio is silently dropped during render; `lint` (inside `check`) flags it.
- **Scenes look blank during transitions** — adjacent scenes must OVERLAP during the crossfade
  window. Clip windows and the `data-track-index` that lets two scenes overlap are
  `hyperframes-core` → `TRACKS_AND_CLIPS`.

If capture itself dies on the host (sandboxed containers, WSL2), re-run through the containerized
path with `--docker`; on low-RAM hosts the CLI auto-enables low-memory mode, which forces screenshot
capture — add `--no-low-memory-mode` to switch back. Output is identical either way.

## Output

- `out/final.mp4` — Final video with voiceover and music
- `out/final.srt` / `out/final.vtt` — Reviewed, toggleable caption sidecars beside the MP4
- `voiceover-with-music.mp3` — Final soundtrack; **the file `index.html`'s `<audio src>` references
  — render is silent without it**
- `audio_request.json` / `audio_meta.json` + `assets/voice/`, `assets/bgm/`, `assets/sfx/` —
  Delegated engine request, result (durations, per-line word timings, music and effect cues), and
  the source audio it wrote
- `vo_section_NN.mp3` → `voiceover.mp3` → `voiceover-normalized.mp3` — Per-section narration, the
  assembled + `VIDEO_DURATION`-padded voiceover, and its normalized form (input to the mix)
- `background-music.mp3` — The confirmed music track (if Step 5.2 ran)
- `transcript.json` — Composition-absolute word timings from `npx hyperframes transcribe`, or
  `voiceover.json` from the standalone-whisper fallback
- `voiceover.srt` / `voiceover.vtt` — Regenerable ASR drafts; never ship as reviewed captions
- `captions-review.json` + `.hve/captions-state.json` — Human-reviewed cue source bound to the final
  audio, and the fingerprints resume validation checks

## Checkpoint

After the confirmed audio choice is mixed (or the confirmed no-music path is prepared), reviewed
caption validation passes against the final soundtrack, the render passes verification, and the user
accepts the result, stamp Phase 5:

```bash
python3 "$SKILL_DIR/scripts/validate_brief.py" \
  --project-dir "$PROJECT_DIR" stamp phase-5
```

A nonzero exit means the exact track or an earlier story field changed; do not report completion
until the stale phase is rerun and stamped.

Surface the **absolute** output paths (issue #21) so the user never has to hunt for the file:

```bash
FINAL="$(cd out && pwd)/final.mp4"     # absolute paths to the render and its sidecars
echo "Final video:    $FINAL"
echo "Captions:       ${FINAL%.mp4}.srt | ${FINAL%.mp4}.vtt"
echo "Project folder: $(pwd)"
```

> "Video rendered! 🎬
>
> Final video: `<absolute path to out/final.mp4>`
> Captions: `<absolute path to out/final.srt>` | `<absolute path to out/final.vtt>`
> Project folder: `<absolute path to the project dir>`
>
> Duration: [X]s | Resolution: [W]×[H] ([aspect]) | Audio: voiceover + music
>
> Watch it and let me know if you'd like any adjustments."

**Offer to open the result — consent-gated, never auto-launch.** Ask (native prompt) whether to open
the project folder or the file. Only after the user says yes, run the platform's own opener
**directly** on the project dir — `open` (macOS), `explorer` (Windows), `xdg-open` (Linux),
`wslview` (WSL), or `code` for VS Code — passing the path as an argv element, never through `eval`,
`sh -c`, or any shell interpolation. Recompute these machine-specific absolute paths from the CWD
each run; never persist them into a committed artifact.
