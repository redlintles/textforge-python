# TextForge for Python

Typed Python bindings for [TextForge](https://github.com/redlintles/textforge),
implemented with PyO3 against its owned portable API. Distribution name:
`textforge-python`; Python import: `textforge`. Requires Python 3.10 or newer.

This repository prepares the first Python release; it has not been published yet.
Once published, installation is `pip install textforge-python`. Do not install the
unrelated `textforge` distribution as a substitute.

```python
from textforge import Pipeline, Processor, Instruction, Variable

plan = Pipeline().add("tbs").add("atb", "🍌 ").add("ate", "!")
pipeline = plan.compile()
assert pipeline.process(" é ") == "🍌 é!"
assert pipeline("fruit") == "🍌 fruit!"

# Edits return a new plan. Both the source and compiled pipelines stay reusable.
assert Pipeline().compile()("unchanged") == "unchanged"
repeated = Pipeline().add("iter", 2, Instruction("ate", "!"))
assert repeated.compile()("é") == "é!!"

# Arguments omit DSL syntax words (assoc, do, times).
variables = Pipeline().add("val", "n", "2").add("rpt", Variable("n"))
assert variables.compile()("é") == "éé"

body = Pipeline().add("ate", "!")
blocks = Pipeline().block("greeting", body).call_block("greeting")
assert blocks.compile()("hello") == "hello!"

processor = Processor()
identifier = processor.register(plan)
assert processor.process_all(identifier, " é ") == "🍌 é!"
```

`Pipeline.contains_each(pattern, body)` checks containment before **each** child,
including after preceding children modify the text. Blocks and conditionals follow
the core's hierarchy validation. Strings keep the core's `{{variable}}` and
`[[ expression ]]` interpolation semantics. Numeric arguments are unsigned 64-bit
integers, further checked against the target's native size by the portable API.
Booleans, floats, negative integers and unsupported argument objects are rejected.

## Errors and files

```python
from pathlib import Path
from textforge import Pipeline, Processor, TextForgeError

processor = Processor()
identifier = processor.register(Pipeline().add("tbs"))
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
pip install --force-reinstall --no-deps --no-index --find-links dist textforge-python
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
