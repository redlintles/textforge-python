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
Unlike Rust's borrowing builder, Python plans are independent of processors.

| Method | Parameters |
| --- | --- |
| `add_to_beginning` | `text: str \| Variable` |
| `add_to_end` | `text: str \| Variable` |
| `block_assoc` | `block_name: str, f: PipelineBody` |
| `call_block` | `block_name: str` |
| `capitalize_chunk` | `start_index: int \| Variable, end_index: int \| Variable` |
| `capitalize_first_word` | `` |
| `capitalize_last_word` | `` |
| `capitalize_range` | `start_index: int \| Variable, end_index: int \| Variable` |
| `capitalize_single_word` | `index: int \| Variable` |
| `delete_after` | `index: int \| Variable` |
| `delete_before` | `index: int \| Variable` |
| `delete_chunk` | `start_index: int \| Variable, end_index: int \| Variable` |
| `delete_first` | `` |
| `delete_last` | `` |
| `delete_single` | `index: int \| Variable` |
| `end` | `` |
| `eval` | `expr: str \| Variable, var_name: str \| Variable` |
| `extract_matches_joined` | `pattern: str \| Variable, separator: str \| Variable` |
| `if_do_contains_each` | `value: str, f: PipelineBody` |
| `insert` | `index: int \| Variable, text_to_insert: str \| Variable` |
| `iter` | `times: int \| Variable, inner: Pipeline \| Instruction \| Variable` |
| `join_to_camel_case` | `` |
| `join_to_kebab_case` | `` |
| `join_to_pascal_case` | `` |
| `join_to_snake_case` | `` |
| `mut_var` | `var_name: str \| Variable, var_value: str \| int \| Variable` |
| `pad_left` | `text: str \| Variable, times: int \| Variable` |
| `pad_right` | `text: str \| Variable, times: int \| Variable` |
| `remove_pattern` | `pattern: str \| Variable` |
| `remove_whitespace` | `` |
| `repeat` | `times: int \| Variable` |
| `replace_all_with` | `pattern: str \| Variable, text_to_replace: str \| Variable` |
| `replace_count_with` | `pattern: str \| Variable, text_to_replace: str \| Variable, count: int \| Variable` |
| `replace_first_with` | `pattern: str \| Variable, text_to_replace: str \| Variable` |
| `replace_last_with` | `pattern: str \| Variable, text_to_replace: str \| Variable` |
| `replace_nth_with` | `pattern: str \| Variable, text_to_replace: str \| Variable, index: int \| Variable` |
| `rotate_left` | `times: int \| Variable` |
| `rotate_right` | `times: int \| Variable` |
| `select` | `start_index: int \| Variable, end_index: int \| Variable` |
| `split_characters` | `` |
| `split_select` | `pattern: str \| Variable, index: int \| Variable` |
| `to_html_escaped` | `` |
| `to_html_unescaped` | `` |
| `to_json_escaped` | `` |
| `to_json_unescaped` | `` |
| `to_lowercase_all` | `` |
| `to_lowercase_chunk` | `start_index: int \| Variable, end_index: int \| Variable` |
| `to_lowercase_single` | `index: int \| Variable` |
| `to_lowercase_word` | `index: int \| Variable` |
| `to_reverse` | `` |
| `to_uppercase_all` | `` |
| `to_uppercase_chunk` | `start_index: int \| Variable, end_index: int \| Variable` |
| `to_uppercase_single` | `index: int \| Variable` |
| `to_uppercase_word` | `index: int \| Variable` |
| `to_url_decoded` | `` |
| `to_url_encoded` | `` |
| `trim_both_sides` | `` |
| `trim_left_side` | `` |
| `trim_right_side` | `` |
| `val` | `var_name: str \| Variable, var_value: str \| int \| Variable` |
| `var` | `var_name: str \| Variable, var_value: str \| int \| Variable` |

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
pass an Instruction snapshot. `end` remains available for explicit low-level
construction; group helpers emit their own structural boundaries.

## Values and validation

- Text parameters accept strings or explicit variable references. String
  interpolation and regex semantics remain those of the Rust engine.
- Counts and indices accept nonnegative integers or references. Booleans and
  floats are rejected; literal integers must fit u64 and the target's native size.
- val/var/mut_var convert literal integers to text, as the Rust builder does;
  references remain references. Use eval for expression results.
- Python type and range errors are immediate. Structural policies are validated
  atomically by compile/register. Variable existence and input-dependent errors
  remain execution-time errors.
- Indices and ranges retain Rust semantics. For example, insert places text after
  the indexed character. Parameter names are preserved for keyword arguments.

Existing add(mnemonic, *arguments), Instruction, block and contains_each remain
available for lower-level integrations; ordinary construction uses named methods.

## Maintenance and conformance

Run `python scripts/generate_builder.py` after updating the vendored Rust builder.
This writes normal Python definitions inside the marked section of Pipeline; it
does not install methods dynamically. Generation reads the public Rust signatures
and registry parameter kinds. CI checks the committed output with --check.

Run `python scripts/generate_builder_reference.py` to refresh the separate Rust
reference executable and expected outputs after a reviewed core update. Its 61
cases invoke the real Rust builder, using its documented examples plus logical
operations. --check re-executes it without changing the saved outputs. The special
test-reference Cargo feature is used only for this test oracle, never for wheels.

`python scripts/check.py` verifies generated sources, re-executes the oracle,
compares Python results, and runs lint/type/format/Rust checks. Do not edit saved
expected outputs to accommodate a failing Python adapter.
