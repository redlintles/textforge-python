# Ownership, callbacks and concurrency

Plans are immutable values; fluent edits return new plans. A plan from
Processor.create_pipeline retains its processor so build() can register it.
Standalone plans use build(processor). Builds can be repeated, create independent
IDs and validate atomically. compile() returns an independent executable that
survives source-plan/processor deletion. Group callbacks are eager construction
helpers, not runtime observers. Internal lowering consumes temporary native plans
only; reusable Python bodies are never moved out from under their aliases.

PortableBuffer owns its spool. Use close() or a context manager for deterministic
release; final native destruction also drops the spool. into_string and buffered
processing consume storage even if the core operation fails. Argument conversion
and borrow checks happen before transfer; their failures leave storage intact. Every alias then reports closed and
raises ValueError on further use. Inspection, ranged reads, copy_to and file output
retain ownership. Failed copy_to leaves the buffer available, but the destination
stream may contain partial bytes. Spilling and thresholds preserve core placement
semantics, not a hard process-wide memory cap.

Reader/writer hooks are synchronous binary operations. The caller owns the stream;
the adapter neither retains it after the call nor closes/flushes it. Readers must
return bytes no larger than requested; writers must return a nonnegative byte
count no larger than supplied. The shared portable bridge validates counts and
UTF-8 across chunks, and retries short writes. Runtime exceptions are converted
to the core's structured I/O errors, preserving their class/message text. A kept
Python exception/traceback can naturally retain its arguments until released.

Observers retain custom callbacks until replacement, clear(), or collection.
Native GC traversal makes cycles involving callbacks visible to Python. reset()
discards results only; clear() also releases schedules and callbacks. Callbacks
run synchronously on the creating/calling thread, returning strings; Python
exceptions become callback-stage TextForgeError with the original class/message
text. An existing report is not overwritten on observer failure; prior observations
may remain until reset. Successful watched runs export then reset results.

Observers are thread-confined, like the core Rc-based watcher list. Use and clear
them on their creating thread; do not transfer their ownership to another thread.
The public facade rejects foreign-thread calls with RuntimeError. Watched runs
retain the GIL and mutable native borrows while invoking callbacks. Re-entering
that processor or mutating that observer during a callback raises a borrow error
before native execution. Callbacks may use independent processors/observers.

Compiled pipelines support shared concurrent execution with fresh contexts.
Ordinary native processing releases the GIL while keeping PyO3 borrow guards;
conflicting mutation raises RuntimeError instead of racing. Buffer calls retain
exclusive borrows while invoking stream callbacks, preventing reentrant close or
processing. BatchPool permits immutable sharing; close() releases workers and
fails if an operation currently borrows it. Calls on a closed pool raise
ValueError. Pool and buffer close operations are idempotent.

Tests use deterministic callbacks and thread synchronization rather than timing
assumptions to exercise re-entrancy and concurrent mutation. Linux descriptor
inspection additionally checks spilled storage release after failure/close.
