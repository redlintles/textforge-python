# Fluent builder API

Pipeline follows the names and argument order of the pinned Rust public builder.
All methods below return a new `Pipeline`, enabling chaining and immutable reuse.
`Variable` is an execution-context reference, conveniently constructed by
`get_var(name)`. Native errors retain their portable code and stage.

```python
from textforge import Pipeline, get_var

plan = Pipeline().add_to_beginning("banana").delete_first().add_to_end("!")
assert plan.compile()("é") == "ananaé!"
assert Pipeline().val("n", 2).repeat(get_var("n")).compile()("é") == "éé"
assert Pipeline().iter(2, Pipeline().add_to_end("!")).compile()("é") == "é!!"
```

The terminal `compile()` returns an independent `CompiledPipeline`. Register a
plan with `Processor.register(plan)` when you need IDs, files or batch processing.
Unlike Rust's borrowing builder, Python plans do not keep a native mutable borrow.
`processor.create_pipeline()` returns a reusable immutable plan retaining that
processor; its terminal `build()` validates/registers and returns an ID. A
standalone `Pipeline` can use `build(processor)`. `push_token(Instruction(...))`
accepts an owned description corresponding to Rust's generic push_token.

`define_replace_map(name, configure)` passes a `ReplaceMapBuilder` to a synchronous
callback. Chain `add_replace(pattern, replacement)` and finish with `end()`.
The callback returns `None`; it is invoked once and never retained. Empty,
unfinished, escaped or double-ended scopes fail without changing the original
immutable pipeline. `end()` emits no pipeline halt instruction. Rules retain
insertion order, variable interpolation and non-cascading engine semantics.
Use `execute_replace_map(name)` to apply them. The old three-argument form remains
supported; `add_replace_rule` is the explicit single-rule operation.

| Method | Parameters |
| --- | --- |
| `define_replace_map` | `name: str \| Variable, configure: ReplaceMapBody` (legacy three-argument form also supported) |
| `add_replace_rule` | `name: str \| Variable, pattern: str \| Variable, replacement: str \| Variable` |
| `add_to_beginning` | `text: str \| Variable` |
| `add_to_end` | `text: str \| Variable` |
| `append_file` | `path: str \| Variable` |
| `append_line` | `text: str \| Variable` |
| `block_assoc` | `block_name: str, f: PipelineBody` |
| `call_block` | `block_name: str` |
| `capitalize_chunk` | `start_index: int \| str \| Variable, end_index: int \| str \| Variable` |
| `capitalize_first_word` | `` |
| `capitalize_last_word` | `` |
| `capitalize_range` | `start_index: int \| str \| Variable, end_index: int \| str \| Variable` |
| `capitalize_single_word` | `index: int \| str \| Variable` |
| `delete_after` | `index: int \| str \| Variable` |
| `delete_before` | `index: int \| str \| Variable` |
| `delete_chunk` | `start_index: int \| str \| Variable, end_index: int \| str \| Variable` |
| `delete_empty_lines` | `` |
| `delete_first` | `` |
| `delete_last` | `` |
| `delete_line` | `line: int \| str \| Variable` |
| `delete_lines_after` | `line: int \| str \| Variable` |
| `delete_lines_before` | `line: int \| str \| Variable` |
| `delete_lines_interval` | `start_line: int \| str \| Variable, end_line: int \| str \| Variable` |
| `delete_lines_matching` | `pattern: str \| Variable` |
| `delete_single` | `index: int \| str \| Variable` |
| `end` | `` |
| `eval` | `expr: str \| Variable, var_name: str \| Variable` |
| `execute_replace_map` | `name: str \| Variable` |
| `extract_matches_joined` | `pattern: str \| Variable, separator: str \| Variable` |
| `if_do_contains_each` | `value: str, f: PipelineBody` |
| `insert` | `index: int \| str \| Variable, text_to_insert: str \| Variable` |
| `insert_file` | `index: int \| str \| Variable, path: str \| Variable` |
| `insert_line` | `line: int \| str \| Variable, text: str \| Variable` |
| `iter` | `times: int \| str \| Variable, inner: Pipeline \| Instruction \| Variable` |
| `join_lines` | `separator: str \| Variable` |
| `join_to_camel_case` | `` |
| `join_to_kebab_case` | `` |
| `join_to_pascal_case` | `` |
| `join_to_snake_case` | `` |
| `keep_lines_matching` | `pattern: str \| Variable` |
| `mut_var` | `var_name: str \| Variable, var_value: str \| int \| Variable` |
| `normalize_unicode` | `mode: str \| Variable` |
| `on_chunk` | `start_index: int \| str \| Variable, end_index: int \| str \| Variable, inner: Pipeline \| Instruction` |
| `on_line` | `line: int \| str \| Variable, inner: Pipeline \| Instruction` |
| `on_line_interval` | `start_line: int \| str \| Variable, end_line: int \| str \| Variable, inner: Pipeline \| Instruction` |
| `pad_left` | `text: str \| Variable, times: int \| str \| Variable` |
| `pad_right` | `text: str \| Variable, times: int \| str \| Variable` |
| `pipeline_join` | `path: str \| Variable` |
| `prepend_file` | `path: str \| Variable` |
| `prepend_line` | `text: str \| Variable` |
| `remove_line_breaks` | `` |
| `remove_pattern` | `pattern: str \| Variable` |
| `remove_whitespace` | `` |
| `repeat` | `times: int \| str \| Variable` |
| `replace_all_with` | `pattern: str \| Variable, text_to_replace: str \| Variable` |
| `replace_count_with` | `pattern: str \| Variable, text_to_replace: str \| Variable, count: int \| str \| Variable` |
| `replace_first_with` | `pattern: str \| Variable, text_to_replace: str \| Variable` |
| `replace_last_with` | `pattern: str \| Variable, text_to_replace: str \| Variable` |
| `replace_line` | `line: int \| str \| Variable, text: str \| Variable` |
| `replace_nth_with` | `pattern: str \| Variable, text_to_replace: str \| Variable, index: int \| str \| Variable` |
| `reverse_lines` | `` |
| `rotate_left` | `times: int \| str \| Variable` |
| `rotate_right` | `times: int \| str \| Variable` |
| `select` | `start_index: int \| str \| Variable, end_index: int \| str \| Variable` |
| `select_lines` | `start_line: int \| str \| Variable, end_line: int \| str \| Variable` |
| `split_characters` | `` |
| `split_select` | `pattern: str \| Variable, index: int \| str \| Variable` |
| `to_html_escaped` | `` |
| `to_html_unescaped` | `` |
| `to_json_escaped` | `` |
| `to_json_unescaped` | `` |
| `to_lowercase_all` | `` |
| `to_lowercase_chunk` | `start_index: int \| str \| Variable, end_index: int \| str \| Variable` |
| `to_lowercase_single` | `index: int \| str \| Variable` |
| `to_lowercase_word` | `index: int \| str \| Variable` |
| `to_reverse` | `` |
| `to_uppercase_all` | `` |
| `to_uppercase_chunk` | `start_index: int \| str \| Variable, end_index: int \| str \| Variable` |
| `to_uppercase_single` | `index: int \| str \| Variable` |
| `to_uppercase_word` | `index: int \| str \| Variable` |
| `to_url_decoded` | `` |
| `to_url_encoded` | `` |
| `trim_both_sides` | `` |
| `trim_left_side` | `` |
| `trim_right_side` | `` |
| `try_ignore` | `inner: Pipeline \| Instruction` |
| `unique_lines` | `` |
| `val` | `var_name: str \| Variable, var_value: str \| int \| Variable` |
| `var` | `var_name: str \| Variable, var_value: str \| int \| Variable` |
| `write_to_file` | `path: str \| Variable` |

