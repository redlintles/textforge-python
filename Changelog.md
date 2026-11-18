# Changelog

Changes are grouped by binding version. Publication dates are omitted where the
Git history only establishes a version change, not an uploaded release.

## 0.2.0 — Unreleased

Embeds **TextForge 0.4.0** (revision `6407329777e5d3c3875e8695ebc2b683f4d4f9e1`); binding releases for
0.3.x were skipped. The public structure of the API is unchanged: every
existing method, class and argument keeps its name and order. What changes is
the engine underneath, so the upgrade notes below come first.

### Upgrade notes (behavior of the embedded engine)

- **Line numbers start at 0**, like every other index: `delete_line(0)` deletes
  the first line (before: `delete_line(1)`), `insert_line(count, …)` appends, and
  an interval end past the last line is clamped instead of failing. Subtract one
  from every line number in plans, saved `.textforge` files and bytecode.
- `insert(0, text)` inserts at the start of the text; other indices are unchanged.
- `{{`, `}}`, `[[` and `]]` that form no variable or expression stay in the
  text (JSON and POSIX regex classes no longer need escaping).
- `replace_last_with` and `replace_nth_with` expand `$1`, `${name}` and `$$` like
  the other replacements; a literal `$` needs `$$`.
- `join_to_camel_case`/`join_to_pascal_case` lowercase each word first; `to_reverse`
  keeps `\r\n` in order; `len()` in expressions counts characters.
- `val` cannot be defined twice; variable names must be identifiers, and the
  built-in names cannot be assigned.
- `end` inside a block or loop stops only that block or loop.
- Expression results must be integers or text; the safety limits fail with
  `LimitExceededError` (code 31) instead of `ValidationError` (20).
- Error messages are rewritten and `str(error)` follows the new core messages;
  I/O and regex details moved from the message to `error.cause`. Match on
  `code`/`kind`, never on message text.
- `write_pipeline_to_file` and `write_to_bytecode_file` create missing files;
  bytecode export requires `.textforgebc` or `.tfb`; `.tft` and `.tfb` are read.

### Added

- `TextForgeError` exposes the 0.4.0 details: `kind`, `trace` (new
  `TraceFrame`), `parameters` (new `ErrorParameter`), `cause`, `hint`,
  `ignorable` and the plain-text `report`. All survive pickling.
- Typed builder methods for the new instructions: `try_ignore` (`tryi`),
  `on_line`/`on_chunk`/`on_line_interval` (`onln`/`onck`/`onlni`),
  `pipeline_join` (`ppjn`), `write_to_file` (`wtf`), `append_file` (`apf`),
  `prepend_file` (`ppf`) and `insert_file` (`inf`). Their instruction argument
  accepts a one-instruction `Pipeline` or an `Instruction`, as Rust's
  `Into<TokenWrapper>`.
- Numeric builder parameters accept text holding a `[[ ]]` expression or a
  `{{ }}` template (`int | str | Variable`), resolved when the instruction runs.
- `ExecutionProfile` (`balanced`, `low_memory`, `fast`, `preset`, `with_limits`,
  `unlimited`) and `Processor.set_profile`/`profile`, mirroring the core's
  spool threshold and safety limits (`max_generated_bytes`, `max_iterations`).
- `Processor.set_pipeline_name`/`pipeline_name` for `__PIPELINE_NAME__`.
- Built-in variables `__LEN_CHARS__`, `__LINES__`, `__TEXTFORGE_VERSION__`,
  `__PIPELINE_NAME__` and `__INPUT_FILE__` work through the existing API.
- `tests/test_core_040.py` and new Rust oracle cases for the nested instructions;
  the processor oracle also compares the new error fields.

### Changed

- The generated method docstrings use the core's new summaries; Rustdoc links
  are rendered as plain names.
- `docs/api-parity.json` covers the new builder methods, and a test now derives
  the portable processor surface from the core sources.
- Direct Rust dependencies follow the core: `rand`/`random-string` removed,
  `uuid` 1.29.3, `html-escape` 0.3.1.

### Documentation

- README: error details, `try_ignore`, section and file instructions, profiles,
  pipeline names, expressions in numeric parameters and 0-based lines.
- Builder reference table regenerated from the real signatures (all methods);
  line, lifecycle (file side effects, profiles), architecture, parity,
  compatibility, dependency, compliance and release guides updated for 0.2.0.

## 0.1.3

### Scoped replacement maps and debug fixes

- Add typed `ReplaceMapBuilder` and `define_replace_map(name, configure)`;
  preserve positional three-argument calls and expose `add_replace_rule`.
- Stage definitions through the portable API; reject unfinished/empty scopes
  and test callback failure, ownership, execution and text/bytecode round-trips.
- Resolve actual block names once during debug execution, including variables
  and whitespace, without destructive context inspection.
- Preserve quoted parameters in text exports and match existing raw/rfw/null
  opcode registry assignments. Regenerate old files with incorrect opcodes.

### Changed

- Embed the optimized TextForge 0.2.0 core at revision
  `c2ed4b8f4c96c9e3ddc53576a3cdbf6ccd38bc9e`, including reduced temporary strings,
  preserved borrowed slices and reuse of owned buffers. This baseline refresh requires no dependency upgrade.
- Expand pinned source integrity checks to all vendored Rust source files.
  Preserve prior independent Rust oracle outputs and errors during the refresh.
- Correct stale core-version references and update installation/release examples
  to the independently versioned `textforgers` 0.1.3 distribution.

### Validation

- Build/install/test the final release wheel and independently rebuild the source
  distribution outside the checkout; verify typing resources and native features.
- Remote platform/interpreter matrix results must pass for the exact release
  commit before publication. Local checks do not establish Windows/macOS support.

## 0.1.2

### Added

- Sixteen typed logical-line transforms from TextForge 0.2.0: `apl`, `dln`,
  `dlna`, `dlnb`, `slnc`, `dlni`, `inl`, `nln`, `rln`, `pln`, `dle`, `klm`,
  `dlm`, `revln`, `uniqln` and `joinln`. Line indices start at one; ranges are
  inclusive. `sortln` is not included.
- Native Rust reference results for every new fluent method, source freshness
  checks, line-boundary unit cases and installed-wheel tests through both typed
  and generic portable instructions.

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
  The exact refreshed TextForge 0.2.0 snapshot is recorded in `vendor/CORE_REVISION`.
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
