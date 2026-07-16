#!/bin/sh
set -eu

SOURCE_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
OUTPUT_DIR=$(dirname "$SOURCE_DIR")
BUILD_ROOT=$(mktemp -d)
trap 'rm -rf "$BUILD_ROOT"' EXIT HUP INT TERM

cp -a "$SOURCE_DIR/." "$BUILD_ROOT/source/"

# DrvFS may expose every file under /mnt/c as executable. Build from WSL's
# native filesystem so debhelper does not treat declarative config as scripts.
find "$BUILD_ROOT/source" -type f -exec chmod 0644 {} +
chmod 0755 \
    "$BUILD_ROOT/source/debian/rules" \
    "$BUILD_ROOT/source/debian/tests/smoke"

cd "$BUILD_ROOT/source"
dpkg-buildpackage -b -us -uc

find "$BUILD_ROOT" -maxdepth 1 -type f \
    \( -name '*.deb' -o -name '*.changes' -o -name '*.buildinfo' \) \
    -exec cp -f {} "$OUTPUT_DIR/" \;
