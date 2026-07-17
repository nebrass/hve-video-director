#!/usr/bin/env bash
#
# check_requirements.sh — verify the hve-spielberg toolchain and (optionally) fix
# what can be safely auto-installed.
#
# Usage:
#   ./scripts/check_requirements.sh          # report only (no changes)
#   ./scripts/check_requirements.sh --fix    # auto-install user-scoped deps;
#                                            # print (never run) sudo/system commands
#   ./scripts/check_requirements.sh --help
#
# Exit status: 0 if every REQUIRED item is satisfied, 1 if any is missing, 2 on an unknown argument.
# Recommended/optional gaps never fail the run — they only warn.

set -u

# ---------------------------------------------------------------------------
# Presentation
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
  BOLD=$'\033[1m'; DIM=$'\033[2m'; RED=$'\033[31m'; GRN=$'\033[32m'
  YEL=$'\033[33m'; RST=$'\033[0m'
else
  BOLD=''; DIM=''; RED=''; GRN=''; YEL=''; RST=''
fi
ok()   { printf '  %s✓%s %s\n' "$GRN" "$RST" "$1"; }
warn() { printf '  %s○%s %s\n' "$YEL" "$RST" "$1"; }
bad()  { printf '  %s✗%s %s\n' "$RED" "$RST" "$1"; }
hint() { printf '      %s↳ %s%s\n' "$DIM" "$1" "$RST"; }
section() { printf '\n%s%s%s\n' "$BOLD" "$1" "$RST"; }

FIX=0
for a in "$@"; do
  case "$a" in
    --fix) FIX=1 ;;
    -h|--help)
      # Self-contained heredoc (not read from "$0"), so --help works when the
      # script is piped — e.g. `curl … | bash -s -- --help`.
      cat <<'EOF'
check_requirements.sh — verify the hve-spielberg toolchain and (optionally) fix
what can be safely auto-installed.

Usage:
  ./scripts/check_requirements.sh          # report only (no changes)
  ./scripts/check_requirements.sh --fix    # auto-install user-scoped deps;
                                           # print (never run) sudo/system commands
  ./scripts/check_requirements.sh --help

Exit status: 0 if every REQUIRED item is satisfied, 1 if any is missing, 2 on an unknown argument.
Recommended/optional gaps never fail the run — they only warn.
EOF
      exit 0 ;;
    *) echo "unknown arg: $a (try --help)" >&2; exit 2 ;;
  esac
done

REQUIRED_FAIL=0   # increments when a REQUIRED item is missing

# ---------------------------------------------------------------------------
# Platform detection (drives install hints + the WSL render note)
# ---------------------------------------------------------------------------
OS="$(uname -s)"
IS_WSL=0
case "$OS" in
  Darwin) PLATFORM="macOS";  PKG="brew install" ;;
  Linux)
    PLATFORM="Linux"; PKG="sudo apt install"
    if grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then IS_WSL=1; PLATFORM="WSL2"; fi
    ;;
  *) PLATFORM="$OS"; PKG="(install via your package manager)" ;;
esac

# ver_ge MAJOR.MINOR  MIN_MAJOR  MIN_MINOR  -> 0 if version >= minimum
ver_ge() {
  local have="$1" maj_min="$2" min_min="${3:-0}"
  local hmaj hmin
  hmaj="${have%%.*}"
  case "$have" in
    *.*) hmin="${have#*.}"; hmin="${hmin%%.*}" ;;
    *)   hmin=0 ;;
  esac
  # strip any non-digit suffix (e.g. "3.10rc1")
  hmaj="${hmaj//[!0-9]/}"; hmin="${hmin//[!0-9]/}"
  [ -z "$hmaj" ] && return 1
  [ "$hmaj" -gt "$maj_min" ] && return 0
  [ "$hmaj" -eq "$maj_min" ] && [ "${hmin:-0}" -ge "$min_min" ] && return 0
  return 1
}

printf '%shve-spielberg requirements check%s  (%s%s%s)\n' \
  "$BOLD" "$RST" "$DIM" "$PLATFORM" "$RST"
[ "$FIX" -eq 1 ] && printf '%s--fix: will auto-install user-scoped deps; sudo/system commands are printed, not run%s\n' "$DIM" "$RST"

# ===========================================================================
section "Required"
# ===========================================================================

# --- Node.js >= 22.12 ------------------------------------------------------
if command -v node >/dev/null 2>&1; then
  NODE_V="$(node --version 2>/dev/null | sed 's/^v//')"
  if ver_ge "$NODE_V" 22 12; then ok "Node.js $NODE_V"
  else bad "Node.js $NODE_V — need >= 22.12 (hyperframes needs >= 22; chrome-devtools-mcp needs ^20.19 || ^22.12 || >=23)"; hint "upgrade via nodejs.org or nvm"; REQUIRED_FAIL=1; fi
else
  bad "Node.js — not found"; hint "install from https://nodejs.org (>= 22.12)"; REQUIRED_FAIL=1
fi

