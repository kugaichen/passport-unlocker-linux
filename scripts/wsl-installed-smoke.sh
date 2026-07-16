#!/bin/sh
set -eu

dpkg-query -W -f='${db:Status-Status} ${Version}\n' passport-unlocker
passport-unlocker --version
passport-unlocker list
python3 -c 'import passport_unlocker; print(passport_unlocker.__version__)'

desktop-file-validate \
    /usr/share/applications/io.github.kugaichen.PassportUnlocker.desktop \
    /etc/xdg/autostart/io.github.kugaichen.PassportUnlocker.Monitor.desktop

test -x /usr/libexec/passport-unlocker-helper
test "$(readlink -f /usr/libexec/passport-unlocker-helper)" = \
    /usr/bin/passport-unlocker-helper

pkaction | grep -Fx io.github.kugaichen.PassportUnlocker.unlock
