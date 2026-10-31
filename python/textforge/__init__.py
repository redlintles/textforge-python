"""Typed, owned construction and execution of TextForge pipelines.

>>> Pipeline().add_to_beginning("🍌").compile()("é")
'🍌é'
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias

from . import _native
from ._arguments import _instruction, _number, _text, _value
from ._buffers import BufferOptions, PortableBuffer, StreamReader, StreamWriter
from ._native import (
    CompiledPipeline as CompiledPipeline,
)
from ._native import Features, FilePath, Observation, features
from ._native import (
    Instruction as Instruction,
)
from ._native import (
    TextForgeError as TextForgeError,
)
from ._native import (
    Variable as Variable,
)
from ._native import (
    __version__ as __version__,
)
from ._observers import Observers
from ._paths import Path
from ._processor import BatchPool, BufferTask, FileTask, Processor

Argument: TypeAlias = str | int | Variable | Instruction

__all__ = [
    "Argument",
    "BatchPool",
    "BufferOptions",
    "BufferTask",
    "Features",
    "FilePath",
    "FileTask",
    "Observation",
    "Observers",
    "Path",
    "PortableBuffer",
    "StreamReader",
    "StreamWriter",
    "features",
    "CompiledPipeline",
    "Instruction",
    "Pipeline",
    "Processor",
    "TextForgeError",
    "Variable",
    "__version__",
    "get_var",
]


@dataclass(frozen=True, slots=True)
class _Group:
    kind: str
    value: str
    body: Pipeline


@dataclass(frozen=True, slots=True, init=False)
class Pipeline:
    """Immutable pipeline plan. Every edit returns a new independent plan.

    Arguments omit DSL literals such as ``assoc``, ``do`` and ``times``.
    String arguments retain TextForge's interpolation rules.

    >>> plan = Pipeline().trim_both_sides().add_to_end("!")
    >>> plan.compile().process(" é ")
    'é!'
    """

    _nodes: tuple[Instruction | _Group, ...]
    _depth: int
    _processor: Processor | None

    def __init__(self, *instructions: Instruction) -> None:
        if any(not isinstance(item, Instruction) for item in instructions):
            raise TypeError("Pipeline accepts Instruction objects")
        object.__setattr__(self, "_nodes", instructions)
        object.__setattr__(self, "_depth", 0)
        object.__setattr__(self, "_processor", None)

    def _append(self, node: Instruction | _Group) -> Pipeline:
        depth = max(self._depth, node.body._depth + 1) if isinstance(node, _Group) else self._depth
        if depth > 32:
            raise ValueError("pipeline group nesting exceeds 32")
        result = Pipeline()
        object.__setattr__(result, "_nodes", (*self._nodes, node))
        object.__setattr__(result, "_depth", depth)
        object.__setattr__(result, "_processor", self._processor)
        return result

    def _operation(self, name: str, *arguments: Argument) -> Pipeline:
        return self._append(Instruction(name, *arguments))

    # BEGIN GENERATED BUILDER METHODS
    def normalize_unicode(self, mode: str | Variable) -> Pipeline:
        """Normalize the complete text to `nfc`, `nfd`, `nfkc` or `nfkd`. Mode names are
        lowercase and may use execution-context variables.

        Matches Rust ``TextForgeBuilderMethods::normalize_unicode``.
        """
        return self._operation("unorm", _text(mode, "mode"))

    def define_replace_map(
        self, name: str | Variable, pattern: str | Variable, replacement: str | Variable
    ) -> Pipeline:
        """Define replace map.

        Matches Rust ``TextForgeBuilderMethods::define_replace_map``.
        """
        return self._operation(
            "rmapd",
            _text(name, "name"),
            _text(pattern, "pattern"),
            _text(replacement, "replacement"),
        )

    def execute_replace_map(self, name: str | Variable) -> Pipeline:
        """Execute replace map.

        Matches Rust ``TextForgeBuilderMethods::execute_replace_map``.
        """
        return self._operation("rmape", _text(name, "name"))

    def append_line(self, text: str | Variable) -> Pipeline:
        """Append one logical line, preserving the final-terminator convention. Line numbers
        start at one; see the logical-line guide.

        Matches Rust ``TextForgeBuilderMethods::append_line``.
        """
        return self._operation("apl", _text(text, "text"))

    def delete_line(self, line: int | Variable) -> Pipeline:
        """Delete one line, including its terminator. Line numbers start at one; see the
        logical-line guide.

        Matches Rust ``TextForgeBuilderMethods::delete_line``.
        """
        return self._operation("dln", _number(line, "line"))

    def delete_lines_after(self, line: int | Variable) -> Pipeline:
        """Delete lines after the given line, retaining that line and its terminator. Line
        numbers start at one; see the logical-line guide.

        Matches Rust ``TextForgeBuilderMethods::delete_lines_after``.
        """
        return self._operation("dlna", _number(line, "line"))

    def delete_lines_before(self, line: int | Variable) -> Pipeline:
        """Delete lines before the given line, retaining that line. Line numbers start at one;
        see the logical-line guide.

        Matches Rust ``TextForgeBuilderMethods::delete_lines_before``.
        """
        return self._operation("dlnb", _number(line, "line"))

    def select_lines(self, start_line: int | Variable, end_line: int | Variable) -> Pipeline:
        """Select an inclusive line interval and discard the remaining lines. Line numbers
        start at one; see the logical-line guide.

        Matches Rust ``TextForgeBuilderMethods::select_lines``.
        """
        return self._operation(
            "slnc", _number(start_line, "start_line"), _number(end_line, "end_line")
        )

    def delete_lines_interval(
        self, start_line: int | Variable, end_line: int | Variable
    ) -> Pipeline:
        """Delete an inclusive interval of lines and retain the rest. Line numbers start at
        one; see the logical-line guide.

        Matches Rust ``TextForgeBuilderMethods::delete_lines_interval``.
        """
        return self._operation(
            "dlni", _number(start_line, "start_line"), _number(end_line, "end_line")
        )

    def insert_line(self, line: int | Variable, text: str | Variable) -> Pipeline:
        """Insert before a line; line count plus one appends a line. Line numbers start at one;
        see the logical-line guide.

        Matches Rust ``TextForgeBuilderMethods::insert_line``.
        """
        return self._operation("inl", _number(line, "line"), _text(text, "text"))

    def remove_line_breaks(self) -> Pipeline:
        """Remove all recognized line terminators without inserting spaces. Line numbers start
        at one; see the logical-line guide.

        Matches Rust ``TextForgeBuilderMethods::remove_line_breaks``.
        """
        return self._operation("nln")

    def replace_line(self, line: int | Variable, text: str | Variable) -> Pipeline:
        """Replace a line content, preserving its terminator. Line numbers start at one; see
        the logical-line guide.

        Matches Rust ``TextForgeBuilderMethods::replace_line``.
        """
        return self._operation("rln", _number(line, "line"), _text(text, "text"))

    def prepend_line(self, text: str | Variable) -> Pipeline:
        """Prepend one logical line. Line numbers start at one; see the logical-line guide.

        Matches Rust ``TextForgeBuilderMethods::prepend_line``.
        """
        return self._operation("pln", _text(text, "text"))

    def delete_empty_lines(self) -> Pipeline:
        """Delete empty lines; lines containing whitespace are retained. Line numbers start at
        one; see the logical-line guide.

        Matches Rust ``TextForgeBuilderMethods::delete_empty_lines``.
        """
        return self._operation("dle")

    def trim_both_sides(self) -> Pipeline:
        """Removes whitespace characters from both the left and right sides of the input.

        Matches Rust ``TextForgeBuilderMethods::trim_both_sides``.
        """
        return self._operation("tbs")

    def trim_left_side(self) -> Pipeline:
        """Removes whitespace characters exclusively from the left side of the input.

        Matches Rust ``TextForgeBuilderMethods::trim_left_side``.
        """
        return self._operation("tls")

    def trim_right_side(self) -> Pipeline:
        """Removes whitespace characters exclusively from the right side of the input.

        Matches Rust ``TextForgeBuilderMethods::trim_right_side``.
        """
        return self._operation("trs")

    def add_to_end(self, text: str | Variable) -> Pipeline:
        """Appends the provided `text` to the end of the input string.

        Matches Rust ``TextForgeBuilderMethods::add_to_end``.
        """
        return self._operation("ate", _text(text, "text"))

    def add_to_beginning(self, text: str | Variable) -> Pipeline:
        """Inserts the provided `text` at the beginning of the input string.

        Matches Rust ``TextForgeBuilderMethods::add_to_beginning``.
        """
        return self._operation("atb", _text(text, "text"))

    def delete_first(self) -> Pipeline:
        """Removes the first character of the input string.

        Matches Rust ``TextForgeBuilderMethods::delete_first``.
        """
        return self._operation("dlf")

    def delete_last(self) -> Pipeline:
        """Removes the last character of the input string.

        Matches Rust ``TextForgeBuilderMethods::delete_last``.
        """
        return self._operation("dll")

    def delete_after(self, index: int | Variable) -> Pipeline:
        """Removes all characters after the provided `index`, keeping the content from
        `0..=index`.

        Matches Rust ``TextForgeBuilderMethods::delete_after``.
        """
        return self._operation("dla", _number(index, "index"))

    def delete_before(self, index: int | Variable) -> Pipeline:
        """Removes all characters before the provided `index`, keeping the content from
        `index..`.

        Matches Rust ``TextForgeBuilderMethods::delete_before``.
        """
        return self._operation("dlb", _number(index, "index"))

    def delete_chunk(self, start_index: int | Variable, end_index: int | Variable) -> Pipeline:
        """Removes all characters between `start_index` and `end_index` (inclusive),
        effectively slicing out that segment from the input string.

        Matches Rust ``TextForgeBuilderMethods::delete_chunk``.
        """
        return self._operation(
            "dlc", _number(start_index, "start_index"), _number(end_index, "end_index")
        )

    def replace_all_with(
        self, pattern: str | Variable, text_to_replace: str | Variable
    ) -> Pipeline:
        """Replaces all occurrences of `pattern` with `text_to_replace`.

        Matches Rust ``TextForgeBuilderMethods::replace_all_with``.
        """
        return self._operation(
            "raw", _text(pattern, "pattern"), _text(text_to_replace, "text_to_replace")
        )

    def replace_first_with(
        self, pattern: str | Variable, text_to_replace: str | Variable
    ) -> Pipeline:
        """Replaces only the first occurrence of `pattern` with `text_to_replace`.

        Matches Rust ``TextForgeBuilderMethods::replace_first_with``.
        """
        return self._operation(
            "rfw", _text(pattern, "pattern"), _text(text_to_replace, "text_to_replace")
        )

    def replace_last_with(
        self, pattern: str | Variable, text_to_replace: str | Variable
    ) -> Pipeline:
        """Replaces only the last occurrence of `pattern` with `text_to_replace`.

        Matches Rust ``TextForgeBuilderMethods::replace_last_with``.
        """
        return self._operation(
            "rlw", _text(pattern, "pattern"), _text(text_to_replace, "text_to_replace")
        )

    def replace_nth_with(
        self, pattern: str | Variable, text_to_replace: str | Variable, index: int | Variable
    ) -> Pipeline:
        """Replaces the nth occurrence (0-based) of `pattern` with `text_to_replace`. If the
        index does not exist, no changes occur.

        Matches Rust ``TextForgeBuilderMethods::replace_nth_with``.
        """
        return self._operation(
            "rnw",
            _text(pattern, "pattern"),
            _text(text_to_replace, "text_to_replace"),
            _number(index, "index"),
        )

    def replace_count_with(
        self, pattern: str | Variable, text_to_replace: str | Variable, count: int | Variable
    ) -> Pipeline:
        """Replaces up to count occurrences of `pattern` with `text_to_replace`, scanning from
        left to right.

        Matches Rust ``TextForgeBuilderMethods::replace_count_with``.
        """
        return self._operation(
            "rcw",
            _text(pattern, "pattern"),
            _text(text_to_replace, "text_to_replace"),
            _number(count, "count"),
        )

    def rotate_left(self, times: int | Variable) -> Pipeline:
        """Rotates the characters of the input to the left `times` positions.

        Matches Rust ``TextForgeBuilderMethods::rotate_left``.
        """
        return self._operation("rtl", _number(times, "times"))

    def rotate_right(self, times: int | Variable) -> Pipeline:
        """Rotates the characters of the input to the right `times` positions.

        Matches Rust ``TextForgeBuilderMethods::rotate_right``.
        """
        return self._operation("rtr", _number(times, "times"))

    def repeat(self, times: int | Variable) -> Pipeline:
        """Repeats the entire input string `times` times.

        Matches Rust ``TextForgeBuilderMethods::repeat``.
        """
        return self._operation("rpt", _number(times, "times"))

    def select(self, start_index: int | Variable, end_index: int | Variable) -> Pipeline:
        """Extracts a substring from `start_index` to `end_index` (inclusive).

        Matches Rust ``TextForgeBuilderMethods::select``.
        """
        return self._operation(
            "slt", _number(start_index, "start_index"), _number(end_index, "end_index")
        )

    def to_uppercase_all(self) -> Pipeline:
        """Converts all characters of the input string to uppercase.

        Matches Rust ``TextForgeBuilderMethods::to_uppercase_all``.
        """
        return self._operation("tua")

    def to_lowercase_all(self) -> Pipeline:
        """Converts all characters of the input string to lowercase.

        Matches Rust ``TextForgeBuilderMethods::to_lowercase_all``.
        """
        return self._operation("tla")

    def to_uppercase_single(self, index: int | Variable) -> Pipeline:
        """Converts only the character at `index` to uppercase. If the index is out of range,
        no character is modified.

        Matches Rust ``TextForgeBuilderMethods::to_uppercase_single``.
        """
        return self._operation("tucs", _number(index, "index"))

    def to_lowercase_single(self, index: int | Variable) -> Pipeline:
        """Converts only the character at `index` to lowercase. If the index is out of range,
        no character is modified.

        Matches Rust ``TextForgeBuilderMethods::to_lowercase_single``.
        """
        return self._operation("tlcs", _number(index, "index"))

    def to_uppercase_chunk(
        self, start_index: int | Variable, end_index: int | Variable
    ) -> Pipeline:
        """Converts a substring between `start_index` and `end_index` (inclusive) to uppercase.
        Returns an error if the indices are invalid.

        Matches Rust ``TextForgeBuilderMethods::to_uppercase_chunk``.
        """
        return self._operation(
            "tucc", _number(start_index, "start_index"), _number(end_index, "end_index")
        )

    def to_lowercase_chunk(
        self, start_index: int | Variable, end_index: int | Variable
    ) -> Pipeline:
        """Converts a substring between `start_index` and `end_index` (inclusive) to lowercase.
        Returns an error if the indices are invalid.

        Matches Rust ``TextForgeBuilderMethods::to_lowercase_chunk``.
        """
        return self._operation(
            "tlcc", _number(start_index, "start_index"), _number(end_index, "end_index")
        )

    def capitalize_first_word(self) -> Pipeline:
        """Capitalizes the first word of the input string. A 'word' is defined as the first
        contiguous sequence of non-whitespace characters.

        Matches Rust ``TextForgeBuilderMethods::capitalize_first_word``.
        """
        return self._operation("cfw")

    def capitalize_last_word(self) -> Pipeline:
        """Capitalizes the last word of the input string.

        Matches Rust ``TextForgeBuilderMethods::capitalize_last_word``.
        """
        return self._operation("clw")

    def split_select(self, pattern: str | Variable, index: int | Variable) -> Pipeline:
        """Splits the input string using `pattern` and selects the part at `index`. If the
        index does not exist, returns an empty string.

        Matches Rust ``TextForgeBuilderMethods::split_select``.
        """
        return self._operation("sslt", _text(pattern, "pattern"), _number(index, "index"))

    def capitalize_chunk(self, start_index: int | Variable, end_index: int | Variable) -> Pipeline:
        """Capitalizes the substring between `start_index` and `end_index` (inclusive). Returns
        an error if the indices are invalid.

        Matches Rust ``TextForgeBuilderMethods::capitalize_chunk``.
        """
        return self._operation(
            "ctc", _number(start_index, "start_index"), _number(end_index, "end_index")
        )

    def capitalize_range(self, start_index: int | Variable, end_index: int | Variable) -> Pipeline:
        """Capitalizes all characters in `input` from `start_index` (inclusive) to `end_index`
        (exclusive). If the indices are invalid, an `TextForgeError` is returned at build-
        time.

        Matches Rust ``TextForgeBuilderMethods::capitalize_range``.
        """
        return self._operation(
            "ctr", _number(start_index, "start_index"), _number(end_index, "end_index")
        )

    def capitalize_single_word(self, index: int | Variable) -> Pipeline:
        """Capitalizes the word located at the given `index` in `input`. Words are delimited
        according to Unicode whitespace rules.

        Matches Rust ``TextForgeBuilderMethods::capitalize_single_word``.
        """
        return self._operation("cts", _number(index, "index"))

    def to_url_encoded(self) -> Pipeline:
        """Converts the entire `input` string into its URL-encoded form according to RFC 3986
        percent-encoding rules.

        Matches Rust ``TextForgeBuilderMethods::to_url_encoded``.
        """
        return self._operation("urle")

    def to_url_decoded(self) -> Pipeline:
        """Decodes a URL-encoded string into its normal representation. Invalid percent-encoded
        sequences remain unchanged.

        Matches Rust ``TextForgeBuilderMethods::to_url_decoded``.
        """
        return self._operation("urld")

    def to_reverse(self) -> Pipeline:
        """Reverses all characters in the input string.

        Matches Rust ``TextForgeBuilderMethods::to_reverse``.
        """
        return self._operation("rev")

    def split_characters(self) -> Pipeline:
        """Splits the entire input string into individual characters separated by spaces.
        Grapheme clusters are preserved (Unicode-aware).

        Matches Rust ``TextForgeBuilderMethods::split_characters``.
        """
        return self._operation("splc")

    def to_html_escaped(self) -> Pipeline:
        """Escapes HTML special characters such as `<`, `>`, `'`, `'`, `&`. Useful for
        preventing HTML injection or rendering raw text.

        Matches Rust ``TextForgeBuilderMethods::to_html_escaped``.
        """
        return self._operation("htmle")

    def to_html_unescaped(self) -> Pipeline:
        """Converts HTML escaped entities back into their literal characters. Example: `'&lt;'
        → '<'`

        Matches Rust ``TextForgeBuilderMethods::to_html_unescaped``.
        """
        return self._operation("htmlu")

    def to_json_escaped(self) -> Pipeline:
        """Escapes JSON characters of `string``

        Matches Rust ``TextForgeBuilderMethods::to_json_escaped``.
        """
        return self._operation("jsone")

    def to_json_unescaped(self) -> Pipeline:
        """Unescapes JSON characters of `string``

        Matches Rust ``TextForgeBuilderMethods::to_json_unescaped``.
        """
        return self._operation("jsonu")

    def insert(self, index: int | Variable, text_to_insert: str | Variable) -> Pipeline:
        """Inserts `text` after `index` of `string`

        Matches Rust ``TextForgeBuilderMethods::insert``.
        """
        return self._operation(
            "ins", _number(index, "index"), _text(text_to_insert, "text_to_insert")
        )

    def to_lowercase_word(self, index: int | Variable) -> Pipeline:
        """Lowercases a single word of `string`

        Matches Rust ``TextForgeBuilderMethods::to_lowercase_word``.
        """
        return self._operation("tlcw", _number(index, "index"))

    def to_uppercase_word(self, index: int | Variable) -> Pipeline:
        """Uppercases a single word of `string`

        Matches Rust ``TextForgeBuilderMethods::to_uppercase_word``.
        """
        return self._operation("tucw", _number(index, "index"))

    def join_to_kebab_case(self) -> Pipeline:
        """If `input` is a string whose words are separated by spaces, join `input` as a
        lowercased kebab-case string

        Matches Rust ``TextForgeBuilderMethods::join_to_kebab_case``.
        """
        return self._operation("jkbc")

    def join_to_snake_case(self) -> Pipeline:
        """If `input` is a string whose words are separated by spaces, join `input` as a
        lowercased snake_case string

        Matches Rust ``TextForgeBuilderMethods::join_to_snake_case``.
        """
        return self._operation("jsnc")

    def join_to_camel_case(self) -> Pipeline:
        """If `input` is a string whose words are separated by spaces, join `input` as a
        camelCase string

        Matches Rust ``TextForgeBuilderMethods::join_to_camel_case``.
        """
        return self._operation("jcmc")

    def join_to_pascal_case(self) -> Pipeline:
        """If `input` is a string whose words are separated by spaces, join `input` as a
        camelCase string

        Matches Rust ``TextForgeBuilderMethods::join_to_pascal_case``.
        """
        return self._operation("jpsc")

    def pad_left(self, text: str | Variable, times: int | Variable) -> Pipeline:
        """Repeats `text` characters until `max_len` is reached, and then insert the result at
        the start of `input`

        Matches Rust ``TextForgeBuilderMethods::pad_left``.
        """
        return self._operation("padl", _text(text, "text"), _number(times, "times"))

    def pad_right(self, text: str | Variable, times: int | Variable) -> Pipeline:
        """Repeats `text` characters until `max_len` is reached, and then insert the result at
        the end of `input`

        Matches Rust ``TextForgeBuilderMethods::pad_right``.
        """
        return self._operation("padr", _text(text, "text"), _number(times, "times"))

    def remove_whitespace(self) -> Pipeline:
        """Removes all whitespaces in `input`

        Matches Rust ``TextForgeBuilderMethods::remove_whitespace``.
        """
        return self._operation("rmws")

    def delete_single(self, index: int | Variable) -> Pipeline:
        """Delete's a single character specified by `index` in `input`

        Matches Rust ``TextForgeBuilderMethods::delete_single``.
        """
        return self._operation("dls", _number(index, "index"))

    def extract_matches_joined(
        self, pattern: str | Variable, separator: str | Variable
    ) -> Pipeline:
        """Extract all non-overlapping matches in input and join them with a separator,
        discarding the rest of the `input`

        Matches Rust ``TextForgeBuilderMethods::extract_matches_joined``.
        """
        return self._operation("emj", _text(pattern, "pattern"), _text(separator, "separator"))

    def val(self, var_name: str | Variable, var_value: str | int | Variable) -> Pipeline:
        """Store's an Immutable Variable in GlobalExecutionContext

        Matches Rust ``TextForgeBuilderMethods::val``.
        """
        return self._operation("val", _text(var_name, "var_name"), _value(var_value, "var_value"))

    def var(self, var_name: str | Variable, var_value: str | int | Variable) -> Pipeline:
        """Store's an mutable Variable in GlobalExecutionContext

        Matches Rust ``TextForgeBuilderMethods::var``.
        """
        return self._operation("var", _text(var_name, "var_name"), _value(var_value, "var_value"))

    def mut_var(self, var_name: str | Variable, var_value: str | int | Variable) -> Pipeline:
        """Assign a new value to a mutable execution-context variable.

        Matches Rust ``TextForgeBuilderMethods::mut_var``.
        """
        return self._operation("mutv", _text(var_name, "var_name"), _value(var_value, "var_value"))

    def eval(self, expr: str | Variable, var_name: str | Variable) -> Pipeline:
        """Evaluate an expression and store its result in the named variable.

        Matches Rust ``TextForgeBuilderMethods::eval``.
        """
        return self._operation("eval", _text(expr, "expr"), _text(var_name, "var_name"))

    def iter(self, times: int | Variable, inner: Pipeline | Instruction | Variable) -> Pipeline:
        """Run one inner instruction repeatedly, using the Rust iter semantics.

        Matches Rust ``TextForgeBuilderMethods::iter``.
        """
        return self._operation("iter", _number(times, "times"), _instruction(inner, "inner"))

    def remove_pattern(self, pattern: str | Variable) -> Pipeline:
        """Remove every match of the pattern from the input.

        Matches Rust ``TextForgeBuilderMethods::remove_pattern``.
        """
        return self._operation("rmp", _text(pattern, "pattern"))

    def end(self) -> Pipeline:
        """End the current logical group, subject to core structural validation.

        Matches Rust ``TextForgeBuilderMethods::end``.
        """
        return self._operation("end")

    # END GENERATED BUILDER METHODS

    def add(self, name: str, *arguments: Argument) -> Pipeline:
        """Low-level mnemonic escape hatch; prefer named fluent methods for normal use."""
        return self._operation(name, *arguments)

    def block(self, name: str, body: Pipeline) -> Pipeline:
        """Define a reusable block without consuming or modifying its body."""
        if not isinstance(name, str):
            raise TypeError("name must be str")
        if not isinstance(body, Pipeline):
            raise TypeError("body must be a Pipeline")
        return self._append(_Group("block", name, body))

    def contains_each(self, pattern: str, body: Pipeline) -> Pipeline:
        """Re-evaluate containment before each child, as in the portable Rust API."""
        if not isinstance(pattern, str):
            raise TypeError("pattern must be str")
        if not isinstance(body, Pipeline):
            raise TypeError("body must be a Pipeline")
        return self._append(_Group("contains_each", pattern, body))

    def block_assoc(self, block_name: str, f: PipelineBody) -> Pipeline:
        """Define a block using a subplan or a callback returning a subplan.

        Mirrors the Rust block builder; callbacks run once during construction.

        >>> Pipeline().block_assoc("suffix", lambda b: b.add_to_end("!")).call_block(
        ...     "suffix"
        ... ).compile()("é")
        'é!'
        """
        return self.block(block_name, _body(f))

    def if_do_contains_each(self, value: str, f: PipelineBody) -> Pipeline:
        """Check containment before each child, following the Rust conditional builder.

        >>> Pipeline().if_do_contains_each(
        ...     "x", lambda b: b.remove_pattern("x").add_to_end("skipped")
        ... ).compile()("x")
        ''
        """
        return self.contains_each(value, _body(f))

    def call_block(self, block_name: str) -> Pipeline:
        """Call a block, following Rust ``TextForgeBlockMethods::call_block``."""
        if not isinstance(block_name, str):
            raise TypeError("block_name must be str")
        return self._operation("cblk", block_name)

    def _lower(self) -> _native.Plan:
        plan = _native.Plan()
        for node in self._nodes:
            if isinstance(node, Instruction):
                plan.add(node)
            elif node.kind == "block":
                plan.block(node.value, node.body._lower())
            else:
                plan.contains_each(node.value, node.body._lower())
        return plan

    def compile(self) -> CompiledPipeline:
        """Validate atomically and create an executable with fresh context per call."""
        return self._lower().compile()

    def push_token(self, instruction: Instruction) -> Pipeline:
        """Append an owned description, corresponding to Rust's push_token."""
        if not isinstance(instruction, Instruction):
            raise TypeError("instruction must be an Instruction")
        return self._append(instruction)

    def build(self, processor: Processor | None = None) -> str:
        """Validate/register this reusable plan; return a new pipeline ID each time.

        create_pipeline() binds a processor; standalone plans must supply one.
        """
        target = processor if processor is not None else self._processor
        if target is None:
            raise ValueError("build requires a processor; use processor.create_pipeline()")
        return target.register(self)


PipelineBody: TypeAlias = Pipeline | Callable[[Pipeline], Pipeline]


def _body(value: PipelineBody) -> Pipeline:
    if isinstance(value, Pipeline):
        return value
    if not callable(value):
        raise TypeError("body must be a Pipeline or a callback returning a Pipeline")
    result = value(Pipeline())
    if not isinstance(result, Pipeline):
        raise TypeError("body callback must return a Pipeline; fluent edits return new plans")
    return result


def get_var(var_name: str) -> Variable:
    """Reference a context variable, following the Rust ``get_var`` helper.

    >>> Pipeline().val("n", 2).repeat(get_var("n")).compile()("é")
    'éé'
    """
    return Variable(var_name)
