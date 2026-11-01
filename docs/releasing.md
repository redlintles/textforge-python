# Release procedure

The prepared binding version is **0.1.3**; the vendored engine is TextForge 0.2.0 at the exact optimized revision in `vendor/CORE_REVISION`. This checkout
does not publish itself. The maintainer reviews CI, pushes/tags the approved
commit and initiates publication. See [Changelog.md](../Changelog.md) and the
[dependency snapshot](dependencies.md).

1. Start from the reviewed binding commit and a clean worktree. Confirm 0.1.3 in
   Cargo.toml, the textforgers Cargo.lock entry and the compatibility document.
   Python version metadata is derived from Cargo.toml, not duplicated in Python.
2. Activate a clean environment, install pip 26.2.2, then `python -m pip install
   --group dev`. Use a new empty artifact directory. Build with
   `maturin build --release --locked --sdist --out dist/0.1.3`, install exactly
   textforgers==0.1.3 from that directory, and run `python scripts/check.py`.
3. Run `python scripts/check_distribution.py --wheel-dir dist/0.1.3 --types` and
   `python -m twine check dist/0.1.3/*`. The validator rejects wheels whose metadata
   disagrees with the source version, and checks installed resources/capabilities.
   Do not mix older candidate artifacts into this directory.
4. Unpack the sdist outside both repositories, rebuild with `--release --locked`,
   and install that wheel into a clean environment. Run its included pytest suite
   and distribution validator. Verify Changelog.md, typing files and licenses are
   present. Source builds need cached Rust dependencies or network access.
5. Review successful jobs for the exact release commit. CI configures CPython
   3.10–3.14 on Linux x86_64, Windows x86_64 and macOS arm64 (macos-15), plus the
   Rust 1.89 check and independent source rebuild. Other targets are not claimed
   as tested wheel platforms. Publish CI manylinux wheels for Linux portability;
   local glibc tags are not evidence of manylinux compatibility.
6. Confirm package ownership and matching Trusted Publishers on PyPI/TestPyPI:
   owner redlintles, repository textforge-python, workflow ci.yml and environments
   pypi/testpypi. Configure required maintainer reviewers on both environments.
   Merely naming an environment in YAML does not enforce manual approval.
7. After approval, push the reviewed commit yourself. Dispatch CI with destination
   testpypi, then install textforgers==0.1.3 from TestPyPI in a clean environment
   and verify it. Use the distribution name textforgers; do not install another
   distribution that provides the same textforge import.
8. Review the successful candidate jobs and artifacts, then manually dispatch the
   pypi destination after release approval. The workflow rebuilds on each dispatch;
   use the same reviewed commit and inspect each resulting candidate. Finish the
   release notes/tag and replace the changelog's Unreleased heading with the
   actual publication date when the maintainer publishes.

The workflow uses OIDC through the PyPA publish action. No long-lived PyPI token
belongs in this repository. Normal pushes/PRs and the manual destination none do
not publish. Cargo publish is disabled because the release artifact is a Python
distribution. Version changes, pushes and publication require the corresponding
maintainer approval; this preparation task authorizes the version update only.

Official references:

- [Maturin distribution guide](https://www.maturin.rs/distribution.html).
- [PyO3 0.30.1](https://pyo3.rs/v0.30.1/).
- [Trusted publisher setup](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).
- [macOS 14 runner retirement](https://github.blog/changelog/2026-10-01-github-actions-macos-14-runner-image-retirement/).

## Local validation for 0.1.3 (2026-11-01)

The prepared source pins optimized core 0.2.0 revision
`c2ed4b8f4c96c9e3ddc53576a3cdbf6ccd38bc9e`. No adapter API or locked dependency
version changes accompany this core refresh.

- `scripts/check.py` passed: Rust formatting, strict Clippy, native Rust tests,
  Ruff, mypy, generated-source checks, independent Rust oracles and the complete
  embedded-core feature checklist.
- All **80 builder** and **41 processor** reference cases reproduced the previous
  outputs/errors. The processor fixture changes only its source revision marker.
- **224 Rust source files** are integrity-checked. A regression requires complete
  source coverage, including optimized transforms/helpers.
- The installed release wheel passed **247 Python tests**, with one Windows-only
  native-wide-path test skipped on Linux. The independently rebuilt sdist wheel,
  installed in a second clean environment, passed the same suite.
- Wheel metadata, native features, typing resources, licenses and an external
  strict-mypy consumer passed distribution validation; wheel/sdist metadata passed
  `twine check`. Rust **1.89.0** passed `cargo check --all-targets --locked`.
- Release-mode embedded-core allocation parity passed its **2,106 original-core
  outcome cases**, including the recorded debug/release compatibility limits.

Local verification is **Linux x86_64 / CPython 3.12**. The local wheel is tagged
`cp310-abi3-manylinux_2_35_x86_64`; this does not claim the broader runtime/platform
matrix passed. Remote jobs for the final pushed commit, publisher configuration,
release approval and publication remain maintainer release steps. No push, tag,
TestPyPI upload or PyPI upload was performed during preparation.
