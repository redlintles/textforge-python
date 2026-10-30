# Binding architecture

`python/textforge/__init__.py` supplies a fully annotated, immutable construction
facade. Native classes `Instruction` and `Variable` are immutable; instruction
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
