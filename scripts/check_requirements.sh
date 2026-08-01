#!/usr/bin/env bash
#
# check_requirements.sh — inspect the hve-video-director toolchain and optionally
# apply explicitly consented, user-scoped fixes.
#
# Exit status: 0 when every required check is ready, 1 when a required check
# is blocked, and 2 for invalid arguments or fix IDs.

set -u

MODE="human"
MODE_SET=0
FIX_REQUESTED=0
FIX_ALL=0
FIX_IDS=""

usage() {
  printf '%s\n' \
    'check_requirements.sh — verify the hve-video-director toolchain and optionally fix' \
    'safe, user-scoped gaps.' \
    '' \
    'Usage:' \
    '  ./scripts/check_requirements.sh                 # human report; no changes' \
    '  ./scripts/check_requirements.sh --json          # JSON-only report; no changes' \
    '  ./scripts/check_requirements.sh --plan          # missing-check plan; no changes' \
    '  ./scripts/check_requirements.sh --fix            # apply every missing safe fix' \
    '  ./scripts/check_requirements.sh --fix=<id,id>    # apply only selected safe fixes' \
    '  ./scripts/check_requirements.sh --help' \
    '' \
    'Safe fix IDs: chrome-shell, hyperframes-skill, whisper' \
    'Repeated scoped form is accepted: --fix=chrome-shell --fix=whisper' \
    '' \
    'Default, --json, and --plan never install or download anything.' \
    'System/sudo commands and environment-variable exports are printed, never run.' \
    '' \
    'Exit status: 0 if every REQUIRED item is satisfied, 1 if any is missing,' \
    '2 on an unknown argument, mode conflict, or unknown fix ID.'
}

set_mode() {
  if [ "$MODE_SET" -eq 1 ] && [ "$MODE" != "$1" ]; then
    printf 'cannot combine --%s and --%s\n' "$MODE" "$1" >&2
    exit 2
  fi
  MODE="$1"
  MODE_SET=1
}

append_fix_id() {
  local raw="$1" id last
  [ -n "$raw" ] || {
    printf 'missing fix ID after --fix=\n' >&2
    exit 2
  }
  while :; do
    last=0
    case "$raw" in
      *,*)
        id="${raw%%,*}"
        raw="${raw#*,}"
        ;;
      *)
        id="$raw"
        raw=""
        last=1
        ;;
    esac
    [ -n "$id" ] || {
      printf 'empty fix ID (safe IDs: chrome-shell, hyperframes-skill, whisper)\n' >&2
      exit 2
    }
    case "$id" in
      chrome-shell|hyperframes-skill|whisper) ;;
      *)
        printf 'unknown fix ID: %s (safe IDs: chrome-shell, hyperframes-skill, whisper)\n' \
          "$id" >&2
        exit 2
        ;;
    esac
    case ",$FIX_IDS," in
      *",$id,"*) ;;
      *) FIX_IDS="${FIX_IDS}${FIX_IDS:+,}${id}" ;;
    esac
    [ "$last" -eq 1 ] && break
  done
}

for arg in "$@"; do
  case "$arg" in
    --json) set_mode json ;;
    --plan) set_mode plan ;;
    --fix)
      FIX_REQUESTED=1
      FIX_ALL=1
      ;;
    --fix=*)
      FIX_REQUESTED=1
      append_fix_id "${arg#--fix=}"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'unknown arg: %s (try --help)\n' "$arg" >&2
      exit 2
      ;;
  esac
done

if [ "$FIX_REQUESTED" -eq 1 ] && [ "$MODE" != human ]; then
  printf '%s is side-effect-free and cannot be combined with --fix\n' "--$MODE" >&2
  exit 2
fi
if [ "$FIX_ALL" -eq 1 ]; then
  FIX_IDS="chrome-shell,hyperframes-skill,whisper"
fi

# ---------------------------------------------------------------------------
# Presentation
# ---------------------------------------------------------------------------
if [ "$MODE" = human ] && [ -t 1 ]; then
  BOLD=$'\033[1m'
  DIM=$'\033[2m'
  RED=$'\033[31m'
  GRN=$'\033[32m'
  YEL=$'\033[33m'
  RST=$'\033[0m'
else
  BOLD=''
  DIM=''
  RED=''
  GRN=''
  YEL=''
  RST=''
fi

ok() { printf '  %s✓%s %s\n' "$GRN" "$RST" "$1"; }
warn() { printf '  %s○%s %s\n' "$YEL" "$RST" "$1"; }
bad() { printf '  %s✗%s %s\n' "$RED" "$RST" "$1"; }
hint() { printf '      %s↳ %s%s\n' "$DIM" "$1" "$RST"; }
section() { printf '\n%s%s%s\n' "$BOLD" "$1" "$RST"; }

# Capture stdout without command substitution discarding trailing newlines.
capture_exact() {
  local __target="$1" __marker=$'\035' __captured __status
  shift
  __captured="$("$@"; __status=$?; printf '%s' "$__marker"; exit "$__status")"
  __status=$?
  case "$__captured" in
    *"$__marker") __captured="${__captured%$__marker}" ;;
    *) return 1 ;;
  esac
  printf -v "$__target" '%s' "$__captured"
  return "$__status"
}

