#!/usr/bin/env bash
#
# Everything CI's Linux job checks, in one command, before you push.
#
# WHY THIS EXISTS: the checks were a list you had to remember, and the list
# had grown to nine items across two languages and three engine lifecycles.
# A push landed on main with green pytest, green tsc, a green bundle and
# four green browser probes -- and a red build, because the golden replay
# was the one item not run. Nothing about that failure was subtle; it was
# simply not on the list in anyone's head. So the list lives here now.
#
# Windows and macOS installer builds are NOT here and cannot be: this
# container can't cross-compile either target. Those two jobs are the only
# things a push should ever discover, and they only run on main.
#
# Usage:  scripts/local-gate.sh            # everything
#         scripts/local-gate.sh --fast     # skip the browser probes (~2 min faster)
#
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$REPO/engine/.venv/bin/python"
FAST=0
[[ "${1:-}" == "--fast" ]] && FAST=1

FAILED=()
step() { printf '\n\033[1m── %s\033[0m\n' "$1"; }
check() { if [[ $1 -eq 0 ]]; then printf '   \033[32mPASS\033[0m  %s\n' "$2"; else printf '   \033[31mFAIL\033[0m  %s\n' "$2"; FAILED+=("$2"); fi; }

[[ -x "$PY" ]] || { echo "no engine venv at $PY -- create it first"; exit 1; }

# The engine owns the project store, so its root has to be set on the
# ENGINE process, not on whatever talks to it. Both engines below are
# started on throwaway roots so a previous run's projects can't collide
# (a leftover project makes /project/create 409 and every scenario abort
# before it runs a single step, which reads as 269 diffs rather than as
# "the store was dirty").
EVAL_ROOT="$(mktemp -d)"
PROBE_ROOT="$(mktemp -d)"
ENGINE_PIDS=()
cleanup() {
  for pid in "${ENGINE_PIDS[@]:-}"; do kill "$pid" 2>/dev/null || true; done
  rm -rf "$EVAL_ROOT" "$PROBE_ROOT"
}
trap cleanup EXIT

# NOT called in a subshell, deliberately. `ENGINE_PIDS+=($!)` inside
# `( ... )` records the pid in a child that then exits, so cleanup has
# nothing to kill and the engine outlives the run. The next run's engine
# then cannot bind, the probes talk to the STALE one, and its projects root
# was deleted by the previous run's trap -- so every probe 404s and the
# failure looks like a broken app rather than a leaked process. Cost me a
# full gate run to work out.
start_engine() { # port, projects_root, logfile
  if curl -sf "http://127.0.0.1:$1/health" >/dev/null 2>&1; then
    echo "port $1 already has an engine on it -- refusing to run against something this script"
    echo "did not start (its projects root is unknown). Stop it first: pkill -f sigma_engine.main"
    return 1
  fi
  (cd "$REPO/engine" && SIGMA_PROJECTS_ROOT="$2" exec "$PY" -m sigma_engine.main --port "$1") > "$3" 2>&1 &
  ENGINE_PIDS+=($!)
  for _ in $(seq 1 40); do
    curl -sf "http://127.0.0.1:$1/health" >/dev/null 2>&1 && return 0
    sleep 0.5
  done
  echo "engine on $1 never came up; log:"; tail -20 "$3"; return 1
}

step "Engine tests"
(cd "$REPO/engine" && "$PY" -m pytest -q 2>&1 | tail -3)
check ${PIPESTATUS[0]} "pytest"

step "Golden-scenario replay (267 steps, 3 scenarios)"
if start_engine 8000 "$EVAL_ROOT" /tmp/local-gate-eval-engine.log; then
  "$PY" "$REPO/evals/harness/run_goldens.py" 2>&1 | tail -6
  check ${PIPESTATUS[0]} "golden replay"
else
  check 1 "golden replay (engine failed to start)"
fi

step "Frontend typecheck + production bundle"
(cd "$REPO/desktop" && npx tsc --noEmit)
check $? "tsc --noEmit"
(cd "$REPO/desktop" && npm run build > /tmp/local-gate-build.log 2>&1)
check $? "vite build"

if [[ $FAST -eq 1 ]]; then
  printf '\n   (browser probes skipped: --fast)\n'
else
  step "Browser probes (packaged-origin condition)"
  unzip -qo "$REPO/examples/coffee-bar-example-project.zip" -d "$PROBE_ROOT"
  # Assert the staging worked before blaming the app: every probe opens this
  # project, so a missing unzip makes all four fail with a 404 that looks
  # like a product bug.
  if [[ ! -f "$PROBE_ROOT/coffee-bar-example/project.json" ]]; then
    check 1 "staging the worked example into $PROBE_ROOT"
  elif start_engine 8756 "$PROBE_ROOT" /tmp/local-gate-probe-engine.log; then
    for probe in xorigin example-project export-project tool-report ondisk-projects; do
      (cd "$REPO/desktop" && node "tools/$probe-probe.mjs" > "/tmp/local-gate-$probe.log" 2>&1)
      check $? "$probe-probe  (log: /tmp/local-gate-$probe.log)"
    done
  else
    check 1 "browser probes (engine failed to start)"
  fi
fi

printf '\n════════════════════════════════════════\n'
if [[ ${#FAILED[@]} -eq 0 ]]; then
  printf '\033[32mLOCAL GATE: PASS\033[0m — safe to push.\n'
  printf 'Still only provable in CI: the Windows and macOS installer builds.\n'
  exit 0
fi
printf '\033[31mLOCAL GATE: FAIL\033[0m — %d check(s):\n' "${#FAILED[@]}"
printf '  · %s\n' "${FAILED[@]}"
exit 1
