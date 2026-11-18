# TextForge for Python

Typed Python bindings for [TextForge](https://github.com/redlintles/textforge),
implemented with PyO3 against its owned portable API. Distribution name:
`textforgers`; Python import: `textforge`. Requires Python 3.10 or newer.

This checkout prepares **0.2.0**, which embeds TextForge **0.4.0**. See
[Changelog.md](Changelog.md) for changes since 0.1.3 — including the upgrade
notes for pipelines written for TextForge 0.2.0 — and
[the dependency snapshot](docs/dependencies.md) for tested versions.

For a published release, use `pip install textforgers`; to build this checkout,
use the commands below. Do not install the unrelated `textforge` distribution as a substitute.

```python
from textforge import Pipeline, Processor, get_var

plan = Pipeline().trim_both_sides().add_to_beginning("🍌 ").add_to_end("!")
pipeline = plan.compile()
assert pipeline.process(" é ") == "🍌 é!"
assert pipeline("fruit") == "🍌 fruit!"

# Edits return a new plan. Both the source and compiled pipelines stay reusable.
assert Pipeline().compile()("unchanged") == "unchanged"
repeated = Pipeline().iter(2, Pipeline().add_to_end("!"))
assert repeated.compile()("é") == "é!!"

# Arguments omit DSL syntax words (assoc, do, times).
variables = Pipeline().val("n", 2).repeat(get_var("n"))
assert variables.compile()("é") == "éé"

body = Pipeline().add_to_end("!")
blocks = Pipeline().block_assoc("greeting", body).call_block("greeting")
assert blocks.compile()("hello") == "hello!"

processor = Processor()
identifier = processor.register(plan)
assert processor.process_all(identifier, " é ") == "🍌 é!"
```

The primary construction API follows Rust's `TextForgeBuilderMethods`,
`TextForgeBlockMethods` and `TextForgeConditionalMethods`: every operation is a
real method with an explicit signature, parameter names, documentation and type
annotations. For example:

```python
from textforge import Pipeline, get_var

pipeline = (
    Pipeline()
    .add_to_beginning("banana")
    .delete_first()
    .replace_all_with(pattern="a", text_to_replace="A")
    .add_to_end("!")
    .compile()
)
assert pipeline("é") == "AnAnAé!"

# Rust's variable helpers normalize literal numbers to text automatically.
assert Pipeline().val("count", 2).repeat(get_var("count")).compile()("é") == "éé"

# A callback receives a fresh immutable plan and returns its completed body.
conditional = Pipeline().if_do_contains_each(
    "x", lambda b: b.remove_pattern("x").add_to_end("skipped")
)
assert conditional.compile()("x") == ""
blocks = Pipeline().block_assoc("suffix", lambda b: b.add_to_end("!"))
assert blocks.call_block("suffix").compile()("é") == "é!"
```

Text arguments accept `str | Variable`; counts and indices accept
`int | str | Variable`, where text is a `[[ ]]` expression or `{{ }}` template the
engine resolves when the instruction runs (`on_line("[[__LINES__ - 1]]", ...)`).
`val`, `var` and `mut_var` also accept integer values and follow Rust's conversion
to string-valued context entries. `get_var("name")` is the convenient counterpart
of Rust's helper; `Variable("name")` remains available. Booleans and unsupported
argument types fail immediately. Numbers must fit an unsigned 64-bit integer,
then pass the portable layer's native-size checks.

`iter(times, inner)` accepts a one-instruction `Pipeline`, an `Instruction`
snapshot or a `Variable` reference. It repeats exactly one instruction, as in
Rust; empty plans, multiple instructions and logical groups are rejected. Strings
retain the core's `{{variable}}` and `[[ expression ]]` interpolation semantics.
Indices, ranges and padding follow the Rust operations: every index, line
numbers included, starts at 0, and `insert(0, text)` inserts at the start while
any other index inserts **after** that character. See the
[complete builder method reference](docs/builder-api.md).

`block_assoc` and `if_do_contains_each` accept either a reusable `Pipeline` body
or a callback `(Pipeline) -> Pipeline`. These group callbacks run once during construction;
they are never retained or invoked during processing. Runtime observer callbacks,
described below, are a separate facility. The conditional checks
containment before **each** child, including after preceding children modify text.
Hierarchy validation uses the same core policies. Existing `block` and
`contains_each` subplan methods remain available.

`compile()` produces an independent executable. To register a plan, use
`Processor.register(plan)`; unlike the Rust builder, a Python plan does not borrow
a processor. For the Rust-style registration workflow,
`processor.create_pipeline().trim_both_sides().build()` returns a registered ID.
Such a plan retains its Python processor and can be built repeatedly. Low-level `add(mnemonic, *arguments)` and `Instruction` remain escape
hatches for dynamic DSL integrations; normal fluent construction needs no DSL
mnemonics.

## Errors and files

```python
from pathlib import Path
from textforge import Pipeline, Processor, TextForgeError

processor = Processor()
identifier = processor.register(Pipeline().trim_both_sides())
try:
    processor.process_all("missing", "input")
except TextForgeError as error:
    print(error.stage, error.code, error.message, error.instruction, error.input)

# Export methods create or replace their destination.
path = Path("pipeline.textforge")
processor.write_pipeline_to_file(identifier, path)
restored = processor.get_pipeline_from_file(path)
assert processor.process_all(restored, " é ") == "é"

bytecode = Path("pipeline.textforgebc")
processor.write_to_bytecode_file(identifier, bytecode)
restored_bytecode = processor.read_from_bytecode_file(bytecode)
```

Text pipelines use `.textforge` (or `.tft`) and bytecode `.textforgebc` (or
`.tfb`); bytecode export requires a bytecode extension. Text and input documents are UTF-8.
Paths accept `FilePath`, strings, bytes and `os.PathLike` values, preserving
Unix byte names and Windows UTF-16 names. Unix surrogateescape and Windows
surrogatepass conversion avoid replacing unrepresentable characters. Explicit
`FilePath.from_native_bytes` and `from_windows_wide` reject the other OS
representation rather than converting it with loss. These conversions preserve
path values; the underlying filesystem may still reject a particular filename
(for example, a non-UTF-8 byte name on macOS).

`process_file(identifier, input, output)` creates or overwrites an output document.
`process_batch([(input, identifier, output), ...], threads=0)` runs file tasks in
parallel and returns one `None` or `TextForgeError` per task in input order. Use
distinct output paths. Zero threads selects the engine's automatic worker count.

`Processor` also supports `process_single`, debug execution, `run_transform`,
`clone_pipeline`, `remove_transform`, `transform_exists`, `list_transforms`,
`get_text_transform_vec`, typed `get_transform_vec` snapshots, execution profiles
(`set_profile`/`profile`) and pipeline names (`set_pipeline_name`/`pipeline_name`). See the shipped
PEP 561 annotations and [architecture](docs/architecture.md).

## Build and check

Wheels do not require Rust. Building from source requires Rust 1.89 or newer and
Python 3.10 or newer. Use an empty artifact directory for each release candidate;
older wheels in the same directory are rejected by the distribution validator.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip==26.2.2
python -m pip install --group dev
maturin build --release --locked --sdist --out dist/0.2.0
python -m pip install --force-reinstall --no-deps --no-index --find-links dist/0.2.0 textforgers==0.2.0
python scripts/check.py
python scripts/check_distribution.py --wheel-dir dist/0.2.0 --types
python -m twine check dist/0.2.0/*
```

On Windows, activate the environment with `.venv\Scripts\Activate.ps1` in
PowerShell. The pinned pip version supports the development group; pyproject.toml
pins maturin and the direct test/lint/type/package tools to the verified stable
versions. There are no Python runtime dependencies. Rust dependencies are locked
in Cargo.lock; use `--locked` when building.

Tests import the installed wheel; do not put `python/` on `PYTHONPATH` for wheel
verification. For editable development, use `maturin develop` in the environment.
The distribution validator checks source/wheel/installed version agreement,
typing files, the native import, enabled capabilities and a typed external client.
CI configures CPython 3.10–3.14 on Linux x86_64, Windows x86_64 and macOS arm64
(`macos-15`). Local Linux checks do not establish those remote jobs have passed.

The vendored core makes an independent clone and sdist self-contained without a
parent TextForge checkout. [Release instructions](docs/releasing.md) describe
wheel platforms, trusted publishing, source-package verification, and the steps
that require the maintainer's PyPI account.

See [development record](docs/development.md) for validation history and how to
resume development. GPLv3 license
text is preserved from the core in `LICENSE` and `vendor/textforge/LICENSE`.

## Observers, buffers and worker pools

```python
from tempfile import TemporaryDirectory
from pathlib import Path
from textforge import BufferOptions, Observers, PortableBuffer, Processor, features

processor = Processor()
id = processor.create_pipeline().add_to_end("!").build()
assert features().watchers and features().buffered
with TemporaryDirectory() as directory:
    options = BufferOptions(memory_threshold=1, spill_directory=directory)
    source = PortableBuffer.from_text("é", options)
    with processor.process_all_buffered(id, source) as result:
        assert source.closed
        assert result.into_string() == "é!"
    observers = Observers()
    observers.set_builtin("size", "current_len_chars")
    observers.schedule_all("size")
    assert processor.process_all_with_watchers(
        id, "é", observers, Path(directory) / "report.json"
    ) == "é!"
```

Custom observers accept `(Observation) -> str`; callback exceptions become
structured callback-stage errors. Observers must be used and cleared on their
creating thread; callbacks cannot re-enter the same mutably borrowed processor. `PortableBuffer.from_reader` and `copy_to` use
borrowed synchronous binary streams and preserve partial reads/writes. Buffers
support ranged byte reads, spill inspection, file export and explicit consuming
`into_string`. Buffered processing consumes its input on success or core execution
failure; argument/borrow checks before transfer leave it untouched.
Spill thresholds are placement choices, not hard process memory limits.

Use `with BatchPool(2) as pool` and
`processor.process_batch_in_pool(pool, tasks)` to reuse workers. Tasks can be
`FileTask(input, pipeline_id, output)` records or the existing tuples.
`process_batch_buffered([BufferTask(pipeline_id, input)], options)` returns one
owned buffer or TextForgeError per task.

See [API parity](docs/parity.md), [ownership and concurrency](docs/lifecycle.md),
and [supported configurations](docs/compatibility.md). All fourteen binding rules
and their evidence are tracked in [the compliance record](docs/compliance.md).

## Logical lines (introduced in 0.1.2)

This binding includes TextForge **0.4.0**. Line numbers start at **0**, like every
other index (they started at 1 up to binding 0.1.3):

```python
from textforge import Pipeline

pipeline = (
    Pipeline()
    .delete_empty_lines()
    .unique_lines()
    .join_lines(" | ")
    .compile()
)
assert pipeline("é\n\né\n🍌") == "é | 🍌"
```

See [line operations](docs/lines.md) for every typed method, terminator rules and
error behavior. The exact core commit is pinned in `vendor/CORE_REVISION`.

## Errors that explain themselves (TextForge 0.4.0)

Besides `stage`, `code`, `message`, `instruction` and `input`, every
`TextForgeError` carries the core's details: `kind` (the stable name of the code),
`trace` (`TraceFrame`s, outermost first, with `file:line` and what a container was
doing), `parameters` (`ErrorParameter`s with the values the instruction ran with),
`cause` (the I/O or regex error behind it), `hint`, `ignorable` and the plain-text
`report` that `txf` prints.

```python
from textforge import Pipeline, TextForgeError

try:
    Pipeline().delete_single(9).compile()("abc")
except TextForgeError as error:
    assert error.kind == "IndexOutOfRange"
    assert error.trace[-1].instruction == "dls 9;"
    assert (error.parameters[0].name, error.parameters[0].value) == ("index", "9")
    assert error.ignorable
    print(error.report)
```

## Robust pipelines: try_ignore, sections, files and profiles

`try_ignore(inner)` runs one instruction and, when it fails, continues as if it had
not run (text, variables, blocks and maps are put back). Safety limits are never
ignored. `on_line`, `on_chunk` and `on_line_interval` apply one instruction to a
part of the text, whose indices then count from the start of that part.

```python
from textforge import ExecutionProfile, Pipeline, Processor

robust = (
    Pipeline()
    .try_ignore(Pipeline().delete_single(99))
    .on_line(0, Pipeline().to_uppercase_all())
    .on_line("[[__LINES__ - 1]]", Pipeline().add_to_end("."))
)
assert robust.compile()("title\nbody") == "TITLE\nbody."

processor = Processor()
processor.set_profile(
    ExecutionProfile.balanced().with_limits(max_generated_bytes=1024, max_iterations=None)
)
identifier = processor.register(Pipeline().add_to_end(" ({{__PIPELINE_NAME__}})"))
processor.set_pipeline_name(identifier, "notes")
assert processor.process_all(identifier, "draft") == "draft (notes)"
```

File instructions read and write UTF-8 files while the pipeline runs:
`write_to_file(path)` (the text is unchanged), `append_file`, `prepend_file`,
`insert_file(index, path)` and `pipeline_join(path)`, which runs another text or
bytecode pipeline in a new context (bytecode exports embed it). Relative paths of
pipelines built in Python start from the working directory. Built-in variables
`__LEN_CHARS__`, `__LINES__`, `__TEXTFORGE_VERSION__`, `__PIPELINE_NAME__` and
`__INPUT_FILE__` can be read in `{{ }}` and `[[ ]]`.

## Scoped replacement maps

```python
from textforge import Pipeline, ReplaceMapBuilder

def animals(map: ReplaceMapBuilder) -> None:
    map.add_replace("cat", "wolf").add_replace("wolf", "dog").end()

plan = Pipeline().define_replace_map("animals", animals).execute_replace_map("animals")
assert plan.compile()("cat wolf") == "wolf dog"
```

Configuration runs synchronously once, with a temporary builder. `end()` closes
configuration and does not halt execution. Empty or unfinished definitions and
reuse outside the callback are rejected; callback failures append nothing.
The previous three-argument form remains supported; `add_replace_rule` explicitly
adds a single rule. See [the builder API](docs/builder-api.md).
