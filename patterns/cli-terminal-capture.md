# CLI / Terminal Capture — asciinema + agg

How to produce a **professional terminal clip** for a hve-video-director CLI scene
when the storyboard calls for *real* command output (a deploy log, a build
spinner, an interactive prompt). For the dependency-free fallback, see the
"authored terminal" path documented inline in
`workflows/phase-2-capture.md` (the `templates/scene-terminal.html` archetype).

The chrome-devtools MCP cannot screencast a terminal — there is no DOM page.
For real terminal motion we record with [asciinema](https://github.com/asciinema/asciinema),
post-process the cast, then render it to MP4 with
[agg](https://github.com/asciinema/agg). The clip is then composed via the
Layer-A `templates/scene-terminal-clip.html` archetype, which wraps the video
in a macOS-style window for brand parity with screenshot mockups.

## When to use this path

Pick the **asciinema path** (skill-driven; see "Recording mode — autonomous"
below) when:

- The motion is the point (a streaming build log, a progress bar, animated
  spinners, a TUI like `htop`/`lazygit`, a real `npm install` cascade).
- The duration is short (≤ 8s of meaningful action) and you want the *real*
  cadence, not a synthetic one.
- The command is **non-interactive** — it runs to completion (or to a
  timeout) without needing keyboard input. asciinema's `--command` mode
  lets the skill execute it autonomously via its Bash tool; the user
  never touches the keyboard.

Pick the **authored-terminal path** (`templates/scene-terminal.html`) when:

- Output is short (≤ 5 lines) and a deterministic typewriter reveal reads
  cleaner than real-time scroll.
- The command takes long enough to be boring without heavy editing.
- You don't have `asciinema` + `agg` installed and don't want a new dep.
- The command genuinely needs a human at the keyboard (interactive prompts,
  mouse-driven TUIs).
- The environment is sensitive in ways `env -i` can't fully sanitize.

## Feature detection (already wired)

`SKILL.md` Prerequisites and `workflows/phase-2-capture.md` Capture-source
detection both probe `command -v asciinema`, `command -v agg`, and
`command -v timeout` (GNU coreutils — absent on stock macOS). If any is
missing the workflow degrades to the authored-terminal path and tells the
user. Do not hard-fail.

## Install

```bash
# macOS — coreutils provides GNU `timeout` (stock macOS has none; verified:
# brew's coreutils installs it unprefixed)
brew install asciinema agg coreutils

# Debian / Ubuntu
sudo apt install asciinema
cargo install --git https://github.com/asciinema/agg   # agg has no apt package

# Arch
sudo pacman -S asciinema
yay -S agg-bin

# Any OS (pip fallback for asciinema)
pipx install asciinema
```

Verify:

```bash
asciinema --version    # 2.x (Python) or 3.x (Rust) — both fine; size is set via
                       # COLUMNS/LINES below, not `rec --cols/--rows` (3.x-only, errors on 2.x)
agg --version          # 1.4+
```

## Recording mode — **autonomous (skill-driven)**

The skill executes `asciinema` itself via its Bash tool. **The user does
not open a terminal or run anything by hand.** This works because
`asciinema rec --command "<cmd>"` is non-interactive: asciinema allocates
its own PTY, runs the command headless, captures stdout/stderr with
timing, and exits when the command exits.

Three things make autonomous recording reliable:

- **`--command`** — non-interactive single-shot mode. No stdin needed.
- **`timeout Ns`** — bounds runaway / non-terminating commands (`htop`,
  dev servers). Exit code 124 is non-fatal; the partial cast up to the
  timeout is still valid and renderable.
- **`env -i …`** — scrubs the parent environment so stray tokens, custom
  `PS1`, oh-my-zsh git status, virtualenv markers, etc. don't leak into
  the recording's PTY.

The single autonomous sequence (also reproduced in
`workflows/phase-2-capture.md` — edit BOTH together):

```bash
# Record — non-interactive, PTY-isolated, timeout-bounded.
# LANG must survive the env scrub — asciinema 2.x (Python) aborts without a
# UTF-8 locale ("asciinema needs a UTF-8 native locale to run").
# Terminal size is set via COLUMNS/LINES (portable across asciinema 2.x Python and
# 3.x Rust; `rec --cols/--rows` exist only on 3.x and error out on 2.x). COLUMNS=175
# keeps wide output (kubectl get, docker ps) from wrapping — size it to the scene.
# RECORD_TIMEOUT = storyboard `Record timeout` (default scene_duration + 2s).
RECORD_TIMEOUT="${RECORD_TIMEOUT:-60}"
WORK_DIR=$(mktemp -d "${TMPDIR:-/tmp}/hve-terminal-clip.XXXXXX")
CAST_TMP="$WORK_DIR/scene.cast"
GIF_TMP="$WORK_DIR/scene.gif"
MP4_TMP="$WORK_DIR/scene.mp4"
CAST_OUT="public/clips/scene-{NN}-{slug}.cast"
MP4_OUT="public/clips/scene-{NN}-{slug}.mp4"

# Preserve any previous result outside the accepted destination so a failed or
# interrupted attempt cannot be mistaken for a fresh terminal clip.
mkdir -p public/clips
[ ! -e "$CAST_OUT" ] || mv "$CAST_OUT" "$WORK_DIR/previous.cast" ||
  { echo "cannot quarantine previous cast — aborting terminal capture" >&2; exit 1; }
[ ! -e "$MP4_OUT" ] || mv "$MP4_OUT" "$WORK_DIR/previous.mp4" ||
  { echo "cannot quarantine previous MP4 — aborting terminal capture" >&2; exit 1; }

record_ok=
if timeout "${RECORD_TIMEOUT}s" env -i HOME="$HOME" PATH="$PATH" SHELL=/bin/bash TERM=xterm-256color \
  LANG="${LANG:-C.UTF-8}" COLUMNS=175 LINES=32 PS1='$ ' \
  asciinema rec --idle-time-limit 1.5 \
    --command "<cmd-from-storyboard>" \
    "$CAST_TMP"; then
  record_ok=1
else
  status=$?
  [ "$status" -eq 124 ] && [ -s "$CAST_TMP" ] && record_ok=1
fi

# Render — agg emits a GIF (it ignores the output extension), so render to a TEMP
# .gif (multi-MB intermediate — keep it out of public/clips/). Never pass
# --cols/--rows: agg reads the size from the cast header (the COLUMNS/LINES
# recorded above); a mismatch wraps/letterboxes the output.
if [ -n "$record_ok" ] && [ -s "$CAST_TMP" ] &&
  agg --font-size 28 --theme monokai --fps-cap 30 "$CAST_TMP" "$GIF_TMP" &&
  ffmpeg -y -i "$GIF_TMP" \
    -vf "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2" \
    -c:v libx264 -profile:v high -pix_fmt yuv420p -movflags +faststart \
    "$MP4_TMP" &&
  [ -s "$MP4_TMP" ] &&
  ffprobe -v error -select_streams v:0 \
    -show_entries stream=nb_frames,avg_frame_rate -of default=noprint_wrappers=1 \
    "$MP4_TMP"; then
  mv "$CAST_TMP" "$CAST_OUT"
  mv "$MP4_TMP" "$MP4_OUT"
  clip_ready=1
else
  clip_ready=
  echo "terminal clip failed — switching this scene to the authored-terminal path" >&2
  # Stop here, rewrite Capture: terminal, and author the deterministic terminal
  # scene. Never continue with stale output from a previous attempt.
fi
```

Only author `templates/scene-terminal-clip.html` when `clip_ready=1`. Otherwise rewrite the
storyboard scene to `Capture: terminal` and author `templates/scene-terminal.html` from the real
command output. The fallback is the accepted result, not a successful clip attempt.

The storyboard carries the inputs the skill needs:

```
Capture: terminal-clip
Command: shipfast deploy --env staging
Record timeout: 8s          # scene duration + ~2s
```

Why `--idle-time-limit 1.5` matters: an unmodified `npm install` cast is
~90% motionless waiting frames. With `--idle-time-limit` set, every pause
longer than 1.5s collapses to 1.5s, giving a clip that *feels* real-time
without dragging.

### Edge cases the autonomous path handles

- **Long-running / non-terminating commands.** `timeout` bounds them. Set
  the storyboard's `Record timeout` to `scene_duration + ~2s` so the
  recorded footage matches the slot.
- **Commands needing piped input.** Wrap in `bash -c`:
  ```bash
  --command "bash -c 'printf \"y\\n\" | npm uninstall foo'"
  ```
- **Commands needing secrets** (e.g. an API key). Inject *only* the needed
  variable into the scrubbed env:
  ```bash
  env -i HOME=$HOME PATH=$PATH SHELL=/bin/bash LANG="${LANG:-C.UTF-8}" PS1='$ ' \
      DEPLOY_TOKEN="$DEPLOY_TOKEN" \
    asciinema rec ...
  ```
  The token is in the PTY's process env but **never echoed to the
  recording** — asciinema captures stdout, not env dumps.
- **TTY allocation failure** (rare; some sandboxes). If `asciinema rec`
  errors with *"could not allocate pty"*, fall back to `script` — note the
  two incompatible syntaxes:
  ```bash
  script -qc "<cmd>" /dev/null      # GNU/Linux (util-linux)
  script -q /dev/null <cmd>         # BSD/macOS — has no -c flag
  ```
  Convert by prepending an asciinema v2 header line
  `{"version":2,"width":175,"height":32}` and timing-stamping each line;
  if that's too brittle for the scene, fall back to the authored-terminal
  path.
- **Commands genuinely needing a human** (interactive prompts, mouse-driven
  TUIs). Out of scope for autonomous mode — switch the storyboard's
  `Capture:` to `terminal` (authored-typewriter path) or `supplied`
  (user provides their own MP4).

## Recording mode — interactive (sub-case)

For multi-step demos where you *want* a human typing for cadence and
authenticity, the same tools work as a hand-recorded session:

```bash
COLUMNS=175 LINES=32 asciinema rec --idle-time-limit 1.5 cast.cast
# ... type commands ...
exit
```

The pre-flight checklist (clean shell, brand prompt, sized window, dark
theme, deliberate pacing) applies. The skill does not drive this mode —
it's a user-side path for scenes where deterministic `--command` mode
won't capture the intent. Drop the resulting cast into the storyboard's
expected location (`public/clips/scene-{NN}-{slug}.cast`) and the skill
will pick up from the render step.

## Editing the cast (optional, recommended)

The `.cast` file is newline-delimited JSON: the first line is the header,
each subsequent line is `[time_seconds, "o", "text"]`. You can hand-edit it.

Common edits:

- **Trim a slow tail.** Open in your editor, delete trailing lines whose
  `time` exceeds the desired duration. Update no other field.
- **Speed up a section.** Multiply the `time` field of a contiguous block by
  `0.5` (2× faster). Keep monotonic ordering — don't let times go backwards.
- **Redact a string.** Find-replace the literal token in the `text` field.
  Quote handling: the value is a JSON string, so backslash-escape `"` and
  control bytes (asciinema already does this on capture).

Re-validate by playing it back: `asciinema play cast.cast`.

## Render to MP4

`agg` is a **GIF generator** — it writes a GIF regardless of the output filename,
so naming the output `.mp4` just produces a GIF inside an `.mp4` name (wrong
container; seek-driven players and `<video>` sync choke on it). There is **one**
reliable path: render to `.gif`, then normalize to constant-fps H.264 with ffmpeg.

Same render + normalize steps as the autonomous sequence above (keep the two
in sync — the flags must not drift):

```bash
# 1. Render the cast to a TEMP GIF. No --cols/--rows — agg reads the size from
#    the cast header; a mismatch wraps/letterboxes.
agg --font-size 28 --theme monokai --fps-cap 30 \
    cast.cast "${TMPDIR:-/tmp}/scene-{NN}-{slug}.gif"

# 2. Normalize to constant-fps MP4 — REQUIRED, not just for odd widths.
ffmpeg -y -i "${TMPDIR:-/tmp}/scene-{NN}-{slug}.gif" \
  -vf "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2" \
  -c:v libx264 -profile:v high -pix_fmt yuv420p -movflags +faststart \
  public/clips/scene-{NN}-{slug}.mp4
```

Why step 2 is mandatory: `agg` emits **change-only frames**, so a short clip
(a 2-line deploy) can be 2–4 frames total at a variable sub-1fps rate, and a GIF
decodes to `yuv444p`. Constant-fps players and HyperFrames' seek-driven `<video>`
sync mishandle such sparse VFR, and `yuv444p` isn't broadly supported. `fps=30`
rebuilds a constant 30fps timeline (a ~5s clip → ~150 frames), `pix_fmt yuv420p`
fixes the colorspace, and `scale=trunc(...)*2` forces even dimensions for H.264.
`agg --fps-cap` is a *cap*, not a floor, so it does not produce constant fps.

### Fill a longer scene window (freeze-extend)

A terminal reveal often finishes in ~4s while the narration over it runs ~20s.
Clone the last frame to fill the slot instead of looping or freezing a dead
`<video>` — swap the step-2 filter for `tpad`:

```bash
ffmpeg -y -i public/clips/scene-{NN}-{slug}.gif \
  -vf "tpad=stop_mode=clone:stop_duration=N,fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2" \
  -c:v libx264 -profile:v high -pix_fmt yuv420p -movflags +faststart \
  public/clips/scene-{NN}-{slug}.mp4
```

`N = scene_duration − clip_duration` (e.g. a 5s clip + `stop_duration=8` → 13s,
constant 30fps).

### Theme palette → brand parity

| `--theme` | Vibe | Pairs with palette |
|---|---|---|
| `monokai` | Warm dev-default | `bold-energetic`, `warm-editorial` |
| `solarized-dark` | Calm corporate | `clean-corporate`, `dark-premium` |
| `dracula` | High-contrast purple | `neon-electric`, `jewel-rich` |
| `nord` | Cool Nordic | `clean-corporate`, `nature-earth` |
| `gruvbox-dark` | Retro warm | `warm-editorial` |
| `github-dark` | Neutral grey | Most palettes |

For a custom theme pass `--theme bg,fg,palette` with explicit hex
(e.g. `--theme 0a0a0a,eaeaea,...`). Match the scene's `background` so the
clip blends seamlessly with the wrapper.

## Quality gate (in addition to the Phase 2 footage gate)

Before accepting a terminal clip:

- **Font size ≥ 24px effective** in the rendered frame. Agg's default is
  small; bump `--font-size` to 28–32 for 1920×1080 compositions.
- **No prompt cruft.** No `(env)` markers, no git branch names from
  oh-my-zsh, no virtualenv indicators (unless they're the story).
- **No long idle gaps.** If the clip has > 1s of motionless frames,
  re-render with a lower `--idle-time-limit`.
- **Aspect.** Agg renders 144×32 → roughly 16:5. The clip wrapper
  (`scene-terminal-clip.html`) crops/letterboxes inside its window chrome,
  but if your composition is 9:16 prefer 80×40 cols and a larger font.
- **Audio.** Cast files have no audio. The clip is muted by design — the
  voiceover narrates over it.

## Wiring into a scene

After the MP4 is at `public/clips/scene-{NN}-{slug}.mp4`:

1. Author the scene from `templates/scene-terminal-clip.html` into
   `scenes/{NN}-terminal-clip.html`. Replace `NN` and `slug` and adjust the
   window title (`zsh`, `npm`, `deploy`) to match the command.
2. The wrapper's `data-composition-id`, animation, and clip-frame chrome are
   pre-wired — never animate the `<video>` itself, animate the `.term-frame`
   wrapper per the *no img-dimension tween* DON'T.
3. Give the scene's `<video>` its explicit clip contract — `id` + `data-start="0"`
   + `data-duration` (= the loader's full crossfade-extended window) +
   `data-media-start` (= storyboard `Clip in`, `0` if whole) + `data-track-index="0"`
   (pre-wired in the template; substitute the `DUR`/`MSTART` placeholders).
   HyperFrames frame-syncs `currentTime` to the scene window from those
   attributes; a bare `<video>` is not time-synced and, with 2+ clip scenes,
   cross-routes (wrong footage / black). Full contract: `workflows/phase-3-design.md`
   § Clip scene.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Cast recorded at wrong size / wide output wraps | terminal size not set (or `rec --cols/--rows` used — 3.x-only, errors on 2.x) | Set `COLUMNS=175 LINES=32` in the `rec` env; the cast header records that size |
| MP4 won't open / stutters in player or scene | agg emits change-only frames (2–4 total); an agg `.mp4` is really a GIF | Run the mandatory `fps=30` ffmpeg normalize (step 2 above) |
| MP4 is letterboxed weirdly | agg `--cols`/`--rows` passed and ≠ the recorded `COLUMNS`/`LINES` | Drop `--cols/--rows` entirely — agg reads the size from the cast header |
| Render fails: "height not divisible by 2" | agg GIF odd-width | Use the ffmpeg `scale=trunc(...)*2` filter (in the normalize) |
| Spinner shows blank chars | Terminal font missing glyphs | `agg --font-family "JetBrains Mono"` (or the font installed on the render host) |
| Output trails off mid-line | `asciinema rec --command` killed by SIGINT | Re-run; let the command exit naturally, or use interactive mode + `exit` |
| Text reads too small in render | Default `--font-size 14` | Use `--font-size 28` or larger for 1080p |

## See also

- `templates/scene-terminal-clip.html` — the clip-wrapper scene archetype
- `templates/scene-terminal.html` — the authored (no-dep) fallback
- `workflows/phase-2-capture.md` § "Recording a CLI scene (terminal)"
- asciinema docs: <https://docs.asciinema.org/>
- agg repo: <https://github.com/asciinema/agg>
