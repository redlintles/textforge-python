# Logical lines

Version 0.1.2 exposes all sixteen TextForge 0.2.0 line transforms through explicit,
typed `Pipeline` methods. Names and argument order mirror the public Rust builder:

| DSL | Python method |
| --- | --- |
| apl | append_line(text) |
| dln | delete_line(line) |
| dlna | delete_lines_after(line) |
| dlnb | delete_lines_before(line) |
| slnc | select_lines(start_line, end_line) |
| dlni | delete_lines_interval(start_line, end_line) |
| inl | insert_line(line, text) |
| nln | remove_line_breaks() |
| rln | replace_line(line, text) |
| pln | prepend_line(text) |
| dle | delete_empty_lines() |
| klm | keep_lines_matching(pattern) |
| dlm | delete_lines_matching(pattern) |
| revln | reverse_lines() |
| uniqln | unique_lines() |
| joinln | join_lines(separator) |

Numbers accept `int | Variable`; text accepts `str | Variable`. Negative,
oversized and non-integer values retain the adapter's checked conversions.
Line zero, absent lines and inverted ranges produce the portable engine error
with its code, stage, message, instruction and input. Input-dependent and bound
parameter errors occur at execution. No line validation is duplicated in Python.

The [vendored core guide](../vendor/textforge/docs/lines.md) specifies terminators,
empty input, empty lines, EOF, insertion payloads, regex matching and exact Unicode
comparison. Filtering is per logical line, without its terminator. `dle` removes
empty lines only; whitespace-only lines remain. Normalize explicitly before
`unique_lines` when canonical equivalence is desired.

Plans and compiled pipelines keep their existing ownership, concurrency and
resource-release guarantees. These operations introduce no foreign callbacks.
Buffered processing uses the core whole-document fallback. Text and bytecode
persistence continue through the portable processor. Independent native fixtures
and installed-artifact tests cover these methods; the exact core snapshot and
supported runtime/platform matrix are recorded in the compatibility guide.
