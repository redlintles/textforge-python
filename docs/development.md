# Development record and continuation guide

## 2026-10-29: first Python adapter

The starting binding repository contained only an empty Rust source file, a
Cargo scaffold using PyO3 0.30.1, and a README. The parent repository also tracked
the same two scaffold files and included the nested crate in its workspace.
Work was performed in separate Git worktrees for the parent and Python repos.

Implemented:

- PyO3 adapter over the existing portable API; no new engine or parser.
- Immutable, fully annotated Python Pipeline with reusable bodies and bounded
  construction depth; Instruction/Variable native values and introspection.
- Independent compiled callables and processors with explicit GIL release.
- Structured TextForgeError fields and pickle-compatible public module identity.
- Registry operations, single/full/debug execution, typed/textual snapshots,
  textual and bytecode persistence, UTF-8 files and parallel file tasks.
- Python >=3.10 stable-ABI wheels, PEP 561 stubs/py.typed, license and package
  metadata; distribution `textforgers` and import `textforge`.
- An identified vendored core snapshot (see vendor/CORE_REVISION), so independent
  Git clones and source distributions need no parent directory or unpublished
  crates.io version of the portable API. Only workspace metadata was adapted.
- CI for quality, three wheel platforms, Python-version compatibility, sdist
  rebuilding outside the checkout, and manual trusted publishing workflows.
- Parent-repository cleanup to stop tracking the nested scaffold and to exclude
  the independent workspace. No dependency, license or public core API was added
  or changed; the existing PyO3 dependency was configured for stable ABI builds.

Observed core behavior was preserved and documented: exports require existing
files, textual export uses `.textforge`, and bytecode import uses `.textforgebc`.
The adapter does not silently create export destinations or change extensions.

Validation performed locally on Linux x86_64 / CPython 3.12:

- 21 Python integration tests exercise Unicode/empty/NUL input, reusable plans,
  groups, nested instruction arguments, variables, error stages, atomic registry
  validation, context isolation, bound checks, read-only descriptions, snapshots,
  missing IDs/files, text+bytecode round trips, ordered batch errors, debug calls,
  thread sharing, exception pickling, README examples and Python doctests.
- Ruff lint and formatting; mypy strict over package, stubs, tests and check script.
- Adapter cargo fmt, clippy with warnings denied, cargo test and a portable doctest.
- Complete AGENTS.md core checklist in both parent and vendored core: fmt,
  clippy default/test_access, and tests default/bytecode/watchers/test_access,
  including doctests. All passed (1,744 core test executions across four feature
  combinations per core checkout; these counts include repeated cases).
- Release abi3 wheel and sdist builds, twine metadata checks, wheel contents
  inspection for types/license, and a release-wheel rebuild from an unpacked
  source distribution outside both repositories. The resulting wheel was
  smoke-tested in a clean virtual environment and run through the Python suite.

Local testing does not establish Windows/macOS or other Python version results.
Those checks are configured in CI and must pass there before release. A local
Linux wheel reflects the host glibc floor; distribute the manylinux CI wheel for
broader compatibility.

No Git push, PyPI upload, crates.io publishing, version bump or account change
was performed. Actual releases need the maintainer's package-name ownership,
trusted-publisher configuration and approval described in releasing.md.

## Next work

The current release scope is deliberately explicit in architecture.md. Resume
portable parity work here, without rewriting the core API:

1. Watchers: wrap Observers/Observation, typed JSON results, built-in metrics and
   schedule windows; preserve callback exceptions and report persistence stages.
   Establish callback lifetime and re-entrancy tests before releasing the GIL.
2. Buffered processing: expose BufferOptions/PortableBuffer, spilling, bounded
   read_at, file/batch variants, and ownership/cleanup tests. Do not imply that a
   spill threshold is a hard memory bound on transforms.
3. Binary stream callbacks: Python read/write protocols, short reads/writes,
   invalid UTF-8, callback failures and cleanup; do not retain borrowed Python data.
4. Native paths: expose portable byte/wide constructors to preserve non-UTF-8 Unix
   names and Windows surrogate paths. The first release supports Unicode paths.
5. Reusable BatchPool and capability queries if optional distributions are added.
   The current batch adapter creates one pool per call and enables only bytecode.
6. Add wheel targets when CI can verify them (Linux arm64, macOS Intel, etc.).
7. Automate snapshot refresh if engine updates become frequent; currently the
   exact process and revision marker are documented in architecture.md.

Run `python scripts/check.py` against an installed wheel after every adapter
change. Repeat sdist rebuilding when packaging or vendored sources change. Keep
Python and parent commits separate, and do not push/publish without approval.

## PyPI distribution rename

The maintainer selected `textforgers` as the PyPI project name and configured its
trusted publisher. Cargo package identity, lockfiles, installation examples and
the CI sdist extraction path now use that distribution name. The Python import
remains `textforge`, the version remains 0.1.0, and the GitHub repository remains
`redlintles/textforge-python`. GitHub URLs and the trusted-publisher repository
field intentionally retain that repository name. TestPyPI configuration remains
a separate account setup step. No publication was performed by this rename.

## 2026-10-30: Rust-style fluent builder

The maintainer requested that the Python API reflect the intentionally ergonomic
public Rust builder instead of requiring mnemonic strings. Pipeline now exposes
all 58 TextForgeBuilderMethods operations as ordinary, typed methods, plus
block_assoc, if_do_contains_each, and call_block. Numeric variable values preserve
Rust's string conversion; get_var mirrors the Rust helper. Iteration accepts a
single named-operation subplan. Group callbacks return an immutable subplan and
run once at construction. Existing mnemonic construction remains compatible as a
low-level escape hatch. The public Rust contract and engine snapshot are unchanged.

A checked generator maintains signatures against the vendored public API and
registry. An independent Rust executable captures all 61 builder cases, using
actual public-builder calls and its original examples. The 97 Python tests compare
outputs against that oracle, alongside explicit Unicode, type-validation, keyword
argument, variable, callback, ownership and structural-validation regressions.
See builder-api.md for the complete named surface and maintenance commands.

Validation passed for the fluent update: generated-source/oracle freshness, all
97 Python tests, Ruff lint/format, mypy strict, adapter formatting/clippy/tests,
the test-only Rust oracle and its clippy check, and the full vendored core
pre-commit checklist. Release wheel/sdist metadata and an external source rebuild
were verified. Production wheels were checked to exclude core test_access.
No version change, Git push or publication was performed.
