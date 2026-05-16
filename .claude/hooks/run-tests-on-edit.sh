#!/usr/bin/env bash
# PostToolUse hook — runs the layer-specific test suite after Edit/Write
# on a matching path. Wired up in .claude/settings.json per ADR-0007.
#
# Contract:
# - Reads the originating tool call as JSON on stdin; extracts file_path.
# - Dispatches by path under backend/src, frontend/src, database/config.
# - Tests run inside dc-plc-datalink-rfc1006-test.yml containers — never
#   on the host (project convention: no local venv).
# - Skips quietly when the matching test image is not built yet so a
#   developer who has not run `docker compose build` is not surprised by
#   long first-time builds.
# - Always exits 0 — hooks are advisory per ADR-0007. Test output goes
#   to stderr where the harness surfaces it back to Claude.

set -uo pipefail

# stdin is expected to be JSON; tolerate missing jq or non-JSON input.
file=""
if command -v jq >/dev/null 2>&1; then
  file=$(jq -r '.tool_input.file_path // empty' 2>/dev/null || true)
fi
[ -z "$file" ] && exit 0

# Resolve repo root — hooks fire with cwd somewhere under the project,
# but explicitly cd'ing keeps the docker-compose -f path stable.
repo_root="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$repo_root" 2>/dev/null || exit 0

COMPOSE_FILE="dc-plc-datalink-rfc1006-test.yml"
[ -f "$COMPOSE_FILE" ] || exit 0

run_in_container() {
  local image="$1"; shift
  local service="$1"; shift
  if ! docker image inspect "$image" >/dev/null 2>&1; then
    echo "[hook] $image not built — skipping. Run:" >&2
    echo "         docker compose -f $COMPOSE_FILE build $service" >&2
    return 0
  fi
  echo "[hook] $service: running tests…" >&2
  docker compose -f "$COMPOSE_FILE" run --rm "$service" "$@" 2>&1 | tail -10 >&2
}

case "$file" in
  */backend/src/*|*/backend/config/*)
    run_in_container plc-datalink-rfc1006-backend-test:dev backend-test \
      pytest -q -m "not integration" test/scripts
    ;;
  */frontend/src/*)
    run_in_container plc-datalink-rfc1006-frontend-test:dev frontend-test
    ;;
  */database/config/*)
    run_in_container plc-datalink-rfc1006-database-test:dev database-test
    ;;
esac

exit 0
