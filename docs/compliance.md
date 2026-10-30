# Binding development rules: compliance record

This update was explicitly requested/approved by the maintainer in the development
chat on 2026-10-30. It addresses the parent repository's Python audit at binding
baseline 4a97f68. This record describes implemented behavior and reproducible
checks; it does not claim to reconstruct historical approvals or remote CI runs.

| AGENTS.md rule | Implementation/evidence |
| --- | --- |
| 1. Independent project | Separate crate/repository/worktree/version; parent excludes the Python workspace |
| 2. Portable API only | Production Rust modules import the portable layer; reference executables use core APIs only under test-reference |
| 3. One-to-one parity | docs/api-parity.json tracks all core builder/processor and portable processor/path/buffer/observer entry points; docs/parity.md explains owned representations |
| 4. Language conventions | Explicit snake_case methods, exceptions, dataclasses, PathLike values and binary stream protocols |
| 5. Core evolution | Pinned revision, source hashes, checked method mapping, generated-method freshness and both real Rust reference executables; refresh procedure in architecture.md |
| 6. Typing | Annotated public facade, native stubs, py.typed, strict mypy and external-consumer type checking against the installed wheel |
| 7. Human approval | This implementation was explicitly authorized; subsequent changes and publication still require the appropriate approval |
| 8. Native docs/tests/commits | pytest/doctests, Ruff, mypy, Rust formatting/clippy/tests, full vendored-core checklist and focused feature/validation commits; current version references updated |
| 9. Compatibility | compatibility.md consolidates exact core revision, Rust minimum, CPython versions, platform/architecture and enabled features; CI tests the configured matrix |
| 10. Errors/conversions | Checked unsigned instruction/count conversion, complete portable error fields, lossless Unix bytes/surrogateescape and Windows wide/surrogatepass paths |
| 11. Ownership/concurrency | lifecycle.md; consumed alias invalidation, idempotent close/context managers, stream ownership, callback cycle collection, thread checks, reentrant/concurrent borrow rejection and failed-spool cleanup tests |
| 12. Parity tests | 61 fluent Rust cases plus 19 processor result/error cases; every error field compared; pinned method/source checks, optional capabilities and edge cases exercised |
| 13. Distribution | check_distribution.py asserts wheel typing/native/license files and installed capabilities, and type-checks an external client; CI installs wheels and independently rebuilds/installs/tests sdist |
| 14. Human-readable code | Focused native/Python modules, direct delegation, isolated runtime glue, explicit typed generated methods with source/regeneration command and freshness checks |

Run `python scripts/check.py` against an installed current wheel, then
`python scripts/check_distribution.py --wheel-dir dist --types`. Before release,
build release wheel/sdist, run twine check, independently rebuild/install the sdist,
and require the configured platform jobs to pass. Local checks do not establish
Windows/macOS success or third-party publisher environment protection.


The 0.1.2 preparation refreshes verified stable dependency versions and both Rust
lockfiles, pins direct Python development tools, migrates macOS CI to macos-15,
and adds source/artifact/installed version agreement checks. See
[dependency versions](dependencies.md) and [version history](../Changelog.md).
