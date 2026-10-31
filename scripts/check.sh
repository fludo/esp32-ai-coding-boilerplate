#!/usr/bin/env bash
# Authoritative quality gate: format, static analysis, host tests, firmware builds.
#
#   scripts/check.sh            # all phases, all board environments
#   scripts/check.sh --quick    # all phases, default environment only
#   scripts/check.sh -e <env>   # all phases, one board environment (repeatable)
#   scripts/check.sh --fix      # apply clang-format instead of only checking it
#
# Exits non-zero on the first failing phase. On-target tests are not run here:
# they need a board (pio test -e <env>).
set -euo pipefail

cd "$(dirname "$0")/.."

if command -v pio >/dev/null 2>&1; then
  PIO=pio
elif [ -x "$HOME/.platformio/penv/bin/pio" ]; then
  PIO="$HOME/.platformio/penv/bin/pio"
else
  echo "error: PlatformIO CLI (pio) not found; install it or add ~/.platformio/penv/bin to PATH" >&2
  exit 127
fi

ENVS=()
QUICK=0
FIX=0
while [ $# -gt 0 ]; do
  case "$1" in
    --quick) QUICK=1 ;;
    --fix) FIX=1 ;;
    -e) shift; ENVS+=("$1") ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

# Board environments = every [env:...] except native, unless narrowed.
if [ ${#ENVS[@]} -eq 0 ]; then
  if [ $QUICK -eq 1 ]; then
    ENVS=("$(sed -n 's/^default_envs *= *//p' platformio.ini | cut -d, -f1 | tr -d ' ')")
  else
    mapfile -t ENVS < <(sed -n 's/^\[env:\(.*\)\]$/\1/p' platformio.ini | grep -vx native)
  fi
fi

phase() { printf '\n=== %s ===\n' "$1"; }

SOURCES=$(git ls-files -co --exclude-standard -- 'src/*' 'lib/*' 'include/*' 'test/*' 2>/dev/null \
  | grep -E '\.(c|cc|cpp|h|hpp)$' || true)
if [ -z "$SOURCES" ]; then
  SOURCES=$(find src lib include test -type f \( -name '*.c' -o -name '*.cpp' -o -name '*.h' -o -name '*.hpp' \) 2>/dev/null)
fi

phase "1/4 format (clang-format)"
if command -v clang-format >/dev/null 2>&1; then
  if [ $FIX -eq 1 ]; then
    echo "$SOURCES" | xargs clang-format -i
    echo "formatted"
  else
    echo "$SOURCES" | xargs clang-format --dry-run --Werror
    echo "ok"
  fi
else
  echo "skipped: clang-format not installed"
fi

phase "2/4 static analysis (pio check)"
for env in "${ENVS[@]}"; do
  "$PIO" check -e "$env" --skip-packages --fail-on-defect=medium --fail-on-defect=high
done

phase "3/4 host tests (pio test -e native)"
"$PIO" test -e native

phase "4/4 firmware build (pio run)"
for env in "${ENVS[@]}"; do
  "$PIO" run -e "$env"
done

printf '\nAll checks passed for: %s\n' "${ENVS[*]}"
