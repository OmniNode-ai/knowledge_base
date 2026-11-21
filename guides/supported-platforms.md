---
type: guide
status: current
date: "2026-11-19"
title: "Supported Platforms"
topics: [install, platforms, macos, linux, quickstart]
refs: []
---

# Supported Platforms

Where the `onex` command-line tool installs, and how. The install path depends on your
computer, not on which quickstart you follow.

| Platform | How it installs | Prebuilt wheels |
|----------|-----------------|-----------------|
| macOS on Apple Silicon (M1 and newer) | `curl -fsSL https://omninode.ai/install.sh \| bash`, nothing extra | Yes |
| Linux, x86_64 | `curl -fsSL https://omninode.ai/install.sh \| bash`, nothing extra | Yes |
| Linux, arm64 | `curl -fsSL https://omninode.ai/install.sh \| bash`, nothing extra | Yes |
| macOS on Intel | Not supported yet | No |
| Windows | Not supported yet | Not applicable |
| Linux with musl (for example Alpine) | Not supported yet | No |

Intel Macs are not supported yet. The required dependency `cryptography` (version 50 or newer,
held there to stay ahead of published security advisories) ships no macOS x86_64 wheel, and the
install line never builds from source.

Check which machine you have: `uname -sm` prints `Darwin arm64` on Apple Silicon and
`Darwin x86_64` on Intel. If it prints `x86_64` on a Mac you know is Apple Silicon, your
terminal is running under Rosetta; open a native terminal instead, and the wheels install
normally.

If you already have `uv` installed, you can use:
`uv tool install --python 3.12 --no-build omninode-onex`

The `--no-build` flag installs only prebuilt packages, never compiling on your machine.

## Support is tested

A scheduled install check installs the tool into an empty home directory on Linux and Apple
Silicon macOS, then runs a delegation against a stub model. If a change breaks one of these
paths, that check fails.