# Commands such as command -v and uname append one record-separator newline.
capture_line() {
  local __target="$1" __line_value __status
  shift
  capture_exact __line_value "$@"
  __status=$?
  case "$__line_value" in
    *$'\n') __line_value="${__line_value%$'\n'}" ;;
  esac
  printf -v "$__target" '%s' "$__line_value"
  return "$__status"
}

command_path() {
  local __target="$1" __name="$2"
  capture_line "$__target" command -v "$__name"
}

# ---------------------------------------------------------------------------
# Platform and canonical skill homes
# ---------------------------------------------------------------------------
if ! capture_line OS uname -s 2>/dev/null; then
  OS="Unknown"
fi
IS_WSL=0
case "$OS" in
  Darwin)
    PLATFORM="macOS"
    FFMPEG_COMMAND="brew install ffmpeg"
    ESPEAK_COMMAND="brew install espeak-ng"
    TERMINAL_COMMAND="brew install asciinema agg coreutils"
    ;;
  Linux)
    PLATFORM="Linux"
    if command -v grep >/dev/null 2>&1 \
      && grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
      IS_WSL=1
      PLATFORM="WSL2"
    fi
    FFMPEG_COMMAND="sudo apt install ffmpeg"
    ESPEAK_COMMAND="sudo apt install espeak-ng"
    TERMINAL_COMMAND="sudo apt install asciinema coreutils && cargo install --git https://github.com/asciinema/agg"
    ;;
  *)
    PLATFORM="$OS"
    FFMPEG_COMMAND="Install ffmpeg and ffprobe with your system package manager."
    ESPEAK_COMMAND="Install espeak-ng with your system package manager."
    TERMINAL_COMMAND="Install asciinema, agg, and a timeout command with your system package manager."
    ;;
esac

# Canonical home list — keep in lock-step with SKILL.md § Runtime Compatibility.
if ! capture_line SKILL_ROOT git rev-parse --show-toplevel 2>/dev/null; then
  SKILL_ROOT="$PWD"
fi
SKILL_HOMES="$HOME/.claude/skills|$HOME/.copilot/skills|$HOME/.agents/skills|$HOME/.pi/agent/skills|$HOME/.config/opencode/skills|$HOME/.cursor/skills|$HOME/.codex/skills|/etc/codex/skills|.claude/skills|.github/skills|.agents/skills|.pi/skills|.opencode/skills|.cursor/skills|.codex/skills|$SKILL_ROOT/.claude/skills|$SKILL_ROOT/.github/skills|$SKILL_ROOT/.agents/skills|$SKILL_ROOT/.pi/skills|$SKILL_ROOT/.opencode/skills|$SKILL_ROOT/.cursor/skills|$SKILL_ROOT/.codex/skills"

find_skill_home() {
  local name="$1" home old_ifs="$IFS"
  IFS='|'
  for home in $SKILL_HOMES; do
    if [ -f "$home/$name/SKILL.md" ]; then
      IFS="$old_ifs"
      printf '%s' "$home"
      return 0
    fi
  done
  IFS="$old_ifs"
  return 1
}

trim_space() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

environment_value() {
  local name="$1" value
  case "$name" in
    [A-Za-z_]*)
      case "$name" in *[!A-Za-z0-9_]*) return 1 ;; esac
      ;;
    *) return 1 ;;
  esac
  if command -v printenv >/dev/null 2>&1; then
    capture_line value printenv "$name" || return 1
  elif [ -x /usr/bin/printenv ]; then
    capture_line value /usr/bin/printenv "$name" || return 1
  else
    return 1
  fi
  printf '%s' "$value"
}

expand_npmrc_value() {
  local value="$1" prefix remainder name suffix replacement expansions=0
  while [[ "$value" == *'${'*'}'* ]]; do
    expansions=$((expansions + 1))
    [ "$expansions" -le 32 ] || break
    prefix="${value%%\$\{*}"
    remainder="${value#*\$\{}"
    name="${remainder%%\}*}"
    suffix="${remainder#*\}}"
    if ! capture_exact replacement environment_value "$name" 2>/dev/null; then
      replacement=""
    fi
    value="$prefix$replacement$suffix"
  done
  printf '%s' "$value"
}

read_npmrc_value() {
  local file="$1" wanted="$2" line key value result=""
  [ -r "$file" ] || return 1
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    line="$(trim_space "$line")"
    case "$line" in
      ""|\#*|\;*) continue ;;
      *=*)
        key="$(trim_space "${line%%=*}")"
        [ "$key" = "$wanted" ] || continue
        value="$(trim_space "${line#*=}")"
        case "$value" in
          \"*\") value="${value#\"}"; value="${value%\"}" ;;
          \'*\') value="${value#\'}"; value="${value%\'}" ;;
        esac
        result="$value"
        ;;
    esac
  done < "$file"
  [ -n "$result" ] || return 1
  case "$result" in
    '~') result="$HOME" ;;
    '~/'*) result="$HOME/${result#\~/}" ;;
  esac
  expand_npmrc_value "$result"
}

default_npm_prefix() {
  local executable bin
  command_path executable npm 2>/dev/null || executable=""
  if [ -z "$executable" ]; then
    command_path executable node 2>/dev/null || executable=""
  fi
  [ -n "$executable" ] || return 1
  bin="${executable%/*}"
  case "$bin" in
    */bin) printf '%s' "${bin%/bin}" ;;
    *) printf '%s' "$bin" ;;
  esac
}

