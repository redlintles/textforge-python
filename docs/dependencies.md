# Dependency snapshot

Verified against the official crates.io sparse index, PyPI JSON API and GitHub
release endpoints on 2026-10-30. These are stable, non-yanked Rust releases;
Python tools and Actions are pinned to the stable releases tested for 0.1.2.

## Rust

| Direct dependency | Required stable version |
| --- | --- |
| PyO3 | 0.30.1 |
| tempfile | 3.27.0 |
| colored | 3.1.1 |
| regex | 1.13.1 |
| shell-words | 1.1.1 |
| uuid | 1.29.0 |
| urlencoding | 2.1.3 |
| html-escape | 0.3.0 |
| serde_json | 1.0.154 |
| serde | 1.0.229 |
| rand | 0.10.3 |
| random-string | 1.1.0 |
| clap | 4.6.7 |
| rayon | 1.12.0 |
| evalexpr | 13.1.0 |

The binding still uses the pinned TextForge 0.1.9 source snapshot. Only dependency
requirements in its copied manifest were refreshed; no core implementation or
public API was changed. Several direct crates, including PyO3, were already at
the newest stable version in Cargo.lock and therefore did not need an upgrade.
Both Rust lockfiles were refreshed. Cargo updated 16 compatible transitive
packages, including libc, rustix, crossbeam, syn and wasm-bindgen.

## Python build and development tools

| Tool | Tested version |
| --- | --- |
| maturin | 1.16.0 |
| pytest | 9.2.0 |
| ruff | 0.17.3 |
| mypy | 2.4.1 |
| build | 1.6.1 |
| twine | 7.0.0 |
| pip | 26.2.2 |

The Python distribution has no Python runtime dependencies. pyproject.toml pins
the build backend and direct development tools; transitive Python tool dependencies
are resolved by pip. The pip bootstrap version is explicit in CI and the README.

## GitHub Actions

| Action | Stable tag |
| --- | --- |
| [actions/checkout](https://github.com/actions/checkout/releases/tag/v7.0.1) | v7.0.1 |
| [actions/setup-python](https://github.com/actions/setup-python/releases/tag/v7.1.0) | v7.1.0 |
| [actions/upload-artifact](https://github.com/actions/upload-artifact/releases/tag/v7.0.2) | v7.0.2 |
| [actions/download-artifact](https://github.com/actions/download-artifact/releases/tag/v8.0.2) | v8.0.2 |
| [PyO3/maturin-action](https://github.com/PyO3/maturin-action/releases/tag/v1.51.0) | v1.51.0 |
| [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish/releases/tag/v1.14.3) | v1.14.3 |

The rust-toolchain action intentionally uses its documented stable and 1.89.0
toolchain refs; it is a toolchain selector rather than a versioned package release.
The maturin action is also configured to install maturin 1.16.0 explicitly.
macOS jobs use macos-15. Hosted jobs must pass before publication.

## Refresh and verify

Consult [crates.io](https://crates.io/), [PyPI](https://pypi.org/), and each
Action release page above before changing versions. Update both Cargo lockfiles
and the copied core manifest without silently replacing the pinned core source.
Run the complete check script, Rust 1.89 minimum check, independent Rust oracles,
and release wheel/sdist validation. Do not rewrite oracle outputs to hide a
behavioral difference introduced by a dependency update.