# --- npx (ships with Node/npm; load-bearing for hyperframes + skills) -------
if command -v npx >/dev/null 2>&1; then ok "npx"
else bad "npx — not found (ships with Node/npm)"; hint "reinstall Node.js from https://nodejs.org (bundles npm/npx)"; REQUIRED_FAIL=1; fi

# --- Python >= 3.10 --------------------------------------------------------
if command -v python3 >/dev/null 2>&1; then
  PY_V="$(python3 --version 2>&1 | awk '{print $2}')"
  if ver_ge "$PY_V" 3 10; then ok "Python $PY_V"
  else bad "Python $PY_V — need >= 3.10"; hint "install from https://python.org"; REQUIRED_FAIL=1; fi
else
  bad "Python 3 — not found"; hint "install from https://python.org (>= 3.10)"; REQUIRED_FAIL=1
fi

# --- ffmpeg + ffprobe (system package; sudo — never auto-run) --------------
for bin in ffmpeg ffprobe; do
  if command -v "$bin" >/dev/null 2>&1; then ok "$bin"
  else
    bad "$bin — not found"; REQUIRED_FAIL=1
    if [ "$PLATFORM" = macOS ]; then hint "brew install ffmpeg"
    else hint "$PKG ffmpeg   ${DIM}(run this yourself — needs sudo)${RST}"; fi
  fi
done

# --- chrome-headless-shell (user-scoped; auto-installable) -----------------
# hyperframes doctor is the source of truth for the render browser. Capture its
# --json output ONCE and read the per-check Chrome `ok` (NOT doctor's exit code
# or top-level `ok`, which goes false when unrelated checks like Docker fail).
CHROME_OK=""; DOC_OUT=""
if command -v npx >/dev/null 2>&1; then
  DOC_OUT="$(npx --yes hyperframes doctor --json 2>/dev/null)"
  CHROME_OK="$(printf '%s' "$DOC_OUT" | node -e 'let d="";process.stdin.on("data",c=>d+=c).on("end",()=>{try{const c=JSON.parse(d).checks.find(x=>x.name==="Chrome");process.stdout.write(c?(c.ok?"1":"0"):"")}catch(e){}})' 2>/dev/null)"
fi
if [ "$CHROME_OK" = 1 ]; then
  ok "chrome-headless-shell (hyperframes doctor passed)"
else
  if [ "$CHROME_OK" = 0 ]; then
    bad "chrome-headless-shell — not detected by hyperframes doctor"
  else
    bad "chrome-headless-shell — hyperframes doctor could not run (Node/npx issue above)"
  fi
  if [ "$FIX" -eq 1 ] && command -v npx >/dev/null 2>&1; then
    printf '      %sinstalling chrome-headless-shell…%s\n' "$DIM" "$RST"
    if npx --yes puppeteer browsers install chrome-headless-shell; then ok "chrome-headless-shell installed"
    else bad "chrome-headless-shell install failed"; hint "retry: npx puppeteer browsers install chrome-headless-shell"; REQUIRED_FAIL=1; fi
  else
    hint "npx puppeteer browsers install chrome-headless-shell   (one-time, ~170MB)"
    REQUIRED_FAIL=1
  fi
fi

# --- hyperframes CLI (auto via npx; only needs network) --------------------
if command -v npx >/dev/null 2>&1 && HF_VER="$(npx --yes hyperframes --version 2>/dev/null)"; then
  ok "hyperframes CLI ($HF_VER)"
else
  bad "hyperframes CLI — not reachable"; hint "npm i -g hyperframes  (or rely on npx; needs network)"; REQUIRED_FAIL=1
fi

# ===========================================================================
section "Companion skills (required for Phases 3–4)"
# ===========================================================================
# Canonical home list — keep in lock-step with SKILL.md § Runtime Compatibility.
SKILL_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SKILL_HOMES="$HOME/.claude/skills|$HOME/.copilot/skills|$HOME/.agents/skills|$HOME/.pi/agent/skills|$HOME/.config/opencode/skills|$HOME/.cursor/skills|$HOME/.codex/skills|/etc/codex/skills|.claude/skills|.github/skills|.agents/skills|.pi/skills|.opencode/skills|.cursor/skills|.codex/skills|$SKILL_ROOT/.claude/skills|$SKILL_ROOT/.github/skills|$SKILL_ROOT/.agents/skills|$SKILL_ROOT/.pi/skills|$SKILL_ROOT/.opencode/skills|$SKILL_ROOT/.cursor/skills|$SKILL_ROOT/.codex/skills"

check_skill() { # name  required(1/0)  install-cmd
  local name="$1" required="$2" inst="$3" home found= old_ifs="$IFS"
  IFS='|'
  for home in $SKILL_HOMES; do
    [ -f "$home/$name/SKILL.md" ] && { found="$home"; break; }
  done
  IFS="$old_ifs"
  if [ -n "$found" ]; then ok "$name skill ($found)"; return; fi
  if [ "$FIX" -eq 1 ] && [ -n "$inst" ] && command -v npx >/dev/null 2>&1; then
    printf '      %sinstalling %s skill…%s\n' "$DIM" "$name" "$RST"
    if npx --yes skills add "$inst" >/dev/null 2>&1; then ok "$name skill installed"; return; fi
    warn "auto-install of $name skill failed — run: npx skills add $inst"
  fi
  if [ "$required" -eq 1 ]; then
    bad "$name skill — not found"; hint "npx skills add $inst"; REQUIRED_FAIL=1
  else
    warn "$name skill — not found (recommended)"; [ -n "$inst" ] && hint "npx skills add $inst"
  fi
}
check_skill hyperframes 1 heygen-com/hyperframes
check_skill gsap        0 ""   # gsap is bundled inside the hyperframes skill — no separate install

