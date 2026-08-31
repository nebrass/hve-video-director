# Recorded Browse-Flow Capture — DevTools Recorder replay

The user records a browsing session with the Chrome/Edge DevTools Recorder, exports it as JSON,
and drops it under the project's `recordings/`. Phase 2 replays that flow through the
chrome-devtools MCP with human pacing while filming one continuous master screencast take, then
cuts per-frame clips and stills from the take. The recording — not improvisation — is the
navigation authority for every frame that binds it (ADR-011): the user demonstrating the flow
beats the agent inferring it, and the result reads like a person driving rather than a script
teleporting through state.

The take itself is `workflows/phase-2-capture.md` § Replaying a recorded flow; this file owns the
long tail: the accepted format, the step→tool mapping, the pacing law, the ledger and cut
discipline, the consent and secrets stance, and troubleshooting. For ordinary web capture with no
recording, use the Step 2.1/2.2 flow in the workflow.

## When to use this path

Phase 1 puts the choice to the user outright: whenever a web capture needs more than a single
URL and a described state, its navigation-authorship question offers *replay my recording* /
*skill navigates* / *I'll record before Phase 2* (recommend, never preselect — ADR-001). The
judgment behind the recommendation:

- Navigation too complex or too stateful to describe as a URL plus a target state: deep SaaS
  surfaces (a Power BI report and its drill paths are the motivating case), multi-step wizards,
  canvas/iframe UIs where improvised clicking is unreliable.
- Apps with no source to reason from — the recording replaces the route knowledge Phase 0 cannot
  gather.
- Any flow the user would rather demonstrate than describe.

**When not:** a single view that one navigate-and-shoot still covers; flows that genuinely need
in-the-moment improvisation (replay never improvises — that is the point); flows whose recorded
actions must not be performed twice (the replay performs them again, and the consent brief says
so).

## Recording the flow (user-side)