## Groups and nested instructions

`block_assoc(block_name, f)` and `if_do_contains_each(value, f)` accept a Pipeline
body or a callable receiving a new Pipeline and returning its completed body.
Return the fluent chain from callbacks: edits produce new immutable plans.
Callbacks run at construction only, and errors propagate without modifying the
source plan. `call_block(block_name)` invokes a previously defined block.

```python
from textforge import Pipeline

suffix = Pipeline().add_to_end("!")
plan = Pipeline().block_assoc("suffix", suffix).call_block("suffix")
assert plan.compile()("é") == "é!"
assert suffix.compile()("x") == "x!"  # The body remains independent.

plan = Pipeline().if_do_contains_each(
    "x", lambda b: b.remove_pattern("x").add_to_end("skipped")
)
assert plan.compile()("x") == ""  # The condition is rechecked before each child.
```

`iter` repeats a single instruction, preserving Rust semantics; it does not accept
multi-step or grouped bodies. Nest an operation as a one-instruction Pipeline or
pass an Instruction snapshot. `try_ignore`, `on_line`, `on_chunk` and
`on_line_interval` take one instruction the same way (a one-instruction Pipeline
or an Instruction, but not a Variable, as Rust's `Into<TokenWrapper>`).

```python
from textforge import Instruction, Pipeline

assert Pipeline().try_ignore(Pipeline().delete_single(9)).compile()("abc") == "abc"
assert Pipeline().on_chunk(1, 2, Instruction("tua")).compile()("abcd") == "aBCd"
```

`end` remains available for explicit low-level
construction; group helpers emit their own structural boundaries.

## Values and validation

- Text parameters accept strings or explicit variable references. String
  interpolation and regex semantics remain those of the Rust engine.
- Counts and indices accept nonnegative integers, references, or text holding a
  `[[ ]]` expression or `{{ }}` template that must give a non-negative integer
  when the instruction runs. Booleans and floats are rejected; literal integers
  must fit u64 and the target's native size. Text that is neither is rejected
  when the plan is compiled.
- val/var/mut_var convert literal integers to text, as the Rust builder does;
  references remain references. Use eval for expression results.
- Python type and range errors are immediate. Structural policies are validated
  atomically by compile/register. Variable existence and input-dependent errors
  remain execution-time errors.
- Indices and ranges retain Rust semantics: all of them, line numbers included,
  start at 0. `insert(0, text)` inserts at the start; any other index inserts
  after that character. Parameter names are preserved for keyword arguments.

Existing add(mnemonic, *arguments), Instruction, block and contains_each remain
available for lower-level integrations; ordinary construction uses named methods.

## Maintenance and conformance

Run `python scripts/generate_builder.py` after updating the vendored Rust builder.
This writes normal Python definitions inside the marked section of Pipeline; it
does not install methods dynamically. Generation reads the public Rust signatures
and registry parameter kinds. CI checks the committed output with --check.

Run `python scripts/generate_builder_reference.py` to refresh the separate Rust
reference executable and expected outputs after a reviewed core update. Its 89
cases invoke the real Rust builder, using its documented examples plus logical
operations. --check re-executes it without changing the saved outputs. The special
test-reference Cargo feature is used only for this test oracle, never for wheels.

`python scripts/check.py` verifies generated sources, re-executes the oracle,
compares Python results, and runs lint/type/format/Rust checks. Do not edit saved
expected outputs to accommodate a failing Python adapter.
