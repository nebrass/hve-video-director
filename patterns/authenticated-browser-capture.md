# Authenticated Browser Capture

Use this pattern when the product is already open and authenticated in Chrome through SSO, MFA,
or an account that cannot sign in inside the MCP-managed browser. The goal is to select that exact
live tab, capture it without navigation, and leave the browser as it was.

## Connection prerequisite

`list_pages` and `select_page` can only see the user's session when the Chrome DevTools MCP server
was configured to connect to the running browser. Tool availability alone does not establish that
connection.

### Preferred: Chrome 144+ automatic connection

1. The user opens the intended Chrome profile and authenticated tab.
2. In Chrome, the user opens `chrome://inspect/#remote-debugging`, enables remote debugging, and
   approves the incoming connection dialog.
3. The user adds `--autoConnect` to the existing Chrome DevTools MCP server arguments and restarts
   the agent runtime.
4. The agent calls `list_pages` as the only readiness probe.

Generic MCP argument example:

```json
{
  "command": "npx",
  "args": ["chrome-devtools-mcp@latest", "--autoConnect"]
}
```

`--autoConnect` connects to Chrome's default active profile and gives the MCP access to every open
window in that profile. Before enabling it, close unrelated sensitive tabs. Prefer a dedicated
Chrome profile when the regular profile contains private browsing unrelated to the video.

### Fallback: dedicated debuggable profile

For a sandboxed/remote runtime, configure the MCP with
`--browser-url=http://127.0.0.1:9222`, then start Chrome manually with the matching local remote
debugging port and a **non-default** user-data directory. Sign in once inside that dedicated
profile and reuse it for capture. Follow the upstream
[running-Chrome instructions](https://github.com/ChromeDevTools/chrome-devtools-mcp#connecting-to-a-running-chrome-instance)
for platform commands and VM/WSL forwarding.

The debugging port permits local applications to control that profile. Bind it to loopback,
close Chrome when finished, never expose it to the network, and do not point it at the user's
default profile. The skill prints setup instructions only: it never edits MCP configuration,
launches a debuggable browser, chooses a profile directory, or accepts Chrome's permission dialog.

## Tab-selection protocol

1. Call `list_pages`. Failure means the connection is not ready; do not fall back to a new browser
   or URL navigation without asking the user.
2. Sanitize each candidate to title + scheme/host/path. Remove the query and fragment, which may
   contain bearer tokens or private identifiers.
3. Present no more than three tabs plus **More tabs** per native prompt. Keep the page-ID mapping
   in memory only.
4. Call `select_page` for the exact user-selected ID.
5. Call `list_pages` again and verify that the same ID is selected before any capture.
6. Report the sanitized title/origin and require final confirmation.

Never persist page IDs, complete URLs, profile paths, DOM snapshots, cookies, storage, request
headers, or authentication material in `context.md`, `storyboard.md`, logs, or generated helper
files. The storyboard persists only `web_capture_source: attached-session` (storyboard frontmatter).

## Read-only capture contract

- Never navigate, reload, follow a link, open a new page, close a page, or alter browser history.
- Never inspect cookies, `localStorage`, `sessionStorage`, saved passwords, authorization headers,
  or network response bodies to recover credentials.
- Never submit forms or trigger purchases, publishing, deletion, logout, account changes, or app
  settings.
- Screenshot the current visible state directly by default. `take_snapshot` may expose an
  accessibility tree beyond the visible viewport; use it only for a specifically consented
  interaction, and never persist or quote unrelated nodes. Any click, scroll, or keypress
  requires exact per-action consent; broad consent for the session is not sufficient.
- Ask the user to prepare the desired app state and confirmed light/dark theme manually. Do not
  change a persistent theme or account preference.
- Do not use a full-page screenshot without separate consent: off-screen content may contain
  private data the user did not prepare for capture.

The accepted capture files intentionally contain visible product data. The Phase-2 gallery review
must check them for email addresses, names, tenant IDs, tokens, financial data, or unrelated tabs
before the user accepts them.

## Temporary viewport changes

Record `window.outerWidth` and `window.outerHeight` before resizing. Then ask:

```json
{
  "questions": [{
    "question": "May I temporarily resize this browser window for the video canvas?",
    "header": "Viewport",
    "options": [
      { "label": "Resize and restore", "description": "Match the confirmed canvas, then restore the original outer dimensions on success or failure." },
      { "label": "Keep current size", "description": "Do not resize; capture the prepared browser window as-is." }
    ],
    "multiSelect": false
  }]
}
```

If approved, use `resize_page`, capture, and restore the original dimensions after the last
artifact and on every failure path. Surface a restoration failure immediately. Never close the tab
or browser as cleanup.

## Failure and resume

- **Expected tab absent:** ask the user to open/authenticate it in the connected profile, then
  call `list_pages` again.
- **Session expired:** stop and let the user authenticate manually. Do not drive a login flow.
- **Tab closed or ID changed:** discard the in-memory mapping and re-list; never guess by index.
- **Connection lost:** retain Phase 2 as incomplete and provide the appropriate `--autoConnect` or
  `--browser-url` setup handoff.
- **Capture source changed:** update `web_capture_source` and treat all prior web captures as
  stale until the user reviews replacements.

On successful completion, restore the viewport, leave the selected tab open at the same URL, and
persist only the accepted screenshots/clips.