Chrome and Edge ship the recorder natively: DevTools → **Recorder** panel → *Start new
recording* → perform the flow → stop → **Export** → **JSON** (the Puppeteer Replay user-flow
format). Save the export under the project's `recordings/` with a slug name
(`recordings/drill-to-details.json`). Firefox has no native recorder; the companion
[HVE Flow Recorder](https://github.com/nebrass/hve-flow-recorder) extension emits the same
schema on Chrome, Edge, and Firefox — enriched with real timing, typing rhythm, and the named
custom steps (see the `hve` fields and § Named custom steps below), and it redacts secret
fields at capture time, which the native recorder does not. It is consent-first: no site access
at install, one browser prompt at the first Start (the user must Allow it for recording to
work), and capture code present on pages only during a recording session.

Record deliberately: the replay reproduces your *steps*, and synthesizes its own pacing, so
stray clicks and dead-end detours are replayed too. Record **after** authenticating (see
Security stance), and prefer one flow per recording — several storyboard frames can take
different step ranges of it.

## Format contract

Baseline is the DevTools Recorder JSON export, consumed verbatim: a top-level object with a
`steps` list; **unknown keys anywhere are ignored**, so a plain Chrome export and an
extension-enriched one both replay. `scripts/replay_flow.py plan` is the executable form of this
contract — when in doubt, its output wins.

| Step type | Replay treatment |
|---|---|
| `setViewport` | overridden by the locked Phase-1 canvas; mismatch warned, never obeyed |
| `navigate` | performed (the recording's own navigation is the only sanctioned navigation); `assertedEvents` navigations are awaited |
| `click` / `doubleClick` | pointer travel + settle, then the real click on the resolved element |
| `change` | click-to-focus, then chunked typing when filmed; instant fill when not filmed |
| `keyDown` / `keyUp` | collapsed into one key press per pair |
| `hover` | pointer travel + settle on the resolved element |
| `scroll` | one eased scroll (page or element), never an instant jump |
| `waitForElement` / `waitForExpression` | polled; no artificial dwell |
| `close` | ignored by design — the take ends instead |
| `emulateNetworkConditions` | ignored with a warning — capture films the real network |

Anything else is reported by `plan` as **unhandled** so the user learns before consent; replay
aborts if it reaches such a step. Selectors are the recorder's own forms — `aria/…`, bare CSS,
`xpath//…`, `pierce/…`, `text/…`, each step carrying a preference-ordered list — plus optional
`frame` index paths for iframe targets (the Power BI case).

**Named custom steps (contract v1.1).** The schema's own extension point is
`customStep { name, parameters }` (it carries `frame`, `target`, `assertedEvents` like any user
step). Three names are part of this contract; an unknown name is reported before consent and
aborts the take if reached. A foreign replayer with no custom-step handler skips or rejects
them — a recorded, deliberate trade.

| Name | Parameters | Replay treatment |
|---|---|---|
| `hve-wheel` | `selectors`, `x`, `y`, `deltaX`, `deltaY`, `ctrl` — one coalesced wheel/zoom burst; trackpad pinch arrives this way (`ctrl: true`), per the wheel-event spec | dispatch a synthetic `WheelEvent` at the target via script evaluation — best-effort: synthetic events are untrusted, which canvas zoom handlers rarely check. CDP itself offers a trusted wheel (`Input.dispatchMouseEvent` `type=mouseWheel`); the exit is a wheel/gesture tool ask on the chrome-devtools MCP |
| `hve-drag` | `kind` (`html5` \| `pointer`), `from`, `to` (selector lists), optional `path` waypoints | resolve both ends to uids and perform the element-to-element drag capability; the waypoints inform pacing, not the mechanism |
| `hve-upload` | `selectors`, `files` (names only — never bytes) | stage each named file under `recordings/files/` before the take; replay resolves the input and uploads the staged file. A missing staged file aborts with a named finding |

**Multi-tab flows.** A step's `target` (schema string, default `main`) is bound to the acting
tab's URL: tabs the flow opens are recorded, their steps carry `target`, and the consent brief
lists every additional tab. Replay: the opening click executes in the main page and the new
page appears as its side effect; before the first `target ≠ main` step, list the open pages and
select the one matching the target URL (origin containment applies to targets too). A target
page that never appears aborts the take with a named finding.

**Reserved enrichment — the `hve` namespace.** A recording producer (the companion extension) may
add a per-step `hve` object; every field is optional:

```json
{ "type": "change", "selectors": [["aria/Region filter"]], "value": "north",
  "hve": { "t": 8450, "dwellAfterMs": 900, "note": "narrow to north", "marker": "drill-start",
           "typingMs": 1800, "keyTimes": [120, 140, 200, 120] } }
```

- `t` — milliseconds since recording start. When present on consecutive steps, the real deltas
  (clamped to the profile's bounds) replace synthesized dwells: the replay paces like the user
  actually did.
- `dwellAfterMs` — explicit post-step dwell; beats both `t` deltas and synthesis, same clamp.
- `note` — free text, shown in the consent brief.
- `marker` — reserved for future marker-based segmentation; not consumed today.
- `typingMs` — how long a `change` value took to type; replay stretches its chunked typing to
  match.
- `keyTimes` — inter-key intervals for a `change` step, **quantized to 20 ms** and capped by
  the producer: keystroke timing is an identifying biometric (the keystroke-dynamics
  literature), so raw intervals are never recorded, and rhythm capture can be disabled at the
  recorder. Replay paces its typing chunks with them.

## Security stance

**Recorder exports are plaintext.** A recorded login puts the password in a `change` step's
`value`, and recorded URLs may carry tokens in query strings. Therefore:

- **Record after authenticating** and replay over `web_capture_source: attached-session`, so the
  export never contains credentials. This is the documented posture, not a nice-to-have.
- `plan` flags secret-like values (password-ish selectors, token-shaped strings) — surface those
  warnings to the user verbatim; the remedy is re-recording, never editing the user's export.
- The consent brief prints hosts without query or fragment and **never prints a typed value**.
- Never commit a recording containing credentials; `recordings/` contents deserve the same
  review as screenshots in the PII gate. No recording ever enters `example/`.
- The replay ledger and sidecars persist only timecodes and element bounding boxes — never
  query strings, typed values, cookies, or tab identity
  (`patterns/authenticated-browser-capture.md`).

## Replay mode — autonomous (skill-driven)

One recording, one take: replay the whole flow once, film it once, and let every bound frame cut
or shoot from the master. Per step:

1. `take_snapshot` → resolve the step's selector to an element uid. **Aria-first ladder:** an
   `aria/` selector matches the accessibility snapshot directly; CSS/xpath/pierce selectors
   resolve via `evaluate_script` locating the element and returning its accessible name, role,
   and bounding box to match in a fresh snapshot. Iframe steps rely on the snapshot's own frame
   traversal.
2. Perform the action with the mapped input capability (`click`, `hover`, `press_key`,
   `type_text` in chunks, `fill`; `evaluate_script` for eased scrolls; navigation only for the
   recording's own `navigate` steps), honoring the pacing schedule.
3. Append the ledger entry, then continue.

**Abort semantics — replay never improvises.** Any of these ends the take with a named finding
(step index + the step's selector list), and prior valid clips stay protected behind their
pending markers: a selector that resolves to nothing (or ambiguously); an unexpected dialog; a
navigation toward an origin the consent brief did not list; an unhandled step type. Recovery is
the user's choice in the workflow: retake after they fix the app state or re-record, degrade the
frame to a range-end still, or skip the frame.

## Human pacing synthesis

The law: **every action is surrounded by intent.** Travel to a target before acting on it,
settle before pressing, dwell after acting long enough to read the result, longer after a
navigation. Typing arrives in bursts, not as an atomic paste. Scrolls ease. Waits poll and add
nothing. When the recording carries real timing (`hve.t` / `hve.dwellAfterMs`), the user's own
rhythm — clamped to sane bounds — replaces synthesis.

The numbers live in **one place**: the pacing-profile block at the top of
`scripts/replay_flow.py` (`POINTER_TRAVEL_MS`, `HOVER_SETTLE_MS`, `READ_DWELL_MS`,
`NAV_DWELL_MS`, `TYPE_CHUNK_CHARS`, `TYPE_CHUNK_PAUSE_MS`, `SCROLL_MS`, `POINTER_EASING`,
`HVE_T_CLAMP_MS`), asserted by `test/unit/test_replay_flow.py`. Cite the block; never restate a
value here or in a workflow — the vo-budget precedent. The schedule `plan` emits is
deterministic per recording but varied per step (no metronome); the agent may stretch a travel
toward the range's top for a long pointer journey and shave toward the bottom for a near target,
never outside the range.

Two structural rules ride with pacing:

- **Lead every take with motion** — an eased scroll nudge before the first step. Screencast
  frames are change-driven (`SCREENCAST_FRAME_EMISSION`), so the lead-in is simultaneously the
  first emitted frame and the ledger's clock anchor.
- **The footage stays pointer-free** (`SCREENCAST_POINTER_ABSENCE`): the human-feel cursor is
  *data* — the ledger's pointer track — rendered by Phase 3's brand pointer, governed by the
  user's `replay_pointer:` choice. Nothing in the replay injects a visible cursor into the page.

## Ledger and cut law

The agent writes the ledger during the take to `.hve/replay/<recording-stem>.json`:

```json
{
  "schema_version": 1,
  "recording": "recordings/drill-to-details.json",
  "recording_sha256": "<64 hex of the exact export replayed>",
  "source": "navigate | attached-session",
  "pointer": "branded | none",
  "canvas": [1920, 1080],
  "steps": [
    { "index": 3, "type": "click", "action": "click",
      "t_start": 4.02, "t_end": 5.31, "bbox": [812, 404, 240, 96] }
  ]
}
```

- **Anchor:** `t = 0` is the wall-clock instant the lead-in motion is issued — it produces the
  first emitted frame — never the moment the screencast was started.
- `t_start`/`t_end` bracket the step's performed action (travel through post-dwell); `bbox` is
  the target's viewport-coordinate box (null for steps with no element), which becomes the
  pointer track.
- **Drift:** after `stitch_clip.py` normalization, `cut` compares the ffprobed master duration
  against the ledger span — a small disagreement proceeds, a moderate one applies a uniform
  end-anchored offset with a warning, a large one refuses and asks for a retake. The bounds are
  `replay_flow.py`'s.
- **Cut boundaries are dwell-aligned by construction:** each frame's segment runs from just
  before its first step's `t_start` to just after its last step's `t_end`, clamped to the take;
  both pads are deliberately smaller than the guaranteed dwell floors, so a boundary always
  lands on quiet footage, never mid-action. Cuts are frame-accurate because the stitcher
  re-encodes every segment.
- **Publish is atomic and fingerprinted:** `cut` writes each clip through a candidate file, then
  publishes clip + `<clip>.replay.json` sidecar as a pair (recording hash, steps, media
  fingerprint, clip-local pointer track); a failure restores the previous pair and leaves the
  pending marker. `check` is the resume predicate — a re-recorded flow (hash), a tampered clip
  (fingerprint), or a rebound frame (steps) all refuse.

## Segmentation

One long recording may feed several storyboard frames: each frame binds
`recording: recordings/<name>.json` plus `recording_steps: A-B` (1-based, inclusive; a single
`A` for one step; omit for the whole flow). The flow is replayed **once**; `cut` slices the
master per frame. Ranges may overlap. A `capture: screenshot` frame's range means "the state
after step B" — its still is taken at that step's post-action dwell (or extracted from the
master afterwards). Never replay a range in isolation: the earlier steps are its prerequisites,
and re-running them multiplies both state mutation and the consent surface (ADR-011).

## Attached-session replay

The recording usually earns its keep against an authenticated tab (record after login, replay in
the live session). That combination is governed by
`patterns/authenticated-browser-capture.md` § Recorded-flow exception: whole-flow consent
(workflow Step 2.1b) replaces per-action consent for exactly the approved steps; containment is
the recording's own origins; every other attached rule stays in force; the take ends at the
flow's disclosed final state with its origin reported. Consent is hash-scoped — a byte-identical
recording can be retaken on the same approval, a re-recorded one re-asks.

## Quality gate (in addition to the Phase-2 footage gate)

- Pacing reads human: dwells around every action, no teleporting state, no metronome rhythm.
- The footage carries **no** pointer (that is correct — the pointer is Phase-3 data); a visible
  cursor in a cut means the upstream behavior changed (`SCREENCAST_POINTER_ABSENCE`) — stop and
  re-read that probe row.
- `replay_flow.py check` passes for every cut; stills exist at their bound paths and meet the
  legibility/retina standards of the workflow's Capture Tips.
- The standard gate still applies: canvas resolution, confirmed theme, no dev artifacts, one
  clean take, duration within the frame's slot.

## Wiring into a scene

Nothing downstream changes: a cut clip is an ordinary bound `clip:` consumed by the Layer-A
clip-scene archetype (`templates/scene-clip.html`), a replay still an ordinary `screenshot:`.
The one addition is the pointer track: the frame packet's item 5 binds the clip's
`<clip>.replay.json` sidecar, and Phase 3's mandatory brand-pointer treatment follows the
track's clip-local timecodes and target boxes when `replay_pointer: branded`
(`workflows/phase-3-design.md` § Clip scene).

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Master take is near-empty / 0 bytes | Take opened with no page change — frames are change-driven (`SCREENCAST_FRAME_EMISSION`) | Lead the take with the eased scroll nudge; keep `screencast_start` before the first action |
| Take fails though screencast is enabled | `ffmpeg` missing on the **MCP server's** PATH (a different machine when the MCP is remote) | Install ffmpeg where the MCP runs; see the workflow's MCP screencast note |
| A selector resolves to nothing | UI changed since recording, or A/B variance | Re-record the flow (cheap by design); do not hand-patch the export |
| Replay aborts on an unexpected dialog | The app now shows a prompt the recording never saw | Dismiss/prepare the app state manually, retake; dialogs are never auto-answered mid-flow |
| Cuts land offset from the action | Ledger anchored at `screencast_start` instead of the lead-in motion | Anchor `t = 0` at the lead-in; `cut`'s drift check catches large cases, not a wrong anchor |
| `cut` refuses with a drift error | Take stalled (slow network, long load) so ledger and footage disagree beyond the bound | Retake; if the app is genuinely that slow, the recording should carry `hve.t` timings |
| Mid-take `take_screenshot` errors | Screenshot-during-screencast varies by MCP version (`SCREENCAST_CONCURRENT_CAPTURE`) | Expected — the workflow's step 7 extracts the still from the master afterwards |
| Extracted still looks soft vs. real screenshots | Frame extraction inherits the take's pixel size, below the retina still standard | Accept with the measured warning, or reshoot that still via a second stills-only pass |
| `check` fails after everything looked fine | The recording file changed since the cut (hash), or the clip was touched (fingerprint) | Retake/re-cut against the current recording; never edit a published clip in place |
| Typing looks pasted, not typed | `fill` used on a filmed frame | Filmed `change` steps use chunked typing; `fill` is for unfilmed state transport |
| A canvas zoom (`hve-wheel`) replays with no effect | The app checks `isTrusted` on wheel events — synthetic dispatch is untrusted | No local fix; note the frame for retake as a still, and see the wheel-tool exit in § Named custom steps |
| An `hve-upload` step aborts | The named file is not staged | Place the exact file under `recordings/files/` before the take |
| A `target` step aborts with "page never appeared" | The opening click did not open the tab this run (popup blocked, state changed) | Let the user unblock popups / restore state, then retake |

## See also

- `workflows/phase-2-capture.md` § Replaying a recorded flow — the take recipe this file backs.
- `workflows/phase-2-capture.md` § Step 2.1b — whole-flow consent and the pointer choice.
- `patterns/authenticated-browser-capture.md` § Recorded-flow exception — the attached-session
  carve-out.
- `templates/storyboard.md` § Capture and clip keys — `recording` / `recording_steps`.
- `scripts/replay_flow.py` — plan / arm / cut / check, and the pacing-profile block.
- `workflows/phase-3-design.md` § Clip scene — pointer-track consumption.
- Chrome DevTools Recorder documentation: https://developer.chrome.com/docs/devtools/recorder
