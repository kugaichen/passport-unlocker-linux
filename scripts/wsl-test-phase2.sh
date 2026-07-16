#!/bin/sh
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
RUFF_BIN=${RUFF_BIN:-"$HOME/.cache/passport-unlocker-tools/bin/ruff"}
cd "$PROJECT_ROOT" || exit 1

failures=0

section() {
    printf '\n=== %s ===\n' "$1"
}

run_check() {
    name=$1
    shift
    if "$@"; then
        printf 'RESULT %s=PASS\n' "$name"
    else
        printf 'RESULT %s=FAIL\n' "$name"
        failures=$((failures + 1))
    fi
}

section "Ruff"
if [ -x "$RUFF_BIN" ]; then
    run_check ruff "$RUFF_BIN" check .
else
    printf 'Ruff executable not found: %s\n' "$RUFF_BIN"
    printf 'RESULT ruff=FAIL\n'
    failures=$((failures + 1))
fi

section "Mypy core and helper"
run_check mypy mypy src/passport_unlocker/core src/passport_unlocker/helper

section "Pytest"
run_check pytest env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q

section "Desktop entries"
run_check desktop_main desktop-file-validate data/io.github.kugaichen.PassportUnlocker.desktop
run_check desktop_autostart desktop-file-validate data/autostart/io.github.kugaichen.PassportUnlocker.Monitor.desktop

section "AppStream metadata"
run_check appstream appstreamcli validate --no-net data/io.github.kugaichen.PassportUnlocker.metainfo.xml

section "Debian build dependencies"
run_check build_deps dpkg-checkbuilddeps

section "CLI smoke test"
run_check cli_version env PYTHONPATH=src python3 -m passport_unlocker.cli.main --version
run_check device_discovery env PYTHONPATH=src python3 -c 'from passport_unlocker.devices.discovery import list_candidate_devices; devices=list_candidate_devices(); print("Candidate devices:", len(devices)); [print(d.display_name, d.serial_suffix) for d in devices]'

section "Summary"
printf 'FAILURES=%s\n' "$failures"
if [ "$failures" -eq 0 ]; then
    printf 'PHASE2=PASS\n'
    exit 0
fi
printf 'PHASE2=FAIL\n'
exit 1
