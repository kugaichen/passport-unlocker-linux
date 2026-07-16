#!/bin/sh
set -u

log_file=$(mktemp)
trap 'rm -f "$log_file"' EXIT HUP INT TERM

status=0
GSK_RENDERER=${GSK_RENDERER:-cairo} \
    timeout 5s passport-unlocker-gui "$@" >"$log_file" 2>&1 || status=$?

cat "$log_file"
if grep -q '^Traceback (most recent call last):' "$log_file"; then
    echo "GUI_TRACEBACK_FAIL"
    exit 1
fi

case "$status" in
    124)
        echo "GUI_TIMEOUT_PASS"
        ;;
    0)
        echo "GUI_EXITED_CLEANLY"
        ;;
    *)
        echo "GUI_EXIT_$status"
        exit "$status"
        ;;
esac
