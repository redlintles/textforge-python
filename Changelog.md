# Changelog

Changes are grouped by binding version. Publication dates are omitted where the
Git history only establishes a version change, not an uploaded release.

## 0.1.2 — Unreleased

### Added

- Typed adapters for Unicode normalization (`unorm`) and named regex replacement
  maps (`rmapd`, `rmape`), delegated to the refreshed portable core.

- Complete processor parity through the existing portable API: watchers/reports,
  buffered single/full/file/batch processing, binary stream hooks, native paths,
  reusable batch pools, capability discovery and transform display.
- Rust-style `Processor.create_pipeline()`, reusable `Pipeline.build()`, and
  owned-description `push_token` and `add_transform` entry points.
- Explicit buffer/pool close and context managers, consumed-alias invalidation,
  callback cycle collection, thread confinement and re-entrancy protections.
- A method-level API map, independent Rust result/error oracles, compatibility and
  lifecycle guides, and tests of failure cleanup and concurrent mutation.
- Wheel metadata/version checks that reject stale or unrelated distribution
  files, plus verification of typing resources and an external typed consumer.

### Fixed

- Canonicalize CRLF to LF when checking pinned source hashes and enforce LF
  checkouts for text files, preventing Windows newline conversion from reporting
  a false source-integrity failure. Other source changes still fail the check.
- Separate Unix native-byte path representation tests from filesystem I/O. Skip
  only the filename-creation probe when a filesystem rejects non-UTF-8 names with
  EILSEQ (as on the macOS runner); preserve other errors and conversion coverage.

### Changed

- Raise copied core dependency requirements to the verified stable versions:
  colored 3.1.1, regex 1.13.1, shell-words 1.1.1 and serde 1.0.229. PyO3 remains
  0.30.1, already the latest stable release checked on 2026-10-30.
- Refresh both Cargo lockfiles, updating 16 compatible transitive packages.
  The exact refreshed TextForge snapshot is recorded in `vendor/CORE_REVISION`.
- Pin development/build tools: maturin 1.16.0, pytest 9.2.0, Ruff 0.17.3, mypy
  2.4.1, build 1.6.1 and twine 7.0.0; use pip 26.2.2 in setup instructions/CI.
- Upgrade the release Actions to their verified stable tags and migrate macOS
  jobs from the retiring macos-14 runner to macos-15.
- Enable production bytecode, watchers and buffered features in wheels, while
  keeping test_access confined to test-only references.
- Expand CI to Python 3.10–3.14 on all three wheel platforms, check Rust 1.89,
  and independently rebuild/install/test source distributions.
- Rewrite setup/release instructions around 0.1.2 artifacts, explicit ownership,
  current capabilities and tested dependency versions. Include this changelog in
  the source distribution.

Existing fluent/mnemonic construction and import name `textforge` remain
compatible. New APIs follow the core's file extensions, error fields, execution
and storage semantics. Publication remains a maintainer action after CI approval.

## 0.1.1

- Advance Cargo/distribution version metadata from 0.1.0 to 0.1.1.
- The version-bump commit (`4a97f68`) contains no functional source changes;
  the typed fluent implementation below was already present.

## 0.1.0

- Introduce the independent PyO3 adapter over TextForge's portable API, owned
  immutable plans, compiled pipelines, registry/file/bytecode operations and
  ordered batch results.
- Add all 58 fluent instruction helpers and block/conditional methods, typed
  arguments, variable helpers, reusable construction callbacks and a real Rust
  builder reference suite.
- Ship annotations, native stubs and py.typed; prepare abi3 wheels, a self-contained
  vendored-core sdist, and manually approved trusted-publisher tooling.
- Set the distribution name to `textforgers`, retaining Python import `textforge`.