resolve_npm_cache() {
  local directory parent cache user_config global_config prefix
  if [ -n "${npm_config_cache:-}" ]; then
    printf '%s' "$npm_config_cache"
    return 0
  fi
  if [ -n "${NPM_CONFIG_CACHE:-}" ]; then
    printf '%s' "$NPM_CONFIG_CACHE"
    return 0
  fi

  directory="$PWD"
  while :; do
    capture_exact cache read_npmrc_value "$directory/.npmrc" cache \
      2>/dev/null || cache=""
    if [ -n "$cache" ]; then
      printf '%s' "$cache"
      return 0
    fi
    [ "$directory" = / ] && break
    parent="${directory%/*}"
    [ -n "$parent" ] || parent=/
    [ "$parent" = "$directory" ] && break
    directory="$parent"
  done

  user_config="${npm_config_userconfig:-${NPM_CONFIG_USERCONFIG:-$HOME/.npmrc}}"
  capture_exact cache read_npmrc_value "$user_config" cache \
    2>/dev/null || cache=""
  if [ -n "$cache" ]; then
    printf '%s' "$cache"
    return 0
  fi
  global_config="${npm_config_globalconfig:-${NPM_CONFIG_GLOBALCONFIG:-}}"
  if [ -z "$global_config" ]; then
    prefix="${npm_config_prefix:-${NPM_CONFIG_PREFIX:-}}"
    if [ -z "$prefix" ]; then
      capture_exact prefix read_npmrc_value "$user_config" prefix \
        2>/dev/null || prefix=""
    fi
    if [ -z "$prefix" ]; then
      capture_exact prefix default_npm_prefix 2>/dev/null || prefix=""
    fi
    [ -n "$prefix" ] && global_config="$prefix/etc/npmrc"
  fi
  capture_exact cache read_npmrc_value "$global_config" cache \
    2>/dev/null || cache=""
  if [ -n "$cache" ]; then
    printf '%s' "$cache"
    return 0
  fi
  case "$OS" in
    MINGW*|MSYS*|CYGWIN*)
      if [ -n "${LOCALAPPDATA:-}" ]; then
        printf '%s' "$LOCALAPPDATA/npm-cache"
        return 0
      fi
      ;;
  esac
  printf '%s' "$HOME/.npm"
}

