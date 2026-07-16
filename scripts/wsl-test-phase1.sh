#!/bin/sh
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
cd "$PROJECT_ROOT" || exit 1

failures=0

section() {
    printf '\n=== %s ===\n' "$1"
}

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        printf 'FOUND %-24s %s\n' "$1" "$(command -v "$1")"
    else
        printf 'MISSING %s\n' "$1"
    fi
}

section "Environment"
cat /etc/os-release
uname -a
python3 --version
printf 'PROJECT_ROOT=%s\n' "$PROJECT_ROOT"

section "Python unit tests"
if PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v; then
    printf 'RESULT unit_tests=PASS\n'
else
    printf 'RESULT unit_tests=FAIL\n'
    failures=$((failures + 1))
fi

section "Python syntax"
if python3 -c 'import ast,pathlib; files=list(pathlib.Path("src").rglob("*.py"))+list(pathlib.Path("tests").rglob("*.py")); [ast.parse(p.read_text(encoding="utf-8"), filename=str(p)) for p in files]; print("Parsed", len(files), "Python files")'; then
    printf 'RESULT python_syntax=PASS\n'
else
    printf 'RESULT python_syntax=FAIL\n'
    failures=$((failures + 1))
fi

section "XML metadata"
if python3 -c 'import pathlib,xml.etree.ElementTree as E; [E.parse(p) for p in pathlib.Path("data").glob("*.xml")]; E.parse("data/io.github.kugaichen.PassportUnlocker.policy"); E.parse("data/io.github.kugaichen.PassportUnlocker.svg"); print("XML metadata parsed")'; then
    printf 'RESULT xml_metadata=PASS\n'
else
    printf 'RESULT xml_metadata=FAIL\n'
    failures=$((failures + 1))
fi

section "Production safety scan"
pattern='shell[[:space:]]*=[[:space:]]*True|os\.system|--password|0xE[23]|secure_erase|change_pass|reset_key|mkfs|fdisk|parted|wipefs|MODE=.0666|GROUP=.disk|/dev/sda|except[[:space:]]*:|sys\.exit'
if grep -REn "$pattern" src; then
    printf 'RESULT safety_scan=FAIL\n'
    failures=$((failures + 1))
else
    printf 'RESULT safety_scan=PASS\n'
fi

section "Runtime modules"
if python3 -c 'import importlib.metadata; import pyudev; print("pyudev", importlib.metadata.version("pyudev"))' 2>&1; then
    printf 'RESULT pyudev=AVAILABLE\n'
else
    printf 'RESULT pyudev=MISSING\n'
fi
if python3 -c 'import gi; gi.require_version("Gtk", "4.0"); gi.require_version("Adw", "1"); from gi.repository import Gtk,Adw; print("GTK/Adw imports OK")' 2>&1; then
    printf 'RESULT gtk_adw=AVAILABLE\n'
else
    printf 'RESULT gtk_adw=MISSING\n'
fi

section "Build and validation commands"
for command_name in dpkg-buildpackage desktop-file-validate appstreamcli ruff mypy pytest; do
    check_command "$command_name"
done

section "Summary"
printf 'FAILURES=%s\n' "$failures"
if [ "$failures" -eq 0 ]; then
    printf 'PHASE1=PASS\n'
    exit 0
fi
printf 'PHASE1=FAIL\n'
exit 1
