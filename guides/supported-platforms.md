---
type: guide
status: current
date: "2026-09-30"
title: "Supported Platforms"
topics: [install, platforms, macos, intel, quickstart]
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
| macOS on Intel | **Built from source**: extra prerequisites, follow the section below | No |
| Windows | Inside WSL, as on Linux | Not applicable |

"Prebuilt wheels" matters because one required dependency, `cryptography` (version 50 or newer,
held there on purpose to stay ahead of published security advisories), ships no macOS x86_64
wheel. On an Intel Mac `uv` therefore compiles it, and that build needs a Rust toolchain and the
OpenSSL headers. Without them the install fails deep inside the compiler with a message like
`Could not find directory of OpenSSL installation`. Nothing else in the tool differs on Intel.

Check which machine you have: `uname -sm` prints `Darwin arm64` on Apple Silicon and
`Darwin x86_64` on Intel. If it prints `x86_64` on a Mac you know is Apple Silicon, your
terminal is running under Rosetta; open a native terminal instead, and the wheels install
normally.

## Intel macOS: build from source

You need three things, all from Homebrew (install [Homebrew](https://brew.sh) first if you
do not have it, which also installs Apple's command line tools):

```bash
brew install openssl@3 rust uv
```

Then run the installer (`curl -fsSL https://omninode.ai/install.sh | bash`), which finds Homebrew's
OpenSSL and Rust and builds only what has no prebuilt package. To install by hand instead, point the build at that OpenSSL explicitly, in the same terminal window:

```bash
export OPENSSL_DIR="$(brew --prefix openssl@3)"
uv tool install --python 3.12 omninode-onex
```

`OPENSSL_DIR` pins the build to Homebrew's OpenSSL, which matters if another OpenSSL is also
installed on the machine. On a default Homebrew setup the build finds `openssl@3` without it, and
the Rust toolchain is the part that is never optional. Verified on a clean macOS 15 Intel machine
(GitHub-hosted runner): with both packages installed the install finishes in about three
minutes.

If you manage Rust with `rustup` instead of Homebrew, skip `brew install rust` and make sure a
default toolchain is set (`rustup default stable`); a `rustup` with no default toolchain fails
with `rustup could not choose a version of cargo`.

The first install compiles `cryptography` and takes several minutes longer than on other
platforms; later installs and upgrades reuse the result. It ends with the same `Installed`
line described in the [quickstart](onex-plugin-quickstart.md), and `onex --version` works.

The installer detects an Intel Mac before it installs anything. It checks for Homebrew's
`openssl@3` and a working `cargo`, sets `OPENSSL_DIR` for you, and stops with the exact `brew`
command for anything missing.

If you would rather not build from source, run the same install inside a Linux container.
The steps are identical to the Linux path.

## Support is tested

A scheduled install check installs the tool into an empty home directory on Linux, on Apple
Silicon macOS, and on Intel macOS using exactly the Intel steps above, then runs a delegation
against a stub model. If a change breaks one of these paths, that check fails.
