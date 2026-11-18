# Rust/Python API parity

The machine-readable mapping in `api-parity.json` covers every current public
builder and processor method and every portable processor, buffer, observer and
path method. Tests compare method names, the core revision and hashes of every vendored Rust
source file,
and verify the named Python entry points exist. Source hashes canonicalize CRLF to
LF only; all other bytes remain significant. Text checkouts use LF through
.gitattributes, and a regression verifies that real source edits still fail. After an approved core update,
review each changed signature/behavior, update the mapping and hashes, regenerate
both Rust reference fixtures, and run `scripts/check.py`. Do not refresh fixtures
to hide an adapter failure.

## Representations

| Rust | Python | Semantics |
| --- | --- | --- |
| `TextForgeProcessor::new`, Default | `Processor()` | Independent registry |
| `ExecutionProfile`, `Limits`, `set_profile`/`profile` | `ExecutionProfile` (frozen dataclass), `Processor.set_profile`/`profile` | Spool threshold and safety limits flattened into one value; presets come from the core |
| `set_pipeline_name`/`pipeline_name` | Same processor names | Owned string result |
| `BindingError` + `BindingErrorDetails` | `TextForgeError` attributes, `TraceFrame`, `ErrorParameter` | Every field copied; tuples instead of vectors |
| `try_ignore`, `on_line`, `on_chunk`, `on_line_interval` (`Into<TokenWrapper>`) | Same `Pipeline` names | Inner instruction is a one-instruction `Pipeline` or an `Instruction`; a `Variable` is rejected as in Rust |
| `TextForgeBuilder::new`, `create_pipeline` | `processor.create_pipeline()` | Immutable owned plan retaining the processor for build; no long-lived Rust borrow |
| Builder operation/group methods | Same `Pipeline` names | Explicit typed methods; edits return new plans; group callbacks run once during construction |
| `define_replace_map`, `ReplaceMapBuilder::add_replace/end` | Scoped callback with `add_replace/end`; `add_replace_rule` for single rules | Checked portable rule staging; temporary callback scope |
| `push_token` | `Pipeline.push_token(Instruction(...))` | Owned description instead of a private trait object |
| `build` | `plan.build()` or `plan.build(processor)` | Validate/register atomically; return a new ID; plan remains reusable |
| Independent portable plan/compiled executable | `Pipeline().compile()` | Executable independent of registry and source plan |
| `add_transform`, snapshots | Same processor names, `Instruction` descriptions | Checked registration and owned snapshots |
| `show_transforms`, debug methods | Same names | Retain native stdout output |
| `process_single` | `process_single(Instruction, text)` | Typed instruction |
| `process_single_buffered` | `process_single_buffered(instruction: str, buffer)` | Retains the core's textual instruction argument |
| Full/single/file processing, persistence | Same processor names | Preserve extensions and errors; exports create missing files (core 0.4.0) |
| `FileTask` | `FileTask(input, pipeline_id, output)` or legacy tuple | Per-task pipeline, ordered error results |
| `BatchPool`, `process_batch_in_pool` | Same names | Reusable explicit-close pool; legacy process_batch threads parameter remains supported |
| `BufferTask` | `BufferTask(pipeline_id, input)` | Ordered buffer/error results |
| Buffer options/buffers/stream hooks | `BufferOptions`, `PortableBuffer`, `StreamReader`, `StreamWriter` | Byte reads, spill placement, explicit materialization, synchronous binary callbacks |
| `Observers`, `Observation` | Same names | Builtins/custom callbacks, replacement, All schedule, reset/manual run/report |
| `FilePath` | Same constructors/exporters; ordinary native Python paths also accepted | Lossless Unix bytes and Windows UTF-16 units |
| `features()` | `features()` | bytecode/watchers/buffered enabled in this distribution |

All optional processor facilities are exposed. Only the schedule implemented by
the core (`All`, through `schedule_all`) is available; commented-out core enum
variants are not advertised. Internal Rust types and identical borrow signatures
are intentionally represented by owned portable values.

## Verification

The builder oracle compares every named instruction/group helper with the real
Rust fluent API. The processor oracle compares in-memory/empty/Unicode output,
text/bytecode round trips, buffered execution, watched output/reports, and errors
for missing IDs/snapshots/removal/variables, regexes, parameter arity/types,
conversion, persistence, callbacks, builtins and invalid UTF-8. Error comparisons
include code, stage, message, instruction, input, kind, cause, hint, ignorable and
the plain report, not only rendered text.

Lifecycle tests additionally cover consuming success/failure, alias invalidation,
stream ownership, callback cycles/replacement, report preservation, re-entrancy,
concurrent mutation and compiled sharing. Linux-only descriptor checks verify
spilled files close on both failure and explicit close. Native Windows/Unix path
branches are platform-gated. Remote platform checks require CI execution.


## 0.1.3 optimized core refresh

The API mapping is unchanged; the embedded engine moves to the exact optimized
TextForge 0.2.0 revision in CORE_REVISION. The previous builder and processor
oracle case outputs/errors are retained. Only the processor fixture's revision
marker changes; independent Rust execution must still reproduce every old value.
The source integrity map now covers transform/helper implementations as well as
public API files, so an API-compatible engine edit cannot evade freshness checks.

## 0.2.0 core 0.4.0 refresh

The embedded engine moves to TextForge 0.4.0 (revision in CORE_REVISION). Nine
builder methods are new and mapped; the portable processor mapping adds
`set_profile`, `profile`, `set_pipeline_name` and `pipeline_name`, and is now
checked against the `impl PortableProcessor` blocks of the core. The oracle
outputs were regenerated by running the real Rust builder and processor: the
line-error cases use 0-based lines, nested-instruction cases build their inner
instruction as a Rust `Box<dyn InstructionMethods>`, and every recorded error
also carries `kind`, `cause`, `hint`, `ignorable` and `report`. File
instructions are checked against real files in `tests/test_core_040.py`.