# ===========================================================================
section "Recommended"
# ===========================================================================

# --- ELEVENLABS_API_KEY (env — cannot be installed, only guided) -----------
if [ -n "${ELEVENLABS_API_KEY:-}" ] || [ -n "${ELEVEN_LABS_API_KEY:-}" ]; then
  ok "ELEVENLABS_API_KEY set (high-quality TTS)"
else
  warn "ELEVENLABS_API_KEY not set — Phase 5 falls back to npx hyperframes tts (local Kokoro-82M, lower quality)"
  hint "get a key at https://elevenlabs.io, then: export ELEVENLABS_API_KEY=..."
fi

# --- Whisper (transcribe-preferred; standalone whisper is the fallback) ----
if command -v npx >/dev/null 2>&1 && npx --yes hyperframes transcribe --help >/dev/null 2>&1; then
  ok "hyperframes transcribe (preferred timing verifier; standalone whisper optional)"
elif command -v whisper >/dev/null 2>&1; then
  ok "whisper (voiceover timing verification)"
else
  if [ "$FIX" -eq 1 ] && command -v pip3 >/dev/null 2>&1; then
    printf '      %sinstalling openai-whisper (pip --user)…%s\n' "$DIM" "$RST"
    pip3 install --user openai-whisper >/dev/null 2>&1 && ok "whisper installed" \
      || warn "whisper install failed — run: pip3 install --user openai-whisper"
  else
    warn "whisper not found (recommended for VO timing)"
    hint "pip3 install --user openai-whisper"
  fi
fi

# ===========================================================================
section "Optional"
# ===========================================================================

# --- FREESOUND_API_KEY -----------------------------------------------------
if [ -n "${FREESOUND_API_KEY:-}" ]; then ok "FREESOUND_API_KEY set (CC music search)"
else warn "FREESOUND_API_KEY not set — music search disabled (user-provided music still works)"
     hint "get a key at https://freesound.org/apiv2/apply, then: export FREESOUND_API_KEY=..."; fi

# --- espeak-ng (system; non-English tts fallback) --------------------------
if command -v espeak-ng >/dev/null 2>&1; then ok "espeak-ng (non-English tts fallback)"
else warn "espeak-ng not found — only needed for non-English voiceover via the tts fallback"
     if [ "$PLATFORM" = macOS ]; then hint "brew install espeak-ng"; else hint "$PKG espeak-ng   ${DIM}(needs sudo)${RST}"; fi; fi

# --- asciinema + agg + timeout (real terminal-clip recording) --------------
A=$(command -v asciinema >/dev/null && echo 1); G=$(command -v agg >/dev/null && echo 1); T=$(command -v timeout >/dev/null && echo 1)
if [ -n "$A" ] && [ -n "$G" ] && [ -n "$T" ]; then ok "asciinema + agg + timeout (real terminal-clip path)"
else
  warn "asciinema/agg/timeout incomplete — CLI scenes use the authored-terminal path"
  if [ "$PLATFORM" = macOS ]; then hint "brew install asciinema agg coreutils"
  else hint "$PKG asciinema && cargo install --git https://github.com/asciinema/agg   ${DIM}(needs sudo + Rust)${RST}"; fi
fi

# --- Docker (only flagged on WSL, where native render can fail) ------------
if [ "$IS_WSL" -eq 1 ]; then
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    ok "Docker running (WSL render path — use: npx hyperframes render … --docker)"
  else
    warn "Docker not running — on WSL native render can fail at Page.captureScreenshot"
    hint "start Docker, then render with: npx hyperframes render . --output out/final.mp4 --docker"
    hint "on <= 8 GB RAM also add --no-low-memory-mode"
  fi
fi

# ===========================================================================
# Summary
# ===========================================================================
echo
if [ "$REQUIRED_FAIL" -eq 0 ]; then
  printf '%s%s✓ All required dependencies satisfied.%s\n' "$BOLD" "$GRN" "$RST"
  [ "$FIX" -eq 0 ] && printf '%s  Re-run with --fix to auto-install the user-scoped recommended/optional deps; sudo/system and env-var items are printed, not installed.%s\n' "$DIM" "$RST"
  exit 0
else
  printf '%s%s✗ Missing required dependencies (see ✗ above).%s\n' "$BOLD" "$RED" "$RST"
  [ "$FIX" -eq 0 ] && printf '%s  Re-run with --fix to auto-install the user-scoped ones; sudo/system commands are printed for you to run.%s\n' "$DIM" "$RST"
  exit 1
fi
