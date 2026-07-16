# Changelog

## Unreleased

- Validated software-only workflows on Ubuntu 22.04 and Ubuntu 26.04 WSL.
- Added compatibility with Setuptools 59.6, GTK 4.6 and Libadwaita 1.1.
- Added Debian copyright metadata and removed all Lintian error-level findings.
- Added GitHub CI, contribution guidance, security/community templates and release gates.
- Adopted the `io.github.kugaichen.PassportUnlocker` application identity and public project URLs.
- Added manual pages for the CLI, GUI and privileged helper.
- Improved GUI smoke tests so Python tracebacks cannot be reported as successful timeouts.
- Hardware status, unlock and rescan remain unverified in the new implementation.

## 0.1.0 - 2026-07-15

- Split the upstream single-file utility into testable protocol, discovery, helper, CLI and GUI layers.
- Added post-write unlock verification, stable device identity and a fixed SG_IO allowlist.
- Added GTK 4/Libadwaita UI, XDG autostart monitoring and Debian packaging metadata.
- Removed password management, secure erase and all other destructive operations from production interfaces.
