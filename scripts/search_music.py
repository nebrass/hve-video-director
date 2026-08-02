#!/usr/bin/env python3
"""
hve-video-director — Background Music Search (Freesound)

The supported way to find a music bed. Searches Freesound for Creative Commons
tracks, filters by duration and licence, and prints candidates with their exact
track-page URL — the provenance `scripts/validate_brief.py` pins for
`music_strategy: freesound`.

It returns *candidates only*. The exact-track confirmation stays with the user
in Phase 5 (ADR-001): searching moves, the choice never does.

Why this is the default rather than a delegated engine: a Freesound track is a
real recording with a human author, a stable URL and an auditable licence. A
generated bed has none of those, and generation is slow and failure-prone in
practice — a real run stalled two hours on an unauthenticated model download
before producing nothing. Catalog *retrieval* through `media-use` remains a
legitimate alternative where a credential exists; local *generation* is not
offered by the Phase-5 workflow.

Requires FREESOUND_API_KEY (free: https://freesound.org/apiv2/apply/).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://freesound.org/apiv2"


def search(query: str, min_duration: int, max_duration: int, page_size: int, token: str):
    params = {
        "query": query,
        "filter": (
            f"duration:[{min_duration} TO {max_duration}] "
            f'license:("Creative Commons 0" OR "Attribution")'
        ),
        "fields": "id,name,duration,license,username,previews,url,tags",
        "page_size": str(page_size),
        "token": token,
    }
    url = f"{API_BASE}/search/text/?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "hve-video-director"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main() -> int:
    parser = argparse.ArgumentParser(description="Search Freesound for video background music")
    parser.add_argument("query", help='e.g. "cinematic corporate uplifting"')
    parser.add_argument("--min-duration", type=int, default=30, help="seconds (default 30)")
    parser.add_argument("--max-duration", type=int, default=180, help="seconds (default 180)")
    parser.add_argument("--page-size", type=int, default=10)
    parser.add_argument("--json", action="store_true", help="emit raw JSON instead of human output")
    args = parser.parse_args()

    token = os.environ.get("FREESOUND_API_KEY")
    if not token:
        print("Error: FREESOUND_API_KEY not set. Get one at https://freesound.org/apiv2/apply",
              file=sys.stderr)
        return 1

    try:
        data = search(args.query, args.min_duration, args.max_duration, args.page_size, token)
    except urllib.error.HTTPError as e:
        print(f"Freesound API error: HTTP {e.code} {e.reason}", file=sys.stderr)
        return 2
    except urllib.error.URLError as e:
        # DNS failure, connection refused, TLS error, socket timeout. Must come
        # after HTTPError — HTTPError is a subclass of URLError.
        print(f"Freesound API error: {e.reason}", file=sys.stderr)
        return 2

    if args.json:
        json.dump(data, sys.stdout, indent=2)
        return 0

    results = data.get("results", [])
    print(f"Got {len(results)} hits for {args.query!r} "
          f"(duration {args.min_duration}–{args.max_duration}s):\n")
    for i, r in enumerate(results, 1):
        previews = r.get("previews", {})
        preview_url = previews.get("preview-hq-mp3") or previews.get("preview-lq-mp3", "")
        print(f"  {i}. [{r['id']}] {r['name']}")
        print(f"      {r['duration']:.1f}s · {r['license']} · by {r['username']}")
        print(f"      page:    {r['url']}")
        print(f"      preview: {preview_url}")
        print()

    if results:
        print("Download a chosen track:")
        print('  curl -sL "<preview-url>" -o background-music.mp3')
        print()
        print("If license is CC-BY (Attribution), record credit in CREDITS.md.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
