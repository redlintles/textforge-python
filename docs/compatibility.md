# Compatibility matrix

| Component | Supported/configured contract | Verification |
| --- | --- | --- |
| Binding | Cargo/Python distribution 0.1.2; import `textforge` | Version metadata checked against the installed native extension |
| Core | 0.1.9; exact revision in `vendor/CORE_REVISION` (`4f88b8c615398d62b15fafb140f7b9fc50fcd007`) | Pinned source hashes, method mapping, independent Rust references |
| Cargo features | bytecode, watchers, buffered enabled | Runtime features() checked in installed artifacts; test_access only in test-reference |
| CPython | 3.10–3.14, ordinary GIL builds | CI matrix configured on every wheel platform; local verification is 3.12 |
| Stable ABI | abi3-py310; metadata allows Python >=3.10 | Later interpreter versions remain unverified until added to CI; free-threaded Python and PyPy are not supported/tested targets |
| Linux wheels | x86_64, manylinux from maturin-action | CI build/install/test; local Linux x86_64 wheel and independent sdist rebuild |
| Windows wheels | x86_64 | CI build/install/test; native wide-path regression is platform-gated |
| macOS wheels | arm64, macos-15 runner | CI build/install/test |
| Other architectures/OS combinations | Source builds may be possible | Not claimed as tested/supported wheel targets |
| Rust source builds | 1.89+ (edition 2024 and pinned dependency requirements) | Local cargo +1.89.0 check passed; minimum-rust CI job checks 1.89 and stable runs the full checklist |
| Paths | Unicode and OS-native representations, without replacement | Unix bytes/surrogateescape and Windows UTF-16/surrogatepass tests |

A configured remote job is not evidence that a particular run passed. Consult
that run's results before release. No CI workflow was dispatched by this update.

The minimum Rust version reflects the current lockfile (notably uuid 1.89).
Review it with dependency/core changes; preserve --locked builds. Source builds
require cached dependencies or network access. Local glibc wheel tags do not
establish manylinux portability; use the CI wheel for distribution.

After a reviewed core refresh, update the revision marker, API mapping/hashes,
reference fixtures and this matrix together. Regenerate Cargo.lock only when the
reviewed dependency graph changes. Test all supported runtime/platform pairs
before publishing; unsupported targets must remain labeled as unverified.


Unix native byte-path conversion is tested independently of filesystem naming
rules. A filesystem may reject a non-UTF-8 filename with EILSEQ; only that file-I/O
case is then skipped. The representation/round-trip checks still run, and other
I/O errors remain test failures. Windows native-wide checks remain platform-gated.
