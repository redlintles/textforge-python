# TextForge for Python

Typed Python bindings for [TextForge](https://github.com/redlintles/textforge),
implemented with PyO3 against its owned portable API. Distribution name:
`textforgers`; Python import: `textforge`. Requires Python 3.10 or newer.

This repository prepares the first Python release; it has not been published yet.
Once published, installation is `pip install textforgers`. Do not install the
unrelated `textforge` distribution as a substitute.

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

Text arguments accept `str | Variable`; counts and indices accept `int | Variable`.
`val`, `var` and `mut_var` also accept integer values and follow Rust's conversion
to string-valued context entries. `get_var("name")` is the convenient counterpart
of Rust's helper; `Variable("name")` remains available. Booleans and unsupported
argument types fail immediately. Numbers must fit an unsigned 64-bit integer,
then pass the portable layer's native-size checks.

`iter(times, inner)` accepts a one-instruction `Pipeline`, an `Instruction`
snapshot or a `Variable` reference. It repeats exactly one instruction, as in
Rust; empty plans, multiple instructions and logical groups are rejected. Strings
retain the core's `{{variable}}` and `[[ expression ]]` interpolation semantics.
Indices, ranges and padding follow the Rust operations, including `insert`
inserting **after** the indexed character. See the
[complete builder method reference](docs/builder-api.md).

`block_assoc` and `if_do_contains_each` accept either a reusable `Pipeline` body
or a callback `(Pipeline) -> Pipeline`. Callbacks run once during construction;
they are never retained or invoked during processing. The conditional checks
containment before **each** child, including after preceding children modify text.
Hierarchy validation uses the same core policies. Existing `block` and
`contains_each` subplan methods remain available.

`compile()` produces an independent executable. To register a plan, use
`Processor.register(plan)`; unlike the Rust builder, a Python plan does not borrow
a processor. Low-level `add(mnemonic, *arguments)` and `Instruction` remain escape
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

# Current core export methods require existing destinations. They overwrite files.
path = Path("pipeline.textforge")
path.touch(exist_ok=True)
processor.write_pipeline_to_file(identifier, path)
restored = processor.get_pipeline_from_file(path)
assert processor.process_all(restored, " é ") == "é"

bytecode = Path("pipeline.textforgebc")
bytecode.touch(exist_ok=True)
processor.write_to_bytecode_file(identifier, bytecode)
restored_bytecode = processor.read_from_bytecode_file(bytecode)
```

The implementation uses the actual core extensions `.textforge` and
`.textforgebc`. Some older project notes mention `.tft`/`.tfb`; those are not the
current core's export/import contract. Text and input documents are UTF-8.
Paths accept strings and `os.PathLike[str]` (`pathlib.Path`), with Unicode names.
The initial adapter accepts Unicode-encodable path strings; native byte paths and
surrogate-containing paths are not exposed yet.

`process_file(identifier, input, output)` creates or overwrites an output document.
`process_batch([(input, identifier, output), ...], threads=0)` runs file tasks in
parallel and returns one `None` or `TextForgeError` per task in input order. Use
distinct output paths. Zero threads selects the engine's automatic worker count.

`Processor` also supports `process_single`, debug execution, `run_transform`,
`clone_pipeline`, `remove_transform`, `transform_exists`, `list_transforms`,
`get_text_transform_vec`, and typed `get_transform_vec` snapshots. See the shipped
PEP 561 annotations and [architecture](docs/architecture.md).

## Build and check

A Rust toolchain supporting edition 2024 and a Python development environment are
required for source builds. Published wheels will not require Rust.

```sh
python3 -m venv .venv
# POSIX; on Windows use .venv\Scripts\activate
. .venv/bin/activate
pip install --group dev
maturin build --locked --out dist
pip install --force-reinstall --no-deps --no-index --find-links dist textforgers
python scripts/check.py
maturin build --release --locked --sdist --out dist
python -m twine check dist/*
```

Use a current pip that supports dependency groups, or install the development
tools explicitly: `pip install maturin pytest ruff mypy build twine`. Tests import
the installed wheel; do not put `python/` on `PYTHONPATH` for wheel verification.
For editable development use `maturin develop` in the virtual environment.

The vendored core makes an independent clone and sdist self-contained without a
parent TextForge checkout. [Release instructions](docs/releasing.md) describe
wheel platforms, trusted publishing, source-package verification, and the steps
that require the maintainer's PyPI account.

See [development record](docs/development.md) for implemented coverage, validation,
remaining portable capabilities, and how to resume development. GPLv3 license
text is preserved from the core in `LICENSE` and `vendor/textforge/LICENSE`.
