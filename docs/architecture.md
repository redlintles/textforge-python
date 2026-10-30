# Binding architecture

`python/textforge/__init__.py` supplies a fully annotated, immutable construction
facade. All 58 named instruction methods are explicit Python definitions matching the
vendored Rust builder, plus its block/conditional methods. A maintenance generator
reads the pinned Rust trait signatures and registry parameter categories, emits
statically typed methods into Pipeline, and fails CI if that source drifts. There
is no runtime method injection or __getattr__ dispatch. Builder-specific numeric
normalization for val/var/mut_var is preserved in the argument conversion helpers.
Native classes `Instruction` and `Variable` are immutable; instruction
arguments can be inspected through `name` and `arguments`. The public Python
processor uses composition rather than subclassing PyO3 internals. Native type
stubs and a `py.typed` marker ship in wheels and source packages.

The private `_native.Plan` is created afresh for compilation or registration.
Lowering a group moves only that temporary native subplan; Python bodies remain
reusable. Group construction and nested instruction construction are bounded at
32 levels before recursion or description cloning can grow without bound. The
core independently enforces its own stricter structural and parameter limits.
Invalid plans cannot partially register pipelines. Python edits defer registry
conversion and structural errors to `compile()` or `register()`.

`src/lib.rs` translates Python arguments into `Argument` and `InstructionSpec`,
then delegates to `PipelinePlan`, `CompiledPipeline`, and `PortableProcessor`.
There is no separate DSL parser, engine, opcode table or execution policy. Error
attributes come directly from `BindingError`; stage names are lower-case.
Unsupported Python types raise TypeError; unsigned overflow raises OverflowError.
Core conversion, validation, execution and persistence errors raise TextForgeError.

Compiled pipelines release the GIL and can be shared across threads. Each call
has a fresh core execution context. Processor operations also release the GIL
while executing native work, retaining PyO3's borrow guards. Conflicting concurrent
mutable use of one processor raises a borrow error rather than racing. Use one
processor per mutable workflow, or share immutable compiled pipelines. Batch
execution uses a caller-sized pool within the portable layer, preserving errors
and result order. Currently a pool is created for each batch call.

The extension uses the CPython stable ABI starting at 3.10. The source distribution
includes the Rust engine snapshot and Cargo.lock. It still needs Rust and access
to crates.io (or a populated Cargo cache) to compile dependencies. No language
runtime, Rust engine object, pointer, or borrowed text escapes into Python.

## Engine snapshot

`vendor/CORE_REVISION` records the TextForge Git revision. Its tracked `src`, tests,
pipeline fixtures, README, Cargo manifest/lockfile, and license were copied,
excluding `src/bindings`. The core manifest's original workspace section was
removed so that it participates as a path dependency in this independent workspace.
Large benchmark data files are omitted; the unit/integration tests generate their
own data or use the included pipeline fixtures. There are no core implementation
changes in the snapshot.

To update, obtain the desired core revision, replace the snapshot from tracked
files only, remove the original workspace section again, update CORE_REVISION,
regenerate the binding Cargo.lock, and run the entire check script and sdist
rebuild. Review the resulting vendor diff as a core update. Never copy build
outputs, a `.git` directory, private local files, or the nested binding itself.

## Initial release scope

Exposed: all four portable argument forms, immutable plans, blocks, containment
groups, compiled execution, registry management, single/full/debug execution,
typed/text snapshots, UTF-8 files, bytecode, parallel file tasks with ordered errors.

Not yet exposed: watcher/observer callbacks and reports, buffered/spilled objects,
binary stream callbacks, reusable BatchPool objects, raw native paths, and
`show_transforms` (use typed/list snapshots instead). These are extension work;
the package does not claim complete portable API parity. Optional watchers and
buffered core features are not enabled in distributed wheels. Bytecode is enabled.

## Builder conformance

`scripts/generate_builder.py` regenerates the marked methods in the public Python
module; it uses development-time Ruff formatting. Handwritten group methods and
terminal compilation remain outside that generated section. Public annotations
resolve at runtime and are visible to static checkers and IDEs.

`scripts/generate_builder_reference.py` builds a separate Rust reference executable
using TextForgeBuilderMethods and the original builder's doctest inputs, plus
logical examples. Its saved results are compared to Python execution for all 61
builder methods. Expected outputs are obtained from actual Rust builder calls,
not from the portable mnemonic mapping. CI re-executes the oracle before Python
tests, so stale fixtures fail instead of silently blessing changed behavior.

The reference executable's `test-reference` feature enables the core's test_access
solely to construct the typed inner token required by Rust's iter test. Those
internal types are not public without test_access in the pinned core. Distributed
wheels continue to enable only the production extension-module feature and the
core bytecode feature; test helpers are not enabled in release packages.