resolve_hyperframes_bin() {
  local found cache candidate
  command_path found hyperframes 2>/dev/null || found=""
  if [ -n "$found" ]; then
    printf '%s' "$found"
    return 0
  fi
  if [ -x "$SKILL_ROOT/node_modules/.bin/hyperframes" ]; then
    printf '%s' "$SKILL_ROOT/node_modules/.bin/hyperframes"
    return 0
  fi
  if [ -x "./node_modules/.bin/hyperframes" ]; then
    printf '%s' "./node_modules/.bin/hyperframes"
    return 0
  fi
  capture_exact cache resolve_npm_cache
  for candidate in "$cache"/_npx/*/node_modules/.bin/hyperframes; do
    if [ -x "$candidate" ] \
      && "$candidate" --version >/dev/null 2>&1; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

find_chrome_shell() {
  local candidate cache
  if [ -n "${PUPPETEER_EXECUTABLE_PATH:-}" ] \
    && [ -x "${PUPPETEER_EXECUTABLE_PATH:-}" ]; then
    printf '%s' "$PUPPETEER_EXECUTABLE_PATH"
    return 0
  fi
  command_path candidate chrome-headless-shell 2>/dev/null || candidate=""
  if [ -n "$candidate" ]; then
    printf '%s' "$candidate"
    return 0
  fi
  cache="${PUPPETEER_CACHE_DIR:-$HOME/.cache/puppeteer}"
  for candidate in \
    "$cache"/chrome-headless-shell/*/*/chrome-headless-shell \
    "$cache"/chrome-headless-shell/*/chrome-headless-shell \
    "$cache"/chrome-headless-shell/*/*/chrome-headless-shell.exe \
    "$cache"/chrome-headless-shell/*/chrome-headless-shell.exe; do
    if [ -x "$candidate" ]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

whisper_available() {
  local hf
  if command -v whisper >/dev/null 2>&1; then
    return 0
  fi
  capture_exact hf resolve_hyperframes_bin 2>/dev/null || hf=""
  [ -n "$hf" ] && "$hf" transcribe --help >/dev/null 2>&1
}

# Evidence that a HeyGen credential exists on this machine, printed as a short
# human phrase. Presence only: this never contacts a provider, never runs the
# heygen CLI, and cannot tell a valid credential from an expired one. A project
# `.env` is deliberately not walked — the checker runs from an arbitrary cwd and
# a cwd-dependent answer is worse than an honest "not found here".
heygen_credential_source() {
  local path
  if [ -n "${HEYGEN_API_KEY:-}" ]; then
    printf 'HEYGEN_API_KEY is set'
    return 0
  fi
  if [ -n "${HYPERFRAMES_API_KEY:-}" ]; then
    printf 'HYPERFRAMES_API_KEY is set'
    return 0
  fi
  path="${HEYGEN_CONFIG_DIR:-$HOME/.heygen}/credentials"
  if [ -f "$path" ]; then
    printf 'stored credential at %s' "$path"
    return 0
  fi
  return 1
}

# ---------------------------------------------------------------------------
# Consent-scoped fixes. These are the only commands this script may execute
# that install or download anything.
# ---------------------------------------------------------------------------
run_selected_fixes() {
  local selected id
  selected="$FIX_IDS"
  [ -n "$selected" ] || return 0

  printf '%s--fix: applying only selected safe, user-scoped actions; sudo/system and environment commands will not run%s\n' \
    "$DIM" "$RST"
  local old_ifs="$IFS"
  IFS=','
  for id in $selected; do
    IFS="$old_ifs"
    case "$id" in
      chrome-shell)
        if find_chrome_shell >/dev/null 2>&1; then
          ok "chrome-shell already ready — no action needed"
        elif ! command -v npx >/dev/null 2>&1; then
          warn "chrome-shell fix not run — npx is unavailable"
          hint "reinstall Node.js >= 22.12 from https://nodejs.org/"
        else
          printf '  %sinstalling chrome-headless-shell…%s\n' "$DIM" "$RST"
          if npx --yes puppeteer browsers install chrome-headless-shell >/dev/null 2>&1; then
            ok "chrome-shell fix command completed"
          else
            warn "chrome-shell fix failed"
            hint "npx --yes puppeteer browsers install chrome-headless-shell"
          fi
        fi
        ;;
      hyperframes-skill)
        if find_skill_home hyperframes >/dev/null 2>&1; then
          ok "hyperframes skill already ready — no action needed"
        elif ! command -v npx >/dev/null 2>&1; then
          warn "hyperframes-skill fix not run — npx is unavailable"
          hint "reinstall Node.js >= 22.12 from https://nodejs.org/"
        else
          printf '  %sinstalling hyperframes skill…%s\n' "$DIM" "$RST"
          if npx --yes skills add heygen-com/hyperframes --global --yes \
            >/dev/null 2>&1; then
            ok "hyperframes-skill fix command completed"
          else
            warn "hyperframes-skill fix failed"
            hint "npx --yes skills add heygen-com/hyperframes --global --yes"
          fi
        fi
        ;;
      whisper)
        if whisper_available; then
          ok "Whisper timing verifier already ready — no action needed"
        elif ! command -v pip3 >/dev/null 2>&1; then
          warn "whisper fix not run — pip3 is unavailable"
          hint "install Python >= 3.10 from https://python.org/"
        else
          printf '  %sinstalling openai-whisper (pip --user)…%s\n' "$DIM" "$RST"
          if pip3 install --user openai-whisper >/dev/null 2>&1; then
            ok "whisper fix command completed"
          else
            warn "whisper fix failed"
            hint "pip3 install --user openai-whisper"
          fi
        fi
        ;;
    esac
    IFS=','
  done
  IFS="$old_ifs"
}

if [ "$FIX_REQUESTED" -eq 1 ]; then
  run_selected_fixes
fi

# ---------------------------------------------------------------------------
# Check collection. Parallel indexed arrays preserve arbitrary path characters
# without requiring associative arrays, which macOS Bash 3.2 lacks.
# ---------------------------------------------------------------------------
CHECK_COUNT=0
CHECK_IDS=()
CHECK_LABELS=()
CHECK_TIERS=()
CHECK_STATES=()
CHECK_PHASES=()
CHECK_DETAILS=()
CHECK_VERSIONS=()
CHECK_KINDS=()
CHECK_FIX_IDS=()
CHECK_COMMANDS=()
CHECK_GROUPS=()
CHECK_MESSAGES=()
HF_BIN=""

add_check() {
  local index="$CHECK_COUNT"
  CHECK_IDS[$index]="$1"
  CHECK_LABELS[$index]="$2"
  CHECK_TIERS[$index]="$3"
  CHECK_STATES[$index]="$4"
  CHECK_PHASES[$index]="$5"
  CHECK_DETAILS[$index]="$6"
  CHECK_VERSIONS[$index]="$7"
  CHECK_KINDS[$index]="$8"
  CHECK_FIX_IDS[$index]="$9"
  CHECK_COMMANDS[$index]="${10}"
  CHECK_GROUPS[$index]="${11}"
  CHECK_MESSAGES[$index]="${12}"
  CHECK_COUNT=$((CHECK_COUNT + 1))
}

load_check() {
  local index="$1"
  CURRENT_ID="${CHECK_IDS[$index]}"
  CURRENT_LABEL="${CHECK_LABELS[$index]}"
  CURRENT_TIER="${CHECK_TIERS[$index]}"
  CURRENT_STATE="${CHECK_STATES[$index]}"
  CURRENT_PHASES="${CHECK_PHASES[$index]}"
  CURRENT_DETAIL="${CHECK_DETAILS[$index]}"
  CURRENT_VERSION="${CHECK_VERSIONS[$index]}"
  CURRENT_KIND="${CHECK_KINDS[$index]}"
  CURRENT_FIX_ID="${CHECK_FIX_IDS[$index]}"
  CURRENT_COMMAND="${CHECK_COMMANDS[$index]}"
  CURRENT_GROUP="${CHECK_GROUPS[$index]}"
  CURRENT_MESSAGE="${CHECK_MESSAGES[$index]}"
}

ver_ge() {
  local have="$1" maj_min="$2" min_min="${3:-0}" hmaj hmin
  hmaj="${have%%.*}"
  case "$have" in
    *.*)
      hmin="${have#*.}"
      hmin="${hmin%%.*}"
      ;;
    *) hmin=0 ;;
  esac
  hmaj="${hmaj//[!0-9]/}"
  hmin="${hmin//[!0-9]/}"
  [ -n "$hmaj" ] || return 1
  [ "$hmaj" -gt "$maj_min" ] && return 0
  [ "$hmaj" -eq "$maj_min" ] && [ "${hmin:-0}" -ge "$min_min" ]
}

collect_checks() {
  local raw version path found a g t

  if command -v node >/dev/null 2>&1; then
    capture_line raw node --version 2>/dev/null || raw=""
    version="${raw#v}"
    if [ -n "$version" ] && ver_ge "$version" 22 12; then
      add_check node "Node.js" required ready "3,4,5" \
        "meets the >= 22.12 runtime requirement" "$version" manual-download "" \
        "Install Node.js >= 22.12 from https://nodejs.org/" Required \
        "Node.js $version"
    else
      add_check node "Node.js" required blocked "3,4,5" \
        "need >= 22.12 (hyperframes needs >= 22; chrome-devtools-mcp needs ^20.19 || ^22.12 || >=23)" \
        "$version" manual-download "" \
        "Install or upgrade Node.js to >= 22.12 from https://nodejs.org/" Required \
        "Node.js ${version:-unknown} — need >= 22.12 (hyperframes needs >= 22; chrome-devtools-mcp needs ^20.19 || ^22.12 || >=23)"
    fi
  else
    add_check node "Node.js" required blocked "3,4,5" "not found" "" \
      manual-download "" "Install Node.js >= 22.12 from https://nodejs.org/" \
      Required "Node.js — not found"
  fi

  if command -v npx >/dev/null 2>&1; then
    add_check npx "npx" required ready "3,4,5" \
      "available locally; report modes do not invoke it" "" manual-download "" \
      "Reinstall Node.js >= 22.12 from https://nodejs.org/ if npx is broken." \
      Required "npx"
  else
    add_check npx "npx" required blocked "3,4,5" \
      "not found (ships with Node.js/npm)" "" manual-download "" \
      "Reinstall Node.js >= 22.12 from https://nodejs.org/ (bundles npm/npx)." \
      Required "npx — not found (ships with Node/npm)"
  fi

  if command -v python3 >/dev/null 2>&1; then
    capture_line raw python3 --version 2>/dev/null || raw=""
    version="${raw#Python }"
    if [ -n "$version" ] && ver_ge "$version" 3 10; then
      add_check python "Python" required ready "2,5" \
        "meets the >= 3.10 helper-script requirement" "$version" manual-download "" \
        "Install Python >= 3.10 from https://python.org/" Required \
        "Python $version"
    else
      add_check python "Python" required blocked "2,5" "need >= 3.10" \
        "$version" manual-download "" \
        "Install or upgrade Python to >= 3.10 from https://python.org/" Required \
        "Python ${version:-unknown} — need >= 3.10"
    fi
  else
    add_check python "Python" required blocked "2,5" "not found" "" \
      manual-download "" "Install Python >= 3.10 from https://python.org/" \
      Required "Python 3 — not found"
  fi

  if command -v ffmpeg >/dev/null 2>&1; then
    command_path path ffmpeg
    add_check ffmpeg "ffmpeg" required ready "2,5" "found at $path" "" \
      manual-system "" "$FFMPEG_COMMAND" Required "ffmpeg"
  else
    add_check ffmpeg "ffmpeg" required blocked "2,5" "not found" "" \
      manual-system "" "$FFMPEG_COMMAND" Required "ffmpeg — not found"
  fi

  if command -v ffprobe >/dev/null 2>&1; then
    command_path path ffprobe
    add_check ffprobe "ffprobe" required ready "2,5" "found at $path" "" \
      manual-system "" "$FFMPEG_COMMAND" Required "ffprobe"
  else
    add_check ffprobe "ffprobe" required blocked "2,5" "not found" "" \
      manual-system "" "$FFMPEG_COMMAND" Required "ffprobe — not found"
  fi

  capture_exact path find_chrome_shell 2>/dev/null || path=""
  if [ -n "$path" ]; then
    add_check chrome-shell "chrome-headless-shell" required ready "3,4,5" \
      "found locally at $path; no online doctor probe was used" "" safe-user \
      chrome-shell "npx --yes puppeteer browsers install chrome-headless-shell" \
      Required "chrome-headless-shell (local)"
  else
    add_check chrome-shell "chrome-headless-shell" required blocked "3,4,5" \
      "not found in PATH, PUPPETEER_EXECUTABLE_PATH, or the local Puppeteer cache" "" \
      safe-user chrome-shell \
      "npx --yes puppeteer browsers install chrome-headless-shell" Required \
      "chrome-headless-shell — not found locally"
  fi

  capture_exact HF_BIN resolve_hyperframes_bin 2>/dev/null || HF_BIN=""
  if [ -n "$HF_BIN" ]; then
    capture_line version "$HF_BIN" --version 2>/dev/null || version=""
    if [ -n "$version" ]; then
      add_check hyperframes-cli "hyperframes CLI" required ready "3,4,5" \
        "installed locally at $HF_BIN; report modes never fetch it with npx" "$version" \
        manual-online "" "npm install --global hyperframes" Required \
        "hyperframes CLI ($version)"
    else
      add_check hyperframes-cli "hyperframes CLI" required blocked "3,4,5" \
        "local binary at $HF_BIN failed its --version check" "" manual-online "" \
        "npm install --global hyperframes" Required \
        "hyperframes CLI — local binary failed"
    fi
  else
    add_check hyperframes-cli "hyperframes CLI" required blocked "3,4,5" \
      "not found in PATH, local node_modules/.bin, or the npm execution cache; no online npx probe was used" "" \
      manual-online "" "npm install --global hyperframes" Required \
      "hyperframes CLI — not installed locally"
  fi

  capture_exact found find_skill_home hyperframes 2>/dev/null || found=""
  if [ -n "$found" ]; then
    add_check hyperframes-skill "hyperframes skill" required ready "3,4" \
      "found in $found" "" safe-user hyperframes-skill \
      "npx --yes skills add heygen-com/hyperframes --global --yes" \
      "Companion skills (required for Phases 3–4)" \
      "hyperframes skill ($found)"
  else
    add_check hyperframes-skill "hyperframes skill" required blocked "3,4" \
      "not found in any canonical skill home" "" safe-user hyperframes-skill \
      "npx --yes skills add heygen-com/hyperframes --global --yes" \
      "Companion skills (required for Phases 3–4)" \
      "hyperframes skill — not found"
  fi

  capture_exact found find_skill_home gsap 2>/dev/null || found=""
  if [ -n "$found" ]; then
    add_check gsap-skill "gsap skill" recommended ready "3,4" \
      "found in $found" "" none "" \
      "No separate install is required when GSAP guidance is bundled with hyperframes." \
      "Companion skills (required for Phases 3–4)" "gsap skill ($found)"
  else
    add_check gsap-skill "gsap skill" recommended degraded "3,4" \
      "not found as a standalone skill; hyperframes includes GSAP guidance" "" none "" \
      "No separate install is required; use the GSAP guidance bundled with the hyperframes skill." \
      "Companion skills (required for Phases 3–4)" \
      "gsap skill — not found (recommended)"
  fi

  capture_exact found find_skill_home media-use 2>/dev/null || found=""
  if [ -n "$found" ]; then
    add_check media-use-skill "media-use skill" recommended ready "5" \
      "found in $found; the delegated audio engine (voiceover, music bed, and effects in one request, with word timestamps) is available" \
      "" manual-online "" \
      "npx --yes skills add heygen-com/hyperframes --global --yes" \
      "Companion skills (Phase 5 audio)" "media-use skill ($found)"
  else
    add_check media-use-skill "media-use skill" recommended degraded "5" \
      "not found in any canonical skill home; Phase 5 falls back to the deprecated scripts/generate_voiceover.py and scripts/search_music.py" \
      "" manual-online "" \
      "npx --yes skills add heygen-com/hyperframes --global --yes" \
      "Companion skills (Phase 5 audio)" \
      "media-use skill — not found (Phase 5 falls back to the deprecated local audio scripts)"
  fi

  capture_exact found heygen_credential_source 2>/dev/null || found=""
  if [ -n "$found" ]; then
    add_check heygen-credential "HeyGen credential" recommended ready "5" \
      "$found; validity and provider reachability are never probed in report modes" \
      "" manual-download "" \
      "Sign in with: heygen auth login --oauth" Recommended \
      "HeyGen credential found ($found; not verified against the provider)"
  elif command -v heygen >/dev/null 2>&1; then
    command_path path heygen
    add_check heygen-credential "HeyGen credential" recommended degraded "5" \
      "heygen CLI found at $path but no credential is visible in the environment or the credential file; the delegated engine cannot use its free TTS/music/effects path" \
      "" manual-download "" \
      "Sign in with: heygen auth login --oauth" Recommended \
      "HeyGen CLI found but no credential — run: heygen auth login --oauth"
  else
    add_check heygen-credential "HeyGen credential" recommended degraded "5" \
      "no heygen CLI and no stored credential; the delegated audio engine skips its first TTS route and has no catalog music/effects retrieval" \
      "" manual-download "" \
      "Install the HeyGen CLI (https://developers.heygen.com/cli), then sign in with: heygen auth login --oauth" \
      Recommended \
      "HeyGen credential not found — delegated TTS falls back to ElevenLabs, then to local Kokoro on explicit confirmation"
  fi

  if [ -n "${ELEVENLABS_API_KEY:-}" ] || [ -n "${ELEVEN_LABS_API_KEY:-}" ]; then
    add_check elevenlabs-key "ELEVENLABS_API_KEY" recommended ready "5" \
      "set; it serves both the delegated audio engine's ElevenLabs TTS route and the deprecated scripts/generate_voiceover.py fallback" \
      "" manual-env "" "export ELEVENLABS_API_KEY=<key>" Recommended \
      "ELEVENLABS_API_KEY set (ElevenLabs TTS route, delegated or local)"
  else
    add_check elevenlabs-key "ELEVENLABS_API_KEY" recommended degraded "5" \
      "not set; the delegated audio engine skips its ElevenLabs route and scripts/generate_voiceover.py cannot run" "" \
      manual-env "" "export ELEVENLABS_API_KEY=<key>" Recommended \
      "ELEVENLABS_API_KEY not set — ElevenLabs voices unavailable; choose Kokoro explicitly for local TTS or configure the key"
  fi

  if command -v whisper >/dev/null 2>&1; then
    add_check whisper "Whisper timing verifier" recommended ready "5" \
      "standalone whisper is available" "" safe-user whisper \
      "pip3 install --user openai-whisper" Recommended \
      "whisper (voiceover timing verification)"
  elif [ -n "$HF_BIN" ] && "$HF_BIN" transcribe --help >/dev/null 2>&1; then
    add_check whisper "Whisper timing verifier" recommended ready "5" \
      "hyperframes transcribe is available; standalone whisper is optional" "" \
      safe-user whisper "pip3 install --user openai-whisper" Recommended \
      "hyperframes transcribe (preferred timing verifier; standalone whisper optional)"
  else
    add_check whisper "Whisper timing verifier" recommended degraded "5" \
      "not found; voiceover timing verification is degraded" "" safe-user whisper \
      "pip3 install --user openai-whisper" Recommended \
      "whisper not found (recommended for VO timing)"
  fi

  if [ -n "${FREESOUND_API_KEY:-}" ]; then
    add_check freesound-key "FREESOUND_API_KEY" optional ready "5" \
      "set; the deprecated scripts/search_music.py fallback can search Creative Commons music" \
      "" manual-env "" "export FREESOUND_API_KEY=<key>" Optional \
      "FREESOUND_API_KEY set (deprecated Creative Commons music fallback)"
  else
    add_check freesound-key "FREESOUND_API_KEY" optional degraded "5" \
      "not set; only the deprecated Freesound fallback is unavailable — delegated music retrieval and user-provided tracks are unaffected" "" \
      manual-env "" "export FREESOUND_API_KEY=<key>" Optional \
      "FREESOUND_API_KEY not set — deprecated Freesound fallback unavailable (delegated music and user-provided tracks still work)"
  fi

  if command -v espeak-ng >/dev/null 2>&1; then
    add_check espeak-ng "espeak-ng" optional ready "5" \
      "non-English local Kokoro TTS is available" "" manual-system "" \
      "$ESPEAK_COMMAND" Optional "espeak-ng (non-English Kokoro tts)"
  else
    add_check espeak-ng "espeak-ng" optional degraded "5" \
      "not found; only needed for non-English voiceover via confirmed local Kokoro TTS" "" \
      manual-system "" "$ESPEAK_COMMAND" Optional \
      "espeak-ng not found — only needed for non-English voiceover via Kokoro TTS"
  fi

  command_path a asciinema 2>/dev/null || a=""
  command_path g agg 2>/dev/null || g=""
  command_path t timeout 2>/dev/null || t=""
  if [ -n "$a" ] && [ -n "$g" ] && [ -n "$t" ]; then
    add_check terminal-capture "asciinema + agg + timeout" optional ready "2" \
      "real terminal-clip path is available" "" manual-system "" \
      "$TERMINAL_COMMAND" Optional \
      "asciinema + agg + timeout (real terminal-clip path)"
  else
    add_check terminal-capture "asciinema + agg + timeout" optional degraded "2" \
      "incomplete; CLI scenes use the authored-terminal path" "" manual-system "" \
      "$TERMINAL_COMMAND" Optional \
      "asciinema/agg/timeout incomplete — CLI scenes use the authored-terminal path"
  fi

  if [ "$IS_WSL" -eq 1 ]; then
    if command -v docker >/dev/null 2>&1; then
      add_check docker-wsl "Docker CLI on WSL" optional ready "4,5" \
        "client found locally; report modes do not contact the daemon" "" \
        manual-system "" \
        "npx hyperframes render . --output out/final.mp4 --docker" Optional \
        "Docker CLI found (daemon not probed; use: npx hyperframes render … --docker)"
    else
      add_check docker-wsl "Docker CLI on WSL" optional degraded "4,5" \
        "client not found; native WSL rendering can fail at Page.captureScreenshot" "" \
        manual-system "" \
        "Start Docker Desktop, then run: npx hyperframes render . --output out/final.mp4 --docker" \
        Optional \
        "Docker CLI not found — on WSL native render can fail at Page.captureScreenshot"
    fi
  fi
}

collect_checks

READY_COUNT=0
DEGRADED_COUNT=0
BLOCKED_COUNT=0
REQUIRED_BLOCKED=0
OVERALL_STATE="ready"

calculate_summary() {
  local index
  READY_COUNT=0
  DEGRADED_COUNT=0
  BLOCKED_COUNT=0
  REQUIRED_BLOCKED=0
  for ((index = 0; index < CHECK_COUNT; index++)); do
    load_check "$index"
    case "$CURRENT_STATE" in
      ready) READY_COUNT=$((READY_COUNT + 1)) ;;
      degraded) DEGRADED_COUNT=$((DEGRADED_COUNT + 1)) ;;
      blocked)
        BLOCKED_COUNT=$((BLOCKED_COUNT + 1))
        [ "$CURRENT_TIER" = required ] \
          && REQUIRED_BLOCKED=$((REQUIRED_BLOCKED + 1))
        ;;
    esac
  done
  if [ "$REQUIRED_BLOCKED" -gt 0 ]; then
    OVERALL_STATE="blocked"
  elif [ "$DEGRADED_COUNT" -gt 0 ]; then
    OVERALL_STATE="degraded"
  else
    OVERALL_STATE="ready"
  fi
}

json_quote() {
  local value="${1-}" code octal control escape
  value=${value//\\/\\\\}
  value=${value//\"/\\\"}
  for ((code = 1; code <= 31; code++)); do
    printf -v octal '%03o' "$code"
    printf -v control '%b' "\\$octal"
    printf -v escape '\\u%04x' "$code"
    value="${value//$control/$escape}"
  done
  printf '"%s"' "$value"
}

json_nullable() {
  if [ -n "${1-}" ]; then
    json_quote "$1"
  else
    printf 'null'
  fi
}

json_phases() {
  local phases="$1" phase old_ifs="$IFS" first=1
  printf '['
  IFS=','
  for phase in $phases; do
    if [ "$first" -eq 0 ]; then printf ','; fi
    printf '%s' "$phase"
    first=0
  done
  IFS="$old_ifs"
  printf ']'
}

render_json() {
  local first=1 index
  calculate_summary
  printf '{\n'
  printf '  "schema_version": 1,\n'
  printf '  "platform": '
  json_quote "$PLATFORM"
  printf ',\n'
  printf '  "summary": {"state": '
  json_quote "$OVERALL_STATE"
  printf ', "ready": %s, "degraded": %s, "blocked": %s, "required_blocked": %s},\n' \
    "$READY_COUNT" "$DEGRADED_COUNT" "$BLOCKED_COUNT" "$REQUIRED_BLOCKED"
  printf '  "checks": [\n'
  for ((index = 0; index < CHECK_COUNT; index++)); do
    load_check "$index"
    if [ "$first" -eq 0 ]; then printf ',\n'; fi
    printf '    {\n'
    printf '      "id": '; json_quote "$CURRENT_ID"; printf ',\n'
    printf '      "label": '; json_quote "$CURRENT_LABEL"; printf ',\n'
    printf '      "tier": '; json_quote "$CURRENT_TIER"; printf ',\n'
    printf '      "state": '; json_quote "$CURRENT_STATE"; printf ',\n'
    printf '      "phases": '; json_phases "$CURRENT_PHASES"; printf ',\n'
    printf '      "detail": '; json_quote "$CURRENT_DETAIL"; printf ',\n'
    printf '      "version": '; json_nullable "$CURRENT_VERSION"; printf ',\n'
    printf '      "fixability": {"kind": '; json_quote "$CURRENT_KIND"
    printf ', "id": '; json_nullable "$CURRENT_FIX_ID"
    printf ', "command": '; json_nullable "$CURRENT_COMMAND"
    printf '}\n'
    printf '    }'
    first=0
  done
  printf '\n  ]\n'
  printf '}\n'
}

render_plan() {
  local phase_text index
  calculate_summary
  printf 'hve-video-director Setup plan (%s)\n' "$PLATFORM"
  printf 'No changes will be made.\n'
  for ((index = 0; index < CHECK_COUNT; index++)); do
    load_check "$index"
    [ "$CURRENT_STATE" = ready ] && continue
    phase_text="${CURRENT_PHASES//,/\, }"
    printf '\n%s [%s] %s (Phases %s)\n' \
      "$CURRENT_STATE" "$CURRENT_TIER" "$CURRENT_LABEL" "$phase_text"
    printf '  %s\n' "$CURRENT_DETAIL"
    if [ -n "$CURRENT_FIX_ID" ]; then
      printf '  Safe fix ID: %s\n' "$CURRENT_FIX_ID"
    fi
    if [ -n "$CURRENT_COMMAND" ]; then
      printf '  Exact action: %s\n' "$CURRENT_COMMAND"
    fi
  done
  printf '\nSummary: %s (%s blocked required check%s).\n' \
    "$OVERALL_STATE" "$REQUIRED_BLOCKED" \
    "$([ "$REQUIRED_BLOCKED" -eq 1 ] && printf '' || printf 's')"
}

render_human() {
  local last_group="" index
  calculate_summary
  printf '%shve-video-director requirements check%s  (%s%s%s)\n' \
    "$BOLD" "$RST" "$DIM" "$PLATFORM" "$RST"
  for ((index = 0; index < CHECK_COUNT; index++)); do
    load_check "$index"
    if [ "$CURRENT_GROUP" != "$last_group" ]; then
      section "$CURRENT_GROUP"
      last_group="$CURRENT_GROUP"
    fi
    case "$CURRENT_STATE" in
      ready) ok "$CURRENT_MESSAGE" ;;
      degraded) warn "$CURRENT_MESSAGE" ;;
      blocked) bad "$CURRENT_MESSAGE" ;;
    esac
    if [ "$CURRENT_STATE" != ready ] && [ -n "$CURRENT_COMMAND" ]; then
      hint "$CURRENT_COMMAND"
    fi
  done

  printf '\n'
  if [ "$REQUIRED_BLOCKED" -eq 0 ]; then
    printf '%s%s✓ All required dependencies satisfied.%s\n' "$BOLD" "$GRN" "$RST"
    [ "$FIX_REQUESTED" -eq 0 ] && printf '%s  Use --plan for exact missing actions, or --fix/--fix=<id,id> for consented safe fixes.%s\n' \
      "$DIM" "$RST"
  else
    printf '%s%s✗ Missing required dependencies (see ✗ above).%s\n' \
      "$BOLD" "$RED" "$RST"
    [ "$FIX_REQUESTED" -eq 0 ] && printf '%s  Use --plan for exact actions; --fix only runs safe user-scoped fixes and never sudo/system/env commands.%s\n' \
      "$DIM" "$RST"
  fi
}

case "$MODE" in
  json) render_json ;;
  plan) render_plan ;;
  human) render_human ;;
esac

calculate_summary
[ "$REQUIRED_BLOCKED" -eq 0 ]
