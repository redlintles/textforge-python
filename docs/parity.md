# Rust/Python API parity

The machine-readable mapping in `api-parity.json` covers every current public
builder and processor method and every portable processor, buffer, observer and
path method. Tests compare method names, the core revision and source hashes,
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
| `TextForgeBuilder::new`, `create_pipeline` | `processor.create_pipeline()` | Immutable owned plan retaining the processor for build; no long-lived Rust borrow |
| Builder operation/group methods | Same `Pipeline` names | Explicit typed methods; edits return new plans; group callbacks run once during construction |
| `push_token` | `Pipeline.push_token(Instruction(...))` | Owned description instead of a private trait object |
| `build` | `plan.build()` or `plan.build(processor)` | Validate/register atomically; return a new ID; plan remains reusable |
| Independent portable plan/compiled executable | `Pipeline().compile()` | Executable independent of registry and source plan |
| `add_transform`, snapshots | Same processor names, `Instruction` descriptions | Checked registration and owned snapshots |
| `show_transforms`, debug methods | Same names | Retain native stdout output |
| `process_single` | `process_single(Instruction, text)` | Typed instruction |
| `process_single_buffered` | `process_single_buffered(instruction: str, buffer)` | Retains the core's textual instruction argument |
| Full/single/file processing, persistence | Same processor names | Preserve extensions, existing-file export validation and errors |
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
include code, stage, message, instruction and input, not only rendered text.

Lifecycle tests additionally cover consuming success/failure, alias invalidation,
stream ownership, callback cycles/replacement, report preservation, re-entrancy,
concurrent mutation and compiled sharing. Linux-only descriptor checks verify
spilled files close on both failure and explicit close. Native Windows/Unix path
branches are platform-gated. Remote platform checks require CI execution.
